"""Proves the server refuses access to other members' records, and audits the refusal."""
import asyncio
import json
import os
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from app.db import get_conn

SERVER = StdioServerParameters(
    command=sys.executable, args=["-m", "app.mcp_server"],
    cwd=str(Path(__file__).resolve().parent.parent),
    env={**os.environ, "CARE_MEMBER_ID": "M1001"},  # this session belongs to Ava only
)


async def call(session, name, args):
    result = await session.call_tool(name, args)
    return json.loads(result.content[0].text)


async def main():
    async with stdio_client(SERVER) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            own = await call(session, "list_claims", {"member_id": "M1001"})
            other = await call(session, "list_claims", {"member_id": "M1002"})
            other_write = await call(session, "update_address", {
                "member_id": "M1002", "street": "1 Test St", "city": "X",
                "state": "NJ", "zip_code": "00000"})

    checks = {
        "own records allowed": "claims" in own,
        "other member's claims refused": "error" in other,
        "other member's address change refused": "error" in other_write,
    }
    with get_conn() as conn:
        denied = conn.execute(
            "SELECT count(*) AS n FROM care.audit_log WHERE allowed = false").fetchone()["n"]
    checks["refusals recorded in audit log"] = denied >= 2

    for name, ok in checks.items():
        print(f"{'PASS' if ok else 'FAIL'}  {name}")


if __name__ == "__main__":
    asyncio.run(main())