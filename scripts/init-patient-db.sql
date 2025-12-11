-- ZFP-FINAL-SCHEMA: ABSOLUTE PATIENT DB STRUCTURE

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Core Patient Schema
CREATE TABLE IF NOT EXISTS patients (
    patient_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    mrn VARCHAR(50) UNIQUE NOT NULL, -- Medical Record Number
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE NOT NULL,
    sex CHAR(1) CHECK (sex IN ('M', 'F', 'O', 'U')),
    ssn_encrypted BYTEA, -- Encrypted PHI (Pillar 4 Enforcement)
    
    phone VARCHAR(20),
    email VARCHAR(255),
    
    insurance_provider VARCHAR(255),
    insurance_policy_number_encrypted BYTEA,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID, -- Placeholder for users(user_id)
    is_deleted BOOLEAN DEFAULT FALSE
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_patients_mrn ON patients(mrn);
CREATE INDEX IF NOT EXISTS idx_patients_name ON patients(last_name, first_name);
CREATE INDEX IF NOT EXISTS idx_patients_dob ON patients(date_of_birth);

-- Core Clinical Encounter Schema
CREATE TABLE IF NOT EXISTS encounters (
    encounter_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES patients(patient_id),
    encounter_type VARCHAR(50) NOT NULL, -- Inpatient, Outpatient, Emergency
    chief_complaint TEXT,
    
    admission_time TIMESTAMPTZ NOT NULL,
    discharge_time TIMESTAMPTZ,
    
    status VARCHAR(20) CHECK (status IN ('Active', 'Discharged', 'Transferred')),
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_encounters_patient ON encounters(patient_id);
CREATE INDEX IF NOT EXISTS idx_encounters_active ON encounters(status) WHERE status = 'Active';

-- Placeholder for Staff/Users for FKs
CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(100) UNIQUE NOT NULL
);

INSERT INTO users (user_id, username) VALUES ('00000000-0000-0000-0000-000000000000', 'system_user') ON CONFLICT (user_id) DO NOTHING;