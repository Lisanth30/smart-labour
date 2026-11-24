-- PostgreSQL Schema for Urban Service Management System

-- Drop tables if they exist (Reverse order of dependencies)
DROP TABLE IF EXISTS complaints CASCADE;
DROP TABLE IF EXISTS worker_rejections CASCADE;
DROP TABLE IF EXISTS feedback CASCADE;
DROP TABLE IF EXISTS customer_favorites CASCADE;
DROP TABLE IF EXISTS assignments CASCADE;
DROP TABLE IF EXISTS service_requests CASCADE;
DROP TABLE IF EXISTS workers CASCADE;
DROP TABLE IF EXISTS admins CASCADE;
DROP TABLE IF EXISTS customers CASCADE;
DROP TABLE IF EXISTS services CASCADE;
DROP TABLE IF EXISTS areas CASCADE;
DROP TABLE IF EXISTS cities CASCADE;
DROP TABLE IF EXISTS system_settings CASCADE;

-- Cities Table
CREATE TABLE cities (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
);

-- Areas Table
CREATE TABLE areas (
    id SERIAL PRIMARY KEY,
    city_id INT REFERENCES cities(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL
);

-- Services Table
CREATE TABLE services (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    icon_name VARCHAR(50),
    base_price DECIMAL(10,2) DEFAULT 499.00
);

-- Customers Table
CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    phone VARCHAR(15),
    address TEXT,
    city_id INT REFERENCES cities(id),
    area_id INT REFERENCES areas(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Workers Table
CREATE TABLE workers (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    phone VARCHAR(15),
    service_id INT REFERENCES services(id),
    city_id INT REFERENCES cities(id),
    status VARCHAR(20) DEFAULT 'Available' CHECK (status IN ('Available', 'Busy', 'Offline')),
    rating_avg DECIMAL(3,2) DEFAULT 5.0,
    jobs_completed INT DEFAULT 0,
    bio TEXT DEFAULT 'Certified professional with over 5 years of experience.',
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Admins Table
CREATE TABLE admins (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL
);

-- Service Requests Table
CREATE TABLE service_requests (
    id SERIAL PRIMARY KEY,
    customer_id INT REFERENCES customers(id),
    service_id INT REFERENCES services(id),
    city_id INT REFERENCES cities(id),
    area_id INT REFERENCES areas(id),
    request_date DATE NOT NULL,
    time_slot VARCHAR(50) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'Requested' CHECK (status IN ('Requested', 'Assigned', 'On the way', 'In Progress', 'Completed', 'Cancelled')),
    service_fee DECIMAL(10,2) DEFAULT 0.0,
    extra_charges DECIMAL(10,2) DEFAULT 0.0,
    total_amount DECIMAL(10,2) DEFAULT 0.0,
    worker_share DECIMAL(10,2) DEFAULT 0.0,
    admin_commission DECIMAL(10,2) DEFAULT 0.0,
    payment_status VARCHAR(50) DEFAULT 'Unpaid',
    cancellation_reason TEXT,
    cancelled_at TIMESTAMP,
    presence_confirmed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Assignments Table
CREATE TABLE assignments (
    id SERIAL PRIMARY KEY,
    request_id INT REFERENCES service_requests(id) ON DELETE CASCADE,
    worker_id INT REFERENCES workers(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    eta TIMESTAMP,
    completed_at TIMESTAMP NULL
);

-- Feedback Table
CREATE TABLE feedback (
    id SERIAL PRIMARY KEY,
    request_id INT REFERENCES service_requests(id) ON DELETE CASCADE,
    rating INT CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Customer Favorites Table
CREATE TABLE customer_favorites (
    id SERIAL PRIMARY KEY,
    customer_id INT REFERENCES customers(id) ON DELETE CASCADE,
    worker_id INT REFERENCES workers(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(customer_id, worker_id)
);

-- System Settings Table
CREATE TABLE system_settings (
    key VARCHAR(100) PRIMARY KEY,
    value VARCHAR(255)
);

-- Complaints Table
CREATE TABLE complaints (
    id SERIAL PRIMARY KEY,
    request_id INT REFERENCES service_requests(id) ON DELETE CASCADE,
    customer_id INT REFERENCES customers(id) ON DELETE CASCADE,
    category VARCHAR(100),
    description TEXT,
    status VARCHAR(50) DEFAULT 'Open',
    resolution_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP
);

-- Worker Rejections Table
CREATE TABLE worker_rejections (
    id SERIAL PRIMARY KEY,
    request_id INT REFERENCES service_requests(id) ON DELETE CASCADE,
    worker_id INT REFERENCES workers(id) ON DELETE CASCADE,
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Performance Indexes
CREATE INDEX IF NOT EXISTS idx_requests_customer ON service_requests(customer_id);
CREATE INDEX IF NOT EXISTS idx_requests_service ON service_requests(service_id);
CREATE INDEX IF NOT EXISTS idx_requests_city ON service_requests(city_id);
CREATE INDEX IF NOT EXISTS idx_requests_status ON service_requests(status);
CREATE INDEX IF NOT EXISTS idx_requests_created ON service_requests(created_at);
CREATE INDEX IF NOT EXISTS idx_assignments_request ON assignments(request_id);
CREATE INDEX IF NOT EXISTS idx_assignments_worker ON assignments(worker_id);
CREATE INDEX IF NOT EXISTS idx_workers_service ON workers(service_id);
CREATE INDEX IF NOT EXISTS idx_workers_city ON workers(city_id);
CREATE INDEX IF NOT EXISTS idx_workers_status ON workers(status);
CREATE INDEX IF NOT EXISTS idx_customers_city ON customers(city_id);
CREATE INDEX IF NOT EXISTS idx_feedback_request ON feedback(request_id);

-- System Settings Initial Data
INSERT INTO system_settings (key, value) VALUES 
('platform_fee', '49.0'), 
('commission_pct', '15.0')
ON CONFLICT (key) DO NOTHING;
