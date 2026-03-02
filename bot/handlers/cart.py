from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from bot.keyboards import (
    get_cart_keyboard, get_main_keyboard, get_order_confirmation_keyboard,
    get_product_actions_keyboard, get_back_keyboard
)
from database.session import get_db
from database.models import User
from config import config
from services.cart import CartService
from services.order import OrderService
from services.product import ProductService

router = Router()

# States for checkout
class CheckoutStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_address = State()
    confirming_order = State()

# Multilingual messages for cart
CART_MESSAGES = {
    "en": {
        "cart_empty": "Your cart is empty! 🛒\n\nBrowse products and add them to cart.",
        "cart_title": "Your Cart",
        "total": "Total",
        "out_of_stock": "❌ Product out of stock!",
        "added_to_cart": "✅ Added to cart!",
        "removed_from_cart": "❌ Removed from cart!",
        "item_not_in_cart": "Item not in cart.",
        "cart_cleared": "🗑 Cart cleared!",
        "checkout_empty": "Your cart is empty!",
        "insufficient_stock": "❌ {product} has insufficient stock!",
        "enter_name": "📝 Please enter your full name:",
        "enter_phone": "📞 Please enter your phone number:",
        "enter_address": "🏠 Please enter your delivery address:",
        "order_summary": "📋 Order Summary",
        "name": "Name",
        "phone": "Phone",
        "address": "Address",
        "items": "Items",
        "order_confirmed": "✅ Order Confirmed!",
        "order_number": "Your order number",
        "delivery_confirmation": "We'll contact you soon for delivery confirmation.",
        "thank_you": "Thank you for shopping with us! 🛍",
        "no_orders": "You haven't placed any orders yet.",
        "your_orders": "Your Orders",
        "status": "Status",
        "date": "Date",
        "change_language": "🌐 Change Language",
        "select_language": "Please select your language:",
        "language_changed": "Language changed to {lang_name}!",
        "language_options": {
            "en": "English 🇬🇧",
            "uz": "O'zbek 🇺🇿",
            "ru": "Русский 🇷🇺"
        },
        "error_occurred": "❌ An error occurred: {error}",
        "unknown_command": "❌ I don't understand that command. Please use the buttons below."
    },
    "uz": {
        "cart_empty": "Savatingiz bo'sh! 🛒\n\nMahsulotlarni ko'rib chiqing va savatga qo'shing.",
        "cart_title": "Savat",
        "total": "Jami",
        "out_of_stock": "❌ Mahsulot omborda yo'q!",
        "added_to_cart": "✅ Savatga qo'shildi!",
        "removed_from_cart": "❌ Savatdan olib tashlandi!",
        "item_not_in_cart": "Mahsulot savatda yo'q.",
        "cart_cleared": "🗑 Savat tozalandi!",
        "checkout_empty": "Savatingiz bo'sh!",
        "insufficient_stock": "❌ {product}da yetarli miqdor yo'q!",
        "enter_name": "📝 Iltimos, to'liq ismingizni kiriting:",
        "enter_phone": "📞 Iltimos, telefon raqamingizni kiriting:",
        "enter_address": "🏠 Iltimos, yetkazib berish manzilini kiriting:",
        "order_summary": "📋 Buyurtma Xulosasi",
        "name": "Ism",
        "phone": "Telefon",
        "address": "Manzil",
        "items": "Mahsulotlar",
        "order_confirmed": "✅ Buyurtma Tasdiqlandi!",
        "order_number": "Buyurtma raqamingiz",
        "delivery_confirmation": "Tez orada yetkazib berish uchun bog'lanamiz.",
        "thank_you": "Xaridingiz uchun rahmat! 🛍",
        "no_orders": "Siz hali buyurtma qilmagansiz.",
        "your_orders": "Buyurtmalaringiz",
        "status": "Holat",
        "date": "Sana",
        "change_language": "🌐 Tilni o'zgartirish",
        "select_language": "Iltimos, tilni tanlang:",
        "language_changed": "Til {lang_name} ga o'zgartirildi!",
        "language_options": {
            "en": "English 🇬🇧",
            "uz": "O'zbek 🇺🇿",
            "ru": "Русский 🇷🇺"
        },
        "error_occurred": "❌ Xatolik yuz berdi: {error}",
        "unknown_command": "❌ Men bu buyruqni tushunmadim. Iltimos, quyidagi tugmalardan foydalaning."
    },
    "ru": {
        "cart_empty": "Ваша корзина пуста! 🛒\n\nПросмотрите товары и добавьте их в корзину.",
        "cart_title": "Корзина",
        "total": "Итого",
        "out_of_stock": "❌ Товара нет в наличии!",
        "added_to_cart": "✅ Добавлено в корзину!",
        "removed_from_cart": "❌ Удалено из корзины!",
        "item_not_in_cart": "Товар не в корзине.",
        "cart_cleared": "🗑 Корзина очищена!",
        "checkout_empty": "Ваша корзина пуста!",
        "insufficient_stock": "❌ {product} недостаточно на складе!",
        "enter_name": "📝 Пожалуйста, введите ваше полное имя:",
        "enter_phone": "📞 Пожалуйста, введите ваш номер телефона:",
        "enter_address": "🏠 Пожалуйста, введите адрес доставки:",
        "order_summary": "📋 Сводка Заказа",
        "name": "Имя",
        "phone": "Телефон",
        "address": "Адрес",
        "items": "Товары",
        "order_confirmed": "✅ Заказ Подтверждён!",
        "order_number": "Номер вашего заказа",
        "delivery_confirmation": "Мы свяжемся с вами для подтверждения доставки.",
        "thank_you": "Спасибо за покупку! 🛍",
        "no_orders": "Вы ещё не сделали заказов.",
        "your_orders": "Ваши Заказы",
        "status": "Статус",
        "date": "Дата",
        "change_language": "🌐 Сменить язык",
        "select_language": "Пожалуйста, выберите язык:",
        "language_changed": "Язык изменён на {lang_name}!",
        "language_options": {
            "en": "English 🇬🇧",
            "uz": "O'zbek 🇺🇿",
            "ru": "Русский 🇷🇺"
        },
        "error_occurred": "❌ Произошла ошибка: {error}",
        "unknown_command": "❌ Я не понимаю эту команду. Пожалуйста, используйте кнопки ниже."
    }
}

