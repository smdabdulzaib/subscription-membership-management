-- ==========================================================
-- Subscription & Membership Management System Database Schema
-- Database: subscription_management
-- Compatible with MySQL 8.0+
-- ==========================================================

CREATE DATABASE IF NOT EXISTS subscription_management
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE subscription_management;

-- ----------------------------------------------------------
-- 1. Customers Table
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS customers (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    phone VARCHAR(20) NOT NULL,
    registration_date DATE NOT NULL,
    account_status ENUM('Active', 'Inactive', 'Suspended') DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_customer_email (email),
    INDEX idx_customer_status (account_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------
-- 2. Plans Table
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS plans (
    plan_id INT AUTO_INCREMENT PRIMARY KEY,
    plan_name VARCHAR(100) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    duration_days INT NOT NULL,
    features TEXT,
    status ENUM('Active', 'Inactive') DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_plan_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------
-- 3. Subscriptions Table
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS subscriptions (
    subscription_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    plan_id INT NOT NULL,
    start_date DATE NOT NULL,
    expiry_date DATE NOT NULL,
    status ENUM('Active', 'Expiring Soon', 'Expired', 'Cancelled') DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_subs_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_subs_plan FOREIGN KEY (plan_id) REFERENCES plans(plan_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    INDEX idx_subs_customer (customer_id),
    INDEX idx_subs_plan (plan_id),
    INDEX idx_subs_status (status),
    INDEX idx_subs_expiry (expiry_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------
-- 4. Payments Table
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS payments (
    payment_id INT AUTO_INCREMENT PRIMARY KEY,
    subscription_id INT NOT NULL,
    customer_id INT NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    payment_date DATETIME NOT NULL,
    payment_method ENUM('Cash', 'UPI', 'Credit Card', 'Debit Card', 'Net Banking') NOT NULL,
    transaction_id VARCHAR(100) NOT NULL UNIQUE,
    payment_status ENUM('Success', 'Pending', 'Failed', 'Refunded') DEFAULT 'Success',
    CONSTRAINT fk_pay_sub FOREIGN KEY (subscription_id) REFERENCES subscriptions(subscription_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_pay_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_pay_sub (subscription_id),
    INDEX idx_pay_cust (customer_id),
    INDEX idx_pay_status (payment_status),
    INDEX idx_pay_date (payment_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------
-- 5. Invoices Table
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS invoices (
    invoice_id INT AUTO_INCREMENT PRIMARY KEY,
    invoice_number VARCHAR(50) NOT NULL UNIQUE,
    payment_id INT NOT NULL,
    customer_id INT NOT NULL,
    subscription_id INT NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    invoice_date DATETIME NOT NULL,
    pdf_path VARCHAR(255),
    CONSTRAINT fk_inv_pay FOREIGN KEY (payment_id) REFERENCES payments(payment_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_inv_cust FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_inv_sub FOREIGN KEY (subscription_id) REFERENCES subscriptions(subscription_id) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_inv_num (invoice_number),
    INDEX idx_inv_cust (customer_id),
    INDEX idx_inv_date (invoice_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------
-- 6. Subscription History Table (Audit Trail)
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS subscription_history (
    history_id INT AUTO_INCREMENT PRIMARY KEY,
    subscription_id INT NOT NULL,
    customer_id INT NOT NULL,
    old_plan_id INT NULL,
    new_plan_id INT NULL,
    action_type ENUM('ACTIVATED', 'UPGRADED', 'DOWNGRADED', 'RENEWED', 'CANCELLED') NOT NULL,
    old_expiry_date DATE NULL,
    new_expiry_date DATE NULL,
    amount DECIMAL(10, 2) DEFAULT 0.00,
    action_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    remarks TEXT,
    CONSTRAINT fk_hist_sub FOREIGN KEY (subscription_id) REFERENCES subscriptions(subscription_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_hist_cust FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_hist_old_plan FOREIGN KEY (old_plan_id) REFERENCES plans(plan_id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_hist_new_plan FOREIGN KEY (new_plan_id) REFERENCES plans(plan_id) ON DELETE SET NULL ON UPDATE CASCADE,
    INDEX idx_hist_sub (subscription_id),
    INDEX idx_hist_cust (customer_id),
    INDEX idx_hist_action (action_type),
    INDEX idx_hist_date (action_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------
-- 7. Notifications Table
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS notifications (
    notification_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    subscription_id INT NOT NULL,
    notification_type VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    notification_status ENUM('Pending', 'Sent', 'Failed') DEFAULT 'Sent',
    CONSTRAINT fk_notif_cust FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_notif_sub FOREIGN KEY (subscription_id) REFERENCES subscriptions(subscription_id) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_notif_cust (customer_id),
    INDEX idx_notif_sub (subscription_id),
    INDEX idx_notif_status (notification_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ==========================================================
-- SEED SAMPLE DATA (Optional / Initial Demonstration)
-- ==========================================================

-- 1. Insert Sample Plans
INSERT INTO plans (plan_id, plan_name, price, duration_days, features, status) VALUES
(1, 'Basic', 499.00, 30, 'SD Streaming, Single Device Access, Standard Email Support, 1080p Web', 'Active'),
(2, 'Standard', 999.00, 90, 'Full HD Streaming, 2 Simultaneous Screens, Priority Email Support, Offline Downloads', 'Active'),
(3, 'Premium', 1999.00, 180, '4K Ultra HD + HDR, 4 Simultaneous Devices, 24/7 Priority Support, Unlimited Access', 'Active'),
(4, 'Enterprise', 3499.00, 365, 'VIP All-Inclusive, Unlimited Devices, Dedicated Account Manager, Custom Workflows, SLA Guarantee', 'Active')
ON DUPLICATE KEY UPDATE plan_name=VALUES(plan_name);

-- 2. Insert 10 Sample Customers
INSERT INTO customers (customer_id, name, email, phone, registration_date, account_status) VALUES
(1, 'Aarav Sharma', 'aarav.sharma@example.com', '+91 9876543210', '2026-01-10', 'Active'),
(2, 'Priya Patel', 'priya.patel@example.com', '+91 9812345678', '2026-01-15', 'Active'),
(3, 'Rohan Verma', 'rohan.verma@example.com', '+91 9723456789', '2026-02-01', 'Active'),
(4, 'Sneha Reddy', 'sneha.reddy@example.com', '+91 9634567890', '2026-02-14', 'Active'),
(5, 'Vikram Malhotra', 'vikram.m@example.com', '+91 9545678901', '2026-02-20', 'Active'),
(6, 'Ananya Iyer', 'ananya.iyer@example.com', '+91 9456789012', '2026-03-01', 'Active'),
(7, 'Kabir Mehta', 'kabir.mehta@example.com', '+91 9367890123', '2026-03-10', 'Active'),
(8, 'Diya Kapoor', 'diya.kapoor@example.com', '+91 9278901234', '2026-03-15', 'Active'),
(9, 'Arjun Singh', 'arjun.singh@example.com', '+91 9189012345', '2026-03-22', 'Inactive'),
(10, 'Neha Joshi', 'neha.joshi@example.com', '+91 9090123456', '2026-04-01', 'Active')
ON DUPLICATE KEY UPDATE name=VALUES(name);

-- 3. Insert Sample Subscriptions
-- Current date assumed around Oct 2026
INSERT INTO subscriptions (subscription_id, customer_id, plan_id, start_date, expiry_date, status) VALUES
(1, 1, 4, '2026-01-10', '2027-01-10', 'Active'),
(2, 2, 2, '2026-08-01', '2026-10-30', 'Active'),
(3, 3, 1, '2026-09-10', '2026-10-10', 'Expiring Soon'),
(4, 4, 3, '2026-04-01', '2026-09-28', 'Expired'),
(5, 5, 2, '2026-07-15', '2026-10-13', 'Expiring Soon'),
(6, 6, 1, '2026-08-15', '2026-09-14', 'Expired'),
(7, 7, 3, '2026-06-01', '2026-11-28', 'Active'),
(8, 8, 4, '2026-03-15', '2027-03-15', 'Active'),
(9, 9, 1, '2026-03-22', '2026-04-21', 'Cancelled'),
(10, 10, 2, '2026-09-01', '2026-11-30', 'Active')
ON DUPLICATE KEY UPDATE status=VALUES(status);

-- 4. Insert Sample Payments
INSERT INTO payments (payment_id, subscription_id, customer_id, amount, payment_date, payment_method, transaction_id, payment_status) VALUES
(1, 1, 1, 3499.00, '2026-01-10 10:15:00', 'Credit Card', 'TXN-20260110-8831', 'Success'),
(2, 2, 2, 999.00, '2026-08-01 11:30:00', 'UPI', 'TXN-20260801-4421', 'Success'),
(3, 3, 3, 499.00, '2026-09-10 14:22:00', 'Debit Card', 'TXN-20260910-1928', 'Success'),
(4, 4, 4, 1999.00, '2026-04-01 09:45:00', 'Net Banking', 'TXN-20260401-7721', 'Success'),
(5, 5, 5, 999.00, '2026-07-15 16:10:00', 'UPI', 'TXN-20260715-6612', 'Success'),
(6, 6, 6, 499.00, '2026-08-15 12:00:00', 'Cash', 'TXN-20260815-3310', 'Success'),
(7, 7, 7, 1999.00, '2026-06-01 18:25:00', 'Credit Card', 'TXN-20260601-9920', 'Success'),
(8, 8, 8, 3499.00, '2026-03-15 13:40:00', 'UPI', 'TXN-20260315-5511', 'Success'),
(9, 9, 9, 499.00, '2026-03-22 15:50:00', 'Credit Card', 'TXN-20260322-2244', 'Success'),
(10, 10, 10, 999.00, '2026-09-01 17:05:00', 'Debit Card', 'TXN-20260901-7733', 'Success')
ON DUPLICATE KEY UPDATE amount=VALUES(amount);

-- 5. Insert Sample Invoices
INSERT INTO invoices (invoice_id, invoice_number, payment_id, customer_id, subscription_id, amount, invoice_date, pdf_path) VALUES
(1, 'INV-20260110-001', 1, 1, 1, 3499.00, '2026-01-10 10:15:00', 'invoices/INV-20260110-001.pdf'),
(2, 'INV-20260801-002', 2, 2, 2, 999.00, '2026-08-01 11:30:00', 'invoices/INV-20260801-002.pdf'),
(3, 'INV-20260910-003', 3, 3, 3, 499.00, '2026-09-10 14:22:00', 'invoices/INV-20260910-003.pdf'),
(4, 'INV-20260401-004', 4, 4, 4, 1999.00, '2026-04-01 09:45:00', 'invoices/INV-20260401-004.pdf'),
(5, 'INV-20260715-005', 5, 5, 5, 999.00, '2026-07-15 16:10:00', 'invoices/INV-20260715-005.pdf'),
(6, 'INV-20260815-006', 6, 6, 6, 499.00, '2026-08-15 12:00:00', 'invoices/INV-20260815-006.pdf'),
(7, 'INV-20260601-007', 7, 7, 7, 1999.00, '2026-06-01 18:25:00', 'invoices/INV-20260601-007.pdf'),
(8, 'INV-20260315-008', 8, 8, 8, 3499.00, '2026-03-15 13:40:00', 'invoices/INV-20260315-008.pdf'),
(9, 'INV-20260322-009', 9, 9, 9, 499.00, '2026-03-22 15:50:00', 'invoices/INV-20260322-009.pdf'),
(10, 'INV-20260901-010', 10, 10, 10, 999.00, '2026-09-01 17:05:00', 'invoices/INV-20260901-010.pdf')
ON DUPLICATE KEY UPDATE invoice_number=VALUES(invoice_number);

-- 6. Insert Sample Subscription History (Audit Log)
INSERT INTO subscription_history (history_id, subscription_id, customer_id, old_plan_id, new_plan_id, action_type, old_expiry_date, new_expiry_date, amount, action_date, remarks) VALUES
(1, 1, 1, NULL, 4, 'ACTIVATED', NULL, '2027-01-10', 3499.00, '2026-01-10 10:15:00', 'Initial Enterprise subscription activation'),
(2, 2, 2, NULL, 2, 'ACTIVATED', NULL, '2026-10-30', 999.00, '2026-08-01 11:30:00', 'Initial Standard plan activation'),
(3, 3, 3, NULL, 1, 'ACTIVATED', NULL, '2026-10-10', 499.00, '2026-09-10 14:22:00', 'Initial Basic plan activation'),
(4, 4, 4, NULL, 3, 'ACTIVATED', NULL, '2026-09-28', 1999.00, '2026-04-01 09:45:00', 'Initial Premium plan activation'),
(5, 5, 5, NULL, 2, 'ACTIVATED', NULL, '2026-10-13', 999.00, '2026-07-15 16:10:00', 'Initial Standard plan activation'),
(6, 6, 6, NULL, 1, 'ACTIVATED', NULL, '2026-09-14', 499.00, '2026-08-15 12:00:00', 'Initial Basic plan activation'),
(7, 7, 7, 2, 3, 'UPGRADED', '2026-08-30', '2026-11-28', 1000.00, '2026-06-01 18:25:00', 'Upgraded from Standard to Premium (Prorated)'),
(8, 8, 8, NULL, 4, 'ACTIVATED', NULL, '2027-03-15', 3499.00, '2026-03-15 13:40:00', 'Annual Enterprise plan activation'),
(9, 9, 9, 1, NULL, 'CANCELLED', '2026-04-21', '2026-04-21', 0.00, '2026-04-05 11:00:00', 'Customer requested cancellation due to relocation'),
(10, 10, 10, NULL, 2, 'ACTIVATED', NULL, '2026-11-30', 999.00, '2026-09-01 17:05:00', 'Initial Standard plan activation')
ON DUPLICATE KEY UPDATE action_type=VALUES(action_type);

-- 7. Insert Sample Notifications
INSERT INTO notifications (notification_id, customer_id, subscription_id, notification_type, message, sent_at, notification_status) VALUES
(1, 3, 3, 'EXPIRY_REMINDER', 'Dear Rohan Verma, your Basic subscription expires on 2026-10-10. Renew today to avoid interruption!', '2026-10-03 09:00:00', 'Sent'),
(2, 5, 5, 'EXPIRY_REMINDER', 'Dear Vikram Malhotra, your Standard subscription expires on 2026-10-13. 7 days remaining.', '2026-10-06 09:00:00', 'Sent'),
(3, 4, 4, 'EXPIRED_ALERT', 'Dear Sneha Reddy, your Premium plan expired on 2026-09-28. Renew now to restore access.', '2026-09-29 08:30:00', 'Sent'),
(4, 9, 9, 'CANCELLATION_CONFIRMATION', 'Dear Arjun Singh, your subscription cancellation has been processed successfully.', '2026-04-05 11:05:00', 'Sent')
ON DUPLICATE KEY UPDATE message=VALUES(message);
