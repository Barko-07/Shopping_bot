from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import Optional

from bot.keyboards import (
    get_main_keyboard, get_categories_keyboard, get_products_keyboard,
    get_product_actions_keyboard, get_language_keyboard, get_back_keyboard
)
from database.session import get_db
from database.models import User
from services.product import ProductService
from services.cart import CartService
from config import config

# Import admin functions at module level
from bot.handlers.admin import admin_panel as admin_panel_handler

router = Router()

# States for search
class SearchStates(StatesGroup):
    waiting_for_search = State()

# Multilingual messages for user interface
USER_MESSAGES = {
    "en": {
        # Welcome & Main Menu
        "welcome": "👋 Welcome to Our Shop, {name}!\n\nUse the buttons below to navigate:",
        "welcome_back": "👋 Welcome back, {name}!",
        "main_menu": "Main Menu",
        
        # Language
        "select_language": "🌐 Please select your language:",
        "language_changed": "✅ Language changed to {language}!",
        
        # Categories
        "browse_categories": "🛍 Browse Categories",
        "select_category": "📂 Select a category:",
        "no_categories": "😔 No categories available at the moment.",
        "categories": "Categories",
        
        # Products
        "products_in_category": "📦 Products in *{category}*:",
        "no_products": "😔 No products in this category.",
        "products_found": "🔍 Found *{count}* products:",
        "no_products_found": "😔 No products found. Try another search.",
        "search_prompt": "🔍 Please enter the product name you're looking for:",
        "product_details": "📦 *{name}*\n\n💰 Price: {price:,.0f} so'm\n📦 Stock: {stock}\n\n📝 Description:\n{description}",
        "product_not_found": "❌ Product not found.",
        "search_results": "Search Results",
        
        # Cart
        "view_cart": "🛒 View Cart",
        "my_orders": "📦 My Orders",
        
        # Admin
        "admin_panel": "⚙️ Admin Panel",
        "admin_access_denied": "⛔ You don't have access to admin panel.",
        
        # Buttons
        "back": "🔙 Back",
        "back_to_categories": "🔙 Back to Categories",
        "back_to_main": "🔙 Main Menu",
        "add_to_cart": "➕ Add to Cart",
        "remove_from_cart": "➖ Remove from Cart",
        "in_cart": "✅ In Cart",
        
        # Pagination
        "previous": "◀️ Previous",
        "next": "Next ▶️",
        "page_info": "Page {page} of {total}",
        
        # Errors
        "error_occurred": "❌ An error occurred: {error}",
        "try_again": "Please try again later."
    },
    "uz": {
        # Welcome & Main Menu
        "welcome": "👋 Do'konimizga xush kelibsiz, {name}!\n\nQuyidagi tugmalardan foydalaning:",
        "welcome_back": "👋 Xush kelibsiz, {name}!",
        "main_menu": "Asosiy menyu",
        
        # Language
        "select_language": "🌐 Iltimos, tilni tanlang:",
        "language_changed": "✅ Til {language} ga o'zgartirildi!",
        
        # Categories
        "browse_categories": "🛍 Kategoriyalar",
        "select_category": "📂 Kategoriyani tanlang:",
        "no_categories": "😔 Hozircha kategoriyalar mavjud emas.",
        "categories": "Kategoriyalar",
        
        # Products
        "products_in_category": "📦 *{category}*:",
        "no_products": "😔 Bu kategoriyada mahsulotlar yo'q.",
        "products_found": "🔍 *{count}* ta mahsulot topildi:",
        "no_products_found": "😔 Mahsulotlar topilmadi. Boshqa qidiruvni sinab ko'ring.",
        "search_prompt": "🔍 Qidirayotgan mahsulot nomini kiriting:",
        "product_details": "📦 *{name}*\n\n💰 Narxi: {price:,.0f} so'm\n📦 Omborda: {stock}\n\n📝 Tavsif:\n{description}",
        "product_not_found": "❌ Mahsulot topilmadi.",
        "search_results": "Qidiruv natijalari",
        
        # Cart
        "view_cart": "🛒 Savat",
        "my_orders": "📦 Buyurtmalarim",
        
        # Admin
        "admin_panel": "⚙️ Admin Panel",
        "admin_access_denied": "⛔ Siz admin panelga kirish huquqiga ega emassiz.",
        
        # Buttons
        "back": "🔙 Orqaga",
        "back_to_categories": "🔙 Kategoriyalarga qaytish",
        "back_to_main": "🔙 Asosiy menyu",
        "add_to_cart": "➕ Savatga qo'shish",
        "remove_from_cart": "➖ Savatdan olib tashlash",
        "in_cart": "✅ Savatda",
        
        # Pagination
        "previous": "◀️ Oldingi",
        "next": "Keyingi ▶️",
        "page_info": "{page} / {total} sahifa",
        
        # Errors
        "error_occurred": "❌ Xatolik yuz berdi: {error}",
        "try_again": "Iltimos, keyinroq qayta urinib ko'ring."
    },
    "ru": {
        # Welcome & Main Menu
        "welcome": "👋 Добро пожаловать в наш магазин, {name}!\n\nИспользуйте кнопки ниже:",
        "welcome_back": "👋 С возвращением, {name}!",
        "main_menu": "Главное меню",
        
        # Language
        "select_language": "🌐 Пожалуйста, выберите язык:",
        "language_changed": "✅ Язык изменен на {language}!",
        
        # Categories
        "browse_categories": "🛍 Категории",
        "select_category": "📂 Выберите категорию:",
        "no_categories": "😔 На данный момент категории отсутствуют.",
        "categories": "Категории",
        
        # Products
        "products_in_category": "📦 Товары в категории *{category}*:",
        "no_products": "😔 В этой категории нет товаров.",
        "products_found": "🔍 Найдено *{count}* товаров:",
        "no_products_found": "😔 Товары не найдены. Попробуйте другой поиск.",
        "search_prompt": "🔍 Введите название товара:",
        "product_details": "📦 *{name}*\n\n💰 Цена: {price:,.0f} so'm\n📦 В наличии: {stock}\n\n📝 Описание:\n{description}",
        "product_not_found": "❌ Товар не найден.",
        "search_results": "Результаты поиска",
        
        # Cart
        "view_cart": "🛒 Корзина",
        "my_orders": "📦 Мои заказы",
        
        # Admin
        "admin_panel": "⚙️ Админ Панель",
        "admin_access_denied": "⛔ У вас нет доступа к админ панели.",
        
        # Buttons
        "back": "🔙 Назад",
        "back_to_categories": "🔙 К категориям",
        "back_to_main": "🔙 Главное меню",
        "add_to_cart": "➕ В корзину",
        "remove_from_cart": "➖ Из корзины",
        "in_cart": "✅ В корзине",
        
        # Pagination
        "previous": "◀️ Предыдущая",
        "next": "Следующая ▶️",
        "page_info": "Страница {page} из {total}",
        
        # Errors
        "error_occurred": "❌ Произошла ошибка: {error}",
        "try_again": "Пожалуйста, попробуйте позже."
    }
}

