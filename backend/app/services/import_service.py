import pandas as pd
from sqlalchemy.orm import Session
from app.models.product import Product, MarketplaceData, ImportLog
from typing import Dict, Any
import re

class ImportService:
    def __init__(self, db: Session):
        self.db = db
    
    def import_1c_data(self, file_path: str) -> ImportLog:
        """Импорт данных из 1С"""
        try:
            df = pd.read_excel(file_path)
            
            # Предполагаемые колонки (нужно уточнить по реальному файлу)
            df.columns = df.columns.str.strip()
            
            records_processed = 0
            records_added = 0
            records_updated = 0
            records_failed = 0
            
            for _, row in df.iterrows():
                try:
                    barcode = str(row.get('ШК', '')).strip()
                    if not barcode or barcode == 'nan':
                        records_failed += 1
                        continue
                    
                    # Проверяем существование товара
                    product = self.db.query(Product).filter(
                        Product.barcode == barcode
                    ).first()
                    
                    # Подготовка данных
                    product_data = {
                        'barcode': barcode,
                        'article_1c': str(row.get('Артикул', '')).strip(),
                        'name': str(row.get('Номенклатура', '')).strip(),
                        'unit': str(row.get('Ед.', '')).strip(),
                        'brand': str(row.get('Фирма', '')).strip(),
                        'product_type': str(row.get('Вид товара', '')).strip(),
                        'product_category': str(row.get('Тип товара', '')).strip(),
                        'collection': str(row.get('Коллекция', '')).strip(),
                        'season': str(row.get('Сезон', '')).strip(),
                        'size': str(row.get('Размер', '')).strip(),
                        'stock_esenina': int(row.get('Склад на Есенина', 0)),
                        'stock_esenina_soft': int(row.get('Склад на Есенина SOFT', 0)),
                        'stock_esenina_far': int(row.get('Склад на Есенина Дальний', 0)),
                        'purchase_price': float(row.get('Закупочная цена', 0))
                    }
                    
                    # Вычисляем общий остаток
                    product_data['stock_total'] = (
                        product_data['stock_esenina'] +
                        product_data['stock_esenina_soft'] +
                        product_data['stock_esenina_far']
                    )
                    
                    if product:
                        # Обновляем существующий товар
                        for key, value in product_data.items():
                            if key != 'barcode':
                                setattr(product, key, value)
                        records_updated += 1
                    else:
                        # Создаем новый товар
                        product = Product(**product_data)
                        self.db.add(product)
                        records_added += 1
                    
                    records_processed += 1
                    
                except Exception as e:
                    records_failed += 1
                    print(f"Ошибка обработки строки: {e}")
                    continue
            
            self.db.commit()
            
            # Создаем лог импорта
            import_log = ImportLog(
                source='1c',
                file_name=file_path,
                records_processed=records_processed,
                records_added=records_added,
                records_updated=records_updated,
                records_failed=records_failed,
                status='success' if records_failed == 0 else 'partial'
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
        """Импорт таблицы с ШК ВБ"""
        try:
            df = pd.read_excel(file_path)
            df.columns = df.columns.str.strip()
            
            records_processed = 0
            records_updated = 0
            records_failed = 0
            
            for _, row in df.iterrows():
                try:
                    barcode = str(row.get('ШК', '')).strip()
                    article_wb = str(row.get('Артикул', '')).strip()
                    external_id = str(row.get('Арт ВБ', '')).strip()
                    
                    if not barcode:
                        records_failed += 1
                        continue
                    
                    # Проверяем существование товара
                    product = self.db.query(Product).filter(
                        Product.barcode == barcode
                    ).first()
                    
                    if not product:
                        records_failed += 1
                        continue
                    
                    # Проверяем существование данных маркетплейса
                    mp_data = self.db.query(MarketplaceData).filter(
                        MarketplaceData.barcode == barcode,
                        MarketplaceData.marketplace == 'wb'
                    ).first()
                    
                    if mp_data:
                        mp_data.article = article_wb
                        mp_data.external_id = external_id
                    else:
                        mp_data = MarketplaceData(
                            barcode=barcode,
                            marketplace='wb',
                            article=article_wb,
                            external_id=external_id
                        )
                        self.db.add(mp_data)
                    
                    records_processed += 1
                    records_updated += 1
                    
                except Exception as e:
                    records_failed += 1
                    print(f"Ошибка обработки строки WB: {e}")
                    continue
            
            self.db.commit()
            
            import_log = ImportLog(
                source='wb_barcodes',
                file_name=file_path,
                records_processed=records_processed,
                records_added=0,
                records_updated=records_updated,
                records_failed=records_failed,
                status='success' if records_failed == 0 else 'partial'
            )
            self.db.add(import_log)
            self.db.commit()
            
            return import_log
            
        except Exception as e:
            self.db.rollback()
            import_log = ImportLog(
                source='wb_barcodes',
                file_name=file_path,
                status='failed',
                error_message=str(e)
            )
            self.db.add(import_log)
            self.db.commit()
            raise e
    
    def import_wb_prices(self, file_path: str) -> ImportLog:
        """Импорт цен ВБ"""
        try:
            df = pd.read_excel(file_path)
            df.columns = df.columns.str.strip()
            
            records_processed = 0
            records_updated = 0
            records_failed = 0
            
            for _, row in df.iterrows():
                try:
                    barcode = str(row.get('ШК', '')).strip()
                    current_price = float(row.get('Текущая цена', 0))
                    discount = float(row.get('Текущая скидка', 0))
                    
                    if not barcode:
                        records_failed += 1
                        continue
                    
                    mp_data = self.db.query(MarketplaceData).filter(
                        MarketplaceData.barcode == barcode,
                        MarketplaceData.marketplace == 'wb'
                    ).first()
                    
                    if mp_data:
                        mp_data.current_price = current_price
                        mp_data.discount_percent = discount
                        records_updated += 1
                    else:
                        records_failed += 1
                        continue
                    
                    records_processed += 1
                    
                except Exception as e:
                    records_failed += 1
                    continue
            
            self.db.commit()
            
            import_log = ImportLog(
                source='wb_prices',
                file_name=file_path,
                records_processed=records_processed,
                records_updated=records_updated,
                status='success' if records_failed == 0 else 'partial'
            )
            self.db.add(import_log)
            self.db.commit()
            
            return import_log
            
        except Exception as e:
            self.db.rollback()
            raise e
    
    def import_wb_min_prices(self, file_path: str) -> ImportLog:
        """Импорт минимальных цен ВБ"""
        try:
            df = pd.read_excel(file_path)
            df.columns = df.columns.str.strip()
            
            records_processed = 0
            records_updated = 0
            records_failed = 0
            
            for _, row in df.iterrows():
                try:
                    external_id = str(row.get('Арт ВБ', '')).strip()
                    min_price_text = str(row.get('Текущая минимальная цена для применения скидки по автоакции', ''))
                    
                    # Извлекаем только цифры до скобок
                    min_price = 0
                    if min_price_text and '(' in min_price_text:
                        min_price = float(min_price_text.split('(')[0].strip())
                    elif min_price_text:
                        min_price = float(re.sub(r'[^\d.]', '', min_price_text))
                    
                    if not external_id:
                        records_failed += 1
                        continue
                    
                    mp_data = self.db.query(MarketplaceData).filter(
                        MarketplaceData.external_id == external_id,
                        MarketplaceData.marketplace == 'wb'
                    ).first()
                    
                    if mp_data:
                        mp_data.min_price = min_price
                        records_updated += 1
                    else:
                        records_failed += 1
                        continue
                    
                    records_processed += 1
                    
                except Exception as e:
                    records_failed += 1
                    print(f"Ошибка обработки строки WB min prices: {e}")
                    continue
            
            self.db.commit()
            
            import_log = ImportLog(
                source='wb_min_prices',
                file_name=file_path,
                records_processed=records_processed,
                records_updated=records_updated,
                records_failed=records_failed,
                status='success' if records_failed == 0 else 'partial'
            )
            self.db.add(import_log)
            self.db.commit()
            
            return import_log
            
        except Exception as e:
            self.db.rollback()
            import_log = ImportLog(
                source='wb_min_prices',
                file_name=file_path,
                status='failed',
                error_message=str(e)
            )
            self.db.add(import_log)
            self.db.commit()
            raise e
    
    def import_ozon_barcodes(self, file_path: str) -> ImportLog:
        """Импорт таблицы с ШК Озон"""
        try:
            df = pd.read_excel(file_path)
            df.columns = df.columns.str.strip()
            
            records_processed = 0
            records_updated = 0
            records_failed = 0
            
            for _, row in df.iterrows():
                try:
                    barcode = str(row.get('ШК', '')).strip()
                    article = str(row.get('Артикул', '')).strip()
                    size = str(row.get('Размер', '')).strip()
                    sku = f"{article}_{size}" if article and size else article
                    product_id = str(row.get('Ozon Product ID', '')).strip()
                    
                    if not barcode:
                        records_failed += 1
                        continue
                    
                    mp_data = self.db.query(MarketplaceData).filter(
                        MarketplaceData.barcode == barcode,
                        MarketplaceData.marketplace == 'ozon'
                    ).first()
                    
                    if mp_data:
                        mp_data.article = article
                        mp_data.sku = sku
                        mp_data.external_id = product_id
                    else:
                        mp_data = MarketplaceData(
                            barcode=barcode,
                            marketplace='ozon',
                            article=article,
                            sku=sku,
                            external_id=product_id
                        )
                        self.db.add(mp_data)
                    
                    records_processed += 1
                    records_updated += 1
                    
                except Exception as e:
                    records_failed += 1
                    continue
            
            self.db.commit()
            
            import_log = ImportLog(
                source='ozon_barcodes',
                file_name=file_path,
                records_processed=records_processed,
                records_updated=records_updated,
                status='success' if records_failed == 0 else 'partial'
            )
            self.db.add(import_log)
            self.db.commit()
            
            return import_log
            
        except Exception as e:
            self.db.rollback()
            raise e
    
    def import_ozon_prices(self, file_path: str) -> ImportLog:
        """Импорт цен Озон"""
        try:
            df = pd.read_excel(file_path)
            df.columns = df.columns.str.strip()
            
            records_processed = 0
            records_updated = 0
            records_failed = 0
            
            for _, row in df.iterrows():
                try:
                    barcode = str(row.get('ШК', '')).strip()
                    price_before = float(row.get('Цена до скидки', 0))
                    current_price = float(row.get('Текущая цена', 0))
                    discount = float(row.get('Скидка %', 0))
                    min_price = float(row.get('Минимальная цена', 0))
                    
                    if not barcode:
                        records_failed += 1
                        continue
                    
                    mp_data = self.db.query(MarketplaceData).filter(
                        MarketplaceData.barcode == barcode,
                        MarketplaceData.marketplace == 'ozon'
                    ).first()
                    
                    if mp_data:
                        mp_data.price_before_discount = price_before
                        mp_data.current_price = current_price
                        mp_data.discount_percent = discount
                        mp_data.min_price = min_price
                        records_updated += 1
                    else:
                        records_failed += 1
                        continue
                    
                    records_processed += 1
                    
                except Exception as e:
                    records_failed += 1
                    continue
            
            self.db.commit()
            
            import_log = ImportLog(
                source='ozon_prices',
                file_name=file_path,
                records_processed=records_processed,
                records_updated=records_updated,
                status='success' if records_failed == 0 else 'partial'
            )
            self.db.add(import_log)
            self.db.commit()
            
            return import_log
            
        except Exception as e:
            self.db.rollback()
            import_log = ImportLog(
                source='ozon_prices',
                file_name=file_path,
                status='failed',
                error_message=str(e)
            )
            self.db.add(import_log)
            self.db.commit()
            raise e