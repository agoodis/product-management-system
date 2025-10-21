import pandas as pd
from sqlalchemy.orm import Session
from app.models.product import Product, MarketplaceData, ImportLog
from typing import Dict, Any
import re
import os
import traceback
import tempfile
from openpyxl import load_workbook
from datetime import datetime

# --- ДОБАВЛЕНО: безопасный парсер XLSX без чтения styles.xml ---
import zipfile
import xml.etree.ElementTree as ET


def safe_read_xlsx_sheet_as_dataframe(xlsx_path: str, sheet_index: int = 1, header_row_index: int = 1) -> pd.DataFrame:
    """
    Читает указанный лист XLSX БЕЗ парсинга styles.xml (устойчиво к битым стилям).
    sheet_index — 0-базовый индекс листа (1 = второй лист).
    header_row_index — 0-базовый индекс строки заголовков (1 = вторая строка).
    Возвращает pandas.DataFrame.
    """
    with zipfile.ZipFile(xlsx_path) as z:
        # 1) sharedStrings
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            root = ET.parse(z.open("xl/sharedStrings.xml")).getroot()
            for si in root:
                parts = []
                for t in si.iter():
                    if t.tag.endswith('t') and t.text is not None:
                        parts.append(t.text)
                shared.append("".join(parts))

        # 2) определяем файл листа по индексу (обычно sheet{n}.xml)
        sheet_path = f"xl/worksheets/sheet{sheet_index + 1}.xml"
        if sheet_path not in z.namelist():
            # Попробуем найти через workbook.xml (на случай нестандартного порядка)
            wb_root = ET.parse(z.open("xl/workbook.xml")).getroot()
            ns = wb_root.tag.split('}')[0].strip('{')
            nsmap = {"ns": ns}
            sheets = wb_root.find("ns:sheets", nsmap)
            sheet_elems = list(sheets) if sheets is not None else []
            if len(sheet_elems) <= sheet_index:
                raise FileNotFoundError("Файл содержит меньше двух листов или не удалось определить sheet2.xml")
            # В большинстве случаев файл всё равно sheet{n}.xml
            if sheet_path not in z.namelist():
                raise FileNotFoundError(f"Не найден {sheet_path} в архиве XLSX.")

        root = ET.parse(z.open(sheet_path)).getroot()
        ns = root.tag.split('}')[0].strip('{')
        nsmap = {"ns": ns}
        sheet_data = root.find("ns:sheetData", nsmap)
        if sheet_data is None:
            return pd.DataFrame()

        def col_letters_to_idx(letters: str) -> int:
            v = 0
            for ch in letters:
                if ch.isalpha():
                    v = v * 26 + (ord(ch.upper()) - ord('A') + 1)
            return v - 1

        rows, max_col = [], -1
        for r in sheet_data.findall("ns:row", nsmap):
            cells = {}
            for c in r.findall("ns:c", nsmap):
                r_addr = c.attrib.get("r", "")
                col_letters = "".join(ch for ch in r_addr if ch.isalpha())
                col_idx = col_letters_to_idx(col_letters) if col_letters else None
                v = c.find("ns:v", nsmap)
                t = c.attrib.get("t")
                text = ""
                if t == "s" and v is not None and v.text:
                    idx = int(v.text)
                    text = shared[idx] if 0 <= idx < len(shared) else ""
                elif t == "inlineStr":
                    is_elem = c.find("ns:is", nsmap)
                    if is_elem is not None:
                        parts = []
                        for n in is_elem.iter():
                            if n.tag.endswith('t') and n.text is not None:
                                parts.append(n.text)
                        text = "".join(parts)
                else:
                    text = v.text if v is not None and v.text is not None else ""
                if col_idx is not None:
                    cells[col_idx] = text
                    if col_idx > max_col:
                        max_col = col_idx
            row_vals = [cells.get(i, "") for i in range(max_col + 1)] if max_col >= 0 else []
            rows.append(row_vals)

        if not rows:
            return pd.DataFrame()

        # применяем header_row_index как в вашем коде (header=1 => заголовок во второй строке)
        if len(rows) <= header_row_index:
            return pd.DataFrame(rows)

        header = [str(x).strip() for x in rows[header_row_index]]
        data = rows[header_row_index + 1:]
        # На случай, если строки короче заголовка
        max_len = max((len(r) for r in data), default=0)
        header = header[:max_len]
        data = [r[:max_len] + [""] * (max_len - len(r)) for r in data]
        df = pd.DataFrame(data, columns=header).fillna("")
        return df


