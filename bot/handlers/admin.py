import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from database.models import Product, User, Order, Category

from bot.keyboards import (
    get_admin_keyboard, get_main_keyboard, get_language_keyboard,
    get_admin_categories_keyboard, get_admin_products_keyboard,
    get_order_status_keyboard, get_confirmation_keyboard, get_back_keyboard
)
from database.session import get_db
from services.product import ProductService
from services.order import OrderService
from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = Router()

# Admin States
class AddProductStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_price = State()
    waiting_for_category = State()
    waiting_for_stock = State()
    waiting_for_image = State()

class UpdateProductStates(StatesGroup):
    waiting_for_product_id = State()
    waiting_for_field = State()
    waiting_for_new_value = State()

class DeleteProductStates(StatesGroup):
    waiting_for_product_id = State()

class UpdateOrderStates(StatesGroup):
    waiting_for_order_id = State()
    waiting_for_status = State()

class AddCategoryStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_description = State()

# Language-specific messages
ADMIN_MESSAGES = {
    "uz": {
        # Admin Panel
        "admin_panel": "⚙️ *Admin Panel*\n\nQuyidagi tugmalardan birini tanlang:",
        "unauthorized": "⛔ Ruxsat berilmagan.",
        "action_cancelled": "❌ Amal bekor qilindi.",
        "back": "🔙 Admin Panelga qaytish",
        "main_menu": "🏠 Asosiy menyu",
        
        # Product Management
        "view_products": "📦 Mahsulotlarni ko'rish",
        "add_product": "➕ Mahsulot qo'shish",
        "update_product": "📝 Mahsulotni yangilash",
        "delete_product": "❌ Mahsulotni o'chirish",
        "view_orders": "📋 Buyurtmalarni ko'rish",
        "update_order_status": "🔄 Buyurtma holatini yangilash",
        "add_category": "➕ Kategoriya qo'shish",
        "view_categories": "📁 Kategoriyalarni ko'rish",
        "stats": "📊 Statistika",
        
        # Add Product Flow
        "select_category": "📂 *Yangi Mahsulot uchun Kategoriyani tanlang*\n\nKategoriyani tanlang:",
        "no_categories": "⚠️ Kategoriyalar mavjud emas!\n\nAvval '➕ Kategoriya qo'shish' tugmasi orqali kategoriya qo'shing.",
        "enter_name": "📝 Mahsulot nomini kiriting:",
        "enter_description": "📝 Mahsulot tavsifini kiriting (bo'sh qoldirish uchun 'skip' yozing):",
        "enter_price": "💰 Mahsulot narxini kiriting (masalan, 10000):",
        "enter_stock": "📦 Ombordagi miqdorni kiriting:",
        "enter_image": "🖼️ Mahsulot rasmini yuklang yoki URL manzilini yuboring (rasmsiz uchun 'skip' yozing):",
        "product_added": "✅ Mahsulot muvaffaqiyatli qo'shildi!\n\n*Mahsulot tafsilotlari:*\nNomi: {name}\nNarxi: {price:,.0f} so'm\nSoni: {stock} dona\nKategoriya: {category}",
        
        # View Products
        "products_list": "📦 *Barcha Mahsulotlar* (jami: {count})\n\n",
        "no_products": "😔 Hali mahsulotlar mavjud emas.\n\n➕ 'Mahsulot qo'shish' tugmasi orqali yangi mahsulot qo'shing.",
        "product_details": "*Mahsulot tafsilotlari:*\nID: {id}\nNomi: {name}\nNarxi: {price:,.0f} so'm\nSoni: {stock} dona\nKategoriya: {category}",
        
        # Delete Product
        "select_product_delete": "🗑️ *Mahsulotni o'chirish*\n\nO'chirish uchun mahsulot ID sini kiriting:",
        "confirm_delete": "⚠️ Ushbu mahsulotni o'chirishni tasdiqlaysizmi?\n\n{product_details}",
        "delete_confirmed": "✅ Mahsulot muvaffaqiyatli o'chirildi!",
        "delete_cancelled": "❌ O'chirish bekor qilindi.",
        
        # Update Product
        "select_product_update": "📝 *Mahsulotni yangilash*\n\nYangilash uchun mahsulot ID sini kiriting:",
        "select_field": "🔧 *Qaysi maydonni yangilamoqchisiz?*",
        "field_options": "• name - Mahsulot nomi\n• price - Mahsulot narxi\n• stock - Ombordagi miqdor\n• description - Mahsulot tavsifi",
        "enter_new_value": "✏️ *{field}* uchun yangi qiymatni kiriting:",
        "confirm_update": "✅ Yangilashni tasdiqlaysizmi?\n\nMaydon: {field}\nYangi qiymat: {value}",
        "product_updated": "✅ Mahsulot muvaffaqiyatli yangilandi!",
        "update_cancelled": "❌ Yangilash bekor qilindi.",
        
        # Add Category
        "add_category_start": "📁 *Yangi Kategoriya qo'shish*\n\nKategoriya nomini kiriting:",
        "enter_category_description": "📝 Kategoriya tavsifini kiriting (bo'sh qoldirish uchun 'skip' yozing):",
        "category_added": "✅ '{name}' kategoriyasi muvaffaqiyatli qo'shildi!",
        "categories_list": "📁 *Barcha Kategoriyalar* (jami: {count})\n\n",
        "no_categories_list": "😔 Hali kategoriyalar mavjud emas.",
        
        # Order Management
        "orders_list": "📋 *Barcha Buyurtmalar* (jami: {count})\n\n",
        "no_orders": "😔 Hali buyurtmalar yo'q.",
        "order_details": "*Buyurtma tafsilotlari*\n\nBuyurtma: `{order_number}`\nMijoz: {customer_name}\nTelefon: {phone}\nManzil: {address}\nJami: {total:,.0f} so'm\nHolat: *{status}*\nSana: {date}",
        "select_order_update": "🔄 *Buyurtma holatini yangilash*\n\nYangilash uchun buyurtma ID sini kiriting:",
        "select_status": "📊 *Yangi holatni tanlang*\n\n#{order_id} buyurtma uchun yangi holatni tanlang:",
        "order_status_updated": "✅ Buyurtma holati *{status}* ga yangilandi!",
        
        # Statistics
        "stats": "📊 *Statistika*\n\n",
        "total_products": "📦 Jami mahsulotlar: {count}",
        "total_categories": "📁 Jami kategoriyalar: {count}",
        "total_orders": "📋 Jami buyurtmalar: {count}",
        "pending_orders": "⏳ Kutilayotgan buyurtmalar: {count}",
        "delivered_orders": "✅ Yetkazilgan buyurtmalar: {count}",
        "cancelled_orders": "❌ Bekor qilingan buyurtmalar: {count}",
        "total_revenue": "💰 Umumiy daromad: {amount:,.0f} so'm",
        "out_of_stock": "⚠️ Omborda yo'q mahsulotlar: {count}",
        "low_stock": "📦 Kam qolgan mahsulotlar (<5): {count}",
        
        # Validation Messages
        "invalid_price": "❌ Iltimos, to'g'ri narx raqamini kiriting (masalan, 10000).",
        "invalid_stock": "❌ Iltimos, to'g'ri miqdor kiriting (musbat butun son).",
        "invalid_product_id": "❌ Noto'g'ri mahsulot ID si. Iltimos, raqam kiriting.",
        "product_not_found": "❌ Mahsulot topilmadi.",
        "invalid_order_id": "❌ Noto'g'ri buyurtma ID si. Iltimos, raqam kiriting.",
        "order_not_found": "❌ Buyurtma topilmadi.",
        "invalid_status": "❌ Noto'g'ri holat. Iltimos, berilgan tugmalardan foydalaning.",
        
        # Error Messages
        "error_occurred": "❌ Xatolik yuz berdi: {error}",
        "failed_update": "❌ Mahsulotni yangilash muvaffaqiyatsiz tugadi.",
        "failed_delete": "❌ Mahsulotni o'chirish muvaffaqiyatsiz tugadi.",
        "failed_add_category": "❌ Kategoriya qo'shish muvaffaqiyatsiz tugadi.",
        
        # Buttons
        "confirm": "✅ Tasdiqlash",
        "cancel": "❌ Bekor qilish",
        "skip": "⏭️ O'tkazib yuborish",
        "refresh": "🔄 Yangilash",
        "back": "🔙 Orqaga",
        
        # Unknown command
        "unknown_command": "❌ Men bu buyruqni tushunmadim. Iltimos, quyidagi tugmalardan foydalaning:"
    },
    "ru": {
        "admin_panel": "⚙️ *Админ Панель*\n\nВыберите действие:",
        "unauthorized": "⛔ Доступ запрещен.",
        "action_cancelled": "❌ Действие отменено.",
        "no_products": "😔 Товары еще не добавлены.\n\n➕ Добавьте новый товар через кнопку 'Добавить товар'.",
        "back": "🔙 Назад",
        "main_menu": "🏠 Главное меню",
        "view_products": "📦 Просмотр товаров",
        "add_product": "➕ Добавить товар",
        "update_product": "📝 Обновить товар",
        "delete_product": "❌ Удалить товар",
        "view_orders": "📋 Просмотр заказов",
        "update_order_status": "🔄 Обновить статус заказа",
        "add_category": "➕ Добавить категорию",
        "view_categories": "📁 Просмотр категорий",
        "stats": "📊 Статистика",
        "select_category": "📂 *Выберите категорию для нового товара*\n\nВыберите категорию:",
        "no_categories": "⚠️ Категории недоступны!\n\nСначала добавьте категорию через кнопку '➕ Добавить категорию'.",
        "enter_name": "📝 Введите название товара:",
        "enter_description": "📝 Введите описание товара (или 'skip'):",
        "enter_price": "💰 Введите цену товара (например, 10000):",
        "enter_stock": "📦 Введите количество на складе:",
        "enter_image": "🖼️ Загрузите изображение или URL (или 'skip'):",
        "product_added": "✅ Товар успешно добавлен!\n\n*Детали товара:*\nНазвание: {name}\nЦена: {price:,.0f} so'm\nКоличество: {stock} шт\nКатегория: {category}",
        "no_products": "😔 Товары еще не добавлены.",
        "invalid_price": "❌ Введите правильную цену.",
        "invalid_stock": "❌ Введите правильное количество.",
        "product_not_found": "❌ Товар не найден.",
        "error_occurred": "❌ Произошла ошибка: {error}",
        "unknown_command": "❌ Я не понимаю эту команду. Пожалуйста, используйте кнопки ниже:"
    },
    "en": {
        "admin_panel": "⚙️ *Admin Panel*\n\nSelect an action:",
        "unauthorized": "⛔ Unauthorized access.",
        "action_cancelled": "❌ Action cancelled.",
        "no_products": "😔 No products available yet.\n\n➕ Add a new product using the 'Add Product' button.",
        "back": "🔙 Back",
        "main_menu": "🏠 Main Menu",
        "view_products": "📦 View Products",
        "add_product": "➕ Add Product",
        "update_product": "📝 Update Product",
        "delete_product": "❌ Delete Product",
        "view_orders": "📋 View Orders",
        "update_order_status": "🔄 Update Order Status",
        "add_category": "➕ Add Category",
        "view_categories": "📁 View Categories",
        "stats": "📊 Statistics",
        "select_category": "📂 *Select Category for New Product*\n\nChoose a category:",
        "no_categories": "⚠️ No categories available!\n\nFirst add a category using the '➕ Add Category' button.",
        "enter_name": "📝 Enter product name:",
        "enter_description": "📝 Enter product description (or 'skip'):",
        "enter_price": "💰 Enter product price (e.g., 10000):",
        "enter_stock": "📦 Enter stock quantity:",
        "enter_image": "🖼️ Upload image or URL (or 'skip'):",
        "product_added": "✅ Product added successfully!\n\n*Product details:*\nName: {name}\nPrice: {price:,.0f} so'm\nStock: {stock} pcs\nCategory: {category}",
        "invalid_price": "❌ Please enter a valid price.",
        "invalid_stock": "❌ Please enter a valid quantity.",
        "product_not_found": "❌ Product not found.",
        "error_occurred": "❌ An error occurred: {error}",
        "unknown_command": "❌ I don't understand this command. Please use the buttons below:"
    }
}

