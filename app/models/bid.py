import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Enum, DateTime, ForeignKey, Numeric, Index, CheckConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class BidStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    OUTBID = "OUTBID"
    WITHDRAWN = "WITHDRAWN"


class Bid(Base):
    __tablename__ = "bids"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False, index=True)
    bidder_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[BidStatus] = mapped_column(Enum(BidStatus), nullable=False, default=BidStatus.PENDING)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    product = relationship("Product", back_populates="bids", foreign_keys=[product_id])
    bidder = relationship("User", back_populates="bids")
    order = relationship("Order", back_populates="bid", uselist=False)

    # Indexes and constraints
    __table_args__ = (
        Index("ix_bids_product_amount", "product_id", "amount"),
        Index("ix_bids_product_bidder_created", "product_id", "bidder_id", "created_at"),
        CheckConstraint("amount > 0", name="ck_bids_amount_positive"),
    )

    def __repr__(self) -> str:
        return f"<Bid(id={self.id}, product_id={self.product_id}, amount={self.amount}, status={self.status})>"
