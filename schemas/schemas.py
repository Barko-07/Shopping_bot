from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime

# Language Schemas
class LanguageUpdate(BaseModel):
    """Schema for language update"""
    language: str

class LanguageResponse(BaseModel):
    """Schema for language response"""
    current_language: str
    supported_languages: List[str]
    languages: Dict[str, str]
    message: str

# Category Schemas
class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class Category(CategoryBase):
    id: int
    
    class Config:
        from_attributes = True  # Pydantic v2 da

# Product Schemas
class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    stock: int
    category_id: Optional[int] = None
    image_url: Optional[str] = None

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None
    category_id: Optional[int] = None
    image_url: Optional[str] = None

class Product(ProductBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Order Item Schemas
class OrderItemBase(BaseModel):
    product_id: int
    quantity: int
    price: float

class OrderItemCreate(OrderItemBase):
    pass

class OrderItem(OrderItemBase):
    id: int
    order_id: int
    
    class Config:
        from_attributes = True

# Order Schemas
class OrderBase(BaseModel):
    user_id: int
    customer_name: str
    phone: str
    address: str
    total_amount: float
    status: str = "pending"

class OrderCreate(BaseModel):
    user_id: int
    customer_name: str
    phone: str
    address: str
    items: List[OrderItemCreate]  # OrderItemCreate ishlatilyapti

class Order(OrderBase):
    id: int
    order_number: str
    created_at: datetime
    items: List[OrderItem] = []  # OrderItem ishlatilyapti
    
    class Config:
        from_attributes = True

# User Schemas
class UserBase(BaseModel):
    telegram_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    language: str = "en"

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: int
    created_at: datetime
    is_admin: bool = False
    
    class Config:
        from_attributes = True

# Cart Schemas
class CartItemBase(BaseModel):
    user_id: int
    product_id: int
    quantity: int

class CartItemCreate(CartItemBase):
    pass

class CartItem(CartItemBase):
    id: int
    created_at: datetime  # 'added_at' emas, 'created_at' bo'lishi kerak
    product: Optional[Product] = None
    
    class Config:
        from_attributes = True