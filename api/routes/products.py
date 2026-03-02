from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List, Optional, Dict, Any

from database.session import get_db
from database.models import User
from services.product import ProductService
from schemas.schemas import Product, ProductCreate, ProductUpdate, Category, LanguageUpdate, LanguageResponse

router = APIRouter()

# Multilingual messages for API responses
PRODUCT_MESSAGES = {
    "en": {
        # Product messages
        "product_not_found": "Product not found",
        "category_not_found": "Category not found",
        "product_deleted": "Product deleted successfully",
        "category_created": "Category created successfully",
        "product_created": "Product created successfully",
        "product_updated": "Product updated successfully",
        "products_retrieved": "Products retrieved successfully",
        "categories_retrieved": "Categories retrieved successfully",
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
        # Product messages
        "product_not_found": "Mahsulot topilmadi",
        "category_not_found": "Kategoriya topilmadi",
        "product_deleted": "Mahsulot muvaffaqiyatli o'chirildi",
        "category_created": "Kategoriya muvaffaqiyatli yaratildi",
        "product_created": "Mahsulot muvaffaqiyatli yaratildi",
        "product_updated": "Mahsulot muvaffaqiyatli yangilandi",
        "products_retrieved": "Mahsulotlar muvaffaqiyatli olindi",
        "categories_retrieved": "Kategoriyalar muvaffaqiyatli olindi",
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
        # Product messages
        "product_not_found": "Товар не найден",
        "category_not_found": "Категория не найдена",
        "product_deleted": "Товар успешно удалён",
        "category_created": "Категория успешно создана",
        "product_created": "Товар успешно создан",
        "product_updated": "Товар успешно обновлён",
        "products_retrieved": "Товары успешно получены",
        "categories_retrieved": "Категории успешно получены",
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
SUPPORTED_LANGUAGES = list(PRODUCT_MESSAGES.keys())

# Helper function to get message by language
def get_product_message(language: str, key: str, **kwargs) -> str:
    """Get product message by language with optional formatting"""
    if language not in PRODUCT_MESSAGES:
        language = "en"
    
    msg_dict = PRODUCT_MESSAGES.get(language, PRODUCT_MESSAGES["en"])
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
        languages=PRODUCT_MESSAGES[language]["language_names"],
        message=get_product_message(language, "supported_languages")
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
                detail=get_product_message("en", "user_not_found")
            )
        
        language = user.language if hasattr(user, 'language') and user.language else "en"
    else:
        # Get from request headers
        language = await get_user_language_from_request(request, db=db)
    
    language_name = PRODUCT_MESSAGES[language]["language_names"][language]
    
    return {
        "language_code": language,
        "language_name": language_name,
        "message": get_product_message(
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
            detail=get_product_message(
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
            detail=get_product_message("en", "user_not_found")
        )
    
    # Update language
    stmt = update(User).where(User.id == user_id).values(language=language_update.language)
    await db.execute(stmt)
    await db.commit()
    
    # Get response in the new language
    language_name = PRODUCT_MESSAGES[language_update.language]["language_names"][language_update.language]
    
    return {
        "user_id": user_id,
        "language_code": language_update.language,
        "language_name": language_name,
        "message": get_product_message(
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
        "language_name": PRODUCT_MESSAGES[lang_code]["language_names"][lang_code],
        "messages": PRODUCT_MESSAGES[lang_code]
    }


# Category Endpoints (with multilingual support)
@router.get("/categories", response_model=List[Category])
async def get_categories(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    language: str = Depends(language_dependency)
):
    """Get all categories"""
    service = ProductService(db)
    categories = await service.get_categories()
    return categories[skip:skip + limit]


@router.post("/categories", response_model=Category, status_code=201)
async def create_category(
    name: str,
    description: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    language: str = Depends(language_dependency)
):
    """Create new category"""
    service = ProductService(db)
    
    # Check if category already exists
    existing_categories = await service.get_categories()
    if any(cat.name.lower() == name.lower() for cat in existing_categories):
        raise HTTPException(
            status_code=400,
            detail=f"Category '{name}' already exists"
        )
    
    try:
        category = await service.create_category(name, description)
        return category
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# Product Endpoints (with multilingual support)
@router.get("/", response_model=List[Product])
async def get_products(
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    language: str = Depends(language_dependency)
):
    """Get all products"""
    service = ProductService(db)
    products = await service.get_products(category_id, skip, limit)
    return products


@router.get("/search", response_model=List[Product])
async def search_products(
    q: str = Query(..., min_length=1, description="Search query"),
    db: AsyncSession = Depends(get_db),
    language: str = Depends(language_dependency)
):
    """Search products by name"""
    service = ProductService(db)
    products = await service.search_products(q)
    return products


@router.get("/{product_id}", response_model=Product)
async def get_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    language: str = Depends(language_dependency)
):
    """Get product by ID"""
    service = ProductService(db)
    product = await service.get_product(product_id)
    
    if not product:
        raise HTTPException(
            status_code=404,
            detail=get_product_message(language, "product_not_found")
        )
    
    return product


@router.post("/", response_model=Product, status_code=201)
async def create_product(
    product: ProductCreate,
    db: AsyncSession = Depends(get_db),
    language: str = Depends(language_dependency)
):
    """Create new product"""
    service = ProductService(db)
    
    # Verify category exists
    if product.category_id:
        categories = await service.get_categories()
        category_exists = any(cat.id == product.category_id for cat in categories)
        if not category_exists:
            raise HTTPException(
                status_code=404,
                detail=get_product_message(language, "category_not_found")
            )
    
    try:
        new_product = await service.create_product(product)
        return new_product
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.put("/{product_id}", response_model=Product)
async def update_product(
    product_id: int,
    product_update: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    language: str = Depends(language_dependency)
):
    """Update product"""
    service = ProductService(db)
    
    # Verify category exists if provided
    if product_update.category_id:
        categories = await service.get_categories()
        category_exists = any(cat.id == product_update.category_id for cat in categories)
        if not category_exists:
            raise HTTPException(
                status_code=404,
                detail=get_product_message(language, "category_not_found")
            )
    
    product = await service.update_product(product_id, product_update)
    
    if not product:
        raise HTTPException(
            status_code=404,
            detail=get_product_message(language, "product_not_found")
        )
    
    return product


@router.delete("/{product_id}")
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    language: str = Depends(language_dependency)
):
    """Delete product"""
    service = ProductService(db)
    deleted = await service.delete_product(product_id)
    
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail=get_product_message(language, "product_not_found")
        )
    
    return {
        "message": get_product_message(language, "product_deleted"),
        "product_id": product_id
    }


# Optional: Endpoint to get product statistics with language support
@router.get("/stats/summary")
async def get_product_summary(
    db: AsyncSession = Depends(get_db),
    language: str = Depends(language_dependency)
):
    """Get product summary statistics"""
    service = ProductService(db)
    products = await service.get_products()
    categories = await service.get_categories()
    
    total_products = len(products)
    total_categories = len(categories)
    out_of_stock = sum(1 for p in products if p.stock == 0)
    low_stock = sum(1 for p in products if 0 < p.stock <= 5)
    
    return {
        "total_products": total_products,
        "total_categories": total_categories,
        "out_of_stock": out_of_stock,
        "low_stock": low_stock,
        "message": get_product_message(language, "products_retrieved")
    }