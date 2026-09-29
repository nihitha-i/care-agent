"""MCP server exposing member-services tools. Every call is written to care.audit_log."""
import json
import os

import numpy as np
from mcp.server.fastmcp import FastMCP
from openai import OpenAI
from pgvector.psycopg import register_vector
from psycopg.types.json import Jsonb

from app.db import get_conn

EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")

mcp = FastMCP("care-tools", log_level="WARNING")
_openai = OpenAI()


def _clean(obj):
    """Make database rows JSON-safe (dates and decimals become strings)."""
    return json.loads(json.dumps(obj, default=str))


def _audit(member_id, tool, args, allowed=True, reason=None):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO care.audit_log (member_id, tool, args, allowed, reason) "
            "VALUES (%s, %s, %s, %s, %s)",
            (member_id, tool, Jsonb(args), allowed, reason),
        )


@mcp.tool()
def search_policy(query: str) -> dict:
    """Search official Medicare policy documents (Medicare & You 2026 handbook and the
    Medicare Benefit Policy Manual). Returns the most relevant passages with source and page."""
    vec = np.array(
        _openai.embeddings.create(model=EMBED_MODEL, input=[query]).data[0].embedding,
        dtype=np.float32,
    )
    with get_conn() as conn:
        register_vector(conn)
        rows = conn.execute(
            "SELECT source, page, content FROM public.chunks "
            "ORDER BY embedding <=> %s LIMIT 4",
            (vec,),
        ).fetchall()
    _audit(None, "search_policy", {"query": query})
    return {"passages": _clean(rows)}


@mcp.tool()
def get_member_profile(member_id: str) -> dict:
    """Get a member's profile: name, date of birth, plan, phone, email and address."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM care.members WHERE member_id = %s", (member_id,)
        ).fetchone()
    _audit(member_id, "get_member_profile", {"member_id": member_id})
    return _clean(row) if row else {"error": f"No member found with id {member_id}"}


@mcp.tool()
def list_claims(member_id: str) -> dict:
    """List a member's claims with service, date, provider, amount, status and any denial reason."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT claim_id, service_date, provider, service, billed_amount, status, "
            "denial_reason FROM care.claims WHERE member_id = %s ORDER BY service_date",
            (member_id,),
        ).fetchall()
    _audit(member_id, "list_claims", {"member_id": member_id})
    return {"member_id": member_id, "claims": _clean(rows)}


@mcp.tool()
def update_address(member_id: str, street: str, city: str, state: str, zip_code: str) -> dict:
    """Update a member's mailing address. This CHANGES member data."""
    with get_conn() as conn:
        row = conn.execute(
            "UPDATE care.members SET street = %s, city = %s, state = %s, zip = %s "
            "WHERE member_id = %s RETURNING member_id, street, city, state, zip",
            (street, city, state, zip_code, member_id),
        ).fetchone()
    _audit(member_id, "update_address",
           {"member_id": member_id, "street": street, "city": city,
            "state": state, "zip_code": zip_code})
    return {"updated": _clean(row)} if row else {"error": f"No member found with id {member_id}"}


@mcp.tool()
def send_message(member_id: str, to_address: str, subject: str, body: str) -> dict:
    """Send a message on behalf of a member. DEMO ONLY: the message is stored, never actually sent."""
    with get_conn() as conn:
        row = conn.execute(
            "INSERT INTO care.messages (member_id, to_address, subject, body) "
            "VALUES (%s, %s, %s, %s) RETURNING id",
            (member_id, to_address, subject, body),
        ).fetchone()
    _audit(member_id, "send_message",
           {"member_id": member_id, "to_address": to_address, "subject": subject})
    return {"status": "stored (demo - not actually sent)", "message_id": row["id"]}


if __name__ == "__main__":
    mcp.run()  # communicates over stdin/stdout (the standard MCP "stdio" transport)