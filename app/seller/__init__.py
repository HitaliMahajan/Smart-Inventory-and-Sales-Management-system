import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.models import Product, Category, OrderItem
from app import db

seller = Blueprint('seller', __name__, url_prefix='/seller')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def seller_required(fn):
    @login_required
    def wrapper(*args, **kwargs):
        if not current_user.is_seller:
            abort(403)
        return fn(*args, **kwargs)
    wrapper.__name__ = fn.__name__
    return wrapper

@seller.route('/dashboard')
@seller_required
def dashboard():
    my_products = Product.query.filter_by(seller_id=current_user.id).all()
    total_products = len(my_products)

    low_stock = [p for p in my_products if p.is_low_stock and not p.is_out_of_stock]
    out_of_stock = [p for p in my_products if p.is_out_of_stock]

    most_sold = (db.session.query(
                    Product.name,
                    db.func.coalesce(db.func.sum(OrderItem.quantity), 0).label('sold_qty'))
                .join(OrderItem, OrderItem.product_id == Product.id)
                .filter(Product.seller_id == current_user.id)
                .group_by(Product.id, Product.name)
                .order_by(db.desc('sold_qty'))
                .limit(5)
                .all())

    return render_template('seller/dashboard.html',
                           total_products=total_products,
                           most_sold=most_sold,
                           low_stock=low_stock,
                           out_of_stock=out_of_stock)

@seller.route('/products')
@seller_required
def product_list():
    products = Product.query.filter_by(seller_id=current_user.id).all()
    return render_template('seller/product_list.html', products=products)

@seller.route('/product/add', methods=['GET', 'POST'])
@seller_required
def product_add():
    categories = Category.query.all()

    if request.method == 'POST':
        image_filename = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                upload_dir = os.path.join(current_app.static_folder, 'SISMS-uploads')
                os.makedirs(upload_dir, exist_ok=True)
                file.save(os.path.join(upload_dir, filename))
                image_filename = filename

        cat_id = request.form.get('category_id')
        p = Product(
            seller_id=current_user.id,
            name=request.form['name'],
            description=request.form.get('description'),
            category_id=int(cat_id) if cat_id else None,
            price=request.form['price'],
            stock_qty=request.form.get('stock_qty', 0, type=int),
            low_stock_threshold=request.form.get('low_stock_threshold', 5, type=int),
            image_filename=image_filename,
        )
        db.session.add(p)
        db.session.commit()
        flash('Product added', 'success')
        return redirect(url_for('seller.product_list'))

    return render_template('seller/product_form.html', action='Add', categories=categories)

@seller.route('/product/<int:pid>/edit', methods=['GET', 'POST'])
@seller_required
def product_edit(pid):
    product = Product.query.get_or_404(pid)
    if product.seller_id != current_user.id:
        abort(403)

    categories = Category.query.all()

    if request.method == 'POST':
        product.name = request.form['name']
        product.description = request.form.get('description')
        cat_id = request.form.get('category_id')
        product.category_id = int(cat_id) if cat_id else None
        product.price = request.form['price']
        product.stock_qty = request.form.get('stock_qty', 0, type=int)
        product.low_stock_threshold = request.form.get('low_stock_threshold', 5, type=int)

        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                upload_dir = os.path.join(current_app.static_folder, 'SISMS-uploads')
                os.makedirs(upload_dir, exist_ok=True)
                file.save(os.path.join(upload_dir, filename))
                product.image_filename = filename

        db.session.commit()
        flash('Product updated', 'success')
        return redirect(url_for('seller.product_list'))

    return render_template('seller/product_form.html', action='Edit', product=product, categories=categories)

@seller.route('/product/<int:pid>/delete', methods=['POST'])
@seller_required
def product_delete(pid):
    product = Product.query.get_or_404(pid)
    if product.seller_id != current_user.id:
        abort(403)
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted', 'success')
    return redirect(url_for('seller.product_list'))