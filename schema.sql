-- ====================================================================
-- Personal Expense Tracker - Database Schema
-- Academic Software Engineering & Financial Analytics System
-- Target Database: MySQL (5.0+ / 8.0+ / MariaDB)
-- ====================================================================

CREATE DATABASE IF NOT EXISTS expense_tracker CHARACTER SET utf8 COLLATE utf8_general_ci;
USE expense_tracker;

-- --------------------------------------------------------------------
-- 1. Users Table
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    currency VARCHAR(10) DEFAULT 'INR',
    theme VARCHAR(10) DEFAULT 'light',
    created_at DATETIME NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------------------
-- 2. Categories Table
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    icon VARCHAR(50) NOT NULL,
    color VARCHAR(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------------------
-- 3. Expenses Table
-- --------------------------------------------------------------------
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

-- --------------------------------------------------------------------
-- 4. Budgets Table
-- --------------------------------------------------------------------
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

-- --------------------------------------------------------------------
-- 5. Password Resets Table
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS password_resets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    token VARCHAR(255) NOT NULL,
    expires_at DATETIME NOT NULL,
    created_at DATETIME NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_token (token)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------------------
-- 6. Seed Default Categories
-- --------------------------------------------------------------------
INSERT INTO categories (id, name, icon, color) VALUES
(1, 'Food & Dining', 'fa-utensils', '#f97316'),
(2, 'Transportation', 'fa-car', '#0ea5e9'),
(3, 'Utilities & Bills', 'fa-bolt', '#eab308'),
(4, 'Entertainment', 'fa-film', '#8b5cf6'),
(5, 'Healthcare', 'fa-heart-pulse', '#ef4444'),
(6, 'Shopping', 'fa-bag-shopping', '#ec4899'),
(7, 'Miscellaneous', 'fa-tags', '#64748b')
ON DUPLICATE KEY UPDATE name=VALUES(name), icon=VALUES(icon), color=VALUES(color);
