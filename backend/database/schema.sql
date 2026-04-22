-- ============================================
-- CardOptimizer Database Schema
-- ============================================
-- PostgreSQL Database Schema for Credit Card Rewards Optimization Platform
-- Created: 2025
-- Components 7: Database Design
-- ============================================

-- ============================================
-- Table 1: Users
-- Stores user account information
-- ============================================

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- ============================================
-- Table 2: Credit Cards
-- Master list of all credit cards in the database
-- ============================================

CREATE TABLE credit_cards (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    issuer VARCHAR(100) NOT NULL,
    annual_fee INTEGER NOT NULL,
    point_value NUMERIC(5,4) NOT NULL,
    rewards JSONB NOT NULL,
    benefits JSONB,
    signup_bonus JSONB
);

-- ============================================
-- Table 3: User Cards
-- Links users to the credit cards they own
-- Junction table for many-to-many relationship
-- ============================================

CREATE TABLE user_cards (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    card_id VARCHAR(50) NOT NULL REFERENCES credit_cards(id) ON DELETE CASCADE,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_custom BOOLEAN DEFAULT FALSE,
    last_four VARCHAR(4),
    nickname VARCHAR(100)
);

-- ============================================
-- Table 4: Transactions
-- Stores user purchase/spending history
-- ============================================

CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    card_id VARCHAR(50),
    amount NUMERIC(10,2) NOT NULL,
    category VARCHAR(50) NOT NULL,
    merchant_name VARCHAR(255),
    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    plaid_transaction_id VARCHAR(255),
    notes TEXT
);

-- ============================================
-- Table 5: Spending Patterns
-- Stores monthly spending by category for each user
-- Using JSONB approach for flexibility
-- ============================================

CREATE TABLE spending_patterns (
    user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    spending JSONB NOT NULL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- Table 6: Benefit Usage
-- Tracks usage of credit card benefits
-- ============================================

CREATE TABLE benefit_usage (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    card_id VARCHAR(50) NOT NULL REFERENCES credit_cards(id) ON DELETE CASCADE,
    benefit_name VARCHAR(255) NOT NULL,
    benefit_value NUMERIC(10,2) NOT NULL,
    used_amount NUMERIC(10,2) DEFAULT 0,
    reset_date DATE,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- Indexes for Performance
-- Create indexes on frequently queried columns
-- ============================================

-- Index on user emails for fast login lookups
CREATE INDEX idx_users_email ON users(email);

-- Index on user_cards for fast card lookups by user
CREATE INDEX idx_user_cards_user_id ON user_cards(user_id);
CREATE INDEX idx_user_cards_card_id ON user_cards(card_id);

-- Index on transactions for fast queries by user and date
CREATE INDEX idx_transactions_user_id ON transactions(user_id);
CREATE INDEX idx_transactions_date ON transactions(transaction_date);
CREATE INDEX idx_transactions_category ON transactions(category);

-- Index on benefit_usage for fast lookups
CREATE INDEX idx_benefit_usage_user_id ON benefit_usage(user_id);
CREATE INDEX idx_benefit_usage_card_id ON benefit_usage(card_id);

-- ============================================
-- Comments for Documentation
-- ============================================

COMMENT ON TABLE users IS 'Stores user account information and authentication data';
COMMENT ON TABLE credit_cards IS 'Master list of all available credit cards with their reward structures';
COMMENT ON TABLE user_cards IS 'Junction table linking users to their credit cards';
COMMENT ON TABLE transactions IS 'Stores all user transactions and purchases';
COMMENT ON TABLE spending_patterns IS 'Stores monthly spending patterns by category for each user';
COMMENT ON TABLE benefit_usage IS 'Tracks benefit usage and remaining value for each user card';

-- ============================================
-- Sample Data Insertion (Optional - for testing)
-- ============================================

-- Insert sample credit cards
INSERT INTO credit_cards (id, name, issuer, annual_fee, point_value, rewards, benefits, signup_bonus) VALUES
('csp', 'Chase Sapphire Preferred', 'Chase', 95, 0.0125, 
 '{"dining": 3, "travel": 5, "default": 1}'::jsonb,
 '["$50 annual hotel credit", "No foreign transaction fees", "Travel and purchase protection"]'::jsonb,
 '{"points": 60000, "spend_requirement": 4000, "time_limit_months": 3}'::jsonb),

('amex-gold', 'American Express Gold', 'American Express', 250, 0.01,
 '{"dining": 4, "groceries": 4, "default": 1}'::jsonb,
 '["$120 Uber Cash annually", "$120 dining credit annually", "No foreign transaction fees"]'::jsonb,
 '{"points": 60000, "spend_requirement": 4000, "time_limit_months": 6}'::jsonb),

('chase-freedom-unlimited', 'Chase Freedom Unlimited', 'Chase', 0, 0.01,
 '{"default": 1.5}'::jsonb,
 '["No annual fee", "0% intro APR for 15 months"]'::jsonb,
 '{"points": 20000, "spend_requirement": 500, "time_limit_months": 3}'::jsonb),

('cap1-venture', 'Capital One Venture', 'Capital One', 95, 0.01,
 '{"default": 2}'::jsonb,
 '["No foreign transaction fees", "TSA PreCheck/Global Entry credit"]'::jsonb,
 '{"points": 75000, "spend_requirement": 4000, "time_limit_months": 3}'::jsonb),

('amex-platinum', 'American Express Platinum', 'American Express', 695, 0.01,
 '{"flights": 5, "hotels": 5, "default": 1}'::jsonb,
 '["$200 airline fee credit", "$200 hotel credit", "$189 CLEAR credit", "$155 Walmart+ credit", "Airport lounge access", "No foreign transaction fees"]'::jsonb,
 '{"points": 80000, "spend_requirement": 6000, "time_limit_months": 6}'::jsonb);

-- ============================================
-- End of Schema
-- ============================================