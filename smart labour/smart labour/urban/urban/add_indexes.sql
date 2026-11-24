-- Add indexes to improve performance (MySQL)

-- Service Requests indexes
CREATE INDEX idx_requests_customer ON service_requests(customer_id);
CREATE INDEX idx_requests_service ON service_requests(service_id);
CREATE INDEX idx_requests_city ON service_requests(city_id);
CREATE INDEX idx_requests_status ON service_requests(status);
CREATE INDEX idx_requests_created ON service_requests(created_at);

-- Assignments indexes
CREATE INDEX idx_assignments_request ON assignments(request_id);
CREATE INDEX idx_assignments_worker ON assignments(worker_id);

-- Workers indexes
CREATE INDEX idx_workers_service ON workers(service_id);
CREATE INDEX idx_workers_city ON workers(city_id);
CREATE INDEX idx_workers_status ON workers(status);

-- Customers indexes
CREATE INDEX idx_customers_city ON customers(city_id);

-- Feedback indexes
CREATE INDEX idx_feedback_request ON feedback(request_id);

