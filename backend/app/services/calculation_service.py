from sqlalchemy.orm import Session
from app.models.product import Product, MarketplaceData, CalculatedData
from typing import Optional
from datetime import datetime, timedelta

class CalculationService:
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_margin(self, barcode: str) -> Optional[dict]:
        """Рассчитать наценку для товара"""
        product = self.db.query(Product).filter(Product.barcode == barcode).first()
        if not product or not product.purchase_price:
            return None
        
        # Находим максимальную цену среди маркетплейсов
        max_price = 0
        for mp_data in product.marketplace_data:
            if mp_data.current_price and mp_data.current_price > max_price:
                max_price = mp_data.current_price
        
        if max_price == 0:
            return None
        
        # Рассчитываем наценку
        margin = max_price - product.purchase_price
        margin_percent = (margin / product.purchase_price) * 100 if product.purchase_price > 0 else 0
        
        # Обновляем или создаем расчетные данные
        calc_data = self.db.query(CalculatedData).filter(
            CalculatedData.barcode == barcode
        ).first()
        
        if calc_data:
            calc_data.margin = margin
            calc_data.margin_percent = margin_percent
        else:
            calc_data = CalculatedData(
                barcode=barcode,
                margin=margin,
                margin_percent=margin_percent
            )
            self.db.add(calc_data)
        
        self.db.commit()
        
        return {
            'barcode': barcode,
            'margin': margin,
            'margin_percent': margin_percent
        }
    
    def calculate_all_margins(self) -> dict:
        """Рассчитать наценку для всех товаров"""
        products = self.db.query(Product).all()
        
        success_count = 0
        failed_count = 0
        
        for product in products:
            try:
                result = self.calculate_margin(product.barcode)
                if result:
                    success_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                print(f"Ошибка расчета для {product.barcode}: {e}")
                failed_count += 1
        
        return {
            'total': len(products),
            'success': success_count,
            'failed': failed_count
        }
    
    def calculate_abc_category(self, barcode: Optional[str] = None) -> dict:
        """
        Рассчитать ABC категорию товаров
        A - 80% выручки (топ товары)
        B - следующие 15% выручки
        C - оставшиеся 5% выручки
        
        Пока используем стоимость остатков как прокси для выручки
        """
        if barcode:
            products = self.db.query(Product).filter(Product.barcode == barcode).all()
        else:
            products = self.db.query(Product).all()
        
        # Рассчитываем стоимость остатков для каждого товара
        product_values = []
        for product in products:
            if product.purchase_price and product.stock_total:
                value = product.purchase_price * product.stock_total
                product_values.append({
                    'barcode': product.barcode,
                    'value': value
                })
        
        # Сортируем по убыванию стоимости
        product_values.sort(key=lambda x: x['value'], reverse=True)
        
        # Рассчитываем общую стоимость
        total_value = sum(p['value'] for p in product_values)
        
        # Определяем границы категорий
        cumulative_value = 0
        threshold_a = total_value * 0.8
        threshold_b = total_value * 0.95
        
        success_count = 0
        
        for item in product_values:
            cumulative_value += item['value']
            
            if cumulative_value <= threshold_a:
                category = 'A'
            elif cumulative_value <= threshold_b:
                category = 'B'
            else:
                category = 'C'
            
            # Обновляем или создаем расчетные данные
            calc_data = self.db.query(CalculatedData).filter(
                CalculatedData.barcode == item['barcode']
            ).first()
            
            if calc_data:
                calc_data.abc_category = category
            else:
                calc_data = CalculatedData(
                    barcode=item['barcode'],
                    abc_category=category
                )
                self.db.add(calc_data)
            
            success_count += 1
        
        self.db.commit()
        
        return {
            'total': len(product_values),
            'success': success_count
        }
    
    def calculate_turnover_rate(self, barcode: str, days: int = 30) -> Optional[dict]:
        """
        Рассчитать оборачиваемость товара
        Требуется история продаж - пока заглушка
        """
        # TODO: Реализовать когда будет таблица с историей продаж
        # Оборачиваемость = Продажи за период / Средний остаток
        
        product = self.db.query(Product).filter(Product.barcode == barcode).first()
        if not product:
            return None
        
        # Заглушка: используем текущий остаток
        # В реальности нужно брать данные продаж
        turnover_rate = 0.0  # Placeholder
        
        calc_data = self.db.query(CalculatedData).filter(
            CalculatedData.barcode == barcode
        ).first()
        
        if calc_data:
            calc_data.turnover_rate = turnover_rate
        else:
            calc_data = CalculatedData(
                barcode=barcode,
                turnover_rate=turnover_rate
            )
            self.db.add(calc_data)
        
        self.db.commit()
        
        return {
            'barcode': barcode,
            'turnover_rate': turnover_rate
        }
    
    def recalculate_all(self) -> dict:
        """Пересчитать все расчетные поля"""
        margin_result = self.calculate_all_margins()
        abc_result = self.calculate_abc_category()
        
        return {
            'margins': margin_result,
            'abc_categories': abc_result
        }
    
    def get_low_stock_products(self, threshold: int = 5):
        """Получить товары с низким остатком"""
        products = self.db.query(Product).filter(
            Product.stock_total <= threshold,
            Product.stock_total > 0
        ).all()
        
        return [
            {
                'barcode': p.barcode,
                'name': p.name,
                'brand': p.brand,
                'stock_total': p.stock_total
            }
            for p in products
        ]
    
    def get_high_margin_products(self, min_margin_percent: float = 50.0):
        """Получить товары с высокой наценкой"""
        calc_data = self.db.query(CalculatedData).filter(
            CalculatedData.margin_percent >= min_margin_percent
        ).all()
        
        result = []
        for cd in calc_data:
            product = self.db.query(Product).filter(
                Product.barcode == cd.barcode
            ).first()
            if product:
                result.append({
                    'barcode': product.barcode,
                    'name': product.name,
                    'brand': product.brand,
                    'margin_percent': cd.margin_percent,
                    'margin': cd.margin
                })
        
        return result
    
    def get_category_summary(self):
        """Получить сводку по ABC категориям"""
        categories = self.db.query(
            CalculatedData.abc_category,
            self.db.func.count(CalculatedData.barcode).label('count')
        ).group_by(CalculatedData.abc_category).all()
        
        return {
            cat: count for cat, count in categories
        }