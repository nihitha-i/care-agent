"""Connects to the MCP server, lists its tools, and calls a few of them."""
import asyncio
import json
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER = StdioServerParameters(
    command=sys.executable,
    args=["-m", "app.mcp_server"],
    cwd=str(Path(__file__).resolve().parent.parent),
)


async def call(session, name, args):
    result = await session.call_tool(name, args)
    data = json.loads(result.content[0].text)
    print(f"\n>>> {name}({args})")
    print(json.dumps(data, indent=2)[:700])


async def main():
    async with stdio_client(SERVER) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print("Tools the server offers:")
            for t in tools.tools:
                print(f"  - {t.name}: {t.description.splitlines()[0]}")

            await call(session, "get_member_profile", {"member_id": "M1001"})
            await call(session, "list_claims", {"member_id": "M1001"})
            await call(session, "search_policy", {"query": "Is cosmetic surgery excluded from coverage?"})


if __name__ == "__main__":
    asyncio.run(main())