from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.export_service import ExportService
import os

router = APIRouter()

@router.get("/wb")
def export_to_wb(db: Session = Depends(get_db)):
    """Экспорт данных для Wildberries"""
    try:
        export_service = ExportService(db)
        filepath = export_service.export_to_wb()
        
        return FileResponse(
            path=filepath,
            filename=os.path.basename(filepath),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка экспорта: {str(e)}")

@router.get("/ozon")
def export_to_ozon(db: Session = Depends(get_db)):
    """Экспорт данных для Ozon"""
    try:
        export_service = ExportService(db)
        filepath = export_service.export_to_ozon()
        
        return FileResponse(
            path=filepath,
            filename=os.path.basename(filepath),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка экспорта: {str(e)}")

@router.get("/full")
def export_full_database(db: Session = Depends(get_db)):
    """Полная выгрузка базы данных"""
    try:
        export_service = ExportService(db)
        filepath = export_service.export_full_database()
        
        return FileResponse(
            path=filepath,
            filename=os.path.basename(filepath),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка экспорта: {str(e)}")