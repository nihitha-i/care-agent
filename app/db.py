import psycopg
from psycopg.rows import dict_row

from app.config import DATABASE_URL

SCHEMA = """
CREATE SCHEMA IF NOT EXISTS care;

CREATE TABLE IF NOT EXISTS care.members (
    member_id     TEXT PRIMARY KEY,
    full_name     TEXT NOT NULL,
    date_of_birth DATE NOT NULL,
    plan          TEXT NOT NULL,
    phone         TEXT NOT NULL,
    email         TEXT NOT NULL,
    street        TEXT NOT NULL,
    city          TEXT NOT NULL,
    state         TEXT NOT NULL,
    zip           TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS care.claims (
    claim_id      TEXT PRIMARY KEY,
    member_id     TEXT NOT NULL REFERENCES care.members(member_id),
    service_date  DATE NOT NULL,
    provider      TEXT NOT NULL,
    service       TEXT NOT NULL,
    billed_amount NUMERIC(10, 2) NOT NULL,
    status        TEXT NOT NULL,
    denial_reason TEXT
);

CREATE TABLE IF NOT EXISTS care.messages (
    id         SERIAL PRIMARY KEY,
    member_id  TEXT NOT NULL,
    to_address TEXT NOT NULL,
    subject    TEXT NOT NULL,
    body       TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS care.audit_log (
    id        SERIAL PRIMARY KEY,
    ts        TIMESTAMPTZ DEFAULT now(),
    member_id TEXT,
    tool      TEXT NOT NULL,
    args      JSONB,
    allowed   BOOLEAN NOT NULL,
    reason    TEXT
);
"""


def get_conn():
    """Connection that returns rows as dictionaries."""
    return psycopg.connect(DATABASE_URL, autocommit=True, row_factory=dict_row)


def init_db():
    with get_conn() as conn:
        conn.execute(SCHEMA)