# Order status translations
ORDER_STATUS = {
    "uz": {
        "pending": "⏳ Kutilmoqda",
        "confirmed": "✅ Tasdiqlangan",
        "shipped": "📦 Yuborilgan",
        "delivered": "🎉 Yetkazilgan",
        "cancelled": "❌ Bekor qilingan"
    },
    "ru": {
        "pending": "⏳ В ожидании",
        "confirmed": "✅ Подтверждён",
        "shipped": "📦 Отправлено",
        "delivered": "🎉 Доставлено",
        "cancelled": "❌ Отменено"
    },
    "en": {
        "pending": "⏳ Pending",
        "confirmed": "✅ Confirmed",
        "shipped": "📦 Shipped",
        "delivered": "🎉 Delivered",
        "cancelled": "❌ Cancelled"
    }
}

async def get_user_language(telegram_id: int) -> str:
    """Get user's language preference"""
    async for session in get_db():
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if user and hasattr(user, 'language') and user.language:
            return user.language
        return "uz"

def get_admin_msg(language: str, key: str, **kwargs) -> str:
    """Get admin message by language with formatting"""
    if language not in ADMIN_MESSAGES:
        language = "uz"
    
    msg_dict = ADMIN_MESSAGES.get(language, ADMIN_MESSAGES["uz"])
    msg = msg_dict.get(key, "")
    
    if kwargs and msg:
        try:
            return msg.format(**kwargs)
        except KeyError:
            return msg
    return msg

