from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.calculation_service import CalculationService
from typing import List, Dict, Any

router = APIRouter()

@router.post("/margins/recalculate")
def recalculate_all_margins(db: Session = Depends(get_db)):
    """Пересчитать наценку для всех товаров"""
    try:
        calc_service = CalculationService(db)
        result = calc_service.calculate_all_margins()
        return {
            "status": "success",
            "message": f"Обработано {result['total']} товаров, успешно: {result['success']}, ошибок: {result['failed']}",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка расчета: {str(e)}")

@router.post("/margins/{barcode}")
def recalculate_margin(barcode: str, db: Session = Depends(get_db)):
    """Пересчитать наценку для конкретного товара"""
    try:
        calc_service = CalculationService(db)
        result = calc_service.calculate_margin(barcode)
        
        if not result:
            raise HTTPException(
                status_code=404, 
                detail="Товар не найден или недостаточно данных для расчета"
            )
        
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка расчета: {str(e)}")

@router.post("/abc-categories/recalculate")
def recalculate_abc_categories(db: Session = Depends(get_db)):
    """Пересчитать ABC категории для всех товаров"""
    try:
        calc_service = CalculationService(db)
        result = calc_service.calculate_abc_category()
        return {
            "status": "success",
            "message": f"ABC категории рассчитаны для {result['success']} товаров",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка расчета: {str(e)}")

@router.post("/recalculate-all")
def recalculate_all(db: Session = Depends(get_db)):
    """Пересчитать все расчетные поля"""
    try:
        calc_service = CalculationService(db)
        result = calc_service.recalculate_all()
        return {
            "status": "success",
            "message": "Все расчетные поля обновлены",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка расчета: {str(e)}")

@router.get("/analytics/low-stock")
def get_low_stock_products(
    threshold: int = 5,
    db: Session = Depends(get_db)
):
    """Получить товары с низким остатком"""
    try:
        calc_service = CalculationService(db)
        products = calc_service.get_low_stock_products(threshold)
        return {
            "status": "success",
            "count": len(products),
            "data": products
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")

@router.get("/analytics/high-margin")
def get_high_margin_products(
    min_margin_percent: float = 50.0,
    db: Session = Depends(get_db)
):
    """Получить товары с высокой наценкой"""
    try:
        calc_service = CalculationService(db)
        products = calc_service.get_high_margin_products(min_margin_percent)
        return {
            "status": "success",
            "count": len(products),
            "data": products
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")

@router.get("/analytics/abc-summary")
def get_abc_summary(db: Session = Depends(get_db)):
    """Получить сводку по ABC категориям"""
    try:
        calc_service = CalculationService(db)
        summary = calc_service.get_category_summary()
        return {
            "status": "success",
            "data": summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")