async def get_user_language(telegram_id: int) -> str:
    """Get user's language preference"""
    async for session in get_db():
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        if user and hasattr(user, 'language') and user.language:
            return user.language
        return "en"

async def set_user_language(telegram_id: int, language: str):
    """Set user's language preference"""
    async for session in get_db():
        await session.execute(
            update(User)
            .where(User.telegram_id == telegram_id)
            .values(language=language)
        )
        await session.commit()

def get_user_msg(language: str, key: str, **kwargs) -> str:
    """Get user message by language with formatting"""
    msg_dict = USER_MESSAGES.get(language, USER_MESSAGES["en"])
    msg = msg_dict.get(key, "")
    if kwargs and msg:
        try:
            return msg.format(**kwargs)
        except KeyError:
            return msg
    return msg

@router.message(CommandStart())
async def cmd_start(message: Message):
    """Handle /start command"""
    try:
        async for session in get_db():
            cart_service = CartService(session)
            
            # Get or create user
            user = await cart_service.get_or_create_user(
                telegram_id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name
            )
            
            # Set default language if not set
            if not hasattr(user, 'language') or not user.language:
                user.language = "en"
                await session.commit()
            
            # Check if user is admin
            is_admin = message.from_user.id in config.ADMIN_IDS
            if is_admin and not user.is_admin:
                user.is_admin = True
                await session.commit()
            
            # Get language
            language = user.language if hasattr(user, 'language') else "en"
            
            welcome_text = get_user_msg(
                language, 
                "welcome", 
                name=message.from_user.first_name or "Customer"
            )
            
            await message.answer(
                welcome_text,
                reply_markup=get_main_keyboard(is_admin, language)
            )
            return
    except Exception as e:
        await message.answer(f"Error: {str(e)}")

