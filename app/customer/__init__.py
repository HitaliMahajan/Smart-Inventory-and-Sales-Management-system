from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app.models import Product, CartItem, Order, OrderItem
from app import db

customer = Blueprint('customer', __name__, url_prefix='/shop')

def customer_required(fn):
    @login_required
    def wrapper(*args, **kwargs):
        if not current_user.is_customer:
            abort(403)
        return fn(*args, **kwargs)
    wrapper.__name__ = fn.__name__
    return wrapper

@customer.route('/catalog')
def catalog():
    products = Product.query.filter(Product.stock_qty > 0).all()
    return render_template('customer/catalog.html', products=products)

@customer.route('/add-to-cart/<int:pid>', methods=['POST'])
def add_to_cart(pid):
    if not current_user.is_authenticated:
        flash('Please log in to add items to your cart', 'info')
        return redirect(url_for('auth.login', next=request.url))

    if not current_user.is_customer:
        abort(403)

    product = Product.query.get_or_404(pid)
    if product.is_out_of_stock:
        flash('Sorry, this item is out of stock', 'warning')
        return redirect(url_for('customer.catalog'))

    existing = CartItem.query.filter_by(
        customer_id=current_user.id,
        product_id=pid
    ).first()

    if existing:
        existing.quantity += 1
    else:
        new_item = CartItem(customer_id=current_user.id, product_id=pid, quantity=1)
        db.session.add(new_item)

    db.session.commit()
    flash('Item added to cart', 'success')
    return redirect(url_for('customer.catalog'))

@customer.route('/cart')
@customer_required
def view_cart():
    cart_items = CartItem.query.filter_by(customer_id=current_user.id).all()
    total = sum(item.product.price * item.quantity for item in cart_items)
    return render_template('customer/cart.html', cart_items=cart_items, total=total)

@customer.route('/cart/update/<int:item_id>', methods=['POST'])
@customer_required
def update_cart(item_id):
    cart_item = CartItem.query.get_or_404(item_id)
    if cart_item.customer_id != current_user.id:
        abort(403)

    new_qty = request.form.get('quantity', 1, type=int)
    if new_qty <= 0:
        db.session.delete(cart_item)
    else:
        cart_item.quantity = new_qty

    db.session.commit()
    flash('Cart updated', 'success')
    return redirect(url_for('customer.view_cart'))

@customer.route('/cart/remove/<int:item_id>', methods=['POST'])
@customer_required
def remove_from_cart(item_id):
    cart_item = CartItem.query.get_or_404(item_id)
    if cart_item.customer_id != current_user.id:
        abort(403)
    db.session.delete(cart_item)
    db.session.commit()
    flash('Item removed from cart', 'success')
    return redirect(url_for('customer.view_cart'))

@customer.route('/checkout', methods=['POST'])
@customer_required
def checkout():
    cart_items = CartItem.query.filter_by(customer_id=current_user.id).all()
    if not cart_items:
        flash('Your cart is empty', 'warning')
        return redirect(url_for('customer.catalog'))

    total = sum(item.product.price * item.quantity for item in cart_items)

    order = Order(customer_id=current_user.id, total_amount=total)
    db.session.add(order)
    db.session.flush()

    for ci in cart_items:
        oi = OrderItem(
            order_id=order.id,
            product_id=ci.product_id,
            quantity=ci.quantity,
            unit_price=ci.product.price
        )
        db.session.add(oi)
        ci.product.stock_qty -= ci.quantity
        db.session.delete(ci)

    db.session.commit()
    flash('Order placed successfully!', 'success')
    return redirect(url_for('customer.order_detail', order_id=order.id))

@customer.route('/orders')
@customer_required
def order_history():
    orders = (Order.query
              .filter_by(customer_id=current_user.id)
              .order_by(Order.created_at.desc())
              .all())
    return render_template('customer/orders.html', orders=orders)

@customer.route('/order/<int:order_id>')
@customer_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    if order.customer_id != current_user.id:
        abort(403)
    return render_template('customer/order_detail.html', order=order)