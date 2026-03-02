from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List, Optional, Dict, Any

from database.session import get_db
from database.models import User
from services.order import OrderService
from services.cart import CartService
from schemas.schemas import Order, OrderCreate, LanguageUpdate, LanguageResponse

router = APIRouter()

# Multilingual messages for API responses
ORDER_MESSAGES = {
    "en": {
        # Order messages
        "order_not_found": "Order not found",
        "cart_empty": "Cart is empty",
        "product_not_found": "Product not found for cart item {item_id}",
        "insufficient_stock": "Insufficient stock for {product_name}",
        "invalid_status": "Status must be one of {allowed_statuses}",
        "status_updated": "Order status updated to {status}",
        "orders_retrieved": "Orders retrieved successfully",
        "order_created": "Order created successfully",
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
        # Order messages
        "order_not_found": "Buyurtma topilmadi",
        "cart_empty": "Savat bo'sh",
        "product_not_found": "Savat elementi {item_id} uchun mahsulot topilmadi",
        "insufficient_stock": "{product_name} uchun yetarli miqdor yo'q",
        "invalid_status": "Holat {allowed_statuses} dan biri bo'lishi kerak",
        "status_updated": "Buyurtma holati {status} ga o'zgartirildi",
        "orders_retrieved": "Buyurtmalar muvaffaqiyatli olindi",
        "order_created": "Buyurtma muvaffaqiyatli yaratildi",
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
        # Order messages
        "order_not_found": "Заказ не найден",
        "cart_empty": "Корзина пуста",
        "product_not_found": "Товар не найден для элемента корзины {item_id}",
        "insufficient_stock": "Недостаточно товара {product_name} на складе",
        "invalid_status": "Статус должен быть одним из {allowed_statuses}",
        "status_updated": "Статус заказа изменён на {status}",
        "orders_retrieved": "Заказы успешно получены",
        "order_created": "Заказ успешно создан",
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
SUPPORTED_LANGUAGES = list(ORDER_MESSAGES.keys())

# Helper function to get message by language
def get_order_message(language: str, key: str, **kwargs) -> str:
    """Get order message by language with optional formatting"""
    if language not in ORDER_MESSAGES:
        language = "en"
    
    msg_dict = ORDER_MESSAGES.get(language, ORDER_MESSAGES["en"])
    msg = msg_dict.get(key, key)
    
    if kwargs and msg:
        try:
            return msg.format(**kwargs)
        except KeyError:
            return msg
    return msg

# Function to get user language from database or header
async def get_user_language_from_request(
    request: Request,
    user_id: Optional[int] = None,
    db: AsyncSession = None
) -> str:
    """
    Get user's language preference from:
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

# Language dependency for routes
async def language_dependency(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> str:
    """Dependency to get user's language preference"""
    # Try to get user_id from query params
    user_id = request.query_params.get("user_id")
    if user_id and user_id.isdigit():
        return await get_user_language_from_request(request, int(user_id), db)
    
    return await get_user_language_from_request(request, db=db)


# Language Management Endpoints
@router.get("/languages", response_model=LanguageResponse)
async def get_available_languages(
    language: str = Depends(language_dependency)
):
    """Get list of available languages"""
    return LanguageResponse(
        current_language=language,
        supported_languages=SUPPORTED_LANGUAGES,
        languages=ORDER_MESSAGES[language]["language_names"],
        message=get_order_message(language, "supported_languages")
    )


@router.get("/languages/current")
async def get_current_language(
    user_id: Optional[int] = Query(None, description="User ID to check language"),
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    """Get current language for user or request"""
    if user_id:
        # Get from database
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=404,
                detail=get_order_message("en", "user_not_found")
            )
        
        language = user.language if hasattr(user, 'language') and user.language else "en"
    else:
        # Get from request headers
        language = await get_user_language_from_request(request, db=db)
    
    language_name = ORDER_MESSAGES[language]["language_names"][language]
    
    return {
        "language_code": language,
        "language_name": language_name,
        "message": get_order_message(
            language,
            "current_language",
            language=language_name
        )
    }


@router.put("/languages/{user_id}")
async def update_user_language(
    user_id: int,
    language_update: LanguageUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update user's language preference"""
    # Check if language is supported
    if language_update.language not in SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=400,
            detail=get_order_message(
                "en",  # Use English for error before we know user's language
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
            detail=get_order_message("en", "user_not_found")
        )
    
    # Update language
    stmt = update(User).where(User.id == user_id).values(language=language_update.language)
    await db.execute(stmt)
    await db.commit()
    
    # Get response in the new language
    language_name = ORDER_MESSAGES[language_update.language]["language_names"][language_update.language]
    
    return {
        "user_id": user_id,
        "language_code": language_update.language,
        "language_name": language_name,
        "message": get_order_message(
            language_update.language,
            "language_updated",
            language=language_name
        )
    }


@router.get("/languages/messages/{lang_code}")
async def get_language_messages(
    lang_code: str
):
    """Get all messages in specified language"""
    if lang_code not in SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=404,
            detail=f"Language '{lang_code}' not supported. Supported: {SUPPORTED_LANGUAGES}"
        )
    
    return {
        "language_code": lang_code,
        "language_name": ORDER_MESSAGES[lang_code]["language_names"][lang_code],
        "messages": ORDER_MESSAGES[lang_code]
    }


# Order Management Endpoints (with multilingual support)
@router.get("/", response_model=List[Order])
async def get_orders(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    language: str = Depends(language_dependency)
):
    """Get orders (filter by user_id if provided)"""
    service = OrderService(db)
    
    try:
        if user_id:
            orders = await service.get_user_orders(user_id)
        else:
            orders = await service.get_all_orders()
        
        # Apply pagination
        paginated_orders = orders[skip:skip + limit]
        
        return paginated_orders
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.get("/{order_id}", response_model=Order)
async def get_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    language: str = Depends(language_dependency)
):
    """Get order by ID"""
    service = OrderService(db)
    order = await service.get_order(order_id)
    
    if not order:
        raise HTTPException(
            status_code=404,
            detail=get_order_message(language, "order_not_found")
        )
    
    return order


@router.post("/", response_model=Order, status_code=201)
async def create_order(
    order: OrderCreate,
    db: AsyncSession = Depends(get_db),
    language: str = Depends(language_dependency)
):
    """Create new order"""
    service = OrderService(db)
    cart_service = CartService(db)
    
    # Verify cart items exist and have sufficient stock
    cart_items = await cart_service.get_cart(order.user_id)
    
    if not cart_items:
        raise HTTPException(
            status_code=400,
            detail=get_order_message(language, "cart_empty")
        )
    
    # Check stock
    for item in cart_items:
        if not item.product:
            raise HTTPException(
                status_code=400,
                detail=get_order_message(
                    language, 
                    "product_not_found", 
                    item_id=item.id
                )
            )
        
        if item.product.stock < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=get_order_message(
                    language,
                    "insufficient_stock",
                    product_name=item.product.name
                )
            )
    
    try:
        # Convert OrderCreate to dict for service
        order_dict = {
            "user_id": order.user_id,
            "customer_name": order.customer_name,
            "phone": order.phone,
            "address": order.address,
            "items": [item.dict() for item in order.items]
        }
        
        created_order = await service.create_order(order_dict)
        return created_order
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.patch("/{order_id}/status")
async def update_order_status(
    order_id: int,
    status: str = Query(..., description="New status for the order"),
    db: AsyncSession = Depends(get_db),
    language: str = Depends(language_dependency)
):
    """Update order status"""
    # Validate allowed statuses
    allowed_statuses = {"pending", "confirmed", "shipped", "delivered", "cancelled"}
    
    if status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail=get_order_message(
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
            detail=get_order_message(language, "order_not_found")
        )
    
    return {
        "message": get_order_message(
            language,
            "status_updated",
            status=status
        ),
        "order_id": order_id,
        "new_status": status
    }