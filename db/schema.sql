-- ============================================================
-- Chicago Building Violations & Scofflaw Database Schema
-- ============================================================
-- Three tables: violations, scofflaws, comments
-- JOIN key: address_norm (UPPER + TRIM of raw address)
-- ============================================================

DROP TABLE IF EXISTS comments;
DROP TABLE IF EXISTS violations;
DROP TABLE IF EXISTS scofflaws;

-- ============================================================
-- VIOLATIONS TABLE
-- Source: Building_Violations CSV (filtered to >= 2024-01-01)
-- ============================================================
CREATE TABLE violations (
    id              INTEGER PRIMARY KEY,          -- City-provided unique violation ID
    violation_date  DATE NOT NULL,                -- Date violation was recorded
    violation_code  TEXT NOT NULL,                -- e.g. "CN104035"
    violation_status TEXT NOT NULL,               -- OPEN | COMPLIED | NO ENTRY
    violation_description TEXT,                   -- e.g. "MAINTAIN WINDOW" (nullable)
    inspector_comments TEXT,                      -- Inspector's notes (nullable)
    address         TEXT NOT NULL,                -- Original address from dataset
    address_norm    TEXT NOT NULL                 -- Normalized: UPPER(TRIM(address))
);

-- ============================================================
-- SCOFFLAWS TABLE
-- Source: Building_Code_Scofflaw_List CSV
-- ============================================================
CREATE TABLE scofflaws (
    record_id       TEXT PRIMARY KEY,             -- e.g. "19-M1-400353-2023-03-01"
    address         TEXT NOT NULL,                -- Original address from dataset
    address_norm    TEXT NOT NULL                 -- Normalized: UPPER(TRIM(address))
);

-- ============================================================
-- COMMENTS TABLE
-- Populated via POST /property/<address>/comments/
-- ============================================================
CREATE TABLE comments (
    id              SERIAL PRIMARY KEY,           -- Auto-incrementing ID
    address         TEXT NOT NULL,                -- Address as submitted by user
    address_norm    TEXT NOT NULL,                -- Normalized for lookups
    author          TEXT NOT NULL,                -- Comment author
    comment         TEXT NOT NULL,                -- Comment content
    created_at      TIMESTAMP DEFAULT NOW()       -- Server-generated timestamp
);

-- ============================================================
-- INDEXES (created after bulk data load for performance)
-- ============================================================
CREATE INDEX idx_violations_address_norm ON violations(address_norm);
CREATE INDEX idx_violations_date ON violations(violation_date);
CREATE INDEX idx_violations_addr_date ON violations(address_norm, violation_date);
CREATE INDEX idx_scofflaws_address_norm ON scofflaws(address_norm);
CREATE INDEX idx_comments_address_norm ON comments(address_norm);
