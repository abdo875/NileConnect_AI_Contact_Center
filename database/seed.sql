-- ============================================================
-- NileConnect AI Contact Center — Seed Data
-- Demo: 1 Admin + 1 Agent + 3 Customers + 2 Cases
-- Passwords are bcrypt hashes of 'Admin@123' and 'Agent@123'
-- ============================================================

-- Users
-- password: Admin@123
INSERT INTO users (id, name, email, password_hash, role, is_active) VALUES
(
    'a1000000-0000-0000-0000-000000000001',
    'System Admin',
    'admin@nileconnect.eg',
    '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW',
    'ADMIN',
    TRUE
)
ON CONFLICT (email) DO NOTHING;

-- password: Agent@123
INSERT INTO users (id, name, email, password_hash, role, is_active) VALUES
(
    'a2000000-0000-0000-0000-000000000002',
    'Sara Hassan',
    'sara.hassan@nileconnect.eg',
    '$2b$12$LxuCW01DazRGbQGPkMFBBeafvyT8jLkAIPAMQkHyiYKVRpK6QFCVS',
    'CALL_CENTER',
    TRUE
)
ON CONFLICT (email) DO NOTHING;

INSERT INTO users (id, name, email, password_hash, role, is_active) VALUES
(
    'a3000000-0000-0000-0000-000000000003',
    'Omar Nabil',
    'omar.nabil@nileconnect.eg',
    '$2b$12$LxuCW01DazRGbQGPkMFBBeafvyT8jLkAIPAMQkHyiYKVRpK6QFCVS',
    'CALL_CENTER',
    TRUE
)
ON CONFLICT (email) DO NOTHING;

-- Customers
INSERT INTO customers (id, name, phone, email, address) VALUES
(
    'c1000000-0000-0000-0000-000000000001',
    'Ahmed Mohamed',
    '01012345678',
    'ahmed.mohamed@gmail.com',
    'Cairo, Nasr City'
)
ON CONFLICT (phone) DO NOTHING;

INSERT INTO customers (id, name, phone, email, address) VALUES
(
    'c2000000-0000-0000-0000-000000000002',
    'Mona Ali',
    '01098765432',
    'mona.ali@yahoo.com',
    'Giza, Dokki'
)
ON CONFLICT (phone) DO NOTHING;

INSERT INTO customers (id, name, phone, email, address) VALUES
(
    'c3000000-0000-0000-0000-000000000003',
    'Khaled Ibrahim',
    '01155566677',
    NULL,
    'Alexandria, Smouha'
)
ON CONFLICT (phone) DO NOTHING;

-- Cases
INSERT INTO cases (id, customer_id, assigned_agent_id, issue, category, description, priority, status) VALUES
(
    'd1000000-0000-0000-0000-000000000001',
    'c1000000-0000-0000-0000-000000000001',
    'a2000000-0000-0000-0000-000000000002',
    'Internet connection keeps disconnecting',
    'CONNECTIVITY',
    'Customer reports repeated connection drops every 30 minutes. Router model: TP-Link Archer C6.',
    'HIGH',
    'IN_PROGRESS'
)
ON CONFLICT DO NOTHING;

INSERT INTO cases (id, customer_id, assigned_agent_id, issue, category, description, priority, status) VALUES
(
    'd2000000-0000-0000-0000-000000000002',
    'c2000000-0000-0000-0000-000000000002',
    'a2000000-0000-0000-0000-000000000002',
    'Very slow internet speed',
    'SPEED',
    'Customer subscribed to 100 Mbps plan but getting only 5 Mbps. Issue started 3 days ago.',
    'MEDIUM',
    'OPEN'
)
ON CONFLICT DO NOTHING;

-- Calls
INSERT INTO calls (id, customer_id, case_id, agent_id, call_type, started_at, ended_at, duration, summary, outcome) VALUES
(
    'e1000000-0000-0000-0000-000000000001',
    'c1000000-0000-0000-0000-000000000001',
    'd1000000-0000-0000-0000-000000000001',
    'a2000000-0000-0000-0000-000000000002',
    'INBOUND_HUMAN',
    NOW() - INTERVAL '2 days',
    NOW() - INTERVAL '2 days' + INTERVAL '15 minutes',
    900,
    'Customer called reporting disconnection issue. Scheduled technician visit.',
    'FOLLOW_UP_REQUIRED'
)
ON CONFLICT DO NOTHING;
