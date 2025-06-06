# EchoShop - Flask E-commerce Web Application

A Flask-based e-commerce website for selling hunting equipment including bows, crossbows, and accessories.

## Features

- Product catalog with categories (Ruční stroje, Velké stroje, Příslušenství)
- Shopping cart functionality
- Blog/promotions system with expiration dates
- Admin panel for managing products, categories, and blog posts
- Email notifications for orders
- Image upload support

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Initialize the database:
```bash
python initialize_categories.py
```

3. Run the application:
```bash
python app.py
```

The application will be available at `http://localhost:5001`

## Admin Access

Navigate to `/admin` and use the configured admin password to access the management interface.

## Project Structure

- `app.py` - Main Flask application
- `models.py` - Database models
- `templates/` - HTML templates
- `static/` - CSS, JS, and image files
- `uploads/` - User uploaded images
- `instance/` - SQLite database