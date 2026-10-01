# app/models.py
from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db, login_manager


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(100), nullable=False)
    email      = db.Column(db.String(120), unique=True, nullable=False)
    password   = db.Column(db.String(256), nullable=False)
    role       = db.Column(db.String(20), nullable=False, default="customer")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    products   = db.relationship(
        "Product",
        back_populates="seller",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    cart_items = db.relationship(
        "CartItem",
        back_populates="customer",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    orders     = db.relationship(
        "Order",
        back_populates="customer",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    def set_password(self, raw_password):
        self.password = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password, raw_password)

    @property
    def is_author(self):
        return self.role == "author"

    @property
    def is_customer(self):
        return self.role == "customer"

    @property
    def is_seller(self):
        return self.role == "seller"

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"


class Category(db.Model):
    __tablename__ = "categories"

    id   = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    products = db.relationship(
        "Product",
        back_populates="category",
        lazy="dynamic",
    )

    def __repr__(self):
        return f"<Category {self.name}>"


class Product(db.Model):
    __tablename__ = "products"

    id                  = db.Column(db.Integer, primary_key=True)
    seller_id           = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    category_id         = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True)

    name                = db.Column(db.String(100), nullable=False)
    description         = db.Column(db.Text, nullable=True)
    price               = db.Column(db.Numeric(10, 2), nullable=False)
    stock_qty           = db.Column(db.Integer, default=0)
    low_stock_threshold = db.Column(db.Integer, default=5)
    image_filename      = db.Column(db.String(200), nullable=True)
    created_at          = db.Column(db.DateTime, default=datetime.utcnow)

    seller      = db.relationship("User", back_populates="products")
    category    = db.relationship("Category", back_populates="products")
    order_items = db.relationship(
        "OrderItem",
        back_populates="product",
        lazy="dynamic",
    )
    cart_items = db.relationship(
        "CartItem",
        back_populates="product",
        lazy="dynamic",
    )

    @property
    def is_low_stock(self):
        return self.stock_qty <= self.low_stock_threshold

    @property
    def is_out_of_stock(self):
        return self.stock_qty == 0

    def __repr__(self):
        return f"<Product {self.name} (qty:{self.stock_qty})>"


class CartItem(db.Model):
    __tablename__ = "cart_items"

    id          = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    product_id  = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    quantity    = db.Column(db.Integer, nullable=False, default=1)
    added_at    = db.Column(db.DateTime, default=datetime.utcnow)

    customer = db.relationship("User", back_populates="cart_items")
    product  = db.relationship("Product", back_populates="cart_items")

    def __repr__(self):
        return f"<CartItem user={self.customer_id} product={self.product_id} qty={self.quantity}>"


class Order(db.Model):
    __tablename__ = "orders"

    id           = db.Column(db.Integer, primary_key=True)
    customer_id  = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    total_amount = db.Column(db.Numeric(12, 2), nullable=False)
    status       = db.Column(db.String(20), default="confirmed")
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    customer = db.relationship("User", back_populates="orders")
    items    = db.relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    def __repr__(self):
        return f"<Order {self.id} by Customer {self.customer_id}>"


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id         = db.Column(db.Integer, primary_key=True)
    order_id   = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    quantity   = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)

    order   = db.relationship("Order", back_populates="items")
    product = db.relationship("Product", back_populates="order_items")

    def __repr__(self):
        return f"<OrderItem order={self.order_id} product={self.product_id} qty={self.quantity}>"