async def is_admin(message_or_callback) -> bool:
    """Check if user is admin"""
    user_id = message_or_callback.from_user.id
    
    # Debug log
    logger.info(f"Checking admin status for user_id: {user_id}, config.ADMIN_IDS: {config.ADMIN_IDS}")
    
    # First check config.ADMIN_IDS (from environment variables)
    if user_id in config.ADMIN_IDS:
        logger.info(f"User {user_id} is admin via config.ADMIN_IDS")
        return True
    
    # Also check database is_admin field
    try:
        async for session in get_db():
            result = await session.execute(
                select(User).where(User.telegram_id == user_id)
            )
            user = result.scalar_one_or_none()
            if user and user.is_admin:
                logger.info(f"User {user_id} is admin via database")
                return True
    except Exception as e:
        logger.error(f"Error checking admin status: {e}")
    
    logger.info(f"User {user_id} is NOT admin")
    return False

async def get_category_name(session: AsyncSession, category_id: int = None) -> str:
    """Get category name by ID"""
    if not category_id:
        return "Kategoriyasiz"
    
    result = await session.execute(select(Category).where(Category.id == category_id))
    category = result.scalar_one_or_none()
    return category.name if category else "Kategoriyasiz"

# Main Admin Panel
@router.message(F.text == "⚙️ Admin Panel")
@router.message(Command("admin"))
async def admin_panel(message: Message):
    if not await is_admin(message):
        language = await get_user_language(message.from_user.id)
        await message.answer(get_admin_msg(language, "unauthorized"))
        return
    
    language = await get_user_language(message.from_user.id)
    
    # Get counts for display
    async for session in get_db():
        product_count = await session.scalar(select(func.count()).select_from(Product))
        order_count = await session.scalar(select(func.count()).select_from(Order))
    
    admin_text = (
        f"⚙️ *Admin Panel*\n\n"
        f"📊 **Statistika:**\n"
        f"📦 Mahsulotlar: {product_count or 0}\n"
        f"📋 Buyurtmalar: {order_count or 0}\n\n"
        f"👇 Quyidagi tugmalardan birini tanlang:"
    )
    
    await message.answer(
        admin_text,
        parse_mode="Markdown",
        reply_markup=get_admin_keyboard(language)
    )

@router.message(Command("cancel"))
@router.message(F.text.casefold().in_(["cancel", "bekor qilish", "отмена"]))
async def cancel_admin_action(message: Message, state: FSMContext):
    """Cancel any admin action"""
    current_state = await state.get_state()
    if current_state is None:
        return
    
    await state.clear()
    language = await get_user_language(message.from_user.id)
    await message.answer(
        get_admin_msg(language, "action_cancelled"),
        reply_markup=get_admin_keyboard(language)
    )

@router.callback_query(F.data == "admin_panel")
async def back_to_admin_panel(callback: CallbackQuery):
    if not await is_admin(callback):
        await callback.answer(get_admin_msg("uz", "unauthorized"), show_alert=True)
        return
    
    language = await get_user_language(callback.from_user.id)
    
    # Get counts for display
    async for session in get_db():
        product_count = await session.scalar(select(func.count()).select_from(Product))
        order_count = await session.scalar(select(func.count()).select_from(Order))
    
    admin_text = (
        f"⚙️ *Admin Panel*\n\n"
        f"📊 **Statistika:**\n"
        f"📦 Mahsulotlar: {product_count or 0}\n"
        f"📋 Buyurtmalar: {order_count or 0}\n\n"
        f"👇 Quyidagi tugmalardan birini tanlang:"
    )
    
    await callback.message.edit_text(
        admin_text,
        parse_mode="Markdown",
        reply_markup=get_admin_keyboard(language)
    )
    await callback.answer()

# main_menu handler from admin router REMOVED:
# This handler conflicts with user/cart handlers and causes "Ruxsat berilmagan" issues
# Admin users should go back to admin_panel, not main_menu

