import asyncio
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def run_client():
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "main.py"],
        env=None
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize connection
            await session.initialize()

            # List available tools
            tools = await session.list_tools()
            print("\n=== Available Tools ===")
            for tool in tools.tools:
                print(f"- {tool.name}: {tool.description}")

            # Example: Search documentation
            print("\n=== Testing 'search_documentation' ===")
            search_query = "demo"
            print(f"Searching for: '{search_query}'")
            
            result = await session.call_tool("search_documentation", arguments={"query": search_query})
            print("\n--- Search Results ---")
            for content in result.content:
                if content.type == "text":
                    print(content.text[:100])

            # Example: Add numbers
            print("\n=== Testing 'add' ===")
            a, b = 10, 5
            print(f"Adding {a} + {b}")
            add_result = await session.call_tool("add", arguments={"a": a, "b": b})
            for content in add_result.content:
                 if content.type == "text":
                    print(f"Result: {content.text}")

if __name__ == "__main__":
    asyncio.run(run_client())
