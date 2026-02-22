CREATE TABLE IF NOT EXISTS service_status (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(50)
);

INSERT INTO service_status (status) VALUES ('initialization_successful');
