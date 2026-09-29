"""MCP server exposing member-services tools.
Each server session is locked to ONE member (CARE_MEMBER_ID); every call is audited."""
import json
import os

import numpy as np
from mcp.server.fastmcp import FastMCP
from openai import OpenAI
from pgvector.psycopg import register_vector
from psycopg.types.json import Jsonb

from app.db import get_conn

EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")
SESSION_MEMBER = os.getenv("CARE_MEMBER_ID")  # set by whoever starts the server

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


def _authorize(tool, member_id, args):
    """Refuse any access to a member other than the one this session belongs to."""
    if SESSION_MEMBER is None:
        _audit(member_id, tool, args, allowed=False, reason="no session member set")
        return {"error": "Access denied: no member session."}
    if member_id != SESSION_MEMBER:
        _audit(member_id, tool, args, allowed=False,
               reason=f"session belongs to {SESSION_MEMBER}")
        return {"error": "Access denied: you can only access your own records."}
    return None


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
    _audit(SESSION_MEMBER, "search_policy", {"query": query})
    return {"passages": _clean(rows)}


@mcp.tool()
def get_member_profile(member_id: str) -> dict:
    """Get a member's profile: name, date of birth, plan, phone, email and address."""
    args = {"member_id": member_id}
    if denied := _authorize("get_member_profile", member_id, args):
        return denied
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM care.members WHERE member_id = %s", (member_id,)
        ).fetchone()
    _audit(member_id, "get_member_profile", args)
    return _clean(row) if row else {"error": f"No member found with id {member_id}"}


@mcp.tool()
def list_claims(member_id: str) -> dict:
    """List a member's claims with service, date, provider, amount, status and any denial reason."""
    args = {"member_id": member_id}
    if denied := _authorize("list_claims", member_id, args):
        return denied
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT claim_id, service_date, provider, service, billed_amount, status, "
            "denial_reason FROM care.claims WHERE member_id = %s ORDER BY service_date",
            (member_id,),
        ).fetchall()
    _audit(member_id, "list_claims", args)
    return {"member_id": member_id, "claims": _clean(rows)}


@mcp.tool()
def update_address(member_id: str, street: str, city: str, state: str, zip_code: str) -> dict:
    """Update a member's mailing address. This CHANGES member data."""
    args = {"member_id": member_id, "street": street, "city": city,
            "state": state, "zip_code": zip_code}
    if denied := _authorize("update_address", member_id, args):
        return denied
    with get_conn() as conn:
        row = conn.execute(
            "UPDATE care.members SET street = %s, city = %s, state = %s, zip = %s "
            "WHERE member_id = %s RETURNING member_id, street, city, state, zip",
            (street, city, state, zip_code, member_id),
        ).fetchone()
    _audit(member_id, "update_address", args)
    return {"updated": _clean(row)} if row else {"error": f"No member found with id {member_id}"}


@mcp.tool()
def send_message(member_id: str, to_address: str, subject: str, body: str) -> dict:
    """Send a message on behalf of a member. DEMO ONLY: the message is stored, never actually sent."""
    args = {"member_id": member_id, "to_address": to_address, "subject": subject}
    if denied := _authorize("send_message", member_id, args):
        return denied
    with get_conn() as conn:
        row = conn.execute(
            "INSERT INTO care.messages (member_id, to_address, subject, body) "
            "VALUES (%s, %s, %s, %s) RETURNING id",
            (member_id, to_address, subject, body),
        ).fetchone()
    _audit(member_id, "send_message", args)
    return {"status": "stored (demo - not actually sent)", "message_id": row["id"]}


if __name__ == "__main__":
    mcp.run()  # stdio transport