from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Optional
from database.models import Category, Product, CartItem

# Language-specific button texts
MAIN_KEYBOARD_LABELS = {
    "en": {
        "browse": "🛍 Browse Categories",
        "search": "🔍 Search Products",
        "cart": "🛒 View Cart",
        "orders": "📦 My Orders",
        "language": "🌐 Change Language",
        "admin": "⚙️ Admin Panel"
    },
    "uz": {
        "browse": "🛍 Kategoriyalar",
        "search": "🔍 Mahsulotlarni qidirish",
        "cart": "🛒 Savat",
        "orders": "📦 Buyurtmalarim",
        "language": "🌐 Tilni o'zgartirish",
        "admin": "⚙️ Admin Panel"
    },
    "ru": {
        "browse": "🛍 Категории",
        "search": "🔍 Поиск товаров",
        "cart": "🛒 Корзина",
        "orders": "📦 Мои заказы",
        "language": "🌐 Сменить язык",
        "admin": "⚙️ Админ Панель"
    }
}

CATEGORY_LABELS = {
    "en": {
        "back": "🔙 Back to Main",
        "back_categories": "🔙 Back to Categories",
        "main_menu": "🏠 Main Menu",
        "select": "Select a category:",
        "no_categories": "No categories available"
    },
    "uz": {
        "back": "🔙 Asosiy menyu",
        "back_categories": "🔙 Kategoriyalarga",
        "main_menu": "🏠 Asosiy menyu",
        "select": "Kategoriyani tanlang:",
        "no_categories": "Kategoriyalar mavjud emas"
    },
    "ru": {
        "back": "🔙 На главную",
        "back_categories": "🔙 К категориям",
        "main_menu": "🏠 Главное меню",
        "select": "Выберите категорию:",
        "no_categories": "Категории недоступны"
    }
}

PRODUCT_LABELS = {
    "en": {
        "back_categories": "🔙 Back to Categories",
        "main_menu": "🏠 Main Menu",
        "prev": "◀️ Previous",
        "next": "Next ▶️",
        "page": "Page {page} of {total}",
        "add": "➕ Add to Cart",
        "remove": "➖ Remove from Cart",
        "in_cart": "✅ In Cart",
        "details": "View Details",
        "price": "💰 Price: ${price}",
        "stock": "📦 Stock: {stock}",
        "out_of_stock": "❌ Out of Stock"
    },
    "uz": {
        "back_categories": "🔙 Kategoriyalarga",
        "main_menu": "🏠 Asosiy menyu",
        "prev": "◀️ Oldingi",
        "next": "Keyingi ▶️",
        "page": "{page} / {total} sahifa",
        "add": "➕ Savatga qo'shish",
        "remove": "➖ Savatdan olib tashlash",
        "in_cart": "✅ Savatda",
        "details": "Batafsil",
        "price": "💰 Narxi: ${price}",
        "stock": "📦 Omborda: {stock}",
        "out_of_stock": "❌ Omborda yo'q"
    },
    "ru": {
        "back_categories": "🔙 К категориям",
        "main_menu": "🏠 Главное меню",
        "prev": "◀️ Предыдущая",
        "next": "Следующая ▶️",
        "page": "Страница {page} из {total}",
        "add": "➕ В корзину",
        "remove": "➖ Из корзины",
        "in_cart": "✅ В корзине",
        "details": "Подробнее",
        "price": "💰 Цена: ${price}",
        "stock": "📦 В наличии: {stock}",
        "out_of_stock": "❌ Нет в наличии"
    }
}

CART_LABELS = {
    "en": {
        "checkout": "✅ Proceed to Checkout",
        "continue": "🔙 Continue Shopping",
        "clear": "🗑 Clear Cart",
        "total": "💰 Total: ${total}",
        "empty": "Your cart is empty",
        "items": "Items in cart: {count}",
        "cart_title": "Your Cart",
        "remove_item": "❌ Remove {name}"
    },
    "uz": {
        "checkout": "✅ Buyurtma berish",
        "continue": "🔙 Xaridni davom ettirish",
        "clear": "🗑 Savatni tozalash",
        "total": "💰 Jami: ${total}",
        "empty": "Savatingiz bo'sh",
        "items": "Savatdagi mahsulotlar: {count}",
        "cart_title": "Savatingiz",
        "remove_item": "❌ {name} ni olib tashlash"
    },
    "ru": {
        "checkout": "✅ Оформить заказ",
        "continue": "🔙 Продолжить покупки",
        "clear": "🗑 Очистить корзину",
        "total": "💰 Итого: ${total}",
        "empty": "Корзина пуста",
        "items": "Товаров в корзине: {count}",
        "cart_title": "Ваша Корзина",
        "remove_item": "❌ Удалить {name}"
    }
}

