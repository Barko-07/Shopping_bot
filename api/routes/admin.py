from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List, Optional
import aiofiles
import os
from uuid import uuid4

from database.session import get_db
from database.models import User
from services.product import ProductService
from services.order import OrderService
from schemas.schemas import Product, ProductCreate, ProductUpdate, Order, LanguageUpdate, LanguageResponse

router = APIRouter()

# Simple admin token for API authentication (in production, use proper auth)
ADMIN_TOKEN = "admin_secret_token_here"

# Multilingual messages for admin API responses
ADMIN_MESSAGES = {
    "en": {
        # Admin messages
        "invalid_token": "Invalid admin token",
        "product_not_found": "Product not found",
        "order_not_found": "Order not found",
        "product_deleted": "Product deleted successfully",
        "order_status_updated": "Order status updated to {status}",
        "image_uploaded": "Image uploaded successfully",
        "invalid_image": "File must be an image",
        "products_retrieved": "Products retrieved successfully",
        "orders_retrieved": "Orders retrieved successfully",
        "product_created": "Product created successfully",
        "product_updated": "Product updated successfully",
        # Language messages
        "language_updated": "Language updated to {language}",
        "language_not_supported": "Language '{language}' is not supported",
        "supported_languages": "Supported languages",
        "current_language": "Your current language is {language}",
        "user_not_found": "User not found",
        # Language names
        "language_names": {
            "en": "English",
            "uz": "O'zbek",
            "ru": "Русский"
        }
    },
    "uz": {
        # Admin messages
        "invalid_token": "Noto'g'ri admin token",
        "product_not_found": "Mahsulot topilmadi",
        "order_not_found": "Buyurtma topilmadi",
        "product_deleted": "Mahsulot muvaffaqiyatli o'chirildi",
        "order_status_updated": "Buyurtma holati {status} ga o'zgartirildi",
        "image_uploaded": "Rasm muvaffaqiyatli yuklandi",
        "invalid_image": "Fayl rasm bo'lishi kerak",
        "products_retrieved": "Mahsulotlar muvaffaqiyatli olindi",
        "orders_retrieved": "Buyurtmalar muvaffaqiyatli olindi",
        "product_created": "Mahsulot muvaffaqiyatli yaratildi",
        "product_updated": "Mahsulot muvaffaqiyatli yangilandi",
        # Language messages
        "language_updated": "Til {language} ga o'zgartirildi",
        "language_not_supported": "{language} tili qo'llab-quvvatlanmaydi",
        "supported_languages": "Qo'llab-quvvatlanadigan tillar",
        "current_language": "Sizning hozirgi tilingiz: {language}",
        "user_not_found": "Foydalanuvchi topilmadi",
        # Language names
        "language_names": {
            "en": "English",
            "uz": "O'zbek",
            "ru": "Русский"
        }
    },
    "ru": {
        # Admin messages
        "invalid_token": "Недействительный токен администратора",
        "product_not_found": "Товар не найден",
        "order_not_found": "Заказ не найден",
        "product_deleted": "Товар успешно удалён",
        "order_status_updated": "Статус заказа изменён на {status}",
        "image_uploaded": "Изображение успешно загружено",
        "invalid_image": "Файл должен быть изображением",
        "products_retrieved": "Товары успешно получены",
        "orders_retrieved": "Заказы успешно получены",
        "product_created": "Товар успешно создан",
        "product_updated": "Товар успешно обновлён",
        # Language messages
        "language_updated": "Язык изменён на {language}",
        "language_not_supported": "Язык '{language}' не поддерживается",
        "supported_languages": "Поддерживаемые языки",
        "current_language": "Ваш текущий язык: {language}",
        "user_not_found": "Пользователь не найден",
        # Language names
        "language_names": {
            "en": "English",
            "uz": "O'zbek",
            "ru": "Русский"
        }
    }
}

# Supported languages
SUPPORTED_LANGUAGES = list(ADMIN_MESSAGES.keys())

def verify_admin_token(token: str, language: str = "en"):
    """Verify admin token with multilingual error message"""
    if token != ADMIN_TOKEN:
        raise HTTPException(
            status_code=403, 
            detail=get_admin_message(language, "invalid_token")
        )

def get_admin_message(language: str, key: str, **kwargs) -> str:
    """Get admin message by language with optional formatting"""
    if language not in ADMIN_MESSAGES:
        language = "en"
    
    msg = ADMIN_MESSAGES[language].get(key, key)
    if kwargs:
        try:
            return msg.format(**kwargs)
        except KeyError:
            return msg
    return msg

