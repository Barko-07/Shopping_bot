from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update
from sqlalchemy.orm import selectinload
from typing import List, Optional, Tuple
from database.models import CartItem, User, Product
from schemas.schemas import CartItemCreate
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CartService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_user(self, telegram_id: int, **kwargs) -> User:
        """Get or create user by telegram ID"""
        try:
            result = await self.db.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                # Default values for new user
                user_data = {
                    'telegram_id': telegram_id,
                    'username': kwargs.get('username'),
                    'first_name': kwargs.get('first_name'),
                    'last_name': kwargs.get('last_name'),
                    'language': kwargs.get('language', 'en'),
                    'is_admin': False
                }
                user = User(**user_data)
                self.db.add(user)
                await self.db.commit()
                await self.db.refresh(user)
                logger.info(f"New user created: {telegram_id}")
            
            return user
        except Exception as e:
            logger.error(f"Error in get_or_create_user: {e}")
            await self.db.rollback()
            raise

    async def get_cart_item(self, user_id: int, product_id: int) -> Optional[CartItem]:
        """Get specific cart item"""
        try:
            result = await self.db.execute(
                select(CartItem)
                .where(
                    CartItem.user_id == user_id,
                    CartItem.product_id == product_id
                )
                .options(selectinload(CartItem.product))
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error in get_cart_item: {e}")
            return None

    async def add_to_cart(self, user_id: int, product_id: int, quantity: int = 1) -> Optional[CartItem]:
        """Add item to cart or update quantity if exists"""
        try:
            # Check if product exists and has stock
            product_result = await self.db.execute(
                select(Product).where(Product.id == product_id)
            )
            product = product_result.scalar_one_or_none()
            
            if not product:
                logger.error(f"Product {product_id} not found")
                return None
            
            # Check if item already in cart
            cart_item = await self.get_cart_item(user_id, product_id)
            
            if cart_item:
                # Check if new quantity exceeds stock
                new_quantity = cart_item.quantity + quantity
                if product.stock < new_quantity:
                    logger.warning(f"Insufficient stock for product {product_id}")
                    return None
                cart_item.quantity = new_quantity
            else:
                # Check if quantity exceeds stock
                if product.stock < quantity:
                    logger.warning(f"Insufficient stock for product {product_id}")
                    return None
                cart_item = CartItem(
                    user_id=user_id,
                    product_id=product_id,
                    quantity=quantity
                )
                self.db.add(cart_item)
            
            await self.db.commit()
            await self.db.refresh(cart_item)
            
            # Load product relationship
            result = await self.db.execute(
                select(CartItem)
                .where(CartItem.id == cart_item.id)
                .options(selectinload(CartItem.product))
            )
            return result.scalar_one()
            
        except Exception as e:
            logger.error(f"Error in add_to_cart: {e}")
            await self.db.rollback()
            return None

    async def update_quantity(self, user_id: int, product_id: int, quantity: int) -> Optional[CartItem]:
        """Update quantity of cart item"""
        try:
            if quantity <= 0:
                # If quantity is 0 or negative, remove item
                await self.remove_from_cart(user_id, product_id)
                return None
            
            # Check if product exists and has stock
            product_result = await self.db.execute(
                select(Product).where(Product.id == product_id)
            )
            product = product_result.scalar_one_or_none()
            
            if not product:
                logger.error(f"Product {product_id} not found")
                return None
            
            # Check stock
            if product.stock < quantity:
                logger.warning(f"Insufficient stock for product {product_id}")
                return None
            
            # Get cart item
            cart_item = await self.get_cart_item(user_id, product_id)
            
            if not cart_item:
                logger.warning(f"Cart item not found for user {user_id}, product {product_id}")
                return None
            
            # Update quantity
            cart_item.quantity = quantity
            await self.db.commit()
            await self.db.refresh(cart_item)
            
            # Load product relationship
            result = await self.db.execute(
                select(CartItem)
                .where(CartItem.id == cart_item.id)
                .options(selectinload(CartItem.product))
            )
            return result.scalar_one()
            
        except Exception as e:
            logger.error(f"Error in update_quantity: {e}")
            await self.db.rollback()
            return None

    async def remove_from_cart(self, user_id: int, product_id: int) -> bool:
        """Remove item from cart"""
        try:
            result = await self.db.execute(
                delete(CartItem).where(
                    CartItem.user_id == user_id,
                    CartItem.product_id == product_id
                )
            )
            await self.db.commit()
            deleted = result.rowcount > 0
            if deleted:
                logger.info(f"Item removed from cart: user {user_id}, product {product_id}")
            return deleted
        except Exception as e:
            logger.error(f"Error in remove_from_cart: {e}")
            await self.db.rollback()
            return False

    async def get_cart(self, user_id: int) -> List[CartItem]:
        """Get user's cart with products"""
        try:
            result = await self.db.execute(
                select(CartItem)
                .where(CartItem.user_id == user_id)
                .options(selectinload(CartItem.product))
                .order_by(CartItem.created_at.desc())  # 'added_at' emas, 'created_at'
            )
            cart_items = result.scalars().all()
            
            # Filter out items with no product (deleted products)
            valid_items = [item for item in cart_items if item.product]
            
            # If there are invalid items, remove them
            if len(valid_items) < len(cart_items):
                for item in cart_items:
                    if not item.product:
                        await self.db.delete(item)
                await self.db.commit()
                logger.info(f"Cleaned up {len(cart_items) - len(valid_items)} invalid cart items")
            
            return valid_items
        except Exception as e:
            logger.error(f"Error in get_cart: {e}")
            return []

    async def clear_cart(self, user_id: int) -> bool:
        """Clear user's cart"""
        try:
            await self.db.execute(
                delete(CartItem).where(CartItem.user_id == user_id)
            )
            await self.db.commit()
            logger.info(f"Cart cleared for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error in clear_cart: {e}")
            await self.db.rollback()
            return False

    async def calculate_cart_total(self, cart_items: List[CartItem]) -> float:
        """Calculate total price of cart"""
        try:
            total = 0.0
            for item in cart_items:
                if item.product:
                    total += item.product.price * item.quantity
            return round(total, 2)
        except Exception as e:
            logger.error(f"Error in calculate_cart_total: {e}")
            return 0.0

    async def get_cart_count(self, user_id: int) -> int:
        """Get number of items in cart"""
        try:
            cart_items = await self.get_cart(user_id)
            return len(cart_items)
        except Exception as e:
            logger.error(f"Error in get_cart_count: {e}")
            return 0

    async def get_cart_summary(self, user_id: int) -> dict:
        """Get cart summary with items and total"""
        try:
            cart_items = await self.get_cart(user_id)
            total = await self.calculate_cart_total(cart_items)
            
            items_list = []
            for item in cart_items:
                if item.product:
                    items_list.append({
                        'id': item.id,
                        'product_id': item.product.id,
                        'name': item.product.name,
                        'price': item.product.price,
                        'quantity': item.quantity,
                        'subtotal': item.product.price * item.quantity,
                        'stock': item.product.stock
                    })
            
            return {
                'items': items_list,
                'total': total,
                'count': len(items_list)
            }
        except Exception as e:
            logger.error(f"Error in get_cart_summary: {e}")
            return {'items': [], 'total': 0.0, 'count': 0}

    async def validate_cart_stock(self, user_id: int) -> Tuple[bool, List[str]]:
        """Validate if all items in cart have sufficient stock"""
        try:
            cart_items = await self.get_cart(user_id)
            errors = []
            
            for item in cart_items:
                if item.product:
                    if item.product.stock < item.quantity:
                        errors.append(f"{item.product.name}: mavjud {item.product.stock}, talab {item.quantity}")
                else:
                    errors.append(f"Mahsulot topilmadi (ID: {item.product_id})")
            
            return len(errors) == 0, errors
        except Exception as e:
            logger.error(f"Error in validate_cart_stock: {e}")
            return False, ["Xatolik yuz berdi"]

    async def merge_carts(self, from_user_id: int, to_user_id: int) -> bool:
        """Merge cart from one user to another (for user login scenarios)"""
        try:
            # Get source cart
            from_cart = await self.get_cart(from_user_id)
            
            for item in from_cart:
                if item.product:
                    # Check if product already in destination cart
                    existing = await self.get_cart_item(to_user_id, item.product_id)
                    
                    if existing:
                        # Update quantity
                        new_quantity = existing.quantity + item.quantity
                        await self.update_quantity(to_user_id, item.product_id, new_quantity)
                    else:
                        # Add new item
                        await self.add_to_cart(to_user_id, item.product_id, item.quantity)
                    
                    # Remove from source cart
                    await self.remove_from_cart(from_user_id, item.product_id)
            
            logger.info(f"Carts merged: from {from_user_id} to {to_user_id}")
            return True
        except Exception as e:
            logger.error(f"Error in merge_carts: {e}")
            await self.db.rollback()
            return False