@router.message(F.text.in_(["🌐 Change Language", "🌐 Tilni o'zgartirish", "🌐 Сменить язык"]))
@router.message(Command("language"))
async def change_language(message: Message):
    """Show language selection"""
    language = await get_user_language(message.from_user.id)
    
    await message.answer(
        get_user_msg(language, "select_language"),
        reply_markup=get_language_keyboard()
    )

@router.callback_query(F.data.startswith("lang_"))
async def handle_language_change(callback: CallbackQuery):
    """Handle language selection"""
    language = callback.data.split("_")[1]
    await set_user_language(callback.from_user.id, language)
    
    # Get updated user info
    async for session in get_db():
        cart_service = CartService(session)
        user = await cart_service.get_or_create_user(callback.from_user.id)
        is_admin = user.is_admin or callback.from_user.id in config.ADMIN_IDS
    
    # Language names for display
    language_names = {
        "en": "English",
        "uz": "O'zbek",
        "ru": "Русский"
    }
    
    # Send confirmation in the selected language
    confirm_msg = get_user_msg(language, "language_changed", language=language_names[language])
    
    await callback.message.edit_text(confirm_msg)
    
    # Show main menu
    welcome_text = get_user_msg(
        language, 
        "welcome", 
        name=callback.from_user.first_name or "Customer"
    )
    
    await callback.message.answer(
        welcome_text,
        reply_markup=get_main_keyboard(is_admin, language)
    )
    await callback.answer()

@router.message(F.text.in_(["🛍 Browse Categories", "🛍 Kategoriyalar", "🛍 Категории"]))
async def browse_categories(message: Message):
    """Handle browse categories"""
    try:
        async for session in get_db():
            product_service = ProductService(session)
            categories = await product_service.get_categories()
            
            language = await get_user_language(message.from_user.id)
            
            if not categories:
                await message.answer(get_user_msg(language, "no_categories"))
                return
            
            await message.answer(
                get_user_msg(language, "select_category"),
                reply_markup=get_categories_keyboard(categories, language)
            )
    except Exception as e:
        language = await get_user_language(message.from_user.id)
        await message.answer(
            get_user_msg(language, "error_occurred", error=str(e))
        )

@router.message(F.text.in_(["🔍 Search Products", "🔍 Mahsulotlarni qidirish", "🔍 Поиск товаров"]))
async def search_products_start(message: Message, state: FSMContext):
    """Start product search"""
    await state.set_state(SearchStates.waiting_for_search)
    
    language = await get_user_language(message.from_user.id)
    
    await message.answer(
        get_user_msg(language, "search_prompt"),
        reply_markup=None
    )

@router.message(SearchStates.waiting_for_search)
async def search_products_process(message: Message, state: FSMContext):
    """Process search query"""
    try:
        async for session in get_db():
            product_service = ProductService(session)
            products = await product_service.search_products(message.text)
            
            await state.clear()
            
            language = await get_user_language(message.from_user.id)
            
            # Get user for admin status
            cart_service = CartService(session)
            user = await cart_service.get_or_create_user(message.from_user.id)
            is_admin = user.is_admin or message.from_user.id in config.ADMIN_IDS
            
            if not products:
                await message.answer(
                    get_user_msg(language, "no_products_found"),
                    reply_markup=get_main_keyboard(is_admin, language)
                )
                return
            
            # Show first page of results
            items_per_page = 5
            total_pages = (len(products) + items_per_page - 1) // items_per_page
            
            await message.answer(
                get_user_msg(language, "products_found", count=len(products)),
                reply_markup=get_products_keyboard(
                    products[:items_per_page], 
                    0, 
                    total_pages,
                    language
                )
            )
    except Exception as e:
        language = await get_user_language(message.from_user.id)
        await message.answer(
            get_user_msg(language, "error_occurred", error=str(e))
        )
        await state.clear()

