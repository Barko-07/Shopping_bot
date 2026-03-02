from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from typing import Optional, List
from database.models import Product, Category
from schemas.schemas import ProductCreate, ProductUpdate

class ProductService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_product(self, product_data: ProductCreate) -> Product:
        """Create a new product"""
        product = Product(**product_data.model_dump())
        self.db.add(product)
        await self.db.commit()
        await self.db.refresh(product)
        return product

    async def get_product(self, product_id: int) -> Optional[Product]:
        """Get product by ID"""
        result = await self.db.execute(
            select(Product).where(Product.id == product_id)
        )
        return result.scalar_one_or_none()

    async def get_products(self, category_id: Optional[int] = None, skip: int = 0, limit: int = 100) -> List[Product]:
        """Get all products with optional category filter"""
        query = select(Product).options(selectinload(Product.category))
        
        if category_id:
            query = query.where(Product.category_id == category_id)
        
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def search_products(self, search_term: str) -> List[Product]:
        """Search products by name"""
        result = await self.db.execute(
            select(Product).where(Product.name.ilike(f"%{search_term}%"))
        )
        return result.scalars().all()

    async def update_product(self, product_id: int, product_data: ProductUpdate) -> Optional[Product]:
        """Update product"""
        update_data = product_data.model_dump(exclude_unset=True)
        if update_data:
            await self.db.execute(
                update(Product).where(Product.id == product_id).values(**update_data)
            )
            await self.db.commit()
        
        return await self.get_product(product_id)

    async def delete_product(self, product_id: int) -> bool:
        """Delete product"""
        result = await self.db.execute(
            delete(Product).where(Product.id == product_id)
        )
        await self.db.commit()
        return result.rowcount > 0

    async def get_categories(self) -> List[Category]:
        """Get all categories"""
        result = await self.db.execute(select(Category))
        return result.scalars().all()

    async def create_category(self, name: str, description: Optional[str] = None) -> Category:
        """Create new category"""
        category = Category(name=name, description=description)
        self.db.add(category)
        await self.db.commit()
        await self.db.refresh(category)
        return category