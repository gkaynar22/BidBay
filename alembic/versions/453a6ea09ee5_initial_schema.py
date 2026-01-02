"""initial_schema

Revision ID: 453a6ea09ee5
Revises:
Create Date: 2026-01-02 16:41:41.169136

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '453a6ea09ee5'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create users table first (no dependencies)
    op.create_table('users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('phone_number', sa.String(length=20), nullable=True),
        sa.Column('role', sa.Enum('BUYER', 'SELLER', 'ADMIN', name='userrole'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # 2. Create categories table (no dependencies)
    op.create_table('categories',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_categories_name'), 'categories', ['name'], unique=True)

    # 3. Create products table (depends on users, categories)
    # Note: accepted_bid_id FK will be added later to avoid circular dependency
    op.create_table('products',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('seller_id', sa.Integer(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('starting_price', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('min_increment', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('auction_end_at', sa.DateTime(), nullable=False),
        sa.Column('status', sa.Enum('ACTIVE', 'CLOSED', 'SOLD', 'EXPIRED', name='productstatus'), nullable=False),
        sa.Column('accepted_bid_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ),
        sa.ForeignKeyConstraint(['seller_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_products_auction_end_at'), 'products', ['auction_end_at'], unique=False)
    op.create_index(op.f('ix_products_category_id'), 'products', ['category_id'], unique=False)
    op.create_index(op.f('ix_products_seller_id'), 'products', ['seller_id'], unique=False)
    op.create_index(op.f('ix_products_status'), 'products', ['status'], unique=False)
    op.create_index('ix_products_status_auction_end', 'products', ['status', 'auction_end_at'], unique=False)
    op.create_index(op.f('ix_products_title'), 'products', ['title'], unique=False)

    # 4. Create bids table (depends on users, products)
    op.create_table('bids',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('bidder_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'ACCEPTED', 'REJECTED', 'OUTBID', 'WITHDRAWN', name='bidstatus'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('amount > 0', name='ck_bids_amount_positive'),
        sa.ForeignKeyConstraint(['bidder_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_bids_bidder_id'), 'bids', ['bidder_id'], unique=False)
    op.create_index('ix_bids_product_amount', 'bids', ['product_id', 'amount'], unique=False)
    op.create_index('ix_bids_product_bidder_created', 'bids', ['product_id', 'bidder_id', 'created_at'], unique=False)
    op.create_index(op.f('ix_bids_product_id'), 'bids', ['product_id'], unique=False)

    # 5. Add FK constraint from products.accepted_bid_id to bids.id (circular dependency resolved)
    op.create_foreign_key('fk_products_accepted_bid', 'products', 'bids', ['accepted_bid_id'], ['id'])

    # 6. Create product_images table (depends on products)
    op.create_table('product_images',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('image_url', sa.String(length=500), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_product_images_product_id'), 'product_images', ['product_id'], unique=False)

    # 7. Create favorites table (depends on users, products)
    op.create_table('favorites',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'product_id')
    )
    op.create_index(op.f('ix_favorites_product_id'), 'favorites', ['product_id'], unique=False)
    op.create_index(op.f('ix_favorites_user_id'), 'favorites', ['user_id'], unique=False)

    # 8. Create orders table (depends on users, products, bids)
    op.create_table('orders',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('buyer_id', sa.Integer(), nullable=False),
        sa.Column('seller_id', sa.Integer(), nullable=False),
        sa.Column('bid_id', sa.Integer(), nullable=False),
        sa.Column('total_amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('status', sa.Enum('AWAITING_PAYMENT', 'PAID', 'CANCELLED', name='orderstatus'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['bid_id'], ['bids.id'], ),
        sa.ForeignKeyConstraint(['buyer_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.ForeignKeyConstraint(['seller_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('bid_id')
    )
    op.create_index(op.f('ix_orders_buyer_id'), 'orders', ['buyer_id'], unique=False)
    op.create_index(op.f('ix_orders_product_id'), 'orders', ['product_id'], unique=False)
    op.create_index(op.f('ix_orders_seller_id'), 'orders', ['seller_id'], unique=False)

    # 9. Create payments table (depends on orders)
    op.create_table('payments',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('payment_ref', sa.String(length=255), nullable=True),
        sa.Column('status', sa.Enum('INITIATED', 'SUCCESS', 'FAILED', name='paymentstatus'), nullable=False),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payments_order_id'), 'payments', ['order_id'], unique=True)


def downgrade() -> None:
    # Drop tables in reverse order of creation
    op.drop_index(op.f('ix_payments_order_id'), table_name='payments')
    op.drop_table('payments')

    op.drop_index(op.f('ix_orders_seller_id'), table_name='orders')
    op.drop_index(op.f('ix_orders_product_id'), table_name='orders')
    op.drop_index(op.f('ix_orders_buyer_id'), table_name='orders')
    op.drop_table('orders')

    op.drop_index(op.f('ix_favorites_user_id'), table_name='favorites')
    op.drop_index(op.f('ix_favorites_product_id'), table_name='favorites')
    op.drop_table('favorites')

    op.drop_index(op.f('ix_product_images_product_id'), table_name='product_images')
    op.drop_table('product_images')

    # Drop the FK constraint before dropping bids table
    op.drop_constraint('fk_products_accepted_bid', 'products', type_='foreignkey')

    op.drop_index(op.f('ix_bids_product_id'), table_name='bids')
    op.drop_index('ix_bids_product_bidder_created', table_name='bids')
    op.drop_index('ix_bids_product_amount', table_name='bids')
    op.drop_index(op.f('ix_bids_bidder_id'), table_name='bids')
    op.drop_table('bids')

    op.drop_index(op.f('ix_products_title'), table_name='products')
    op.drop_index('ix_products_status_auction_end', table_name='products')
    op.drop_index(op.f('ix_products_status'), table_name='products')
    op.drop_index(op.f('ix_products_seller_id'), table_name='products')
    op.drop_index(op.f('ix_products_category_id'), table_name='products')
    op.drop_index(op.f('ix_products_auction_end_at'), table_name='products')
    op.drop_table('products')

    op.drop_index(op.f('ix_categories_name'), table_name='categories')
    op.drop_table('categories')

    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
