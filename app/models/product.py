import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import String, Text, Enum, DateTime, ForeignKey, Numeric, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ProductStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"
    SOLD = "SOLD"
    EXPIRED = "EXPIRED"


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    seller_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    starting_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    min_increment: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("1.00"))
    auction_end_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    status: Mapped[ProductStatus] = mapped_column(
        Enum(ProductStatus), nullable=False, default=ProductStatus.ACTIVE, index=True
    )
    accepted_bid_id: Mapped[int | None] = mapped_column(ForeignKey("bids.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    seller = relationship("User", back_populates="products", foreign_keys=[seller_id])
    category = relationship("Category", back_populates="products")
    images = relationship("ProductImage", back_populates="product", cascade="all, delete-orphan")
    bids = relationship("Bid", back_populates="product", foreign_keys="Bid.product_id")
    accepted_bid = relationship("Bid", foreign_keys=[accepted_bid_id], post_update=True)
    favorites = relationship("Favorite", back_populates="product", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="product")

    # Composite indexes for common queries
    __table_args__ = (
        Index("ix_products_status_auction_end", "status", "auction_end_at"),
    )

    def __repr__(self) -> str:
        return f"<Product(id={self.id}, title={self.title}, status={self.status})>"
