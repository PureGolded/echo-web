from app import app
from models import db, Category

def initialize_categories():
    """Ensures that the required categories exist in the database"""
    with app.app_context():
        # Check if categories exist, create them if they don't
        # We'll keep the old category names in the database for compatibility but update translations
        required_categories = ['bow', 'crossbow', 'utility']
        
        for category_name in required_categories:
            category = Category.query.filter_by(name=category_name).first()
            if not category:
                print(f"Creating category: {category_name}")
                category = Category(name=category_name)
                db.session.add(category)
        
        db.session.commit()
        print("Categories initialized successfully!")
        
        # Print all categories
        all_categories = Category.query.all()
        print("All categories:", [c.name for c in all_categories])

if __name__ == "__main__":
    initialize_categories()