from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Product(Base):
    __tablename__ = "products"
    
    barcode = Column(String, primary_key=True, index=True)
    article_1c = Column(String, index=True)
    name = Column(String, nullable=False)
    unit = Column(String)  # Ед.
    brand = Column(String, index=True)  # Фирма (Бренд)
    product_type = Column(String, index=True)  # Вид товара
    product_category = Column(String, index=True)  # Тип товара
    collection = Column(String)  # Коллекция
    season = Column(String)  # Сезон
    size = Column(String)  # Размер
    
    # Остатки и цены из 1С
    stock_esenina = Column(Integer, default=0)
    stock_esenina_soft = Column(Integer, default=0)
    stock_esenina_far = Column(Integer, default=0)
    stock_total = Column(Integer, default=0)
    purchase_price = Column(Float)  # Закупочная цена
    
    # Дополнительные поля (гибкие)
    product_metadata = Column(JSON)  # Метки и другие кастомные поля
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Связи
    marketplace_data = relationship("MarketplaceData", back_populates="product", cascade="all, delete-orphan")
    calculated_data = relationship("CalculatedData", back_populates="product", uselist=False, cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_brand_category', 'brand', 'product_category'),
    )


class MarketplaceData(Base):
    __tablename__ = "marketplace_data"
    
    id = Column(Integer, primary_key=True, index=True)
    barcode = Column(String, ForeignKey("products.barcode", ondelete="CASCADE"), nullable=False)
    marketplace = Column(String, nullable=False)  # 'wb' или 'ozon'
    
    # Артикулы маркетплейса
    article = Column(String, index=True)
    external_id = Column(String, index=True)  # Арт ВБ или Ozon Product ID
    sku = Column(String)  # Для Озон
    
    # Цены и скидки
    price_before_discount = Column(Float)  # Цена до скидки
    current_price = Column(Float)  # Текущая цена (со скидкой)
    discount_percent = Column(Float)  # Скидка %
    min_price = Column(Float)  # Минимальная цена
    
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    product = relationship("Product", back_populates="marketplace_data")
    
    __table_args__ = (
        Index('idx_marketplace_barcode', 'marketplace', 'barcode'),
        Index('idx_marketplace_article', 'marketplace', 'article'),
    )


class CalculatedData(Base):
    __tablename__ = "calculated_data"
    
    barcode = Column(String, ForeignKey("products.barcode", ondelete="CASCADE"), primary_key=True)
    
    # Расчетные поля
    margin = Column(Float)  # Наценка
    margin_percent = Column(Float)  # Наценка %
    turnover_rate = Column(Float)  # Оборачиваемость
    abc_category = Column(String)  # ABC категория
    xyz_category = Column(String)  # XYZ категория
    days_in_stock = Column(Integer)  # Дней на складе
    
    # Дополнительные расчетные поля
    calculated_fields = Column(JSON)
    
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    product = relationship("Product", back_populates="calculated_data")


class ImportLog(Base):
    __tablename__ = "import_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    source = Column(String, nullable=False)  # '1c', 'wb', 'ozon'
    file_name = Column(String)
    records_processed = Column(Integer)
    records_added = Column(Integer)
    records_updated = Column(Integer)
    records_failed = Column(Integer)
    status = Column(String)  # 'success', 'partial', 'failed'
    error_message = Column(String)
    error_report_file = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())