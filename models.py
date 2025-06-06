from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

product_tags = db.Table('product_tags',
    db.Column('product_id', db.Integer, db.ForeignKey('product.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    subcategories_json = db.Column(db.Text, nullable=False, default='[]')
    brands_json = db.Column(db.Text, nullable=False, default='[]')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    TRANSLATIONS = {
        'bow': 'Ruční stroje',
        'crossbow': 'Velké stroje',
        'utility': 'Příslušenství'
    }
    
    @property
    def translated_name(self):
        return self.TRANSLATIONS.get(self.name, self.name.capitalize())
    
    @property
    def subcategories(self):
        try:
            return json.loads(self.subcategories_json)
        except:
            return []
    
    @subcategories.setter
    def subcategories(self, value):
        self.subcategories_json = json.dumps(value)
    
    @property
    def brands(self):
        try:
            return json.loads(self.brands_json)
        except:
            return []
    
    @brands.setter
    def brands(self, value):
        self.brands_json = json.dumps(value)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(20))  # Keep for migration
    price = db.Column(db.Float)
    image = db.Column(db.String(255), nullable=False, default='placeholder.jpeg')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    brand_id = db.Column(db.Integer, db.ForeignKey('brand.id'), nullable=False)
    brand = db.relationship('Brand', backref=db.backref('products', lazy=True))
    
    tags = db.relationship('Tag', secondary=product_tags, lazy='subquery',
                          backref=db.backref('products', lazy=True))
                          
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    category_rel = db.relationship('Category', backref=db.backref('products', lazy=True))
    subcategory = db.Column(db.String(100))

class Brand(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content_json = db.Column(db.Text, nullable=False, default='[]')  # JSON string of content blocks
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    expiration_date = db.Column(db.DateTime, nullable=True)  # Date when the promotion expires
    
    @property
    def content(self):
        try:
            return json.loads(self.content_json)
        except:
            return []
    
    @content.setter
    def content(self, value):
        self.content_json = json.dumps(value)
        
    def get_first_image(self):
        """Returns the filename of the first image in the blog post, or None if there is no image"""
        blocks = self.content
        for block in blocks:
            if block.get('type') == 'image':
                return block.get('data', {}).get('filename')
            elif block.get('type') == 'gallery' and block.get('data', {}).get('images'):
                images = block.get('data', {}).get('images')
                if images and len(images) > 0:
                    return images[0].get('filename')
        return None