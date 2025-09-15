-- Create database if it doesn't exist
CREATE DATABASE IF NOT EXISTS ravi_db;

-- Use the database
USE ravi_db;

-- Create table if it doesn't exist
CREATE TABLE IF NOT EXISTS eren (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Check if table exists
SHOW TABLES;

-- Check table structure
DESCRIBE eren;