ADMIN_LABELS = {
    "en": {
        "welcome": "👋 Welcome, Admin!",
        "menu": "Admin Panel",
        "products": "📦 Products",
        "orders": "📋 Orders",
        "categories": "📁 Categories",
        "stats": "📊 Statistics",
        "add_product": "➕ Add Product",
        "add_category": "➕ Add Category",
        "view_products": "📦 View Products",
        "update_product": "📝 Update Product",
        "delete_product": "❌ Delete Product",
        "view_orders": "📋 View Orders",
        "update_order_status": "🔄 Update Order Status",
        "back": "🔙 Back to Main",
        "back_admin": "🔙 Back to Admin",
        "confirm": "✅ Confirm",
        "cancel": "❌ Cancel",
        "select_category": "Select Category",
        "enter_name": "Enter product name",
        "enter_price": "Enter price",
        "enter_stock": "Enter stock",
        "enter_description": "Enter description",
        "enter_image": "Send image or URL",
        "product_added": "✅ Product added successfully!",
        "category_added": "✅ Category added successfully!",
        "product_updated": "✅ Product updated successfully!",
        "product_deleted": "✅ Product deleted successfully!",
        "order_updated": "✅ Order status updated successfully!",
        "unknown_command": "❌ I didn't understand this command. Please use the buttons below:"
    },
    "uz": {
        "welcome": "👋 Xush kelibsiz, Admin!",
        "menu": "Admin Panel",
        "products": "📦 Mahsulotlar",
        "orders": "📋 Buyurtmalar",
        "categories": "📁 Kategoriyalar",
        "stats": "📊 Statistika",
        "add_product": "➕ Mahsulot qo'shish",
        "add_category": "➕ Kategoriya qo'shish",
        "view_products": "📦 Mahsulotlarni ko'rish",
        "update_product": "📝 Mahsulotni yangilash",
        "delete_product": "❌ Mahsulotni o'chirish",
        "view_orders": "📋 Buyurtmalarni ko'rish",
        "update_order_status": "🔄 Buyurtma holatini yangilash",
        "back": "🔙 Asosiy menyu",
        "back_admin": "🔙 Admin panelga",
        "confirm": "✅ Tasdiqlash",
        "cancel": "❌ Bekor qilish",
        "select_category": "Kategoriyani tanlang",
        "enter_name": "Mahsulot nomini kiriting",
        "enter_price": "Narxni kiriting",
        "enter_stock": "Miqdorni kiriting",
        "enter_description": "Tavsifni kiriting",
        "enter_image": "Rasm yoki URL yuboring",
        "product_added": "✅ Mahsulot muvaffaqiyatli qo'shildi!",
        "category_added": "✅ Kategoriya muvaffaqiyatli qo'shildi!",
        "product_updated": "✅ Mahsulot muvaffaqiyatli yangilandi!",
        "product_deleted": "✅ Mahsulot muvaffaqiyatli o'chirildi!",
        "order_updated": "✅ Buyurtma holati muvaffaqiyatli yangilandi!",
        "unknown_command": "❌ Men bu buyruqni tushunmadim. Iltimos, quyidagi tugmalardan foydalaning:"
    },
    "ru": {
        "welcome": "👋 Добро пожаловать, Админ!",
        "menu": "Панель администратора",
        "products": "📦 Товары",
        "orders": "📋 Заказы",
        "categories": "📁 Категории",
        "stats": "📊 Статистика",
        "add_product": "➕ Добавить товар",
        "add_category": "➕ Добавить категорию",
        "view_products": "📦 Просмотр товаров",
        "update_product": "📝 Обновить товар",
        "delete_product": "❌ Удалить товар",
        "view_orders": "📋 Просмотр заказов",
        "update_order_status": "🔄 Обновить статус заказа",
        "back": "🔙 На главную",
        "back_admin": "🔙 В админ панель",
        "confirm": "✅ Подтвердить",
        "cancel": "❌ Отмена",
        "select_category": "Выберите категорию",
        "enter_name": "Введите название товара",
        "enter_price": "Введите цену",
        "enter_stock": "Введите количество",
        "enter_description": "Введите описание",
        "enter_image": "Отправьте изображение или URL",
        "product_added": "✅ Товар успешно добавлен!",
        "category_added": "✅ Категория успешно добавлена!",
        "product_updated": "✅ Товар успешно обновлён!",
        "product_deleted": "✅ Товар успешно удалён!",
        "order_updated": "✅ Статус заказа успешно обновлён!",
        "unknown_command": "❌ Я не понял эту команду. Пожалуйста, используйте кнопки ниже:"
    }
}

