"""LangGraph agent that uses the MCP server's tools, with human approval for write actions."""
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import AsyncOpenAI

from app.config import CHAT_MODEL

WRITE_TOOLS = {"update_address", "send_message"}  # these change data or send something
MAX_STEPS = 8
PROJECT_DIR = str(Path(__file__).resolve().parent.parent)

SYSTEM = """You are a Medicare member-services assistant helping the logged-in member {member_id}.
Rules:
1. Use the tools to look up facts. Never guess member data or Medicare policy.
2. For ANY question about whether something is covered, why a claim was denied, or appeals:
   a. call get_member_profile to check the member's plan,
   b. call search_policy with a SPECIFIC query naming the service (e.g. "cosmetic surgery
      exclusion", not "claim denial reasons"),
   c. if it involves the member's claims, also call list_claims.
3. Connect the answer to the member's own record: name the specific claim (ID, service,
   status, denial reason), then explain what Medicare policy says about it.
4. If the member is on a Medicare Advantage plan, say that their plan may offer extra
   benefits beyond Original Medicare and that they should check their plan's coverage.
5. Only cite sources you retrieved with search_policy in THIS conversation, in this form:
   (source: <document name>, page <number>). Never state a Medicare rule from memory; if you
   have not searched for it, search first.
6. Before sending any message that describes the member's data, look that data up first.
7. Read each claim's status carefully before saying claims are denied, approved or pending.
8. Only look up or change data for member {member_id}.
9. Only update data or send messages when the member clearly asked for it. send_message is a
   demo tool: tell the member the message was stored, not delivered.
10. Be concise and friendly."""


class AgentState(TypedDict):
    messages: list
    steps: int
    tool_log: list


def server_for(member_id: str) -> StdioServerParameters:
    """Start an MCP server session locked to one member."""
    return StdioServerParameters(
        command=sys.executable,
        args=["-m", "app.mcp_server"],
        cwd=PROJECT_DIR,
        env={**os.environ, "CARE_MEMBER_ID": member_id},
    )


async def cli_approve(tool: str, args: dict) -> bool:
    """Ask the human in the terminal before any write action."""
    print(f"\n[APPROVAL NEEDED] The agent wants to call {tool} with {json.dumps(args)}")
    reply = await asyncio.to_thread(input, "Allow? (y/n): ")
    return reply.strip().lower() == "y"


class CareAgent:
    def __init__(self, session: ClientSession, tools: list, approve):
        self.session = session
        self.tools = tools
        self.approve = approve
        self.llm_client = AsyncOpenAI()
        self.graph = self._build()

    async def call_llm(self, state: AgentState) -> dict:
        resp = await self.llm_client.chat.completions.create(
            model=CHAT_MODEL, temperature=0, messages=state["messages"], tools=self.tools,
        )
        msg = resp.choices[0].message
        out = {"role": "assistant", "content": msg.content or ""}
        if msg.tool_calls:
            out["tool_calls"] = [
                {"id": tc.id, "type": "function",
                 "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                for tc in msg.tool_calls
            ]
        return {"messages": state["messages"] + [out], "steps": state["steps"] + 1}

    async def run_tools(self, state: AgentState) -> dict:
        calls = state["messages"][-1]["tool_calls"]
        new_messages, log = [], list(state["tool_log"])
        for tc in calls:
            name = tc["function"]["name"]
            args = json.loads(tc["function"]["arguments"] or "{}")
            if name in WRITE_TOOLS and not await self.approve(name, args):
                output = json.dumps({"error": "The member did not approve this action."})
                log.append({"tool": name, "args": args, "approved": False})
            else:
                result = await self.session.call_tool(name, args)
                output = result.content[0].text if result.content else "{}"
                log.append({"tool": name, "args": args, "approved": True})
            new_messages.append({"role": "tool", "tool_call_id": tc["id"], "content": output})
        return {"messages": state["messages"] + new_messages, "tool_log": log}

    @staticmethod
    def next_step(state: AgentState) -> str:
        last = state["messages"][-1]
        if last.get("tool_calls") and state["steps"] < MAX_STEPS:
            return "tools"
        return "end"

    def _build(self):
        g = StateGraph(AgentState)
        g.add_node("llm", self.call_llm)
        g.add_node("tools", self.run_tools)
        g.add_edge(START, "llm")
        g.add_conditional_edges("llm", self.next_step, {"tools": "tools", "end": END})
        g.add_edge("tools", "llm")
        return g.compile()


async def load_tools(session: ClientSession) -> list:
    """Turn the MCP server's tool list into the format the LLM expects."""
    listed = await session.list_tools()
    return [
        {"type": "function",
         "function": {"name": t.name, "description": t.description or "",
                      "parameters": t.inputSchema}}
        for t in listed.tools
    ]


async def run_agent(question: str, member_id: str = "M1001", approve=cli_approve) -> dict:
    async with stdio_client(server_for(member_id)) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            agent = CareAgent(session, await load_tools(session), approve)
            state = await agent.graph.ainvoke({
                "messages": [
                    {"role": "system", "content": SYSTEM.format(member_id=member_id)},
                    {"role": "user", "content": question},
                ],
                "steps": 0,
                "tool_log": [],
            })
    last = state["messages"][-1]
    answer = last["content"] if not last.get("tool_calls") else "Stopped: too many steps."
    return {"answer": answer, "tool_log": state["tool_log"], "steps": state["steps"]}


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "Why was my claim C1001-3 denied?"
    result = asyncio.run(run_agent(q))
    print("\nAnswer:\n" + result["answer"])
    print(f"\nTools used ({result['steps']} LLM steps):")
    for t in result["tool_log"]:
        print(f"  - {t['tool']}({t['args']}) approved={t['approved']}")