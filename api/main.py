from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import os

from api.routes import products, orders, admin
from database.session import init_db, close_db
from config import config

# Create FastAPI app
app = FastAPI(
    title="Telegram Shop API",
    description="API for Telegram Shopping Bot",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You may restrict this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create uploads directory if it doesn't exist
os.makedirs("uploads", exist_ok=True)

# Mount static files for uploaded images
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include routers
app.include_router(products.router, prefix="/api/products", tags=["products"])
app.include_router(orders.router, prefix="/api/orders", tags=["orders"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    try:
        await init_db()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        raise

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Close database connections on shutdown."""
    try:
        await close_db()
        print("✅ Database connections closed successfully")
    except Exception as e:
        print(f"❌ Error closing database connections: {e}")

# Root endpoint
@app.get("/", summary="Root endpoint")
async def root():
    return {
        "message": "Telegram Shop API",
        "version": app.version,
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
        "endpoints": {
            "products": "/api/products",
            "orders": "/api/orders",
            "admin": "/api/admin"
        }
    }

# Health check endpoint
@app.get("/health", summary="Health check")
async def health_check():
    return {
        "status": "healthy",
        "version": app.version,
        "database": "connected"
    }

# Start the server
def start():
    """Start the FastAPI server."""
    import os
    is_production = os.environ.get("RAILWAY_ENVIRONMENT") is not None
    
    print(f"🚀 Starting FastAPI server on {config.API_HOST}:{config.API_PORT}")
    print(f"📚 Documentation available at http://{config.API_HOST}:{config.API_PORT}/docs")
    
    uvicorn.run(
        "api.main:app",  # Correct import path for your FastAPI app
        host=config.API_HOST,
        port=config.API_PORT,
        reload=False,  # Disable reload in production
        log_level="info"
    )

if __name__ == "__main__":
    start()