# Function to get user language from database or header
async def get_admin_language(
    request: Request,
    user_id: Optional[int] = None,
    db: AsyncSession = None
) -> str:
    """
    Get admin's language preference from:
    1. Database if user_id is provided
    2. X-Language header
    3. Accept-Language header
    4. Default to "en"
    """
    # Try to get from database if user_id provided
    if user_id and db:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user and hasattr(user, 'language') and user.language in SUPPORTED_LANGUAGES:
            return user.language
    
    # Try custom header
    lang = request.headers.get("X-Language", "")
    if lang in SUPPORTED_LANGUAGES:
        return lang
    
    # Try Accept-Language header
    accept_language = request.headers.get("Accept-Language", "")
    if accept_language:
        # Get first language code (simple parsing)
        preferred = accept_language.split(",")[0][:2]
        if preferred in SUPPORTED_LANGUAGES:
            return preferred
    
    # Default to English
    return "en"

# Language dependency for admin routes
async def admin_language_dependency(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> str:
    """Dependency to get admin's language preference"""
    # Try to get user_id from query params
    user_id = request.query_params.get("user_id")
    if user_id and user_id.isdigit():
        return await get_admin_language(request, int(user_id), db)
    
    return await get_admin_language(request, db=db)


# Language Management Endpoints for Admin
@router.get("/languages", response_model=LanguageResponse)
async def admin_get_available_languages(
    token: str,
    language: str = Depends(admin_language_dependency)
):
    """Admin: Get list of available languages"""
    verify_admin_token(token, language)
    return LanguageResponse(
        current_language=language,
        supported_languages=SUPPORTED_LANGUAGES,
        languages=ADMIN_MESSAGES[language]["language_names"],
        message=get_admin_message(language, "supported_languages")
    )


@router.get("/languages/current")
async def admin_get_current_language(
    token: str,
    user_id: Optional[int] = Query(None, description="User ID to check language"),
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    """Admin: Get current language for user or request"""
    verify_admin_token(token)
    
    if user_id:
        # Get from database
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=404,
                detail=get_admin_message("en", "user_not_found")
            )
        
        language = user.language if hasattr(user, 'language') else "en"
    else:
        # Get from request headers
        language = await get_admin_language(request, db=db)
    
    language_name = ADMIN_MESSAGES[language]["language_names"][language]
    
    return {
        "language_code": language,
        "language_name": language_name,
        "message": get_admin_message(
            language,
            "current_language",
            language=language_name
        )
    }


@router.put("/languages/{user_id}")
async def admin_update_user_language(
    user_id: int,
    language_update: LanguageUpdate,
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """Admin: Update user's language preference"""
    verify_admin_token(token)
    
    # Check if language is supported
    if language_update.language not in SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=400,
            detail=get_admin_message(
                "en",
                "language_not_supported",
                language=language_update.language
            )
        )
    
    # Check if user exists
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=404,
            detail=get_admin_message("en", "user_not_found")
        )
    
    # Update language
    stmt = update(User).where(User.id == user_id).values(language=language_update.language)
    await db.execute(stmt)
    await db.commit()
    
    # Get response in the new language
    language_name = ADMIN_MESSAGES[language_update.language]["language_names"][language_update.language]
    
    return {
        "user_id": user_id,
        "language_code": language_update.language,
        "language_name": language_name,
        "message": get_admin_message(
            language_update.language,
            "language_updated",
            language=language_name
        )
    }


@router.get("/languages/messages/{lang_code}")
async def admin_get_language_messages(
    lang_code: str,
    token: str
):
    """Admin: Get all messages in specified language"""
    verify_admin_token(token)
    
    if lang_code not in SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=404,
            detail=f"Language '{lang_code}' not supported. Supported: {SUPPORTED_LANGUAGES}"
        )
    
    return {
        "language_code": lang_code,
        "language_name": ADMIN_MESSAGES[lang_code]["language_names"][lang_code],
        "messages": ADMIN_MESSAGES[lang_code]
    }


# Admin Product Management Endpoints (with multilingual support)
@router.post("/products", response_model=Product)
async def admin_create_product(
    product: ProductCreate,
    token: str,
    db: AsyncSession = Depends(get_db),
    language: str = Depends(admin_language_dependency)
):
    """Admin: Create product"""
    verify_admin_token(token, language)
    service = ProductService(db)
    
    try:
        new_product = await service.create_product(product)
        return new_product
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.put("/products/{product_id}", response_model=Product)
async def admin_update_product(
    product_id: int,
    product_update: dict,
    token: str,
    db: AsyncSession = Depends(get_db),
    language: str = Depends(admin_language_dependency)
):
    """Admin: Update product"""
    verify_admin_token(token, language)
    service = ProductService(db)
    
    # Verify category exists if provided
    if product_update.get('category_id'):
        categories = await service.get_categories()
        category_exists = any(cat.id == product_update['category_id'] for cat in categories)
        if not category_exists:
            raise HTTPException(
                status_code=404,
                detail=get_admin_message(language, "category_not_found")
            )
    
    product = await service.update_product(product_id, ProductUpdate(**product_update))
    
    if not product:
        raise HTTPException(
            status_code=404,
            detail=get_admin_message(language, "product_not_found")
        )
    
    return product