class ImportService:
    def __init__(self, db: Session):
        self.db = db
    
    def import_1c_data(self, file_path: str) -> ImportLog:
        """Импорт данных из 1С с детальным логированием ошибок"""
        try:
            df = pd.read_excel(file_path, dtype=str).fillna('')  # Читаем все как строки
            df.columns = df.columns.str.strip()
            
            records_processed = 0
            records_added = 0
            records_updated = 0
            records_failed = 0
            error_details = []  # Список для хранения деталей ошибок

            for index, row in df.iterrows():
                try:
                    barcode = str(row.get('ШК', '')).strip()
                    if not barcode:
                        # Если штрихкода нет, это критическая ошибка для строки
                        raise ValueError("Штрихкод (ШК) отсутствует или пуст")
                    
                    # Проверяем существование товара
                    product = self.db.query(Product).filter(
                        Product.barcode == barcode
                    ).first()
                    
                    product_data = {
                        'barcode': barcode,
                        'article_1c': str(row.get('Артикул', '')).strip(),
                        'name': str(row.get('Номенклатура', '')).strip(),
                        'unit': str(row.get('Ед.', '')).strip(),
                        'brand': str(row.get('Свойство: Фирма', '')).strip(),
                        'product_type': str(row.get('Свойство: Вид товара', '')).strip(),
                        'product_category': str(row.get('Свойство: Тип товара', '')).strip(),
                        'collection': str(row.get('Свойство: Коллекция', '')).strip(),
                        'season': str(row.get('Свойство: Сезон', '')).strip(),
                        'size': str(row.get('Свойство: Размер', '')).strip(),
                        'stock_esenina': int(row.get('Склад на Есенина', 0) or 0),
                        'stock_esenina_soft': int(row.get('Склад на Есенина SOFT', 0) or 0),
                        'stock_esenina_far': int(row.get('Склад на Есенина Дальний', 0) or 0),
                        'purchase_price': float(row.get('Цена: Закупочная,руб.', 0) or 0)
                    }
                    
                    product_data['stock_total'] = (
                        product_data['stock_esenina'] +
                        product_data['stock_esenina_soft'] +
                        product_data['stock_esenina_far']
                    )
                    
                    if product:
                        for key, value in product_data.items():
                            if key != 'barcode':
                                setattr(product, key, value)
                        records_updated += 1
                    else:
                        product = Product(**product_data)
                        self.db.add(product)
                        records_added += 1
                    
                    records_processed += 1
                    
                except Exception as e:
                    records_failed += 1
                    # Сохраняем детали ошибки
                    error_details.append({
                        'Строка в Excel': index + 2,  # +2 т.к. index с 0 и есть строка заголовков
                        'Штрихкод': row.get('ШК', 'N/A'),
                        'Номенклатура': row.get('Номенклатура', 'N/A'),
                        'Причина ошибки': str(e)
                    })
                    continue
            
            self.db.commit()

            # --- Создание отчета об ошибках ---
            error_report_filename = None
            if error_details:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                error_report_filename = f"error_report_1c_{timestamp}.xlsx"
                error_df = pd.DataFrame(error_details)
                
                # Убедимся, что папка exports существует
                output_dir = "exports"
                os.makedirs(output_dir, exist_ok=True)
                
                error_df.to_excel(os.path.join(output_dir, error_report_filename), index=False)

            # Создаем лог импорта
            import_log = ImportLog(
                source='1c',
                file_name=os.path.basename(file_path),
                records_processed=records_processed,
                records_added=records_added,
                records_updated=records_updated,
                records_failed=records_failed,
                status='success' if records_failed == 0 else 'partial',
                error_report_file=error_report_filename  # Сохраняем имя файла
            )
            self.db.add(import_log)
            self.db.commit()
            
            return import_log
            
        except Exception as e:
            self.db.rollback()
            import_log = ImportLog(
                source='1c',
                file_name=file_path,
                records_processed=0,
                records_added=0,
                records_updated=0,
                records_failed=0,
                status='failed',
                error_message=str(e)
            )
            self.db.add(import_log)
            self.db.commit()
            raise e
        
    def import_wb_barcodes(self, file_path: str) -> ImportLog:
        """Импорт таблицы с ШК ВБ с детальным логированием ошибок"""
        df = None
        try:
            df = pd.read_excel(file_path, sheet_name="Товары", header=2, dtype=str).fillna('')
            df.columns = df.columns.str.strip()

            # --- ФИНАЛЬНЫЙ ШТРИХ: Удаляем первую строку с описаниями ---
            if not df.empty:
                df = df.iloc[1:].reset_index(drop=True)

            records_processed = 0
            records_updated = 0
            records_failed = 0
            error_details = []

            for index, row in df.iterrows():
                try:
                    barcode = str(row.get('Баркод', '')).strip()
                    article_seller = str(row.get('Артикул продавца', '')).strip()
                    article_wb = str(row.get('Артикул WB', '')).strip()
                    
                    if not barcode:
                        if article_seller or article_wb:
                           raise ValueError("Баркод отсутствует, хотя другие данные присутствуют")
                        else: 
                           continue

                    product = self.db.query(Product).filter(Product.barcode == barcode).first()
                    
                    if not product:
                        raise ValueError(f"Товар со штрихкодом {barcode} не найден в базе данных")
                    
                    mp_data = self.db.query(MarketplaceData).filter(
                        MarketplaceData.barcode == barcode,
                        MarketplaceData.marketplace == 'wb'
                    ).first()
                    
                    if mp_data:
                        mp_data.article = article_seller
                        mp_data.external_id = article_wb
                    else:
                        mp_data = MarketplaceData(
                            barcode=barcode,
                            marketplace='wb',
                            article=article_seller,
                            external_id=article_wb
                        )
                        self.db.add(mp_data)
                    
                    records_processed += 1
                    records_updated += 1
                    
                except Exception as e:
                    records_failed += 1
                    error_details.append({
                        'Строка в Excel': index + 5,  # +5, т.к. 3 строки заголовка + 1 строка описания
                        'Баркод': row.get('Баркод', 'N/A'),
                        'Артикул продавца': row.get('Артикул продавца', 'N/A'),
                        'Причина ошибки': str(e)
                    })
                    continue
            
            self.db.commit()

            error_report_filename = None
            if error_details:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                error_report_filename = f"error_report_wb_barcodes_{timestamp}.xlsx"
                error_df = pd.DataFrame(error_details)
                output_dir = "exports"
                os.makedirs(output_dir, exist_ok=True)
                error_df.to_excel(os.path.join(output_dir, error_report_filename), index=False)
            
            import_log = ImportLog(
                source='wb_barcodes',
                file_name=os.path.basename(file_path),
                records_processed=records_processed,
                records_added=0,
                records_updated=records_updated,
                records_failed=records_failed,
                status='success' if records_failed == 0 else 'partial',
                error_report_file=error_report_filename
            )
            self.db.add(import_log)
            self.db.commit()
            
            return import_log
            
        except Exception as e:
            # traceback.print_exc()  # Можно закомментировать или удалить
            self.db.rollback()
            total_rows = df.shape[0] if df is not None else 0
            import_log = ImportLog(
                source='wb_barcodes',
                file_name=os.path.basename(file_path),
                records_processed=0,
                records_added=0,
                records_updated=0,
                records_failed=total_rows,
                status='failed',
                error_message=str(e)
            )
            self.db.add(import_log)
            self.db.commit()
            raise e
    
    def import_wb_prices(self, file_path: str) -> ImportLog:
        """Импорт цен ВБ с детальным логированием и корректным расчетом цены со скидкой"""
        df = None
        try:
            df = pd.read_excel(file_path, dtype=str).fillna('')
            df.columns = df.columns.str.strip()
            
            records_processed = 0
            records_updated = 0
            records_failed = 0
            error_details = []

            for index, row in df.iterrows():
                try:
                    article_wb = str(row.get('Артикул WB', '')).strip()
                    barcode = str(row.get('Последний баркод', '')).strip()

                    if not article_wb and not barcode:
                        if any(row.values): 
                            raise ValueError("Отсутствуют 'Артикул WB' и 'Последний баркод'")
                        else: 
                            continue

                    mp_data = None
                    if article_wb:
                        mp_data = self.db.query(MarketplaceData).filter(
                            MarketplaceData.marketplace == 'wb',
                            MarketplaceData.external_id == article_wb
                        ).first()
                    
                    if not mp_data and barcode:
                        mp_data = self.db.query(MarketplaceData).filter(
                            MarketplaceData.marketplace == 'wb',
                            MarketplaceData.barcode == barcode
                        ).first()

                    if not mp_data:
                        raise ValueError(f"Товар с Артикулом WB '{article_wb}' или Баркодом '{barcode}' не найден")

                    # --- НАЧАЛО НОВОЙ ЛОГИКИ РАСЧЕТА СОГЛАСНО ФОРМУЛЕ EXCEL ---
                    current_price_raw = row.get('Текущая цена', '0')
                    new_price_raw = row.get('Новая цена', '')
                    current_discount_raw = row.get('Текущая скидка', '0')
                    new_discount_raw = row.get('Новая скидка', '')

                    base_price_for_calc = float(new_price_raw or current_price_raw or 0)
                    discount_for_calc = float(new_discount_raw or current_discount_raw or 0)
                    
                    if base_price_for_calc > 0 and discount_for_calc >= 0:
                        final_price = round(base_price_for_calc * (1 - (discount_for_calc / 100)), 2)
                    else:
                        final_price = base_price_for_calc

                    mp_data.price_before_discount = base_price_for_calc
                    mp_data.discount_percent = discount_for_calc
                    mp_data.current_price = final_price
                    # --- КОНЕЦ НОВОЙ ЛОГИКИ РАСЧЕТА ---
                    
                    records_processed += 1
                    records_updated += 1

                except Exception as e:
                    records_failed += 1
                    error_details.append({
                        'Строка в Excel': index + 2,
                        'Артикул WB': row.get('Артикул WB', 'N/A'),
                        'Последний баркод': row.get('Последний баркод', 'N/A'),
                        'Причина ошибки': str(e)
                    })
                    continue
            
            self.db.commit()

            error_report_filename = None
            if error_details:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                error_report_filename = f"error_report_wb_prices_{timestamp}.xlsx"
                error_df = pd.DataFrame(error_details)
                output_dir = "exports"
                os.makedirs(output_dir, exist_ok=True)
                error_df.to_excel(os.path.join(output_dir, error_report_filename), index=False)
            
            import_log = ImportLog(
                source='wb_prices',
                file_name=os.path.basename(file_path),
                records_processed=records_processed,
                records_added=0,
                records_updated=records_updated,
                records_failed=records_failed,
                status='success' if records_failed == 0 else 'partial',
                error_report_file=error_report_filename
            )
            self.db.add(import_log)
            self.db.commit()
            
            return import_log
            
        except Exception as e:
            # traceback.print_exc()
            self.db.rollback()
            total_rows = df.shape[0] if df is not None else 0
            import_log = ImportLog(
                source='wb_prices',
                file_name=os.path.basename(file_path),
                records_processed=0,
                records_added=0,
                records_updated=0,
                records_failed=total_rows,
                status='failed',
                error_message=str(e)
            )
            self.db.add(import_log)
            self.db.commit()
            raise e
    
    def import_wb_min_prices(self, file_path: str) -> ImportLog:
        """Imports WB minimum prices with detailed error logging"""
        df = None
        try:
            df = pd.read_excel(file_path, dtype=str).fillna('')
            df.columns = df.columns.str.strip()
            
            records_processed = 0
            records_updated = 0
            records_failed = 0
            error_details = []
            min_price_col = 'Текущая минимальная цена для применения скидки по автоакции'

            for index, row in df.iterrows():
                try:
                    article_wb = str(row.get('Артикул WB', '')).strip()
                    
                    if not article_wb:
                        if any(row.values):
                           raise ValueError("Артикул WB отсутствует")
                        else:
                           continue

                    mp_data = self.db.query(MarketplaceData).filter(
                        MarketplaceData.marketplace == 'wb',
                        MarketplaceData.external_id == article_wb
                    ).first()
                    
                    if not mp_data:
                        raise ValueError(f"Товар с Артикулом WB '{article_wb}' не найден в базе данных")
                    
                    min_price_text = str(row.get(min_price_col, '0')).strip()
                    min_price = 0.0
                    
                    match = re.match(r'^\s*([\d\.]+)', min_price_text)
                    if match:
                        min_price = float(match.group(1))
                        
                    mp_data.min_price = min_price
                    records_processed += 1
                    records_updated += 1

                except Exception as e:
                    records_failed += 1
                    error_details.append({
                        'Строка в Excel': index + 2,
                        'Артикул WB': row.get('Артикул WB', 'N/A'),
                        'Значение в ячейке': row.get(min_price_col, 'N/A'),
                        'Причина ошибки': str(e)
                    })
                    continue
            
            self.db.commit()

            error_report_filename = None
            if error_details:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                error_report_filename = f"error_report_wb_min_prices_{timestamp}.xlsx"
                error_df = pd.DataFrame(error_details)
                output_dir = "exports"
                os.makedirs(output_dir, exist_ok=True)
                error_df.to_excel(os.path.join(output_dir, error_report_filename), index=False)
            
            import_log = ImportLog(
                source='wb_min_prices',
                file_name=os.path.basename(file_path),
                records_processed=records_processed,
                records_added=0,
                records_updated=records_updated,
                records_failed=records_failed,
                status='success' if records_failed == 0 else 'partial',
                error_report_file=error_report_filename
            )
            self.db.add(import_log)
            self.db.commit()
            
            return import_log
            
        except Exception as e:
            # traceback.print_exc()
            self.db.rollback()
            total_rows = df.shape[0] if df is not None else 0
            import_log = ImportLog(
                source='wb_min_prices',
                file_name=os.path.basename(file_path),
                records_processed=0,
                records_added=0,
                records_updated=0,
                records_failed=total_rows,
                status='failed',
                error_message=str(e)
            )
            self.db.add(import_log)
            self.db.commit()
            raise e
    
    def import_ozon_barcodes(self, file_path: str) -> ImportLog:
        """Импорт таблицы с ШК Озон с устойчивым чтением XLSX: calamine -> безопасный парсер без стилей"""
        df = None
        try:
            # --- ГЛАВНОЕ: читаем ВТОРОЙ лист (sheet_name=1) и заголовок на второй строке (header=1) ---
            try:
                # 1) Пробуем через calamine (устойчиво к битым стилям, быстро, без зависимостей от openpyxl)
                df = pd.read_excel(file_path, sheet_name=1, header=1, dtype=str, engine="calamine").fillna('')
            except Exception:
                # 2) Fallback: безопасный парсер без чтения styles.xml
                df = safe_read_xlsx_sheet_as_dataframe(file_path, sheet_index=1, header_row_index=1)

            # Нормализуем колонки
            df.columns = df.columns.str.strip()

            # Валидация обязательных колонок (по желанию можно убрать)
            required_cols = {'Штрихкод', 'Артикул', 'Ozon Product ID'}
            missing = [c for c in required_cols if c not in df.columns]
            if missing:
                # Не падаем насмерть — это данные от Озона периодически меняют подписи.
                # Но сообщим через частичный статус и error_details.
                pass

            # Удаляем строки с описаниями, которые Ozon вставляет после заголовка
            if 'Артикул' in df.columns:
                df = df[~df['Артикул'].astype(str).str.contains('Уникальный идентификатор', na=False)]
            df = df.reset_index(drop=True)

            records_processed = 0
            records_updated = 0
            records_failed = 0
            error_details = []

            for index, row in df.iterrows():
                try:
                    barcode = str(row.get('Штрихкод', '')).strip()
                    article = str(row.get('Артикул', '')).strip()
                    ozon_product_id = str(row.get('Ozon Product ID', '')).strip()
                    
                    if not barcode and not article:
                        if any(row.values):
                            raise ValueError("Отсутствуют 'Штрихкод' и 'Артикул'")
                        else:
                            continue

                    product = self.db.query(Product).filter(Product.barcode == barcode).first()
                    
                    # Если товар не найден в нашей базе, пропускаем его (тихая обработка)
                    if not product:
                        continue
                    
                    mp_data = self.db.query(MarketplaceData).filter(
                        MarketplaceData.barcode == barcode,
                        MarketplaceData.marketplace == 'ozon'
                    ).first()
                    
                    sku = article
                    
                    if mp_data:
                        mp_data.article = article
                        mp_data.sku = sku
                        mp_data.external_id = ozon_product_id
                    else:
                        mp_data = MarketplaceData(
                            barcode=barcode,
                            marketplace='ozon',
                            article=article,
                            sku=sku,
                            external_id=ozon_product_id
                        )
                        self.db.add(mp_data)
                    
                    records_processed += 1
                    records_updated += 1
                    
                except Exception as e:
                    records_failed += 1
                    error_details.append({
                        'Строка в Excel': index + 5,  # +5: шапка/служебные строки у отчёта Озона
                        'Штрихкод': row.get('Штрихкод', 'N/A'),
                        'Артикул': row.get('Артикул', 'N/A'),
                        'Причина ошибки': str(e)
                    })
                    continue
            
            self.db.commit()

            error_report_filename = None
            if error_details:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                error_report_filename = f"error_report_ozon_barcodes_{timestamp}.xlsx"
                error_df = pd.DataFrame(error_details)
                output_dir = "exports"
                os.makedirs(output_dir, exist_ok=True)
                error_df.to_excel(os.path.join(output_dir, error_report_filename), index=False)
            
            import_log = ImportLog(
                source='ozon_barcodes',
                file_name=os.path.basename(file_path),
                records_processed=records_processed,
                records_added=0,
                records_updated=records_updated,
                records_failed=records_failed,
                status='success' if records_failed == 0 else 'partial',
                error_report_file=error_report_filename
            )
            self.db.add(import_log)
            self.db.commit()
            
            return import_log
            
        except Exception as e:
            # traceback.print_exc()
            self.db.rollback()
            total_rows = df.shape[0] if df is not None else 0
            import_log = ImportLog(
                source='ozon_barcodes',
                file_name=os.path.basename(file_path),
                records_processed=0,
                records_added=0,
                records_updated=0,
                records_failed=total_rows,
                status='failed',
                error_message=str(e)
            )
            self.db.add(import_log)
            self.db.commit()
            raise e
    
    def import_ozon_prices(self, file_path: str) -> ImportLog:
        """Импорт цен Ozon из шаблона XLSX (игнорирует строки 'Нередактируемое' и т.п.)"""
        def _to_float(x):
            if x is None:
                return None
            s = str(x).strip()
            if not s:
                return None
            s = s.replace(" ", "").replace("\u00A0", "").replace(",", ".")
            import re
            m = re.match(r"^[+-]?\d+(?:\.\d+)?", s)
            if not m:
                return None
            try:
                return float(m.group(0))
            except Exception:
                return None

        df = None
        try:
            # --- Чтение таблицы устойчивым способом ---
            try:
                df = pd.read_excel(file_path, sheet_name=0, header=1, dtype=str, engine="calamine").fillna('')
            except Exception:
                df = safe_read_xlsx_sheet_as_dataframe(file_path, sheet_index=0, header_row_index=1)

            df.columns = df.columns.str.strip()

            # Определяем колонки (из шаблона)
            col_barcode = 'Штрихкод'
            col_before  = 'Цена до скидки, руб.'
            col_curr    = 'Текущая цена (со скидкой), руб.'
            col_disc    = 'Скидка, %'
            col_min     = 'Минимальная цена, руб.'

            # --- Убираем служебные строки и описания ---
            bad_values = ['Нередактируемое', 'Редактируемое', 'Основные характеристики товара']
            df = df[~df.apply(lambda r: any(str(v).strip() in bad_values for v in r.values), axis=1)]
            df = df[~df.astype(str).apply(lambda r: ''.join(r.values).strip() == '', axis=1)]
            df = df.reset_index(drop=True)

            records_processed = 0
            records_updated = 0
            records_failed = 0
            error_details = []

            for index, row in df.iterrows():
                try:
                    barcode = str(row.get(col_barcode, '')).strip()
                    if not barcode:
                        if any(str(v).strip() for v in row.values):
                            raise ValueError("Отсутствует 'Штрихкод'")
                        else:
                            continue

                    mp_data = self.db.query(MarketplaceData).filter(
                        MarketplaceData.barcode == barcode,
                        MarketplaceData.marketplace == 'ozon'
                    ).first()

                    if not mp_data:
                        raise ValueError(f"Товар с ШК {barcode} (marketplace=ozon) не найден")

                    price_before = _to_float(row.get(col_before, ''))
                    current_price = _to_float(row.get(col_curr, ''))
                    discount_percent = _to_float(row.get(col_disc, ''))
                    new_min_price = _to_float(row.get(col_min, ''))

                    # --- Пересчёт скидки, если отсутствует ---
                    if discount_percent is None and price_before not in (None, 0) and current_price not in (None, 0):
                        try:
                            discount_percent = round((1 - (current_price / price_before)) * 100, 2)
                        except Exception:
                            pass

                    changed = False

                    if price_before is not None:
                        mp_data.price_before_discount = price_before
                        changed = True

                    if current_price is not None:
                        mp_data.current_price = current_price
                        changed = True

                    if discount_percent is not None:
                        mp_data.discount_percent = discount_percent
                        changed = True

                    if new_min_price is not None:
                        mp_data.min_price = new_min_price
                        changed = True

                    records_processed += 1
                    if changed:
                        records_updated += 1

                except Exception as e:
                    records_failed += 1
                    error_details.append({
                        'Строка в Excel': index + 2,
                        'Штрихкод': row.get(col_barcode, 'N/A'),
                        'Причина ошибки': str(e)
                    })
                    continue

            self.db.commit()

            error_report_filename = None
            if error_details:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                error_report_filename = f"error_report_ozon_prices_{timestamp}.xlsx"
                error_df = pd.DataFrame(error_details)
                output_dir = "exports"
                os.makedirs(output_dir, exist_ok=True)
                error_df.to_excel(os.path.join(output_dir, error_report_filename), index=False)

            import_log = ImportLog(
                source='ozon_prices',
                file_name=os.path.basename(file_path),
                records_processed=records_processed,
                records_added=0,
                records_updated=records_updated,
                records_failed=records_failed,
                status='success' if records_failed == 0 else 'partial',
                error_report_file=error_report_filename
            )
            self.db.add(import_log)
            self.db.commit()

            return import_log

        except Exception as e:
            self.db.rollback()
            total_rows = df.shape[0] if df is not None else 0
            import_log = ImportLog(
                source='ozon_prices',
                file_name=os.path.basename(file_path),
                records_processed=0,
                records_added=0,
                records_updated=0,
                records_failed=total_rows,
                status='failed',
                error_message=str(e)
            )
            self.db.add(import_log)
            self.db.commit()
            raise