# Statistics
@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    """Show admin statistics"""
    if not await is_admin(callback):
        await callback.answer(get_admin_msg("uz", "unauthorized"), show_alert=True)
        return
    
    language = await get_user_language(callback.from_user.id)
    
    async for session in get_db():
        # Get counts
        total_products = await session.scalar(select(func.count()).select_from(Product)) or 0
        total_categories = await session.scalar(select(func.count()).select_from(Category)) or 0
        total_orders = await session.scalar(select(func.count()).select_from(Order)) or 0
        
        # Get orders by status
        pending_orders = await session.scalar(
            select(func.count()).select_from(Order).where(Order.status == "pending")
        ) or 0
        delivered_orders = await session.scalar(
            select(func.count()).select_from(Order).where(Order.status == "delivered")
        ) or 0
        cancelled_orders = await session.scalar(
            select(func.count()).select_from(Order).where(Order.status == "cancelled")
        ) or 0
        
        # Get total revenue
        delivered_orders_list = await session.execute(
            select(Order).where(Order.status == "delivered")
        )
        total_revenue = sum(order.total_amount for order in delivered_orders_list.scalars().all())
        
        # Get stock info
        products = await session.execute(select(Product))
        products_list = products.scalars().all()
        out_of_stock = sum(1 for p in products_list if p.stock == 0)
        low_stock = sum(1 for p in products_list if 0 < p.stock <= 5)
        
        stats_text = (
            f"📊 *Statistika*\n\n"
            f"📦 Jami mahsulotlar: {total_products}\n"
            f"📁 Jami kategoriyalar: {total_categories}\n"
            f"📋 Jami buyurtmalar: {total_orders}\n"
            f"{'─' * 20}\n"
            f"⏳ Kutilayotgan buyurtmalar: {pending_orders}\n"
            f"✅ Yetkazilgan buyurtmalar: {delivered_orders}\n"
            f"❌ Bekor qilingan buyurtmalar: {cancelled_orders}\n"
            f"{'─' * 20}\n"
            f"💰 Umumiy daromad: {total_revenue:,.0f} so'm\n"
            f"⚠️ Omborda yo'q mahsulotlar: {out_of_stock}\n"
            f"📦 Kam qolgan mahsulotlar (<5): {low_stock}"
        )
        
        # Create keyboard with refresh button
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Yangilash", callback_data="admin_stats")],
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_panel")]
        ])
        
        await callback.message.edit_text(
            stats_text,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
    
    await callback.answer()

# View Categories
@router.callback_query(F.data == "admin_view_categories")
async def admin_view_categories(callback: CallbackQuery):
    """View all categories"""
    if not await is_admin(callback):
        await callback.answer(get_admin_msg("uz", "unauthorized"), show_alert=True)
        return
    
    language = await get_user_language(callback.from_user.id)
    
    async for session in get_db():
        categories = await session.execute(select(Category).order_by(Category.name))
        categories_list = categories.scalars().all()
        
        if not categories_list:
            await callback.message.edit_text(
                "😔 Hali kategoriyalar mavjud emas.\n\n➕ 'Kategoriya qo'shish' tugmasi orqali yangi kategoriya qo'shing.",
                reply_markup=get_admin_keyboard(language)
            )
        else:
            categories_text = f"📁 *Barcha Kategoriyalar* (jami: {len(categories_list)})\n\n"
            
            for i, category in enumerate(categories_list, 1):
                # Count products in this category
                product_count = await session.scalar(
                    select(func.count()).select_from(Product).where(Product.category_id == category.id)
                ) or 0
                
                categories_text += f"{i}. 📁 *{category.name}* ({product_count} mahsulot)\n"
                if category.description:
                    categories_text += f"   📝 {category.description}\n"
                categories_text += f"   🆔 ID: `{category.id}`\n\n"
            
            await callback.message.edit_text(
                categories_text,
                parse_mode="Markdown",
                reply_markup=get_admin_keyboard(language)
            )
    
    await callback.answer()

# Add Category
@router.callback_query(F.data == "admin_add_category")
async def admin_add_category_start(callback: CallbackQuery, state: FSMContext):
    """Start add category process"""
    if not await is_admin(callback):
        await callback.answer(get_admin_msg("uz", "unauthorized"), show_alert=True)
        return
    
    language = await get_user_language(callback.from_user.id)
    
    await state.set_state(AddCategoryStates.waiting_for_name)
    await callback.message.edit_text("📁 *Yangi Kategoriya qo'shish*\n\nKategoriya nomini kiriting:")
    await callback.answer()

@router.message(AddCategoryStates.waiting_for_name)
async def admin_add_category_name(message: Message, state: FSMContext):
    """Get category name"""
    language = await get_user_language(message.from_user.id)
    
    await state.update_data(name=message.text)
    await state.set_state(AddCategoryStates.waiting_for_description)
    await message.answer("📝 Kategoriya tavsifini kiriting (bo'sh qoldirish uchun 'skip' yozing):")

@router.message(AddCategoryStates.waiting_for_description)
async def admin_add_category_description(message: Message, state: FSMContext):
    """Get category description and create category"""
    language = await get_user_language(message.from_user.id)
    
    description = message.text if message.text.lower() != 'skip' else ""
    data = await state.get_data()
    name = data["name"]
    
    async for session in get_db():
        try:
            # Check if category already exists
            existing = await session.execute(
                select(Category).where(Category.name == name)
            )
            if existing.scalar_one_or_none():
                await message.answer(
                    f"❌ '{name}' nomli kategoriya allaqachon mavjud!",
                    reply_markup=get_admin_keyboard(language)
                )
                await state.clear()
                return
            
            category = Category(name=name, description=description)
            session.add(category)
            await session.commit()
            
            await message.answer(
                f"✅ '{name}' kategoriyasi muvaffaqiyatli qo'shildi!",
                reply_markup=get_admin_keyboard(language)
            )
        except Exception as e:
            logger.error(f"Error adding category: {e}")
            await message.answer(
                f"❌ Xatolik yuz berdi: {str(e)}",
                reply_markup=get_admin_keyboard(language)
            )
    
    await state.clear()

# View Products
@router.callback_query(F.data == "admin_view_products")
async def admin_view_products(callback: CallbackQuery):
    """View all products"""
    if not await is_admin(callback):
        await callback.answer(get_admin_msg("uz", "unauthorized"), show_alert=True)
        return
    
    language = await get_user_language(callback.from_user.id)
    
    async for session in get_db():
        products = await session.execute(
            select(Product).order_by(Product.id.desc())
        )
        products_list = products.scalars().all()
        
        if not products_list:
            await callback.message.edit_text(
                "😔 *Hali mahsulotlar mavjud emas*\n\n"
                "➕ 'Mahsulot qo'shish' tugmasi orqali yangi mahsulot qo'shing.\n\n"
                "📌 *Qo'shish uchun:*\n"
                "1. Avval kategoriya yarating (agar kerak bo'lsa)\n"
                "2. Keyin 'Mahsulot qo'shish' tugmasini bosing\n"
                "3. Barcha ma'lumotlarni kiriting",
                parse_mode="Markdown",
                reply_markup=get_admin_keyboard(language)
            )
        else:
            products_text = f"📦 *Barcha Mahsulotlar* (jami: {len(products_list)})\n\n"
            
            for i, product in enumerate(products_list[:20], 1):
                # Get category name
                category_name = await get_category_name(session, product.category_id)
                
                # Stock status emoji
                stock_emoji = "✅" if product.stock > 10 else "⚠️" if product.stock > 0 else "❌"
                
                products_text += (
                    f"{i}. {stock_emoji} *{product.name}*\n"
                    f"   🆔 ID: `{product.id}`\n"
                    f"   💰 Narx: {product.price:,.0f} so'm\n"
                    f"   📦 Soni: {product.stock} dona\n"
                    f"   📁 Kategoriya: {category_name}\n"
                )
                if product.description:
                    short_desc = product.description[:50] + "..." if len(product.description) > 50 else product.description
                    products_text += f"   📝 {short_desc}\n"
                products_text += "\n"
            
            if len(products_list) > 20:
                products_text += f"... va yana {len(products_list) - 20} ta mahsulot"
            
            await callback.message.edit_text(
                products_text,
                parse_mode="Markdown",
                reply_markup=get_admin_keyboard(language)
            )
    
    await callback.answer()

# Add Product Flow
@router.callback_query(F.data == "admin_add_product")
async def admin_add_product_start(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback):
        await callback.answer(get_admin_msg("uz", "unauthorized"), show_alert=True)
        return
    
    language = await get_user_language(callback.from_user.id)
    
    async for session in get_db():
        categories = await session.execute(select(Category).order_by(Category.name))
        categories_list = categories.scalars().all()
        
        if not categories_list:
            await callback.message.edit_text(
                "⚠️ *Kategoriyalar mavjud emas!*\n\n"
                "Avval '➕ Kategoriya qo'shish' tugmasi orqali kategoriya qo'shing.",
                parse_mode="Markdown",
                reply_markup=get_admin_keyboard(language)
            )
        else:
            await callback.message.edit_text(
                "📂 *Yangi Mahsulot uchun Kategoriyani tanlang*",
                parse_mode="Markdown",
                reply_markup=get_admin_categories_keyboard(categories_list, language)
            )
    await callback.answer()

@router.callback_query(F.data.startswith("admin_select_category_"))
async def admin_select_category(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback):
        await callback.answer(get_admin_msg("uz", "unauthorized"), show_alert=True)
        return
    
    category_id = int(callback.data.split("_")[-1])
    
    # Get category name
    async for session in get_db():
        category = await session.get(Category, category_id)
        category_name = category.name if category else "Noma'lum"
        await state.update_data(category_id=category_id, category_name=category_name)
    
    await state.set_state(AddProductStates.waiting_for_name)
    await callback.message.edit_text("📝 Mahsulot nomini kiriting:")
    await callback.answer()

@router.message(AddProductStates.waiting_for_name)
async def admin_add_product_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(AddProductStates.waiting_for_description)
    await message.answer("📝 Mahsulot tavsifini kiriting (bo'sh qoldirish uchun 'skip' yozing):")

@router.message(AddProductStates.waiting_for_description)
async def admin_add_product_description(message: Message, state: FSMContext):
    description = message.text if message.text.lower() != 'skip' else ""
    await state.update_data(description=description)
    await state.set_state(AddProductStates.waiting_for_price)
    await message.answer("💰 Mahsulot narxini kiriting (masalan, 10000):")

@router.message(AddProductStates.waiting_for_price)
async def admin_add_product_price(message: Message, state: FSMContext):
    try:
        price = float(message.text.replace(',', '.'))
        if price <= 0:
            raise ValueError
        
        await state.update_data(price=price)
        await state.set_state(AddProductStates.waiting_for_stock)
        await message.answer("📦 Ombordagi miqdorni kiriting:")
    except ValueError:
        await message.answer("❌ Iltimos, to'g'ri narx raqamini kiriting (masalan, 10000).")

@router.message(AddProductStates.waiting_for_stock)
async def admin_add_product_stock(message: Message, state: FSMContext):
    try:
        stock = int(message.text)
        if stock < 0:
            raise ValueError
        
        await state.update_data(stock=stock)
        await state.set_state(AddProductStates.waiting_for_image)
        await message.answer("🖼️ Mahsulot rasmini yuklang yoki URL manzilini yuboring (rasmsiz uchun 'skip' yozing):")
    except ValueError:
        await message.answer("❌ Iltimos, to'g'ri miqdor kiriting (musbat butun son).")

@router.message(AddProductStates.waiting_for_image)
async def admin_add_product_image(message: Message, state: FSMContext):
    language = await get_user_language(message.from_user.id)
    
    try:
        # Handle image URL or photo
        image_url = None
        if message.photo:
            photo = message.photo[-1]
            file = await message.bot.get_file(photo.file_id)
            image_url = f"https://api.telegram.org/file/bot{config.BOT_TOKEN}/{file.file_path}"
        elif message.text and message.text.lower() != 'skip':
            image_url = message.text
        
        # Get all data
        data = await state.get_data()
        
        # Create product
        async for session in get_db():
            product = Product(
                name=data["name"],
                description=data.get("description", ""),
                price=data["price"],
                category_id=data["category_id"],
                stock=data["stock"],
                image_url=image_url or ""
            )
            session.add(product)
            await session.commit()
            
            # Get category name for display
            category_name = data.get("category_name", "Kategoriyasiz")
            
            await message.answer(
                f"✅ *Mahsulot muvaffaqiyatli qo'shildi!*\n\n"
                f"*Mahsulot tafsilotlari:*\n"
                f"• Nomi: {product.name}\n"
                f"• Narxi: {product.price:,.0f} so'm\n"
                f"• Soni: {product.stock} dona\n"
                f"• Kategoriya: {category_name}",
                parse_mode="Markdown"
            )
            await message.answer(
                "⚙️ *Admin Panel*",
                parse_mode="Markdown",
                reply_markup=get_admin_keyboard(language)
            )
        
        await state.clear()
    except Exception as e:
        logger.error(f"Error adding product: {e}")
        await message.answer(
            f"❌ Xatolik yuz berdi: {str(e)}",
            reply_markup=get_admin_keyboard(language)
        )
        await state.clear()

# Delete Product Handlers
@router.callback_query(F.data == "admin_delete_product")
async def admin_delete_product_start(callback: CallbackQuery, state: FSMContext):
    """Start delete product process"""
    if not await is_admin(callback):
        await callback.answer(get_admin_msg("uz", "unauthorized"), show_alert=True)
        return
    
    language = await get_user_language(callback.from_user.id)
    
    # Show list of products to delete
    async for session in get_db():
        products = await session.execute(select(Product).order_by(Product.id.desc()))
        products_list = products.scalars().all()
        
        if not products_list:
            await callback.message.edit_text(
                get_admin_msg(language, "no_products"),
                reply_markup=get_admin_keyboard(language)
            )
        else:
            await state.set_state(DeleteProductStates.waiting_for_product_id)
            products_text = "🗑️ *Mahsulotni o'chirish*\n\nO'chirish uchun mahsulot ID sini kiriting yoki quyidagi ro'yxatdan tanlang:\n\n"
            
            for product in products_list[:15]:
                products_text += f"• {product.name} (ID: `{product.id}`) - {product.price:,.0f} so'm\n"
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=f"❌ {product.name[:20]}", callback_data=f"delete_product_{product.id}")]
                for product in products_list[:10]
            ])
            keyboard.inline_keyboard.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_panel")])
            
            await callback.message.edit_text(
                products_text,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
    
    await callback.answer()

@router.message(DeleteProductStates.waiting_for_product_id)
async def admin_delete_product_id(message: Message, state: FSMContext):
    """Handle product deletion by ID text input"""
    language = await get_user_language(message.from_user.id)
    
    try:
        product_id = int(message.text)
    except ValueError:
        await message.answer(get_admin_msg(language, "invalid_product_id"))
        return

    async for session in get_db():
        product = await session.get(Product, product_id)
        
        if not product:
            await message.answer(
                get_admin_msg(language, "product_not_found"),
                reply_markup=get_admin_keyboard(language)
            )
            await state.clear()
            return
        
        try:
            product_name = product.name
            await session.delete(product)
            await session.commit()
            await message.answer(f"✅ *Mahsulot o'chirildi!*\n\n❌ '{product_name}' muvaffaqiyatli o'chirildi.", parse_mode="Markdown", reply_markup=get_admin_keyboard(language))
        except Exception as e:
            logger.error(f"Error deleting product: {e}")
            await message.answer(f"❌ Xatolik: Mahsulotni o'chirib bo'lmadi (buyurtmalarda mavjud bo'lishi mumkin).", reply_markup=get_admin_keyboard(language))
    await state.clear()

@router.callback_query(F.data.startswith("delete_product_"))
async def admin_delete_product_confirm(callback: CallbackQuery, state: FSMContext):
    """Confirm and delete product"""
    if not await is_admin(callback):
        await callback.answer(get_admin_msg("uz", "unauthorized"), show_alert=True)
        return
    
    product_id = int(callback.data.split("_")[-1])
    language = await get_user_language(callback.from_user.id)
    
    async for session in get_db():
        product = await session.get(Product, product_id)
        
        if not product:
            await callback.message.edit_text(
                get_admin_msg(language, "product_not_found"),
                reply_markup=get_admin_keyboard(language)
            )
            await callback.answer()
            return
        
        # Delete product
        try:
            product_name = product.name
            await session.delete(product)
            await session.commit()
            
            await callback.message.edit_text(
                f"✅ *Mahsulot o'chirildi!*\n\n❌ '{product_name}' muvaffaqiyatli o'chirildi.",
                parse_mode="Markdown",
                reply_markup=get_admin_keyboard(language)
            )
        except Exception as e:
            logger.error(f"Error deleting product: {e}")
            await callback.message.edit_text(f"❌ Xatolik: Mahsulotni o'chirib bo'lmadi.", reply_markup=get_admin_keyboard(language))
    
    await state.clear()
    await callback.answer()

# Update Product Handlers
@router.callback_query(F.data == "admin_update_product")
async def admin_update_product_start(callback: CallbackQuery, state: FSMContext):
    """Start update product process"""
    if not await is_admin(callback):
        await callback.answer(get_admin_msg("uz", "unauthorized"), show_alert=True)
        return
    
    language = await get_user_language(callback.from_user.id)
    
    async for session in get_db():
        products = await session.execute(select(Product).order_by(Product.id.desc()))
        products_list = products.scalars().all()
        
        if not products_list:
            await callback.message.edit_text(
                get_admin_msg(language, "no_products"),
                reply_markup=get_admin_keyboard(language)
            )
        else:
            await state.set_state(UpdateProductStates.waiting_for_product_id)
            products_text = "📝 *Mahsulotni yangilash*\n\nYangilash uchun mahsulotni tanlang:\n\n"
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=f"📝 {product.name[:20]}", callback_data=f"update_product_{product.id}")]
                for product in products_list[:10]
            ])
            keyboard.inline_keyboard.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_panel")])
            
            await callback.message.edit_text(
                products_text,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
    
    await callback.answer()

@router.message(UpdateProductStates.waiting_for_product_id)
async def admin_update_product_id(message: Message, state: FSMContext):
    """Handle product update by ID text input"""
    language = await get_user_language(message.from_user.id)
    
    try:
        product_id = int(message.text)
    except ValueError:
        await message.answer(get_admin_msg(language, "invalid_product_id"))
        return

    await state.update_data(product_id=product_id)
    
    async for session in get_db():
        product = await session.get(Product, product_id)
        if not product:
            await message.answer(
                get_admin_msg(language, "product_not_found"),
                reply_markup=get_admin_keyboard(language)
            )
            await state.clear()
            return
        
        category_name = await get_category_name(session, product.category_id)
        
        product_info = (
            f"📝 *Mahsulotni yangilash*\n\n"
            f"*Hozirgi ma'lumotlar:*\n"
            f"• Nomi: {product.name}\n"
            f"• Narx: {product.price:,.0f} so'm\n"
            f"• Soni: {product.stock}\n"
            f"• Kategoriya: {category_name}\n\n"
            f"*Yangilash uchun maydonni tanlang:*"
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📛 Nomi", callback_data=f"update_field_{product_id}_name")],
            [InlineKeyboardButton(text="💰 Narxi", callback_data=f"update_field_{product_id}_price")],
            [InlineKeyboardButton(text="📦 Soni", callback_data=f"update_field_{product_id}_stock")],
            [InlineKeyboardButton(text="📝 Tavsifi", callback_data=f"update_field_{product_id}_description")],
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_panel")]
        ])
        
        await message.answer(product_info, parse_mode="Markdown", reply_markup=keyboard)