ORDER_STATUS_LABELS = {
    "en": {
        "pending": "⏳ Pending",
        "confirmed": "✅ Confirmed",
        "paid": "✅ Paid",
        "shipped": "📦 Shipped",
        "delivered": "🎉 Delivered",
        "cancelled": "❌ Cancelled"
    },
    "uz": {
        "pending": "⏳ Kutilmoqda",
        "confirmed": "✅ Tasdiqlangan",
        "paid": "✅ To'langan",
        "shipped": "📦 Yuborilgan",
        "delivered": "🎉 Yetkazilgan",
        "cancelled": "❌ Bekor qilingan"
    },
    "ru": {
        "pending": "⏳ В ожидании",
        "confirmed": "✅ Подтверждён",
        "paid": "✅ Оплачено",
        "shipped": "📦 Отправлено",
        "delivered": "🎉 Доставлено",
        "cancelled": "❌ Отменено"
    }
}

def get_main_keyboard(is_admin: bool = False, language: str = "en") -> ReplyKeyboardMarkup:
    """Get main menu keyboard with language support"""
    lbl = MAIN_KEYBOARD_LABELS.get(language, MAIN_KEYBOARD_LABELS["en"])
    
    keyboard = [
        [KeyboardButton(text=lbl["browse"])],
        [KeyboardButton(text=lbl["search"])],
        [KeyboardButton(text=lbl["cart"]), KeyboardButton(text=lbl["orders"])],
    ]
    
    # Language button row
    bottom_row = [KeyboardButton(text=lbl["language"])]
    if is_admin:
        bottom_row.insert(0, KeyboardButton(text=lbl["admin"]))
    keyboard.append(bottom_row)
    
    # Input field placeholder based on language
    placeholder = {
        "en": "Choose an option...",
        "uz": "Tanlang...",
        "ru": "Выберите..."
    }.get(language, "Choose an option...")
    
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder=placeholder
    )

def get_admin_keyboard(language: str = "en") -> InlineKeyboardMarkup:
    """Get admin panel inline keyboard (changed from ReplyKeyboardMarkup)"""
    lbl = ADMIN_LABELS.get(language, ADMIN_LABELS["en"])
    
    builder = InlineKeyboardBuilder()
    
    builder.button(text=lbl["view_products"], callback_data="admin_view_products")
    builder.button(text=lbl["add_product"], callback_data="admin_add_product")
    builder.button(text=lbl["update_product"], callback_data="admin_update_product")
    builder.button(text=lbl["delete_product"], callback_data="admin_delete_product")
    builder.button(text=lbl["view_orders"], callback_data="admin_view_orders")
    builder.button(text=lbl["update_order_status"], callback_data="admin_update_order_status")
    builder.button(text=lbl["stats"], callback_data="admin_stats")
    builder.button(text=lbl["back"], callback_data="main_menu")
    
    builder.adjust(2)
    
    return builder.as_markup()

