import asyncio
# You need to install the 'mcp' package: pip install mcp
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    # Define the command to start the YouTube MCP server.
    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "@sinco-lab/mcp-youtube-transcript"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()

            # List available tools to confirm connection
            tools = await session.list_tools()
            print(f"Connected! Available tools: {[t.name for t in tools.tools]}")
            
            # Print the definition of get_transcripts
            gt_tool = next(t for t in tools.tools if t.name == "get_transcripts")
            print(f"Tool definition: {gt_tool}")

            # Define the URL of the video to process
            video_url = "https://www.youtube.com/watch?v=EMd3H0pNvSE"

            # Call the 'get_transcripts' tool
            print(f"\nFetching transcript for: {video_url}...")
            result = await session.call_tool(
                "get_transcripts",
                arguments={"url": video_url}
            )

            # Print the result
            if result.content:
                print("\n--- Transcript Snippet ---")
                # The content is usually a list of TextContent or similar
                print(result.content[0].text[:500] + "...")
            else:
                print("No content returned.")

if __name__ == "__main__":
    asyncio.run(main())
