from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload
from typing import Optional, List, Dict, Any
from datetime import datetime
import random
import string

from database.models import Order, OrderItem, User, Product
from schemas.schemas import OrderCreate

class OrderService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def generate_order_number(self) -> str:
        """Generate unique order number"""
        while True:
            # Generate order number: INV + YYYYMMDD + 6 random digits
            date_part = datetime.now().strftime("%Y%m%d")
            random_part = ''.join(random.choices(string.digits, k=6))
            order_number = f"INV-{date_part}-{random_part}"
            
            # Check if exists
            existing = await self.db.execute(
                select(Order).where(Order.order_number == order_number)
            )
            if not existing.scalar_one_or_none():
                return order_number
    
    async def get_user_orders(self, user_id: int) -> List[Order]:
        """Get all orders for a specific user"""
        result = await self.db.execute(
            select(Order)
            .where(Order.user_id == user_id)
            .options(selectinload(Order.items).selectinload(OrderItem.product))
            .order_by(Order.created_at.desc())
        )
        return result.scalars().all()
    
    async def get_all_orders(self) -> List[Order]:
        """Get all orders (for admin)"""
        result = await self.db.execute(
            select(Order)
            .options(selectinload(Order.items).selectinload(OrderItem.product))
            .order_by(Order.created_at.desc())
        )
        return result.scalars().all()
    
    async def get_order(self, order_id: int) -> Optional[Order]:
        """Get order by ID"""
        result = await self.db.execute(
            select(Order)
            .where(Order.id == order_id)
            .options(selectinload(Order.items).selectinload(OrderItem.product))
        )
        return result.scalar_one_or_none()
    
    async def get_order_by_number(self, order_number: str) -> Optional[Order]:
        """Get order by order number"""
        result = await self.db.execute(
            select(Order)
            .where(Order.order_number == order_number)
            .options(selectinload(Order.items).selectinload(OrderItem.product))
        )
        return result.scalar_one_or_none()
    
    async def create_order(self, order_data: Dict[str, Any]) -> Order:
        """Create new order"""
        # Generate order number
        order_number = await self.generate_order_number()
        
        # Calculate total amount
        total_amount = 0
        for item in order_data["items"]:
            total_amount += item["price"] * item["quantity"]
        
        # Create order
        order = Order(
            user_id=order_data["user_id"],
            order_number=order_number,
            customer_name=order_data["customer_name"],
            phone=order_data["phone"],
            address=order_data["address"],
            total_amount=total_amount,
            status="pending"
        )
        
        self.db.add(order)
        await self.db.flush()  # Get order ID
        
        # Create order items
        for item_data in order_data["items"]:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item_data["product_id"],
                quantity=item_data["quantity"],
                price=item_data["price"]
            )
            self.db.add(order_item)
            
            # Update product stock
            product = await self.db.get(Product, item_data["product_id"])
            if product:
                product.stock -= item_data["quantity"]
        
        await self.db.commit()
        await self.db.refresh(order)
        
        # Load items for the order
        result = await self.db.execute(
            select(Order)
            .where(Order.id == order.id)
            .options(selectinload(Order.items).selectinload(OrderItem.product))
        )
        return result.scalar_one()
    
    async def update_order_status(self, order_id: int, status: str) -> Optional[Order]:
        """Update order status"""
        order = await self.get_order(order_id)
        if order:
            order.status = status
            await self.db.commit()
            await self.db.refresh(order)
        return order
    
    async def cancel_order(self, order_id: int) -> bool:
        """Cancel order and restore stock"""
        order = await self.get_order(order_id)
        if not order or order.status == "cancelled":
            return False
        
        # Restore stock for each item
        for item in order.items:
            product = await self.db.get(Product, item.product_id)
            if product:
                product.stock += item.quantity
        
        order.status = "cancelled"
        await self.db.commit()
        return True
    
    async def delete_order(self, order_id: int) -> bool:
        """Delete order (admin only)"""
        order = await self.get_order(order_id)
        if order:
            await self.db.delete(order)
            await self.db.commit()
            return True
        return False
    
    async def get_orders_by_status(self, status: str) -> List[Order]:
        """Get orders by status"""
        result = await self.db.execute(
            select(Order)
            .where(Order.status == status)
            .options(selectinload(Order.items).selectinload(OrderItem.product))
            .order_by(Order.created_at.desc())
        )
        return result.scalars().all()
    
    async def get_orders_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Order]:
        """Get orders within date range"""
        result = await self.db.execute(
            select(Order)
            .where(Order.created_at.between(start_date, end_date))
            .options(selectinload(Order.items).selectinload(OrderItem.product))
            .order_by(Order.created_at.desc())
        )
        return result.scalars().all()
    
    async def get_order_statistics(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Get order statistics for user or all users"""
        query = select(Order)
        if user_id:
            query = query.where(Order.user_id == user_id)
        
        result = await self.db.execute(query)
        orders = result.scalars().all()
        
        total_orders = len(orders)
        total_spent = sum(order.total_amount for order in orders)
        avg_order_value = total_spent / total_orders if total_orders > 0 else 0
        
        # Count by status
        status_counts = {}
        for order in orders:
            status_counts[order.status] = status_counts.get(order.status, 0) + 1
        
        return {
            "total_orders": total_orders,
            "total_spent": total_spent,
            "average_order_value": round(avg_order_value, 2),
            "status_breakdown": status_counts
        }
    
    async def get_recent_orders(self, limit: int = 10) -> List[Order]:
        """Get recent orders"""
        result = await self.db.execute(
            select(Order)
            .options(selectinload(Order.items).selectinload(OrderItem.product))
            .order_by(Order.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_user_order_count(self, user_id: int) -> int:
        """Get number of orders for a user"""
        result = await self.db.execute(
            select(func.count()).select_from(Order).where(Order.user_id == user_id)
        )
        return result.scalar() or 0
    
    async def get_user_total_spent(self, user_id: int) -> float:
        """Get total amount spent by user"""
        result = await self.db.execute(
            select(func.sum(Order.total_amount)).where(Order.user_id == user_id)
        )
        return result.scalar() or 0.0