def get_language_keyboard() -> InlineKeyboardMarkup:
    """Get language selection keyboard"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="🇺🇿 O'zbekcha", callback_data="lang_uz")
    builder.button(text="🇷🇺 Русский", callback_data="lang_ru")
    builder.button(text="🇬🇧 English", callback_data="lang_en")
    builder.adjust(1)
    
    return builder.as_markup()

def get_categories_keyboard(categories: List[Category], language: str = "en") -> InlineKeyboardMarkup:
    """Get categories inline keyboard"""
    lbl = CATEGORY_LABELS.get(language, CATEGORY_LABELS["en"])
    
    builder = InlineKeyboardBuilder()
    
    for category in categories:
        builder.button(
            text=f"📁 {category.name}",
            callback_data=f"category_{category.id}"
        )
    
    builder.button(text=lbl["main_menu"], callback_data="main_menu")
    builder.adjust(2)
    
    return builder.as_markup()

def get_products_keyboard(
    products: List[Product], 
    page: int = 0, 
    total_pages: int = 1, 
    language: str = "en",
    category_id: Optional[int] = None
) -> InlineKeyboardMarkup:
    """Get products inline keyboard with pagination"""
    lbl = PRODUCT_LABELS.get(language, PRODUCT_LABELS["en"])
    
    builder = InlineKeyboardBuilder()
    
    # Product buttons with prices
    for product in products:
        stock_status = "✅" if product.stock > 0 else "❌"
        builder.button(
            text=f"{stock_status} {product.name[:30]} - ${product.price:.2f}",
            callback_data=f"product_{product.id}"
        )
    
    builder.adjust(1)
    
    # Pagination row
    pagination_buttons = []
    
    if page > 0:
        pagination_buttons.append(
            InlineKeyboardButton(
                text=lbl["prev"], 
                callback_data=f"page_{page-1}" + (f"_cat_{category_id}" if category_id else "")
            )
        )
    
    # Page indicator
    if total_pages > 1:
        pagination_buttons.append(
            InlineKeyboardButton(
                text=lbl["page"].format(page=page+1, total=total_pages),
                callback_data="ignore"
            )
        )
    
    if page < total_pages - 1:
        pagination_buttons.append(
            InlineKeyboardButton(
                text=lbl["next"], 
                callback_data=f"page_{page+1}" + (f"_cat_{category_id}" if category_id else "")
            )
        )
    
    if pagination_buttons:
        builder.row(*pagination_buttons)
    
    # Navigation buttons
    builder.row(
        InlineKeyboardButton(text=lbl["back_categories"], callback_data="back_to_categories"),
        InlineKeyboardButton(text=lbl["main_menu"], callback_data="main_menu"),
        width=2
    )
    
    return builder.as_markup()

def get_product_actions_keyboard(
    product_id: int, 
    in_cart: bool = False, 
    language: str = "en",
    stock: int = 0
) -> InlineKeyboardMarkup:
    """Get product action buttons"""
    lbl = PRODUCT_LABELS.get(language, PRODUCT_LABELS["en"])
    cart_lbl = CART_LABELS.get(language, CART_LABELS["en"])
    
    builder = InlineKeyboardBuilder()
    
    # Add to cart button (disabled if out of stock)
    if stock > 0:
        if in_cart:
            builder.button(text=lbl["in_cart"], callback_data="ignore")
            builder.button(text=lbl["remove"], callback_data=f"remove_{product_id}")
        else:
            builder.button(text=lbl["add"], callback_data=f"add_{product_id}")
    else:
        builder.button(text=lbl["out_of_stock"], callback_data="ignore")
    
    builder.adjust(1)
    
    # Navigation buttons
    builder.row(
        InlineKeyboardButton(text=lbl["back_categories"], callback_data="back_to_categories"),
        InlineKeyboardButton(text=cart_lbl["cart_title"], callback_data="view_cart"),
        width=2
    )
    
    return builder.as_markup()

def get_cart_keyboard(
    cart_items: List[CartItem], 
    language: str = "en",
    total: float = 0.0
) -> InlineKeyboardMarkup:
    """Get cart inline keyboard"""
    lbl = CART_LABELS.get(language, CART_LABELS["en"])
    
    builder = InlineKeyboardBuilder()
    
    # Remove buttons for each item
    for item in cart_items:
        if item.product:
            builder.button(
                text=lbl["remove_item"].format(name=item.product.name[:20]),
                callback_data=f"remove_{item.product.id}"
            )
    
    if cart_items:
        builder.adjust(1)
        
        # Total display (non-clickable)
        total_text = lbl["total"].format(total=total)
        builder.row(
            InlineKeyboardButton(text=total_text, callback_data="ignore"),
            width=1
        )
        
        # Checkout and clear buttons
        builder.row(
            InlineKeyboardButton(text=lbl["checkout"], callback_data="checkout"),
            InlineKeyboardButton(text=lbl["clear"], callback_data="clear_cart"),
            width=2
        )
    
    # Continue shopping button
    builder.row(
        InlineKeyboardButton(text=lbl["continue"], callback_data="main_menu"),
        width=1
    )
    
    return builder.as_markup()

def get_order_confirmation_keyboard(language: str = "en") -> InlineKeyboardMarkup:
    """Get order confirmation keyboard"""
    lbl = ADMIN_LABELS.get(language, ADMIN_LABELS["en"])
    
    builder = InlineKeyboardBuilder()
    
    builder.button(text=lbl["confirm"], callback_data="confirm_order")
    builder.button(text=lbl["cancel"], callback_data="main_menu")
    builder.adjust(2)
    
    return builder.as_markup()

def get_admin_categories_keyboard(categories: List[Category], language: str = "en") -> InlineKeyboardMarkup:
    """Get admin categories selection keyboard"""
    lbl = ADMIN_LABELS.get(language, ADMIN_LABELS["en"])
    
    builder = InlineKeyboardBuilder()
    
    for category in categories:
        builder.button(
            text=f"📁 {category.name}",
            callback_data=f"admin_select_category_{category.id}"
        )
    
    builder.button(text=lbl["back_admin"], callback_data="admin_panel")
    builder.adjust(1)
    
    return builder.as_markup()

def get_admin_products_keyboard(
    products: List[Product], 
    language: str = "en",
    action: str = "update"
) -> InlineKeyboardMarkup:
    """Get admin products selection keyboard"""
    lbl = ADMIN_LABELS.get(language, ADMIN_LABELS["en"])
    
    builder = InlineKeyboardBuilder()
    
    for product in products[:10]:  # Limit to 10 products
        action_prefix = "update" if action == "update" else "delete"
        builder.button(
            text=f"{'📝' if action == 'update' else '❌'} {product.name[:20]} - ${product.price:.2f}",
            callback_data=f"admin_{action_prefix}_product_{product.id}"
        )
    
    builder.button(text=lbl["back_admin"], callback_data="admin_panel")
    builder.adjust(1)
    
    return builder.as_markup()

def get_order_status_keyboard(order_id: int, language: str = "en") -> InlineKeyboardMarkup:
    """Get order status selection keyboard"""
    status_lbl = ORDER_STATUS_LABELS.get(language, ORDER_STATUS_LABELS["en"])
    admin_lbl = ADMIN_LABELS.get(language, ADMIN_LABELS["en"])
    
    builder = InlineKeyboardBuilder()
    
    for status_key, status_text in status_lbl.items():
        builder.button(
            text=status_text,
            callback_data=f"set_order_status_{order_id}_{status_key}"
        )
    
    builder.button(text=admin_lbl["back_admin"], callback_data="admin_panel")
    builder.adjust(2)
    
    return builder.as_markup()

def get_confirmation_keyboard(
    language: str = "en",
    confirm_callback: str = "confirm",
    cancel_callback: str = "cancel"
) -> InlineKeyboardMarkup:
    """Get confirmation keyboard (Yes/No)"""
    lbl = ADMIN_LABELS.get(language, ADMIN_LABELS["en"])
    
    builder = InlineKeyboardBuilder()
    
    builder.button(text=lbl["confirm"], callback_data=confirm_callback)
    builder.button(text=lbl["cancel"], callback_data=cancel_callback)
    builder.adjust(2)
    
    return builder.as_markup()

def get_back_keyboard(
    callback_data: str = "main_menu",
    language: str = "en"
) -> InlineKeyboardMarkup:
    """Simple back button keyboard"""
    cat_lbl = CATEGORY_LABELS.get(language, CATEGORY_LABELS["en"])
    
    builder = InlineKeyboardBuilder()
    
    builder.button(text=cat_lbl["back"], callback_data=callback_data)
    
    return builder.as_markup()

def get_pagination_keyboard(
    current_page: int,
    total_pages: int,
    base_callback: str,
    language: str = "en"
) -> InlineKeyboardMarkup:
    """Generic pagination keyboard"""
    lbl = PRODUCT_LABELS.get(language, PRODUCT_LABELS["en"])
    
    builder = InlineKeyboardBuilder()
    
    pagination_buttons = []
    
    if current_page > 0:
        pagination_buttons.append(
            InlineKeyboardButton(
                text=lbl["prev"],
                callback_data=f"{base_callback}_{current_page-1}"
            )
        )
    
    if total_pages > 1:
        pagination_buttons.append(
            InlineKeyboardButton(
                text=lbl["page"].format(page=current_page+1, total=total_pages),
                callback_data="ignore"
            )
        )
    
    if current_page < total_pages - 1:
        pagination_buttons.append(
            InlineKeyboardButton(
                text=lbl["next"],
                callback_data=f"{base_callback}_{current_page+1}"
            )
        )
    
    builder.row(*pagination_buttons)
    
    return builder.as_markup()

def get_admin_stats_keyboard(language: str = "en") -> InlineKeyboardMarkup:
    """Get admin statistics keyboard"""
    lbl = ADMIN_LABELS.get(language, ADMIN_LABELS["en"])
    
    builder = InlineKeyboardBuilder()
    
    refresh_text = {
        "en": "🔄 Refresh",
        "uz": "🔄 Yangilash",
        "ru": "🔄 Обновить"
    }.get(language, "🔄 Refresh")
    
    builder.button(text=refresh_text, callback_data="admin_refresh_stats")
    builder.button(text=lbl["back_admin"], callback_data="admin_panel")
    builder.adjust(2)
    
    return builder.as_markup()