@router.callback_query(F.data.startswith("update_product_"))
async def admin_update_product_select_field(callback: CallbackQuery, state: FSMContext):
    """Select field to update"""
    if not await is_admin(callback):
        await callback.answer(get_admin_msg("uz", "unauthorized"), show_alert=True)
        return
    
    product_id = int(callback.data.split("_")[-1])
    await state.update_data(product_id=product_id)
    
    language = await get_user_language(callback.from_user.id)
    
    # Get product info
    async for session in get_db():
        product = await session.get(Product, product_id)
        if not product:
            await callback.message.edit_text(
                get_admin_msg(language, "product_not_found"),
                reply_markup=get_admin_keyboard(language)
            )
            await callback.answer()
            return
        
        category_name = await get_category_name(session, product.category_id)
        
        product_info = (
            f"📝 *Mahsulotni yangilash*\n\n"
            f"*Hozirgi ma'lumotlar:*\n"
            f"• Nomi: {product.name}\n"
            f"• Narx: {product.price:,.0f} so'm\n"
            f"• Soni: {product.stock}\n"
            f"• Kategoriya: {category_name}\n\n"
            f"*Yangilash uchun maydonni tanlang:*"
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📛 Nomi", callback_data=f"update_field_{product_id}_name")],
            [InlineKeyboardButton(text="💰 Narxi", callback_data=f"update_field_{product_id}_price")],
            [InlineKeyboardButton(text="📦 Soni", callback_data=f"update_field_{product_id}_stock")],
            [InlineKeyboardButton(text="📝 Tavsifi", callback_data=f"update_field_{product_id}_description")],
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_panel")]
        ])
        
        await callback.message.edit_text(
            product_info,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
    
    await callback.answer()

@router.callback_query(F.data.startswith("update_field_"))
async def admin_update_product_get_value(callback: CallbackQuery, state: FSMContext):
    """Get new value for field"""
    if not await is_admin(callback):
        await callback.answer(get_admin_msg("uz", "unauthorized"), show_alert=True)
        return
    
    parts = callback.data.split("_")
    product_id = int(parts[2])
    field = parts[3]
    
    await state.update_data(product_id=product_id, field=field)
    await state.set_state(UpdateProductStates.waiting_for_new_value)
    
    language = await get_user_language(callback.from_user.id)
    
    field_names = {
        "name": "nomi (yangi nom)",
        "price": "narxi (yangi narx)",
        "stock": "soni (yangi miqdor)",
        "description": "tavsifi (yangi tavsif)"
    }
    
    await callback.message.edit_text(
        f"✏️ *{field_names.get(field, field)}* uchun yangi qiymatni kiriting:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data=f"update_product_{product_id}")]
        ])
    )
    
    await callback.answer()

