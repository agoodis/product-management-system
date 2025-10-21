from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.product import Product, MarketplaceData, CalculatedData
from app.schemas.product import (
    ProductResponse, ProductCreate, ProductUpdate, 
    ProductListResponse
)
import math

router = APIRouter()

@router.get("/", response_model=ProductListResponse)
def get_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=1000),
    search: Optional[str] = None,
    brand: Optional[str] = None,
    product_category: Optional[str] = None,
    marketplace: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Получить список товаров с фильтрацией и пагинацией"""
    query = db.query(Product)
    
    # Фильтры
    if search:
        query = query.filter(
            (Product.name.ilike(f"%{search}%")) |
            (Product.barcode.ilike(f"%{search}%")) |
            (Product.article_1c.ilike(f"%{search}%"))
        )
    
    if brand:
        query = query.filter(Product.brand == brand)
    
    if product_category:
        query = query.filter(Product.product_category == product_category)
    
    if marketplace:
        query = query.join(MarketplaceData).filter(
            MarketplaceData.marketplace == marketplace
        )
    
    # Подсчет общего количества
    total = query.count()
    
    # Пагинация
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()
    
    total_pages = math.ceil(total / page_size)
    
    return ProductListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

@router.get("/{barcode}", response_model=ProductResponse)
def get_product(barcode: str, db: Session = Depends(get_db)):
    """Получить товар по штрихкоду"""
    product = db.query(Product).filter(Product.barcode == barcode).first()
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    return product

@router.post("/", response_model=ProductResponse, status_code=201)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    """Создать новый товар"""
    existing = db.query(Product).filter(Product.barcode == product.barcode).first()
    if existing:
        raise HTTPException(status_code=400, detail="Товар с таким штрихкодом уже существует")
    
    db_product = Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@router.patch("/{barcode}", response_model=ProductResponse)
def update_product(
    barcode: str, 
    product_update: ProductUpdate, 
    db: Session = Depends(get_db)
):
    """Обновить товар"""
    product = db.query(Product).filter(Product.barcode == barcode).first()
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    update_data = product_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)
    
    db.commit()
    db.refresh(product)
    return product

@router.delete("/{barcode}", status_code=204)
def delete_product(barcode: str, db: Session = Depends(get_db)):
    """Удалить товар"""
    product = db.query(Product).filter(Product.barcode == barcode).first()
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    db.delete(product)
    db.commit()
    return None

@router.get("/filters/brands", response_model=List[str])
def get_brands(db: Session = Depends(get_db)):
    """Получить список всех брендов"""
    brands = db.query(Product.brand).distinct().filter(Product.brand.isnot(None)).all()
    return [b[0] for b in brands]

@router.get("/filters/categories", response_model=List[str])
def get_categories(db: Session = Depends(get_db)):
    """Получить список всех категорий"""
    categories = db.query(Product.product_category).distinct().filter(
        Product.product_category.isnot(None)
    ).all()
    return [c[0] for c in categories]