@router.callback_query(F.data.startswith("category_"))
async def show_category_products(callback: CallbackQuery):
    """Show products in category"""
    try:
        category_id = int(callback.data.split("_")[1])
        
        async for session in get_db():
            product_service = ProductService(session)
            
            # Get category name
            categories = await product_service.get_categories()
            category_obj = next((c for c in categories if c.id == category_id), None)
            category_name = category_obj.name if category_obj else "Unknown"
            
            products = await product_service.get_products(category_id=category_id)
            
            language = await get_user_language(callback.from_user.id)
            
            if not products:
                await callback.message.edit_text(
                    get_user_msg(language, "no_products"),
                    reply_markup=get_categories_keyboard(
                        await product_service.get_categories(), 
                        language
                    )
                )
                return
            
            items_per_page = 5
            total_pages = (len(products) + items_per_page - 1) // items_per_page
            
            await callback.message.edit_text(
                get_user_msg(language, "products_in_category", category=category_name),
                parse_mode="Markdown",
                reply_markup=get_products_keyboard(
                    products[:items_per_page], 
                    0, 
                    total_pages,
                    language,
                    category_id=category_id
                )
            )
        
        await callback.answer()
    except Exception as e:
        await callback.answer(f"Error: {str(e)}", show_alert=True)

@router.callback_query(F.data.startswith("page_"))
async def paginate_products(callback: CallbackQuery):
    """Handle product pagination"""
    try:
        data_parts = callback.data.split("_")
        page = int(data_parts[1])
        
        # Check if category_id is in callback data
        category_id = None
        if len(data_parts) > 3 and data_parts[2] == "cat":
            category_id = int(data_parts[3])
        
        async for session in get_db():
            product_service = ProductService(session)
            
            # Get language first
            language = await get_user_language(callback.from_user.id)
            
            # Get products (filter by category if specified)
            if category_id:
                products = await product_service.get_products(category_id=category_id)
                category_name = None
                categories = await product_service.get_categories()
                category_obj = next((c for c in categories if c.id == category_id), None)
                category_name = category_obj.name if category_obj else "Unknown"
                title = get_user_msg(language, "products_in_category", category=category_name)
            else:
                products = await product_service.get_products()
                title = get_user_msg(language, "search_results")
            
            items_per_page = 5
            total_pages = (len(products) + items_per_page - 1) // items_per_page
            
            # Ensure page is within bounds
            if page < 0:
                page = 0
            elif page >= total_pages:
                page = total_pages - 1
            
            start = page * items_per_page
            end = min(start + items_per_page, len(products))
            
            await callback.message.edit_text(
                title,
                parse_mode="Markdown",
                reply_markup=get_products_keyboard(
                    products[start:end], 
                    page, 
                    total_pages,
                    language,
                    category_id=category_id
                )
            )
        
        await callback.answer()
    except Exception as e:
        await callback.answer(f"Error: {str(e)}", show_alert=True)

@router.callback_query(F.data == "back_to_categories")
async def back_to_categories(callback: CallbackQuery):
    """Go back to categories"""
    try:
        async for session in get_db():
            product_service = ProductService(session)
            categories = await product_service.get_categories()
            
            language = await get_user_language(callback.from_user.id)
            
            await callback.message.edit_text(
                get_user_msg(language, "select_category"),
                reply_markup=get_categories_keyboard(categories, language)
            )
        
        await callback.answer()
    except Exception as e:
        await callback.answer(f"Error: {str(e)}", show_alert=True)

@router.callback_query(F.data.startswith("product_"))
async def show_product(callback: CallbackQuery):
    """Show product details"""
    try:
        product_id = int(callback.data.split("_")[1])
        
        async for session in get_db():
            product_service = ProductService(session)
            cart_service = CartService(session)
            
            product = await product_service.get_product(product_id)
            if not product:
                language = await get_user_language(callback.from_user.id)
                await callback.message.edit_text(get_user_msg(language, "product_not_found"))
                await callback.answer()
                return
            
            # Check if product is in cart
            user = await cart_service.get_or_create_user(telegram_id=callback.from_user.id)
            cart_items = await cart_service.get_cart(user.id)
            in_cart = any(item.product_id == product_id for item in cart_items)
            
            # Get language
            language = await get_user_language(callback.from_user.id)
            
            # Create product message
            description = product.description or "No description"
            product_text = get_user_msg(
                language, 
                "product_details",
                name=product.name,
                price=product.price,
                stock=product.stock,
                description=description
            )
            
            if product.image_url:
                # Send photo with caption
                await callback.message.delete()
                await callback.message.answer_photo(
                    photo=product.image_url,
                    caption=product_text,
                    parse_mode="Markdown",
                    reply_markup=get_product_actions_keyboard(product_id, in_cart, language, product.stock)
                )
            else:
                # Send text only
                await callback.message.edit_text(
                    product_text,
                    parse_mode="Markdown",
                    reply_markup=get_product_actions_keyboard(product_id, in_cart, language, product.stock)
                )
        
        await callback.answer()
    except Exception as e:
        await callback.answer(f"Error: {str(e)}", show_alert=True)