@router.message(UpdateProductStates.waiting_for_new_value)
async def admin_update_product_save(message: Message, state: FSMContext):
    """Save updated product value"""
    data = await state.get_data()
    product_id = data.get("product_id")
    field = data.get("field")
    new_value = message.text
    
    if not product_id or not field:
        await message.answer("❌ Xatolik yuz berdi. Qayta urinib ko'ring.")
        await state.clear()
        return
    
    language = await get_user_language(message.from_user.id)
    
    async for session in get_db():
        product = await session.get(Product, product_id)
        
        if not product:
            await message.answer(
                get_admin_msg(language, "product_not_found"),
                reply_markup=get_admin_keyboard(language)
            )
            await state.clear()
            return
        
        # Update field
        try:
            if field == "name":
                product.name = new_value
            elif field == "price":
                product.price = float(new_value.replace(',', '.'))
            elif field == "stock":
                product.stock = int(new_value)
            elif field == "description":
                product.description = new_value
            
            await session.commit()
            
            field_names_uz = {
                "name": "nomi",
                "price": "narxi", 
                "stock": "soni",
                "description": "tavsifi"
            }
            
            await message.answer(
                f"✅ *Mahsulot yangilandi!*\n\n{field_names_uz.get(field, field)}: {new_value}",
                parse_mode="Markdown",
                reply_markup=get_admin_keyboard(language)
            )
        except Exception as e:
            logger.error(f"Error updating product: {e}")
            await message.answer(
                f"❌ Xatolik yuz berdi: {str(e)}",
                reply_markup=get_admin_keyboard(language)
            )
    
    await state.clear()

