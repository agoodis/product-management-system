import pandas as pd
from sqlalchemy.orm import Session
from app.models.product import Product, MarketplaceData
from typing import List, Optional
import os
from datetime import datetime

class ExportService:
    def __init__(self, db: Session):
        self.db = db
    
    def export_to_wb(self, output_dir: str = "exports") -> str:
        """Экспорт данных для Wildberries"""
        os.makedirs(output_dir, exist_ok=True)
        
        # Получаем данные для WB
        query = self.db.query(
            Product.barcode,
            Product.article_1c,
            Product.name,
            Product.brand,
            Product.size,
            Product.stock_total,
            MarketplaceData.article.label('article_wb'),
            MarketplaceData.external_id.label('wb_id'),
            MarketplaceData.current_price,
            MarketplaceData.discount_percent
        ).join(
            MarketplaceData,
            (Product.barcode == MarketplaceData.barcode) &
            (MarketplaceData.marketplace == 'wb')
        ).filter(
            Product.stock_total > 0  # Только товары с остатками
        )
        
        results = query.all()
        
        # Создаем DataFrame
        data = []
        for row in results:
            data.append({
                'Штрихкод': row.barcode,
                'Артикул': row.article_wb,
                'Арт ВБ': row.wb_id,
                'Название': row.name,
                'Бренд': row.brand,
                'Размер': row.size,
                'Остаток': row.stock_total,
                'Цена': row.current_price,
                'Скидка %': row.discount_percent
            })
        
        df = pd.DataFrame(data)
        
        # Сохраняем в Excel
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"export_wb_{timestamp}.xlsx"
        filepath = os.path.join(output_dir, filename)
        
        df.to_excel(filepath, index=False, sheet_name='Wildberries')
        
        return filepath
    
    def export_to_ozon(self, output_dir: str = "exports") -> str:
        """Экспорт данных для Ozon"""
        os.makedirs(output_dir, exist_ok=True)
        
        # Получаем данные для Ozon
        query = self.db.query(
            Product.barcode,
            Product.article_1c,
            Product.name,
            Product.brand,
            Product.size,
            Product.stock_total,
            MarketplaceData.sku,
            MarketplaceData.external_id.label('ozon_product_id'),
            MarketplaceData.price_before_discount,
            MarketplaceData.current_price,
            MarketplaceData.discount_percent,
            MarketplaceData.min_price
        ).join(
            MarketplaceData,
            (Product.barcode == MarketplaceData.barcode) &
            (MarketplaceData.marketplace == 'ozon')
        ).filter(
            Product.stock_total > 0
        )
        
        results = query.all()
        
        # Создаем DataFrame
        data = []
        for row in results:
            data.append({
                'Штрихкод': row.barcode,
                'SKU': row.sku,
                'Ozon Product ID': row.ozon_product_id,
                'Название': row.name,
                'Бренд': row.brand,
                'Размер': row.size,
                'Остаток': row.stock_total,
                'Цена до скидки': row.price_before_discount,
                'Цена со скидкой': row.current_price,
                'Скидка %': row.discount_percent,
                'Минимальная цена': row.min_price
            })
        
        df = pd.DataFrame(data)
        
        # Сохраняем в Excel
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"export_ozon_{timestamp}.xlsx"
        filepath = os.path.join(output_dir, filename)
        
        df.to_excel(filepath, index=False, sheet_name='Ozon')
        
        return filepath
    
    def export_full_database(self, output_dir: str = "exports") -> str:
        """Полная выгрузка базы данных"""
        os.makedirs(output_dir, exist_ok=True)
        
        # Получаем все данные
        products = self.db.query(Product).all()
        
        data = []
        for product in products:
            row = {
                'Штрихкод': product.barcode,
                'Артикул 1С': product.article_1c,
                'Название': product.name,
                'Единица': product.unit,
                'Бренд': product.brand,
                'Вид товара': product.product_type,
                'Тип товара': product.product_category,
                'Коллекция': product.collection,
                'Сезон': product.season,
                'Размер': product.size,
                'Остаток Есенина': product.stock_esenina,
                'Остаток Есенина SOFT': product.stock_esenina_soft,
                'Остаток Есенина Дальний': product.stock_esenina_far,
                'Остаток общий': product.stock_total,
                'Закупочная цена': product.purchase_price
            }
            
            # Добавляем данные WB
            wb_data = next((m for m in product.marketplace_data if m.marketplace == 'wb'), None)
            if wb_data:
                row['WB Артикул'] = wb_data.article
                row['WB ID'] = wb_data.external_id
                row['WB Цена'] = wb_data.current_price
                row['WB Скидка %'] = wb_data.discount_percent
            
            # Добавляем данные Ozon
            ozon_data = next((m for m in product.marketplace_data if m.marketplace == 'ozon'), None)
            if ozon_data:
                row['Ozon SKU'] = ozon_data.sku
                row['Ozon Product ID'] = ozon_data.external_id
                row['Ozon Цена до скидки'] = ozon_data.price_before_discount
                row['Ozon Цена'] = ozon_data.current_price
                row['Ozon Скидка %'] = ozon_data.discount_percent
                row['Ozon Мин. цена'] = ozon_data.min_price
            
            # Добавляем расчетные данные
            if product.calculated_data:
                row['Наценка'] = product.calculated_data.margin
                row['Наценка %'] = product.calculated_data.margin_percent
                row['Оборачиваемость'] = product.calculated_data.turnover_rate
                row['ABC категория'] = product.calculated_data.abc_category
            
            data.append(row)
        
        df = pd.DataFrame(data)
        
        # Сохраняем в Excel
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"export_full_{timestamp}.xlsx"
        filepath = os.path.join(output_dir, filename)
        
        df.to_excel(filepath, index=False, sheet_name='Все товары')
        
        return filepath