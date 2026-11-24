-- Update the status check constraint to include 'On the way' (MySQL 8.0.16+)
ALTER TABLE service_requests 
DROP CONSTRAINT IF EXISTS service_requests_status_check;

ALTER TABLE service_requests 
ADD CONSTRAINT service_requests_status_check 
CHECK (status IN ('Requested', 'Assigned', 'On the way', 'In Progress', 'Completed', 'Cancelled'));
