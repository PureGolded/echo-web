from app import app
from models import db, BlogPost
from sqlalchemy import text

def add_expiration_date_column():
    """Add expiration_date column to BlogPost model"""
    with app.app_context():
        # Check if the column already exists
        inspector = db.inspect(db.engine)
        columns = [column['name'] for column in inspector.get_columns('blog_post')]
        if 'expiration_date' not in columns:
            print("Adding expiration_date column to BlogPost model...")
            # SQLite doesn't support ALTER TABLE ADD COLUMN with constraints,
            # so we need to use simple syntax without constraints
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE blog_post ADD COLUMN expiration_date TIMESTAMP'))
                conn.commit()
            print("Column added successfully!")
        else:
            print("expiration_date column already exists.")

if __name__ == "__main__":
    add_expiration_date_column()
