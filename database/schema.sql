-- ============================================================
-- NileConnect AI Contact Center — PostgreSQL Schema
-- Phase 1
-- ============================================================

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- ENUMS
-- ============================================================

CREATE TYPE user_role AS ENUM ('ADMIN', 'CALL_CENTER');

CREATE TYPE case_status AS ENUM (
    'OPEN',
    'IN_PROGRESS',
    'FOLLOW_UP_PENDING',
    'AI_FOLLOW_UP_SCHEDULED',
    'AI_FOLLOW_UP_COMPLETED',
    'NEEDS_HUMAN',
    'RESOLVED'
);

CREATE TYPE case_priority AS ENUM ('LOW', 'MEDIUM', 'HIGH', 'URGENT');

CREATE TYPE case_category AS ENUM (
    'CONNECTIVITY',
    'SPEED',
    'BILLING',
    'EQUIPMENT',
    'OUTAGE',
    'INSTALLATION',
    'OTHER'
);

CREATE TYPE call_type AS ENUM ('INBOUND_HUMAN', 'OUTBOUND_HUMAN', 'OUTBOUND_AI');

CREATE TYPE call_outcome AS ENUM ('RESOLVED', 'FOLLOW_UP_REQUIRED', 'NO_ANSWER', 'ESCALATED', 'PENDING');

CREATE TYPE document_status AS ENUM ('UPLOADING', 'PROCESSING', 'READY', 'FAILED');

CREATE TYPE followup_status AS ENUM ('SCHEDULED', 'IN_PROGRESS', 'COMPLETED', 'FAILED', 'CANCELLED');

CREATE TYPE followup_result AS ENUM ('YES', 'NO', 'NO_ANSWER', 'UNKNOWN');

-- ============================================================
-- TABLES
-- ============================================================

-- users
CREATE TABLE IF NOT EXISTS users (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name        VARCHAR(255)        NOT NULL,
    email       VARCHAR(255)        NOT NULL UNIQUE,
    password_hash VARCHAR(255)      NOT NULL,
    role        user_role           NOT NULL DEFAULT 'CALL_CENTER',
    is_active   BOOLEAN             NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ         NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ         NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role  ON users(role);

-- customers
CREATE TABLE IF NOT EXISTS customers (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name        VARCHAR(255)    NOT NULL,
    phone       VARCHAR(50)     NOT NULL UNIQUE,
    email       VARCHAR(255),
    address     TEXT,
    notes       TEXT,
    created_at  TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers(phone);
CREATE INDEX IF NOT EXISTS idx_customers_name  ON customers(name);

-- cases
CREATE TABLE IF NOT EXISTS cases (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id       UUID            NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    assigned_agent_id UUID            REFERENCES users(id) ON DELETE SET NULL,
    issue             VARCHAR(500)    NOT NULL,
    category          case_category   NOT NULL DEFAULT 'OTHER',
    description       TEXT,
    priority          case_priority   NOT NULL DEFAULT 'MEDIUM',
    status            case_status     NOT NULL DEFAULT 'OPEN',
    created_at        TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    resolved_at       TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_cases_customer_id  ON cases(customer_id);
CREATE INDEX IF NOT EXISTS idx_cases_agent_id     ON cases(assigned_agent_id);
CREATE INDEX IF NOT EXISTS idx_cases_status       ON cases(status);
CREATE INDEX IF NOT EXISTS idx_cases_created_at   ON cases(created_at DESC);

-- calls
CREATE TABLE IF NOT EXISTS calls (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID            NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    case_id     UUID            REFERENCES cases(id) ON DELETE SET NULL,
    agent_id    UUID            REFERENCES users(id) ON DELETE SET NULL,
    call_type   call_type       NOT NULL,
    started_at  TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    ended_at    TIMESTAMPTZ,
    duration    INTEGER,                    -- seconds
    summary     TEXT,
    outcome     call_outcome    NOT NULL DEFAULT 'PENDING',
    transcript  TEXT,
    created_at  TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_calls_customer_id ON calls(customer_id);
CREATE INDEX IF NOT EXISTS idx_calls_case_id     ON calls(case_id);
CREATE INDEX IF NOT EXISTS idx_calls_agent_id    ON calls(agent_id);
CREATE INDEX IF NOT EXISTS idx_calls_started_at  ON calls(started_at DESC);

-- ai_followups
CREATE TABLE IF NOT EXISTS ai_followups (
    id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_id        UUID               NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    customer_id    UUID               NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    scheduled_at   TIMESTAMPTZ        NOT NULL,
    status         followup_status    NOT NULL DEFAULT 'SCHEDULED',
    attempt_number INTEGER            NOT NULL DEFAULT 1,
    result         followup_result,
    call_id        UUID               REFERENCES calls(id) ON DELETE SET NULL,
    notes          TEXT,
    created_at     TIMESTAMPTZ        NOT NULL DEFAULT NOW(),
    completed_at   TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_followups_case_id     ON ai_followups(case_id);
CREATE INDEX IF NOT EXISTS idx_followups_customer_id ON ai_followups(customer_id);
CREATE INDEX IF NOT EXISTS idx_followups_status      ON ai_followups(status);
CREATE INDEX IF NOT EXISTS idx_followups_scheduled   ON ai_followups(scheduled_at);

-- documents
CREATE TABLE IF NOT EXISTS documents (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filename     VARCHAR(500)      NOT NULL,
    original_name VARCHAR(500)     NOT NULL,
    file_type    VARCHAR(50)       NOT NULL,
    storage_path VARCHAR(1000)     NOT NULL,
    file_size    BIGINT,
    uploaded_by  UUID              REFERENCES users(id) ON DELETE SET NULL,
    status       document_status   NOT NULL DEFAULT 'UPLOADING',
    created_at   TIMESTAMPTZ       NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ       NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_documents_uploaded_by ON documents(uploaded_by);
CREATE INDEX IF NOT EXISTS idx_documents_status      ON documents(status);

-- audit_logs
CREATE TABLE IF NOT EXISTS audit_logs (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID            REFERENCES users(id) ON DELETE SET NULL,
    action      VARCHAR(100)    NOT NULL,
    entity_type VARCHAR(100)    NOT NULL,
    entity_id   UUID,
    details     JSONB,
    ip_address  VARCHAR(50),
    created_at  TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id     ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_entity_type ON audit_logs(entity_type);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at  ON audit_logs(created_at DESC);
