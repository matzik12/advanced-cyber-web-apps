import sqlite3
import hashlib
import os

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), 'flowers.db')

def init_database():
    """Initialize the database with tables and seed data"""
    
    # Remove existing database
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    
    # Create connection
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT,
            role TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create products table
    cursor.execute('''
        CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            image_url TEXT,
            stock INTEGER DEFAULT 100,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create orders table
    cursor.execute('''
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_id INTEGER,
            quantity INTEGER DEFAULT 1,
            total_price REAL,
            credit_card TEXT,
            cvv TEXT,
            order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    ''')
    
    # Create sessions table
    cursor.execute('''
        CREATE TABLE sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            token TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Create AI conversations table
    cursor.execute('''
        CREATE TABLE ai_conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_message TEXT NOT NULL,
            ai_response TEXT NOT NULL,
            user_ip TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create comments table (VULNERABILITY: XSS - comments not sanitized)
    cursor.execute('''
        CREATE TABLE comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            author_name TEXT NOT NULL,
            comment_text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    ''')
    
    # VULNERABILITY: Store passwords in plain text (bad practice for demonstration)
    # Insert default users
    users = [
        ('user', 'user123', 'user@flowers.com', 'user'),
        ('admin', 'admin123', 'admin@flowers.com', 'admin'),
        ('guest', 'guest123', 'guest@flowers.com', 'user'),
        # SECRET ADMIN ACCOUNT (for discovery)
        ('superadmin', 'SuperSecret2024!', 'super@flowers.com', 'superadmin')
    ]
    
    cursor.executemany(
        'INSERT INTO users (username, password, email, role) VALUES (?, ?, ?, ?)',
        users
    )
    
    # Insert products
    products = [
        ('Rose Elegance', 'Stunning red roses perfect for any romantic occasion', 49.99, '/images/roses.jpg', 50),
        ('Tulip Dreams', 'Colorful tulips bringing spring joy to your home', 39.99, '/images/tulips.jpg', 75),
        ('Orchid Paradise', 'Exotic orchids for the sophisticated flower lover', 69.99, '/images/orchids.jpg', 30),
        ('Sunflower Joy', 'Bright sunflowers to light up any room', 34.99, '/images/sunflowers.jpg', 100),
        ('Lily Garden', 'Graceful lilies with an enchanting fragrance', 44.99, '/images/lilies.jpg', 60),
        ('Peony Bliss', 'Lush peonies perfect for special celebrations', 59.99, '/images/peonies.jpg', 40),
        ('Daisies Delight', 'Cheerful daisies symbolizing innocence and purity', 32.99, '/images/daisies.jpg', 80),
        ('Mixed Bouquet', 'Beautiful mix of seasonal flowers', 49.99, '/images/mixed.jpg', 40)
    ]
    
    cursor.executemany(
        'INSERT INTO products (name, description, price, image_url, stock) VALUES (?, ?, ?, ?, ?)',
        products
    )
    
    conn.commit()
    conn.close()
    
    print(f"✅ Database initialized successfully at {DB_PATH}")
    print(f"📊 Created {len(users)} users and {len(products)} products")
    print("\n🔐 Default accounts:")
    for username, password, _, role in users:
        print(f"   {role.upper()}: {username} / {password}")

if __name__ == '__main__':
    init_database()
