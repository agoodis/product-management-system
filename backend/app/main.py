from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.api import products, imports, exports, calculations

# Создание таблиц
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Product Management System",
    description="Система управления товарами для маркетплейсов",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Роутеры
app.include_router(products.router, prefix="/api/products", tags=["products"])
app.include_router(imports.router, prefix="/api/imports", tags=["imports"])
app.include_router(exports.router, prefix="/api/exports", tags=["exports"])
app.include_router(calculations.router, prefix="/api/calculations", tags=["calculations"])

@app.get("/")
def read_root():
    return {"message": "Product Management System API"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}