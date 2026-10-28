import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
DB_PORT = int(os.getenv('DB_PORT', 3306))
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'expense_tracker')
DB_SSL = os.getenv('DB_SSL', 'false').lower() in ('true', '1')

def get_db_connection(use_database=True):
    """
    Establishes a connection to the MySQL database.
    Compatible with MySQL 5.0 through 8.x+, MariaDB, and Cloud MySQL.
    """
    kwargs = {
        'host': DB_HOST,
        'port': DB_PORT,
        'user': DB_USER,
        'password': DB_PASSWORD,
        'charset': 'utf8',
        'use_pure': True,
        'autocommit': True
    }
    if DB_SSL:
        kwargs['ssl_disabled'] = False
    if use_database:
        kwargs['database'] = DB_NAME
    return mysql.connector.connect(**kwargs)

def init_db():
    """
    Creates database if permissions allow, then initializes tables and default categories.
    """
    try:
        # Step 1: Attempt to create database if not exists (local MySQL)
        try:
            conn = get_db_connection(use_database=False)
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8 COLLATE utf8_general_ci")
            cursor.close()
            conn.close()
        except Exception:
            # On managed cloud databases (e.g. Aiven, Clever Cloud), database is pre-created
            pass


        # Step 2: Create tables and default records
        conn = get_db_connection(use_database=True)
        cursor = conn.cursor()

        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                full_name VARCHAR(100) NOT NULL,
                email VARCHAR(150) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                currency VARCHAR(10) DEFAULT 'INR',
                theme VARCHAR(10) DEFAULT 'light',
                created_at DATETIME NOT NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8;
        """)

        # Categories table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(50) NOT NULL UNIQUE,
                icon VARCHAR(50) NOT NULL,
                color VARCHAR(20) NOT NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8;
        """)

        # Expenses table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                title VARCHAR(150) NOT NULL,
                amount DECIMAL(12, 2) NOT NULL,
                category_id INT NOT NULL,
                expense_date DATE NOT NULL,
                notes TEXT,
                created_at DATETIME NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE RESTRICT,
                INDEX idx_user_date (user_id, expense_date),
                INDEX idx_user_category (user_id, category_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8;
        """)

        # Budgets table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                month INT NOT NULL,
                year INT NOT NULL,
                budget_amount DECIMAL(12, 2) NOT NULL,
                created_at DATETIME NOT NULL,
                UNIQUE KEY unique_user_month_year (user_id, month, year),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8;
        """)

        # Password Resets table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS password_resets (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                token VARCHAR(255) NOT NULL,
                expires_at DATETIME NOT NULL,
                created_at DATETIME NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_token (token)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8;
        """)

        # Seed categories if empty
        cursor.execute("SELECT COUNT(*) FROM categories")
        count = cursor.fetchone()[0]
        if count == 0:
            default_categories = [
                (1, 'Food & Dining', 'fa-utensils', '#f97316'),
                (2, 'Transportation', 'fa-car', '#0ea5e9'),
                (3, 'Utilities & Bills', 'fa-bolt', '#eab308'),
                (4, 'Entertainment', 'fa-film', '#8b5cf6'),
                (5, 'Healthcare', 'fa-heart-pulse', '#ef4444'),
                (6, 'Shopping', 'fa-bag-shopping', '#ec4899'),
                (7, 'Miscellaneous', 'fa-tags', '#64748b')
            ]
            cursor.executemany("""
                INSERT INTO categories (id, name, icon, color)
                VALUES (%s, %s, %s, %s)
            """, default_categories)
            conn.commit()

        cursor.close()
        conn.close()
        print("[DB] Database and tables successfully initialized.")
        return True
    except Error as e:
        print(f"[DB Error] Error initializing database: {e}")
        return False

if __name__ == '__main__':
    init_db()