async def get_user_language(telegram_id: int) -> str:
    """Get user's language preference"""
    async for session in get_db():
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if user and hasattr(user, 'language') and user.language:
            return user.language
        return "en"

def get_cart_msg(language: str, key: str, **kwargs) -> str:
    """Get cart message by language with formatting"""
    msg_dict = CART_MESSAGES.get(language, CART_MESSAGES["en"])
    msg = msg_dict.get(key, "")
    if kwargs and msg:
        try:
            return msg.format(**kwargs)
        except KeyError:
            return msg
    return msg

def get_language_keyboard(language: str = "en") -> InlineKeyboardMarkup:
    """Inline keyboard with three language options"""
    msg = CART_MESSAGES.get(language, CART_MESSAGES["en"])
    buttons = [
        [InlineKeyboardButton(text=msg["language_options"]["en"], callback_data="set_lang_en")],
        [InlineKeyboardButton(text=msg["language_options"]["uz"], callback_data="set_lang_uz")],
        [InlineKeyboardButton(text=msg["language_options"]["ru"], callback_data="set_lang_ru")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Ignore callback for non-clickable buttons
@router.callback_query(F.data == "ignore")
async def ignore_callback(callback: CallbackQuery):
    """Ignore callback (for non-clickable buttons)"""
    await callback.answer()

# Language selection handlers
@router.message(F.text == "/language")
async def cmd_language(message: Message):
    """Handle /language command"""
    language = await get_user_language(message.from_user.id)
    await message.answer(
        get_cart_msg(language, "select_language"),
        reply_markup=get_language_keyboard(language)
    )

@router.message(F.text.in_([
    CART_MESSAGES["en"]["change_language"],
    CART_MESSAGES["uz"]["change_language"],
    CART_MESSAGES["ru"]["change_language"]
]))
async def change_language_prompt(message: Message):
    """Show language selection when user clicks the button"""
    language = await get_user_language(message.from_user.id)
    await message.answer(
        get_cart_msg(language, "select_language"),
        reply_markup=get_language_keyboard(language)
    )

@router.callback_query(F.data.startswith("set_lang_"))
async def set_language(callback: CallbackQuery):
    """Update user's language preference in database"""
    lang_code = callback.data.split("_")[2]  # "en", "uz", or "ru"
    
    async for session in get_db():
        # Update language
        stmt = update(User).where(User.telegram_id == callback.from_user.id).values(language=lang_code)
        await session.execute(stmt)
        await session.commit()
        
        # Get confirmation message in the new language
        language_names = {"en": "English", "uz": "O'zbek", "ru": "Русский"}
        
        # Edit the callback message to show confirmation
        confirm_text = get_cart_msg(lang_code, "language_changed", lang_name=language_names[lang_code])
        await callback.message.edit_text(confirm_text)
        
        # Send main menu in the new language
        is_admin = callback.from_user.id in config.ADMIN_IDS
        welcome_text = get_cart_msg(lang_code, "welcome", name=callback.from_user.first_name or "Customer")
        await callback.message.answer(
            welcome_text,
            reply_markup=get_main_keyboard(is_admin, lang_code)
        )
    
    await callback.answer()

# Cart view handlers
@router.message(F.text.in_(["🛒 View Cart", "🛒 Savat", "🛒 Корзина"]))
async def view_cart_message(message: Message):
    """Show user's cart"""
    try:
        language = await get_user_language(message.from_user.id)
        
        async for session in get_db():
            cart_service = CartService(session)
            
            user = await cart_service.get_or_create_user(telegram_id=message.from_user.id)
            cart_items = await cart_service.get_cart(user.id)
            
            is_admin = user.is_admin or message.from_user.id in config.ADMIN_IDS
            if not cart_items:
                await message.answer(
                    get_cart_msg(language, "cart_empty"),
                    reply_markup=get_main_keyboard(is_admin, language)
                )
                return
            
            # Calculate total
            total = await cart_service.calculate_cart_total(cart_items)
            
            # Create cart message
            cart_text = f"🛒 *{get_cart_msg(language, 'cart_title')}*\n\n"
            for item in cart_items:
                if item.product:
                    cart_text += (
                        f"• {item.product.name} x{item.quantity} = "
                        f"{item.product.price * item.quantity:,.0f} so'm\n"
                    )
            
            cart_text += f"\n💰 *{get_cart_msg(language, 'total')}: {total:,.0f} so'm*"
            
            await message.answer(
                cart_text,
                parse_mode="Markdown",
                reply_markup=get_cart_keyboard(cart_items, language, total)
            )
    except Exception as e:
        language = await get_user_language(message.from_user.id)
        await message.answer(
            get_cart_msg(language, "error_occurred", error=str(e))
        )

@router.message(F.text.in_(["📦 My Orders", "📦 Buyurtmalarim", "📦 Мои заказы"]))
async def show_orders(message: Message):
    """Show user's orders"""
    try:
        language = await get_user_language(message.from_user.id)
        
        async for session in get_db():
            cart_service = CartService(session)
            order_service = OrderService(session)
            
            user = await cart_service.get_or_create_user(telegram_id=message.from_user.id)
            orders = await order_service.get_user_orders(user.id)
            
            is_admin = user.is_admin or message.from_user.id in config.ADMIN_IDS
            if not orders:
                await message.answer(
                    get_cart_msg(language, "no_orders"),
                    reply_markup=get_main_keyboard(is_admin, language)
                )
                return
            
            orders_text = f"📦 *{get_cart_msg(language, 'your_orders')}*\n\n"
            for order in orders:
                orders_text += (
                    f"Buyurtma: `{order.order_number}`\n"
                    f"{get_cart_msg(language, 'status')}: *{order.status}*\n"
                    f"{get_cart_msg(language, 'total')}: {order.total_amount:,.0f} so'm\n"
                    f"{get_cart_msg(language, 'date')}: {order.created_at.strftime('%Y-%m-%d %H:%M')}\n"
                    f"{'─' * 20}\n"
                )
            
            await message.answer(
                orders_text,
                parse_mode="Markdown",
                reply_markup=get_main_keyboard(is_admin, language)
            )
    except Exception as e:
        language = await get_user_language(message.from_user.id)
        await message.answer(
            get_cart_msg(language, "error_occurred", error=str(e))
        )

@router.callback_query(F.data == "view_cart")
async def view_cart_callback(callback: CallbackQuery):
    """Handle view cart callback from inline keyboard"""
    try:
        language = await get_user_language(callback.from_user.id)
        
        async for session in get_db():
            cart_service = CartService(session)
            
            user = await cart_service.get_or_create_user(telegram_id=callback.from_user.id)
            cart_items = await cart_service.get_cart(user.id)
            
            is_admin = user.is_admin or callback.from_user.id in config.ADMIN_IDS
            if not cart_items:
                await callback.message.edit_text(
                    get_cart_msg(language, "cart_empty"),
                    reply_markup=get_main_keyboard(is_admin, language)
                )
                await callback.answer()
                return
            
            # Calculate total
            total = await cart_service.calculate_cart_total(cart_items)
            
            # Create cart message
            cart_text = f"🛒 *{get_cart_msg(language, 'cart_title')}*\n\n"
            for item in cart_items:
                if item.product:
                    cart_text += (
                        f"• {item.product.name} x{item.quantity} = "
                        f"${item.product.price * item.quantity:.2f}\n"
                    )
            
            cart_text += f"\n💰 *{get_cart_msg(language, 'total')}: ${total:.2f}*"
            
            await callback.message.edit_text(
                cart_text,
                parse_mode="Markdown",
                reply_markup=get_cart_keyboard(cart_items, language, total)
            )
        
        await callback.answer()
    except Exception as e:
        language = await get_user_language(callback.from_user.id)
        await callback.answer(
            get_cart_msg(language, "error_occurred", error="Xatolik yuz berdi"),
            show_alert=True
        )

@router.callback_query(F.data.startswith("add_"))
async def add_to_cart(callback: CallbackQuery):
    """Add product to cart"""
    try:
        product_id = int(callback.data.split("_")[1])
        language = await get_user_language(callback.from_user.id)
        
        async for session in get_db():
            cart_service = CartService(session)
            product_service = ProductService(session)
            
            # Check stock
            product = await product_service.get_product(product_id)
            if not product or product.stock < 1:
                await callback.answer(get_cart_msg(language, "out_of_stock"), show_alert=True)
                return
            
            user = await cart_service.get_or_create_user(telegram_id=callback.from_user.id)
            await cart_service.add_to_cart(user.id, product_id)
            
            await callback.answer(get_cart_msg(language, "added_to_cart"))
            
            # Update message with "in cart" status
            cart_items = await cart_service.get_cart(user.id)
            in_cart = any(item.product_id == product_id for item in cart_items)
            
            await callback.message.edit_reply_markup(
                reply_markup=get_product_actions_keyboard(
                    product_id, 
                    in_cart, 
                    language,
                    product.stock
                )
            )
    except Exception as e:
        language = await get_user_language(callback.from_user.id)
        await callback.answer(
            get_cart_msg(language, "error_occurred", error="Xatolik yuz berdi"),
            show_alert=True
        )

@router.callback_query(F.data.startswith("remove_"))
async def remove_from_cart(callback: CallbackQuery):
    """Remove product from cart"""
    try:
        product_id = int(callback.data.split("_")[1])
        language = await get_user_language(callback.from_user.id)
        
        async for session in get_db():
            cart_service = CartService(session)
            
            user = await cart_service.get_or_create_user(telegram_id=callback.from_user.id)
            removed = await cart_service.remove_from_cart(user.id, product_id)
            
            if removed:
                await callback.answer(get_cart_msg(language, "removed_from_cart"))
            else:
                await callback.answer(get_cart_msg(language, "item_not_in_cart"))
            
            # Refresh cart view
            cart_items = await cart_service.get_cart(user.id)
            
            if cart_items:
                total = await cart_service.calculate_cart_total(cart_items)
                
                cart_text = f"🛒 *{get_cart_msg(language, 'cart_title')}*\n\n"
                for item in cart_items:
                    if item.product:
                        cart_text += (
                            f"• {item.product.name} x{item.quantity} = "
                            f"{item.product.price * item.quantity:,.0f} so'm\n"
                        )
                
                cart_text += f"\n💰 *{get_cart_msg(language, 'total')}: {total:,.0f} so'm*"
                
                await callback.message.edit_text(
                    cart_text,
                    parse_mode="Markdown",
                    reply_markup=get_cart_keyboard(cart_items, language, total)
                )
            else:
                is_admin = user.is_admin or callback.from_user.id in config.ADMIN_IDS
                await callback.message.edit_text(
                    get_cart_msg(language, "cart_empty"),
                    reply_markup=get_main_keyboard(is_admin, language)
                )
        
        await callback.answer()
    except Exception as e:
        language = await get_user_language(callback.from_user.id)
        await callback.answer(
            get_cart_msg(language, "error_occurred", error="Xatolik yuz berdi"),
            show_alert=True
        )

@router.callback_query(F.data == "clear_cart")
async def clear_cart(callback: CallbackQuery):
    """Clear all items from cart"""
    try:
        language = await get_user_language(callback.from_user.id)
        
        async for session in get_db():
            cart_service = CartService(session)
            
            user = await cart_service.get_or_create_user(telegram_id=callback.from_user.id)
            await cart_service.clear_cart(user.id)
            
            is_admin = user.is_admin or callback.from_user.id in config.ADMIN_IDS
            await callback.message.edit_text(
                get_cart_msg(language, "cart_cleared"),
                reply_markup=get_main_keyboard(is_admin, language)
            )
        
        await callback.answer()
    except Exception as e:
        language = await get_user_language(callback.from_user.id)
        await callback.answer(
            get_cart_msg(language, "error_occurred", error="Xatolik yuz berdi"),
            show_alert=True
        )

@router.callback_query(F.data == "checkout")
async def checkout_start(callback: CallbackQuery, state: FSMContext):
    """Start checkout process"""
    try:
        language = await get_user_language(callback.from_user.id)
        
        async for session in get_db():
            cart_service = CartService(session)
            
            user = await cart_service.get_or_create_user(telegram_id=callback.from_user.id)
            cart_items = await cart_service.get_cart(user.id)
            
            if not cart_items:
                await callback.answer(get_cart_msg(language, "checkout_empty"), show_alert=True)
                return
            
            # Check stock for all items
            for item in cart_items:
                if item.product and item.product.stock < item.quantity:
                    await callback.answer(
                        get_cart_msg(language, "insufficient_stock", product=item.product.name),
                        show_alert=True
                    )
                    return
            
            await state.set_state(CheckoutStates.waiting_for_name)
            await callback.message.answer(get_cart_msg(language, "enter_name"))
        
        await callback.answer()
    except Exception as e:
        language = await get_user_language(callback.from_user.id)
        await callback.answer(
            get_cart_msg(language, "error_occurred", error="Xatolik yuz berdi"),
            show_alert=True
        )

@router.message(CheckoutStates.waiting_for_name)
async def checkout_get_name(message: Message, state: FSMContext):
    """Get customer name"""
    try:
        language = await get_user_language(message.from_user.id)
        
        await state.update_data(customer_name=message.text)
        await state.set_state(CheckoutStates.waiting_for_phone)
        await message.answer(get_cart_msg(language, "enter_phone"))
    except Exception as e:
        language = await get_user_language(message.from_user.id)
        await message.answer(
            get_cart_msg(language, "error_occurred", error=str(e))
        )
        await state.clear()

@router.message(CheckoutStates.waiting_for_phone)
async def checkout_get_phone(message: Message, state: FSMContext):
    """Get customer phone"""
    try:
        language = await get_user_language(message.from_user.id)
        
        await state.update_data(phone=message.text)
        await state.set_state(CheckoutStates.waiting_for_address)
        await message.answer(get_cart_msg(language, "enter_address"))
    except Exception as e:
        language = await get_user_language(message.from_user.id)
        await message.answer(
            get_cart_msg(language, "error_occurred", error=str(e))
        )
        await state.clear()

@router.message(CheckoutStates.waiting_for_address)
async def checkout_get_address(message: Message, state: FSMContext):
    """Get delivery address and show order summary"""
    try:
        language = await get_user_language(message.from_user.id)
        
        async for session in get_db():
            await state.update_data(address=message.text)
            
            # Get cart items
            cart_service = CartService(session)
            user = await cart_service.get_or_create_user(telegram_id=message.from_user.id)
            cart_items = await cart_service.get_cart(user.id)
            total = await cart_service.calculate_cart_total(cart_items)
            
            # Get collected data
            data = await state.get_data()
            
            # Create order summary
            summary = f"📋 *{get_cart_msg(language, 'order_summary')}*\n\n"
            summary += f"👤 {get_cart_msg(language, 'name')}: {data['customer_name']}\n"
            summary += f"📞 {get_cart_msg(language, 'phone')}: {data['phone']}\n"
            summary += f"🏠 {get_cart_msg(language, 'address')}: {data['address']}\n\n"
            summary += f"*{get_cart_msg(language, 'items')}:*\n"
            
            for item in cart_items:
                if item.product:
                    summary += f"• {item.product.name} x{item.quantity} = {item.product.price * item.quantity:,.0f} so'm\n"
            
            summary += f"\n💰 *{get_cart_msg(language, 'total')}: {total:,.0f} so'm*"
            
            await state.set_state(CheckoutStates.confirming_order)
            await message.answer(
                summary,
                parse_mode="Markdown",
                reply_markup=get_order_confirmation_keyboard(language)
            )
    except Exception as e:
        language = await get_user_language(message.from_user.id)
        await message.answer(
            get_cart_msg(language, "error_occurred", error=str(e))
        )
        await state.clear()

@router.callback_query(F.data == "confirm_order")
async def confirm_order(callback: CallbackQuery, state: FSMContext):
    """Confirm and create order"""
    try:
        language = await get_user_language(callback.from_user.id)
        is_admin = callback.from_user.id in config.ADMIN_IDS
        
        async for session in get_db():
            # Get state data
            data = await state.get_data()
            
            # Get cart items
            cart_service = CartService(session)
            order_service = OrderService(session)
            
            user = await cart_service.get_or_create_user(telegram_id=callback.from_user.id)
            cart_items = await cart_service.get_cart(user.id)
            
            # Create order items
            order_items = []
            for item in cart_items:
                if item.product:
                    order_items.append({
                        "product_id": item.product.id,
                        "quantity": item.quantity,
                        "price": item.product.price
                    })
            
            # Create order
            order = await order_service.create_order({
                "user_id": user.id,
                "customer_name": data["customer_name"],
                "phone": data["phone"],
                "address": data["address"],
                "items": order_items
            })
            
            # Clear cart
            await cart_service.clear_cart(user.id)
            
            # Clear state
            await state.clear()
            
            # Send confirmation
            await callback.message.edit_text(
                f"✅ *{get_cart_msg(language, 'order_confirmed')}*\n\n"
                f"{get_cart_msg(language, 'order_number')}: `{order.order_number}`\n\n"
                f"{get_cart_msg(language, 'delivery_confirmation')}\n"
                f"{get_cart_msg(language, 'thank_you')}",
                parse_mode="Markdown",
                reply_markup=get_main_keyboard(is_admin, language)
            )
        
        await callback.answer()
    except Exception as e:
        language = await get_user_language(callback.from_user.id)
        await callback.answer(
            get_cart_msg(language, "error_occurred", error="Xatolik yuz berdi"),
            show_alert=True
        )
        await state.clear()

# Add back to main menu handler
@router.callback_query(F.data == "main_menu")
async def back_to_main_menu(callback: CallbackQuery):
    """Go back to main menu"""
    language = await get_user_language(callback.from_user.id)
    is_admin = callback.from_user.id in config.ADMIN_IDS
    
    await callback.message.delete()
    welcome_text = get_cart_msg(language, "welcome", name=callback.from_user.first_name or "Customer")
    await callback.message.answer(
        welcome_text,
        reply_markup=get_main_keyboard(is_admin, language)
    )
    await callback.answer()

# Add back to categories handler
@router.callback_query(F.data == "back_to_categories")
async def back_to_categories(callback: CallbackQuery):
    """Go back to categories"""
    try:
        async for session in get_db():
            from services.product import ProductService
            product_service = ProductService(session)
            categories = await product_service.get_categories()
            
            language = await get_user_language(callback.from_user.id)
            
            from bot.keyboards import get_categories_keyboard
            await callback.message.edit_text(
                get_cart_msg(language, "select_category"),
                reply_markup=get_categories_keyboard(categories, language)
            )
        
        await callback.answer()
    except Exception as e:
        await callback.answer(f"Error: {str(e)}", show_alert=True)


def ensure_welcome_message():
    """Ensure welcome message exists in all language dictionaries"""
    for lang in ["en", "uz", "ru"]:
        if "welcome" not in CART_MESSAGES[lang]:
            CART_MESSAGES[lang]["welcome"] = CART_MESSAGES[lang].get("welcome", "👋 Welcome, {name}!")

# Call this function to ensure welcome message exists
ensure_welcome_message()