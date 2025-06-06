from flask import Flask, render_template, abort, request, redirect, url_for, make_response, send_from_directory, jsonify
from werkzeug.utils import secure_filename
from functools import wraps
import re, os, json
from unicodedata import normalize
from models import db, Product, Brand, Tag, BlogPost, Category
from flask_mail import Mail, Message
from datetime import datetime

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///echoshop.db'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'temdy.starbound@gmail.com'
app.config['MAIL_PASSWORD'] = 'qskx ybyl pmbf rfgs'
app.config['MAIL_DEFAULT_SENDER'] = ('Forest Profi Technik', 'temdy.starbound@gmail.com')
app.config['SHOP_EMAIL'] = 'temdy.starbound@gmail.com'

mail = Mail(app)

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

db.init_app(app)
with app.app_context():
    db.create_all()

ADMIN_PASSWORD = "admin123"
ADMIN_COOKIE_NAME = 'admin_auth'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        admin_cookie = request.cookies.get(ADMIN_COOKIE_NAME)
        if not admin_cookie or admin_cookie != ADMIN_PASSWORD:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def model_to_dict(obj):
    if isinstance(obj, (Product, Brand, Tag, BlogPost)):
        d = {}
        for column in obj.__table__.columns:
            d[column.name] = getattr(obj, column.name)
        if isinstance(obj, Product):
            d['brand'] = model_to_dict(obj.brand)
            d['tags'] = [model_to_dict(tag) for tag in obj.tags]
            if obj.category_rel:
                d['category'] = obj.category_rel.name
                d['category_translated'] = obj.category_rel.translated_name
        return d
    return str(obj)

@app.route('/')
def home():
    return render_template('home.html', title='Domů', body_class='home-page')

@app.route('/bows')
def bows():
    products = Product.query.join(Product.category_rel).filter(Category.name == 'bow').all()
    return render_template('bows.html', title='Ruční stroje', products=products)

@app.route('/crossbows')
def crossbows():
    products = Product.query.join(Product.category_rel).filter(Category.name == 'crossbow').all()
    return render_template('crossbows.html', title='Velké stroje', products=products)

@app.route('/utilities')
def utilities():
    products = Product.query.join(Product.category_rel).filter(Category.name == 'utility').all()
    return render_template('utilities.html', title='Příslušenství', products=products)

@app.route('/akce')
def akce():
    posts = BlogPost.query.order_by(BlogPost.created_at.desc()).all()
    return render_template('akce.html', title='Akce', posts=posts)

@app.route('/akce/<slug>')
def akce_detail(slug):
    post = BlogPost.query.filter_by(slug=slug).first_or_404()
    return render_template('akce_detail.html', post=post, title=post.title)

# Keep the old routes for backward compatibility
@app.route('/blog')
def blog():
    return redirect(url_for('akce'))

@app.route('/cart')
def cart():
    return render_template('cart.html', title='Košík')

