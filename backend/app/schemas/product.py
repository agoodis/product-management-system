from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class MarketplaceDataBase(BaseModel):
    marketplace: str
    article: Optional[str] = None
    external_id: Optional[str] = None
    sku: Optional[str] = None
    price_before_discount: Optional[float] = None
    current_price: Optional[float] = None
    discount_percent: Optional[float] = None
    min_price: Optional[float] = None

class MarketplaceDataResponse(MarketplaceDataBase):
    id: int
    barcode: str
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class CalculatedDataBase(BaseModel):
    margin: Optional[float] = None
    margin_percent: Optional[float] = None
    turnover_rate: Optional[float] = None
    abc_category: Optional[str] = None
    xyz_category: Optional[str] = None
    days_in_stock: Optional[int] = None
    calculated_fields: Optional[Dict[str, Any]] = None

class CalculatedDataResponse(CalculatedDataBase):
    barcode: str
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class ProductBase(BaseModel):
    barcode: str
    article_1c: Optional[str] = None
    name: str
    unit: Optional[str] = None
    brand: Optional[str] = None
    product_type: Optional[str] = None
    product_category: Optional[str] = None
    collection: Optional[str] = None
    season: Optional[str] = None
    size: Optional[str] = None
    stock_esenina: int = 0
    stock_esenina_soft: int = 0
    stock_esenina_far: int = 0
    stock_total: int = 0
    purchase_price: Optional[float] = None
    product_metadata: Optional[Dict[str, Any]] = None

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    article_1c: Optional[str] = None
    name: Optional[str] = None
    unit: Optional[str] = None
    brand: Optional[str] = None
    product_type: Optional[str] = None
    product_category: Optional[str] = None
    collection: Optional[str] = None
    season: Optional[str] = None
    size: Optional[str] = None
    stock_esenina: Optional[int] = None
    stock_esenina_soft: Optional[int] = None
    stock_esenina_far: Optional[int] = None
    stock_total: Optional[int] = None
    purchase_price: Optional[float] = None
    product_metadata: Optional[Dict[str, Any]] = None

class ProductResponse(ProductBase):
    created_at: datetime
    updated_at: Optional[datetime] = None
    marketplace_data: List[MarketplaceDataResponse] = []
    calculated_data: Optional[CalculatedDataResponse] = None
    
    class Config:
        from_attributes = True

class ProductListResponse(BaseModel):
    items: List[ProductResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

class ImportLogResponse(BaseModel):
    id: int
    source: str
    file_name: Optional[str] = None
    records_processed: int
    records_added: int
    records_updated: int
    records_failed: int
    status: str
    error_message: Optional[str] = None
    error_report_file: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True