# View Orders Handlers
@router.callback_query(F.data == "admin_view_orders")
async def admin_view_orders(callback: CallbackQuery):
    """View all orders"""
    if not await is_admin(callback):
        await callback.answer(get_admin_msg("uz", "unauthorized"), show_alert=True)
        return
    
    language = await get_user_language(callback.from_user.id)
    
    async for session in get_db():
        orders = await session.execute(
            select(Order).order_by(Order.created_at.desc()).limit(20)
        )
        orders_list = orders.scalars().all()
        
        if not orders_list:
            await callback.message.edit_text(
                get_admin_msg(language, "no_orders"),
                reply_markup=get_admin_keyboard(language)
            )
        else:
            orders_text = f"📋 *Barcha Buyurtmalar* (oxirgi 20 ta)\n\n"
            
            for order in orders_list:
                status_emoji = "⏳" if order.status == "pending" else "✅" if order.status == "confirmed" else "📦" if order.status == "shipped" else "🎉" if order.status == "delivered" else "❌"
                
                orders_text += (
                    f"{status_emoji} *#{order.order_number}*\n"
                    f"   👤 Mijoz: {order.customer_name}\n"
                    f"   💰 Jami: {order.total_amount:,.0f} so'm\n"
                    f"   📊 Holat: {order.status}\n"
                    f"   📅 Sana: {order.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
                )
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Yangilash", callback_data="admin_view_orders")],
                [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_panel")]
            ])
            
            await callback.message.edit_text(
                orders_text,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
    
    await callback.answer()

# Update Order Status Handlers
@router.callback_query(F.data == "admin_update_order_status")
async def admin_update_order_status_start(callback: CallbackQuery, state: FSMContext):
    """Start update order status process"""
    if not await is_admin(callback):
        await callback.answer(get_admin_msg("uz", "unauthorized"), show_alert=True)
        return
    
    language = await get_user_language(callback.from_user.id)
    
    async for session in get_db():
        orders = await session.execute(
            select(Order).order_by(Order.created_at.desc()).limit(10)
        )
        orders_list = orders.scalars().all()
        
        if not orders_list:
            await callback.message.edit_text(
                get_admin_msg(language, "no_orders"),
                reply_markup=get_admin_keyboard(language)
            )
        else:
            orders_text = "🔄 *Buyurtma holatini yangilash*\n\nBuyurtma holatini o'zgartirish uchun buyurtmani tanlang:\n\n"
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=f"#{order.order_number} - {order.status}", callback_data=f"update_order_status_{order.id}")]
                for order in orders_list
            ])
            keyboard.inline_keyboard.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_panel")])
            
            await callback.message.edit_text(
                orders_text,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
    
    await callback.answer()

@router.callback_query(F.data.startswith("update_order_status_"))
async def admin_update_order_select_status(callback: CallbackQuery):
    """Select new status for order"""
    if not await is_admin(callback):
        await callback.answer(get_admin_msg("uz", "unauthorized"), show_alert=True)
        return
    
    order_id = int(callback.data.split("_")[-1])
    language = await get_user_language(callback.from_user.id)
    
    # Show status options
    status_options = [
        ("⏳ Kutilmoqda", "pending"),
        ("✅ Tasdiqlangan", "confirmed"),
        ("📦 Yuborilgan", "shipped"),
        ("🎉 Yetkazilgan", "delivered"),
        ("❌ Bekor qilingan", "cancelled")
    ]
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=text, callback_data=f"set_order_status_{order_id}_{status}")]
        for text, status in status_options
    ])
    keyboard.inline_keyboard.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_view_orders")])
    
    await callback.message.edit_text(
        f"📊 *{order_id} - Buyurtma holatini yangilash*\n\nYangi holatni tanlang:",
        parse_mode="Markdown",
        reply_markup=keyboard
    )
    
    await callback.answer()