@router.delete("/products/{product_id}")
async def admin_delete_product(
    product_id: int,
    token: str,
    db: AsyncSession = Depends(get_db),
    language: str = Depends(admin_language_dependency)
):
    """Admin: Delete product"""
    verify_admin_token(token, language)
    service = ProductService(db)
    deleted = await service.delete_product(product_id)
    
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail=get_admin_message(language, "product_not_found")
        )
    
    return {
        "message": get_admin_message(language, "product_deleted"),
        "product_id": product_id
    }


# Admin Order Management Endpoints (with multilingual support)
@router.get("/orders", response_model=List[Order])
async def admin_get_orders(
    token: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None, description="Filter by order status"),
    db: AsyncSession = Depends(get_db),
    language: str = Depends(admin_language_dependency)
):
    """Admin: Get all orders with optional status filter"""
    verify_admin_token(token, language)
    service = OrderService(db)
    orders = await service.get_all_orders()
    
    # Filter by status if provided
    if status:
        orders = [o for o in orders if o.status == status]
    
    return orders[skip:skip + limit]


@router.get("/orders/{order_id}", response_model=Order)
async def admin_get_order(
    order_id: int,
    token: str,
    db: AsyncSession = Depends(get_db),
    language: str = Depends(admin_language_dependency)
):
    """Admin: Get order by ID"""
    verify_admin_token(token, language)
    service = OrderService(db)
    order = await service.get_order(order_id)
    
    if not order:
        raise HTTPException(
            status_code=404,
            detail=get_admin_message(language, "order_not_found")
        )
    
    return order


@router.patch("/orders/{order_id}/status")
async def admin_update_order_status(
    order_id: int,
    status: str = Query(..., description="New status for the order"),
    token: str = None,
    db: AsyncSession = Depends(get_db),
    language: str = Depends(admin_language_dependency)
):
    """Admin: Update order status"""
    verify_admin_token(token, language)
    
    # Validate allowed statuses
    allowed_statuses = {"pending", "confirmed", "shipped", "delivered", "cancelled"}
    if status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail=get_admin_message(
                language,
                "invalid_status",
                allowed_statuses=", ".join(allowed_statuses)
            )
        )
    
    service = OrderService(db)
    order = await service.update_order_status(order_id, status)
    
    if not order:
        raise HTTPException(
            status_code=404,
            detail=get_admin_message(language, "order_not_found")
        )
    
    return {
        "message": get_admin_message(language, "order_status_updated", status=status),
        "order_id": order_id,
        "new_status": status
    }


# Admin Image Upload Endpoint (with multilingual support)
@router.post("/rasmlar", response_model=dict)
async def upload_product_image(
    file: UploadFile = File(...),
    token: str = None,
    language: str = Depends(admin_language_dependency)
):
    """Upload product image"""
    verify_admin_token(token, language)
    
    # Validate file type
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=400,
            detail=get_admin_message(language, "invalid_image")
        )
    
    # Generate unique filename
    file_extension = os.path.splitext(file.filename)[1]
    filename = f"{uuid4()}{file_extension}"
    filepath = f"uploads/{filename}"
    
    # Ensure upload directory exists
    os.makedirs("uploads", exist_ok=True)
    
    try:
        # Save file
        async with aiofiles.open(filepath, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)
        
        # Return URL (in production, use proper base URL)
        return {
            "message": get_admin_message(language, "image_uploaded"),
            "image_url": f"/uploads/{filename}",
            "filename": filename
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# Admin Dashboard Statistics (with multilingual support)
@router.get("/dashboard/stats")
async def admin_get_dashboard_stats(
    token: str,
    db: AsyncSession = Depends(get_db),
    language: str = Depends(admin_language_dependency)
):
    """Admin: Get dashboard statistics"""
    verify_admin_token(token, language)
    
    product_service = ProductService(db)
    order_service = OrderService(db)
    
    # Get products
    products = await product_service.get_products()
    total_products = len(products)
    out_of_stock = sum(1 for p in products if p.stock == 0)
    low_stock = sum(1 for p in products if 0 < p.stock <= 5)
    
    # Get orders
    orders = await order_service.get_all_orders()
    total_orders = len(orders)
    pending_orders = sum(1 for o in orders if o.status == "pending")
    completed_orders = sum(1 for o in orders if o.status == "delivered")
    
    # Calculate total revenue
    total_revenue = sum(o.total_amount for o in orders if o.status == "delivered")
    
    return {
        "products": {
            "total": total_products,
            "out_of_stock": out_of_stock,
            "low_stock": low_stock
        },
        "orders": {
            "total": total_orders,
            "pending": pending_orders,
            "completed": completed_orders
        },
        "revenue": {
            "total": total_revenue,
            "formatted": f"${total_revenue:.2f}"
        },
        "message": get_admin_message(language, "products_retrieved")
    }