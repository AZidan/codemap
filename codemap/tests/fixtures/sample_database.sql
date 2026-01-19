-- Sample SQL file demonstrating various SQL constructs
-- for CodeMap SQL parser testing

-- Users table with various column types
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- Orders table with foreign key
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Simple view
CREATE VIEW active_users AS
SELECT id, username, email, created_at
FROM users
WHERE is_active = true;

-- Materialized view for reporting
CREATE MATERIALIZED VIEW user_order_summary AS
SELECT
    u.id AS user_id,
    u.username,
    COUNT(o.id) AS order_count,
    COALESCE(SUM(o.total_amount), 0) AS total_spent
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
GROUP BY u.id, u.username;

-- Index for email lookups
CREATE INDEX idx_users_email ON users(email);

-- Composite index
CREATE INDEX idx_orders_user_status ON orders(user_id, status);

-- Function to get user by email
CREATE FUNCTION get_user_by_email(user_email VARCHAR) RETURNS users AS $$
SELECT * FROM users WHERE email = user_email LIMIT 1;
$$ LANGUAGE SQL;

-- Function with multiple parameters
CREATE FUNCTION calculate_discount(amount DECIMAL, discount_rate DECIMAL) RETURNS DECIMAL AS $$
BEGIN
    RETURN amount * (1 - discount_rate);
END;
$$ LANGUAGE plpgsql;

-- Trigger function
CREATE FUNCTION update_timestamp() RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for automatic timestamp update
CREATE TRIGGER users_update_timestamp
BEFORE UPDATE ON users
FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- Enum type for order status
CREATE TYPE order_status AS ENUM ('pending', 'processing', 'shipped', 'delivered', 'cancelled');

-- Sequence for custom IDs
CREATE SEQUENCE invoice_number_seq START WITH 1000 INCREMENT BY 1;

-- Schema for analytics
CREATE SCHEMA analytics;

-- Database creation (usually in separate script)
CREATE DATABASE ecommerce_db;