@router.callback_query(F.data.startswith("set_order_status_"))
async def admin_set_order_status(callback: CallbackQuery):
    """Set new status for order"""
    if not await is_admin(callback):
        await callback.answer(get_admin_msg("uz", "unauthorized"), show_alert=True)
        return
    
    parts = callback.data.split("_")
    order_id = int(parts[3])
    new_status = parts[4]
    language = await get_user_language(callback.from_user.id)
    
    async for session in get_db():
        order = await session.get(Order, order_id)
        
        if not order:
            await callback.message.edit_text(
                get_admin_msg(language, "order_not_found"),
                reply_markup=get_admin_keyboard(language)
            )
            await callback.answer()
            return
        
        old_status = order.status
        order.status = new_status
        await session.commit()
        
        status_names = {
            "pending": "Kutilmoqda",
            "confirmed": "Tasdiqlangan", 
            "shipped": "Yuborilgan",
            "delivered": "Yetkazilgan",
            "cancelled": "Bekor qilingan"
        }
        
        await callback.message.edit_text(
            f"✅ *Buyurtma holati yangilandi!*\n\n"
            f"Buyurtma: `{order.order_number}`\n"
            f"Eski holat: {status_names.get(old_status, old_status)}\n"
            f"Yangi holat: {status_names.get(new_status, new_status)}",
            parse_mode="Markdown",
            reply_markup=get_admin_keyboard(language)
        )
    
    await callback.answer()

# Removed the catch-all handler - it was intercepting all messages from admin users
# and showing admin panel even when clicking user buttons
