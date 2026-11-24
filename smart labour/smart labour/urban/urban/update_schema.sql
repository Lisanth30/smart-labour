-- Add missing columns to Workers
ALTER TABLE workers ADD COLUMN IF NOT EXISTS rating_avg FLOAT DEFAULT 5.0;
ALTER TABLE workers ADD COLUMN IF NOT EXISTS jobs_completed INT DEFAULT 0;
ALTER TABLE workers ADD COLUMN IF NOT EXISTS bio TEXT DEFAULT 'Experienced professional ready to help.';
ALTER TABLE workers ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT FALSE;

-- Add missing columns to Service Requests
ALTER TABLE service_requests ADD COLUMN IF NOT EXISTS payment_status VARCHAR(50) DEFAULT 'Unpaid';
ALTER TABLE service_requests ADD COLUMN IF NOT EXISTS service_fee DECIMAL(10,2) DEFAULT 0.0;
ALTER TABLE service_requests ADD COLUMN IF NOT EXISTS extra_charges DECIMAL(10,2) DEFAULT 0.0;
ALTER TABLE service_requests ADD COLUMN IF NOT EXISTS total_amount DECIMAL(10,2) DEFAULT 0.0;
ALTER TABLE service_requests ADD COLUMN IF NOT EXISTS worker_share DECIMAL(10,2) DEFAULT 0.0;
ALTER TABLE service_requests ADD COLUMN IF NOT EXISTS admin_commission DECIMAL(10,2) DEFAULT 0.0;
ALTER TABLE service_requests ADD COLUMN IF NOT EXISTS cancellation_reason TEXT;
ALTER TABLE service_requests ADD COLUMN IF NOT EXISTS cancelled_at TIMESTAMP;
ALTER TABLE service_requests ADD COLUMN IF NOT EXISTS presence_confirmed BOOLEAN DEFAULT FALSE;

-- Add base_price to Services
ALTER TABLE services ADD COLUMN IF NOT EXISTS base_price DECIMAL(10,2) DEFAULT 499.00;

-- Create System Settings Table
CREATE TABLE IF NOT EXISTS system_settings (
    key VARCHAR(100) PRIMARY KEY,
    value VARCHAR(255)
);

-- Seed System Settings
INSERT INTO system_settings (key, value) VALUES 
('platform_fee', '49.0'), 
('commission_pct', '15.0') 
ON CONFLICT (key) DO NOTHING;

-- Create Complaints Table
CREATE TABLE IF NOT EXISTS complaints (
    id SERIAL PRIMARY KEY,
    request_id INT,
    customer_id INT,
    category VARCHAR(100),
    description TEXT,
    status VARCHAR(50) DEFAULT 'Open',
    resolution_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    FOREIGN KEY (request_id) REFERENCES service_requests(id),
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

-- Create Customer Favorites Table
CREATE TABLE IF NOT EXISTS customer_favorites (
    customer_id INT,
    worker_id INT,
    PRIMARY KEY (customer_id, worker_id),
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (worker_id) REFERENCES workers(id)
);

-- Create Worker Rejections Table
CREATE TABLE IF NOT EXISTS worker_rejections (
    id SERIAL PRIMARY KEY,
    request_id INT,
    worker_id INT,
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (request_id) REFERENCES service_requests(id),
    FOREIGN KEY (worker_id) REFERENCES workers(id)
);

-- Add sample bio to existing workers
UPDATE workers SET bio = 'Certified professional with over 5 years of experience.' WHERE bio IS NULL;