@router.callback_query(F.data == "main_menu")
async def back_to_main_menu(callback: CallbackQuery):
    """Go back to main menu"""
    try:
        language = await get_user_language(callback.from_user.id)
        
        async for session in get_db():
            cart_service = CartService(session)
            user = await cart_service.get_or_create_user(callback.from_user.id)
            is_admin = user.is_admin or callback.from_user.id in config.ADMIN_IDS
        
        welcome_text = get_user_msg(
            language, 
            "welcome", 
            name=callback.from_user.first_name or "Customer"
        )
        
        # Delete the previous message and send new main menu
        await callback.message.delete()
        await callback.message.answer(
            welcome_text,
            reply_markup=get_main_keyboard(is_admin, language)
        )
        await callback.answer()
    except Exception as e:
        await callback.answer(f"Error: {str(e)}", show_alert=True)

@router.message(F.text.in_(["⚙️ Admin Panel", "⚙️ Админ Панель"]))
async def admin_panel_from_button(message: Message):
    """Handle Admin Panel button click"""
    await admin_panel_handler(message)

@router.message(F.text.in_(["📦 My Orders", "📦 Buyurtmalarim", "📦 Мои заказы"]))
async def show_my_orders(message: Message):
    """Show user's orders"""
    try:
        async for session in get_db():
            from services.order import OrderService
            cart_service = CartService(session)
            order_service = OrderService(session)
            
            user = await cart_service.get_or_create_user(message.from_user.id)
            orders = await order_service.get_user_orders(user.id)
            
            language = await get_user_language(message.from_user.id)
            
            if not orders:
                is_admin = user.is_admin or message.from_user.id in config.ADMIN_IDS
                await message.answer(
                    "📦 You haven't placed any orders yet." if language == "en" else
                    "📦 Siz hali buyurtma bermagansiz." if language == "uz" else
                    "📦 Вы еще не сделали заказов.",
                    reply_markup=get_main_keyboard(is_admin, language)
                )
                return
            
            orders_text = "📦 *Your Orders*\n\n" if language == "en" else \
                         "📦 *Buyurtmalaringiz*\n\n" if language == "uz" else \
                         "📦 *Ваши заказы*\n\n"
            
            for order in orders:
                status_emoji = {
                    "pending": "⏳",
                    "confirmed": "✅",
                    "paid": "✅",
                    "shipped": "📦",
                    "delivered": "🎉",
                    "cancelled": "❌"
                }.get(order.status, "📋")
                
                status_text = {
                    "en": order.status.capitalize(),
                    "uz": {
                        "pending": "Kutilmoqda",
                        "confirmed": "Tasdiqlangan",
                        "paid": "To'langan",
                        "shipped": "Yuborilgan",
                        "delivered": "Yetkazilgan",
                        "cancelled": "Bekor qilingan"
                    }.get(order.status, order.status),
                    "ru": {
                        "pending": "В ожидании",
                        "confirmed": "Подтверждён",
                        "paid": "Оплачено",
                        "shipped": "Отправлено",
                        "delivered": "Доставлено",
                        "cancelled": "Отменено"
                    }.get(order.status, order.status)
                }.get(language, order.status)
                
                orders_text += (
                    f"{status_emoji} Order: `{order.order_number}`\n"
                    f"💰 Total: {order.total_amount:,.0f} so'm\n"
                    f"📅 {order.created_at.strftime('%Y-%m-%d %H:%M')}\n"
                    f"{'─' * 25}\n"
                )
            
            is_admin = user.is_admin or message.from_user.id in config.ADMIN_IDS
            await message.answer(
                orders_text,
                parse_mode="Markdown",
                reply_markup=get_main_keyboard(is_admin, language)
            )
    except Exception as e:
        language = await get_user_language(message.from_user.id)
        await message.answer(
            get_user_msg(language, "error_occurred", error=str(e))
        )

# Removed the catch-all handler - handlers should be explicit
# This prevents the "I don't understand" message for button clicks
