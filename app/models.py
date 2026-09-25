from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


# Flask-Login needs this to load a user from the session
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ── USER TABLE ──────────────────────────────────────────────────
class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(100), nullable=False)
    email      = db.Column(db.String(120), unique=True, nullable=False)
    password   = db.Column(db.String(256), nullable=False)
    role       = db.Column(db.String(10), nullable=False)  # 'seller' or 'customer'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    products = db.relationship('Product', backref='seller', lazy=True)
    orders   = db.relationship('Order', backref='customer', lazy=True)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def __repr__(self):
        return f'<User {self.email} ({self.role})>'


# ── CATEGORY TABLE ──────────────────────────────────────────────
class Category(db.Model):
    __tablename__ = 'categories'

    id   = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    products = db.relationship('Product', backref='category', lazy=True)

    def __repr__(self):
        return f'<Category {self.name}>'


# ── PRODUCT TABLE ───────────────────────────────────────────────
class Product(db.Model):
    __tablename__ = 'products'

    id                  = db.Column(db.Integer, primary_key=True)
    seller_id           = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category_id         = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    name                = db.Column(db.String(100), nullable=False)
    description         = db.Column(db.Text, nullable=True)
    price               = db.Column(db.Numeric(10, 2), nullable=False)
    stock_qty           = db.Column(db.Integer, default=0)
    low_stock_threshold = db.Column(db.Integer, default=5)
    image_filename      = db.Column(db.String(200), nullable=True)
    created_at          = db.Column(db.DateTime, default=datetime.utcnow)

    order_items = db.relationship('OrderItem', backref='product', lazy=True)

    @property
    def is_low_stock(self):
        return self.stock_qty <= self.low_stock_threshold

    @property
    def is_out_of_stock(self):
        return self.stock_qty == 0

    def __repr__(self):
        return f'<Product {self.name} (qty: {self.stock_qty})>'


# ── ORDER TABLE ─────────────────────────────────────────────────
class Order(db.Model):
    __tablename__ = 'orders'

    id           = db.Column(db.Integer, primary_key=True)
    customer_id  = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    status       = db.Column(db.String(20), default='confirmed')  # confirmed, cancelled
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship('OrderItem', backref='order', lazy=True)

    def __repr__(self):
        return f'<Order {self.id} by Customer {self.customer_id}>'


# ── ORDER ITEM TABLE ────────────────────────────────────────────
class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id         = db.Column(db.Integer, primary_key=True)
    order_id   = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity   = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)  # price at time of order

    def __repr__(self):
        return f'<OrderItem order={self.order_id} product={self.product_id}>'