@app.route('/checkout', methods=['POST'])
def checkout():
    try:
        customer_name = request.form.get('customer_name')
        customer_email = request.form.get('customer_email')
        customer_phone = request.form.get('customer_phone', '')
        customer_message = request.form.get('customer_message', '')
        cart_items_json = request.form.get('cart_items', '{}')
        cart_total = request.form.get('cart_total', '0 Kč')
        
        cart_items = json.loads(cart_items_json)
        
        product_slugs = list(cart_items.keys())
        products = {}
        
        if product_slugs:
            products_query = Product.query.filter(Product.slug.in_(product_slugs)).all()
            for product in products_query:
                products[product.slug] = {
                    'name': product.name,
                    'price': float(product.price) if product.price else 0,
                    'quantity': cart_items.get(product.slug, 1)
                }

        products_html = ""
        for slug, product_data in products.items():
            products_html += f"""
            <tr>
                <td>{product_data['name']}</td>
                <td>{product_data['quantity']}</td>
                <td>{product_data['price']} Kč</td>
                <td>{product_data['price'] * product_data['quantity']} Kč</td>
            </tr>
            """

        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <h2>Nová objednávka z Czech Bow Hunting</h2>
            <p><strong>Od:</strong> {customer_name}</p>
            <p><strong>Email:</strong> {customer_email}</p>
            <p><strong>Telefon:</strong> {customer_phone}</p>
            <p><strong>Datum:</strong> {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
            
            <h3>Položky objednávky:</h3>
            <table>
                <tr>
                    <th>Produkt</th>
                    <th>Množství</th>
                    <th>Cena za kus</th>
                    <th>Celkem</th>
                </tr>
                {products_html}
            </table>
            
            <h3>Celková cena: {cart_total}</h3>
            
            <h3>Zpráva od zákazníka:</h3>
            <p>{customer_message or 'Žádná zpráva'}</p>
        </body>
        </html>
        """

        subject = f"Nová objednávka - Czech Bow Hunting - {customer_name}"
        msg = Message(
            subject=subject,
            recipients=[app.config['SHOP_EMAIL']],
            html=html_content,
            reply_to=customer_email
        )
        
        mail.send(msg)
        
        return jsonify({"success": True})
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/admin')
def admin_login():
    admin_cookie = request.cookies.get(ADMIN_COOKIE_NAME)
    if admin_cookie and admin_cookie == ADMIN_PASSWORD:
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/login.html')

@app.route('/admin/login', methods=['POST'])
def admin_login_post():
    password = request.form.get('password')
    if password == ADMIN_PASSWORD:
        response = make_response(redirect(url_for('admin_dashboard')))
        response.set_cookie(ADMIN_COOKIE_NAME, ADMIN_PASSWORD)
        return response
    return redirect(url_for('admin_login'))

@app.route('/admin/logout')
def admin_logout():
    response = make_response(redirect(url_for('admin_login')))
    response.delete_cookie(ADMIN_COOKIE_NAME)
    return response

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    products = Product.query.all()
    posts = BlogPost.query.all()
    tags = Tag.query.all()
    brands = Brand.query.all()
    return render_template('admin/dashboard.html', 
                           title='Dashboard',
                           products=products,
                           posts=posts,
                           tags=tags,
                           brands=brands)

@app.route('/admin/catalog')
@admin_required
def admin_catalog():
    categories = Category.query.all()
    categories_data = [{
        'id': c.id,
        'name': c.name,
        'subcategories': c.subcategories,
        'brands': c.brands
    } for c in categories]
    return render_template('admin/catalog.html', categories=categories_data)

@app.route('/admin/akce')
@admin_required
def admin_akce():
    posts = BlogPost.query.order_by(BlogPost.created_at.desc()).all()
    posts_dict = {post.slug:{
        'id': post.id,
        'title': post.title,
        'content': post.content,
        'date': post.expiration_date.strftime('%d. %B %Y') if post.expiration_date else 'neurčito'
    } for post in posts}
    return render_template('admin/akce.html', blog_posts=posts_dict)
    
# Keep old route for backward compatibility
@app.route('/admin/blog')
@admin_required
def admin_blog():
    return redirect(url_for('admin_akce'))

@app.route('/admin/tags')
@admin_required
def admin_tags():
    tags = Tag.query.all()
    brands = Brand.query.all()
    
    tags_data = [{
        'name': tag.name,
        'count': len(tag.products)
    } for tag in tags]
    
    brands_data = [{
        'name': brand.name,
        'count': len(brand.products)
    } for brand in brands]
    
    return render_template('admin/tags.html', 
                           tags=tags_data,
                           brands=brands_data)

@app.route('/admin/products')
@admin_required
def admin_products():
    products = Product.query.all()
    tags = Tag.query.all()
    brands = Brand.query.all()
    
    products_json = [model_to_dict(p) for p in products]
    return render_template('admin/products.html', 
                           products=products_json,
                           tags=tags,
                           brands=brands,
                           Category=Category)

@app.route('/admin/api/product/save', methods=['POST'])
@admin_required
def admin_save_product():
    data = request.form
    image = request.files.get('image')
    
    image_filename = None
    if image and allowed_file(image.filename):
        filename = secure_filename(image.filename)
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        image_filename = filename

    brand = Brand.query.filter_by(name=data['brand']).first()
    if not brand:
        brand = Brand(name=data['brand'])
        db.session.add(brand)
    
    tags = []
    tag_names = request.form.getlist('tags')
    for tag_name in tag_names:
        tag = Tag.query.filter_by(name=tag_name).first()
        if not tag:
            tag = Tag(name=tag_name)
            db.session.add(tag)
        tags.append(tag)

    category = None
    if data.get('category_id'):
        category = Category.query.get(data['category_id'])
    else:
        category = Category.query.filter_by(name=data['category']).first()

    if not category:
        return {'success': False, 'error': 'Invalid category'}, 400

    if data.get('id'):
        product = Product.query.get_or_404(data['id'])
        product.name = data['name']
        product.description = data['description']
        product.category_rel = category
        product.subcategory = data.get('subcategory')
        product.price = float(data['price']) if data.get('price') else None
        if image_filename:
            product.image = image_filename
        product.brand = brand
        product.tags = tags
    else:
        base_slug = slugify(data['name'])
        slug = base_slug
        counter = 1
        while Product.query.filter_by(slug=slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1

        product = Product(
            slug=slug,
            name=data['name'],
            description=data['description'],
            category_rel=category,
            subcategory=data.get('subcategory'),
            price=float(data['price']) if data.get('price') else None,
            image=image_filename or 'placeholder.jpeg',
            brand=brand,
            tags=tags
        )
        db.session.add(product)

    try:
        db.session.commit()
        return {'success': True, 'id': product.id}
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'error': str(e)}, 500

@app.route('/admin/api/product/delete', methods=['POST'])
@admin_required
def admin_delete_product():
    product_id = request.json.get('id')
    product = Product.query.get_or_404(product_id)
    
    if product.image != 'placeholder.jpeg':
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], product.image))
        except OSError:
            pass
    
    db.session.delete(product)
    db.session.commit()
    return {'success': True}

@app.route('/admin/api/blog/save', methods=['POST'])
@admin_required
def admin_save_blog():
    data = request.json
    title = data.get('title')
    content = data.get('content')
    expiration_date_str = data.get('expiration_date')
    
    if not title:
        return {'success': False, 'error': 'Missing title'}, 400
    
    # Parse expiration date if provided
    expiration_date = None
    if expiration_date_str:
        try:
            expiration_date = datetime.strptime(expiration_date_str, '%Y-%m-%d')
        except ValueError:
            return {'success': False, 'error': 'Invalid date format'}, 400
    
    if data.get('id'):
        post = BlogPost.query.get_or_404(data['id'])
        post.title = title
        post.content = content
        post.expiration_date = expiration_date
    else:
        slug = slugify(title)
        base_slug = slug
        counter = 1
        while BlogPost.query.filter_by(slug=slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1
            
        post = BlogPost(
            slug=slug,
            title=title,
            content=content,
            expiration_date=expiration_date
        )
        db.session.add(post)

    db.session.commit()
    return {'success': True, 'id': post.id}

@app.route('/admin/api/blog/delete', methods=['POST'])
@admin_required
def admin_delete_blog():
    post_id = request.json.get('id')
    post = BlogPost.query.get_or_404(post_id)
    
    for block in post.content:
        if block.get('type') == 'image' and block.get('data', {}).get('filename'):
            try:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], block['data']['filename']))
            except OSError:
                pass
        elif block.get('type') == 'gallery':
            for image in block.get('data', {}).get('images', []):
                if image.get('filename'):
                    try:
                        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], image['filename']))
                    except OSError:
                        pass
    
    db.session.delete(post)
    db.session.commit()
    return {'success': True}

@app.route('/admin/api/tags/update', methods=['POST'])
@admin_required
def admin_update_tags():
    data = request.json
    
    if 'tags' in data:
        existing_tags = Tag.query.all()
        existing_names = {tag.name for tag in existing_tags}
        
        for name in data['tags']:
            if name not in existing_names:
                db.session.add(Tag(name=name))
        
        for tag in existing_tags:
            if tag.name not in data['tags']:
                db.session.delete(tag)
    
    if 'brands' in data:
        existing_brands = Brand.query.all()
        existing_names = {brand.name for brand in existing_brands}
        
        for name in data['brands']:
            if name not in existing_names:
                db.session.add(Brand(name=name))
        
        for brand in existing_brands:
            if brand.name not in data['brands']:
                db.session.delete(brand)
    
    db.session.commit()
    return {'success': True}

@app.route('/admin/api/catalog/add', methods=['POST'])
@admin_required
def admin_add_category():
    data = request.json
    name = data.get('name')
    
    if not name:
        abort(400)
    
    category = Category(name=name)
    db.session.add(category)
    db.session.commit()
    
    return {'success': True, 'id': category.id}

@app.route('/admin/api/catalog/update', methods=['POST'])
@admin_required
def admin_update_category():
    data = request.json
    category_id = data.get('id')
    category = Category.query.get_or_404(category_id)
    
    if 'name' in data:
        category.name = data['name']
    if 'subcategories' in data:
        category.subcategories = data['subcategories']
    if 'brands' in data:
        category.brands = data['brands']
    
    db.session.commit()
    return {'success': True}

@app.route('/admin/api/catalog/delete', methods=['POST'])
@admin_required
def admin_delete_category():
    data = request.json
    category_id = data.get('id')
    category = Category.query.get_or_404(category_id)
    
    for product in category.products:
        product.category = None
        product.subcategory = None
    
    db.session.delete(category)
    db.session.commit()
    return {'success': True}

@app.route('/api/blog/get/<slug>')
def get_blog_post(slug):
    try:
        post = BlogPost.query.filter_by(slug=slug).first()
        if not post:
            return jsonify({'success': False, 'error': 'Post not found'}), 404
          # Format expiration_date for frontend if it exists
        expiration_date = None
        if post.expiration_date:
            expiration_date = post.expiration_date.strftime('%Y-%m-%d')
            
        return jsonify({
            'success': True,
            'post': {
                'id': post.id,
                'title': post.title,
                'content': post.content,
                'expiration_date': expiration_date
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/products/details', methods=['POST'])
def get_product_details():
    try:
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400
            
        data = request.get_json()
        
        if not data or 'slugs' not in data:
            return jsonify({'error': 'No slugs provided'}), 400
            
        slugs = data['slugs']
        if not isinstance(slugs, list):
            return jsonify({'error': 'Slugs must be an array'}), 400
            
        products = {}
        for slug in slugs:
            product = Product.query.filter_by(slug=slug).first()
            if product:
                products[slug] = {
                    'id': product.id,
                    'name': product.name,
                    'description': product.description,
                    'price': float(product.price) if product.price else 0,
                    'image': product.image,
                    'brand': {'name': product.brand.name} if product.brand else None
                }
        
        return jsonify(products)
    except Exception as e:
        return jsonify({'error': 'Server error'}), 500

@app.route('/admin/api/upload', methods=['POST'])
@admin_required
def upload_file():
    if 'image' not in request.files:
        return {'error': 'No file provided'}, 400
        
    file = request.files['image']
    if file.filename == '':
        return {'error': 'No file selected'}, 400
        
    if not allowed_file(file.filename):
        return {'error': 'Invalid file type'}, 400

    filename = secure_filename(file.filename)
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return {'url': url_for('uploaded_file', filename=filename)}

def slugify(text):
    text = str(text)
    text = text.lower()
    text = normalize('NFD', text).encode('ascii', 'ignore').decode('utf-8')
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    text = text.strip('-')
    return text if text else 'product'

if __name__ == '__main__':
    app.run(debug=True, port=5001)