from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.services.import_service import ImportService
from app.schemas.product import ImportLogResponse
from app.models.product import ImportLog
import os
import shutil
from datetime import datetime

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/1c", response_model=ImportLogResponse)
async def import_1c(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Импорт данных из 1С"""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Файл должен быть в формате Excel")
    
    # Сохраняем файл
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = os.path.join(UPLOAD_DIR, f"1c_{timestamp}_{file.filename}")
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Импортируем данные
        import_service = ImportService(db)
        import_log = import_service.import_1c_data(file_path)
        
        return import_log
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка импорта: {str(e)}")
    
    finally:
        # Опционально: удаляем файл после импорта
        # os.remove(file_path)
        pass

@router.post("/wb/barcodes", response_model=ImportLogResponse)
async def import_wb_barcodes(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Импорт таблицы с ШК Wildberries"""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Файл должен быть в формате Excel")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = os.path.join(UPLOAD_DIR, f"wb_barcodes_{timestamp}_{file.filename}")
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        import_service = ImportService(db)
        import_log = import_service.import_wb_barcodes(file_path)
        
        return import_log
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка импорта: {str(e)}")

@router.post("/wb/prices", response_model=ImportLogResponse)
async def import_wb_prices(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Импорт цен Wildberries"""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Файл должен быть в формате Excel")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = os.path.join(UPLOAD_DIR, f"wb_prices_{timestamp}_{file.filename}")
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        import_service = ImportService(db)
        import_log = import_service.import_wb_prices(file_path)
        
        return import_log
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка импорта: {str(e)}")

@router.post("/wb/min-prices", response_model=ImportLogResponse)
async def import_wb_min_prices(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Импорт минимальных цен Wildberries"""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Файл должен быть в формате Excel")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = os.path.join(UPLOAD_DIR, f"wb_min_prices_{timestamp}_{file.filename}")
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        import_service = ImportService(db)
        import_log = import_service.import_wb_min_prices(file_path)
        
        return import_log
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка импорта: {str(e)}")

@router.post("/ozon/barcodes", response_model=ImportLogResponse)
async def import_ozon_barcodes(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Импорт таблицы с ШК Ozon"""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Файл должен быть в формате Excel")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = os.path.join(UPLOAD_DIR, f"ozon_barcodes_{timestamp}_{file.filename}")
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        import_service = ImportService(db)
        import_log = import_service.import_ozon_barcodes(file_path)
        
        return import_log
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка импорта: {str(e)}")

@router.post("/ozon/prices", response_model=ImportLogResponse)
async def import_ozon_prices(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Импорт цен Ozon"""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Файл должен быть в формате Excel")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = os.path.join(UPLOAD_DIR, f"ozon_prices_{timestamp}_{file.filename}")
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        import_service = ImportService(db)
        import_log = import_service.import_ozon_prices(file_path)
        
        return import_log
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка импорта: {str(e)}")

@router.get("/logs", response_model=List[ImportLogResponse])
def get_import_logs(
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Получить историю импортов"""
    logs = db.query(ImportLog).order_by(ImportLog.created_at.desc()).limit(limit).all()
    return logs