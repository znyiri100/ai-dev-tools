import os
import requests
import zipfile
import minsearch
from fastmcp import FastMCP

mcp = FastMCP("Demo 🚀")

# Search initialization logic
def download_and_extract():
    url = "https://github.com/jlowin/fastmcp/archive/refs/heads/main.zip"
    zip_path = "fastmcp-main.zip"
    
    if not os.path.exists(zip_path):
        # Only download if not exists (simple caching)
        response = requests.get(url)
        with open(zip_path, "wb") as f:
            f.write(response.content)
            
    return zip_path

def get_documents():
    zip_path = download_and_extract()
    documents = []
    
    with zipfile.ZipFile(zip_path, 'r') as z:
        for file_info in z.infolist():
            if file_info.is_dir():
                continue
            
            if not (file_info.filename.endswith(".md") or file_info.filename.endswith(".mdx")):
                continue
                
            # Remove first part of path
            parts = file_info.filename.split("/", 1)
            if len(parts) > 1:
                filename = parts[1]
            else:
                filename = file_info.filename
                
            with z.open(file_info) as f:
                content = f.read().decode("utf-8")
                
            documents.append({
                "filename": filename,
                "content": content
            })
            
    return documents

def build_index(documents):
    index = minsearch.Index(
        text_fields=["content", "filename"],
        keyword_fields=[]
    )
    
    index.fit(documents)
    return index

# Initialize index on startup
documents = get_documents()
search_index = build_index(documents)


@mcp.tool
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

def fetch_page_markdown(url: str) -> str:
    """Fetch page content as markdown using Jina Reader."""
    jina_url = f"https://r.jina.ai/{url}"
    response = requests.get(jina_url)
    response.raise_for_status()
    return response.text


@mcp.tool
def scrape_web(url: str) -> str:
    """Scrape a web page and return its content in markdown format."""
    return fetch_page_markdown(url)


@mcp.tool
def search_documentation(query: str) -> str:
    """Search the FastMCP documentation for a given query."""
    results = search_index.search(
        query=query,
        filter_dict={},
        boost_dict={"filename": 1, "content": 1},
        num_results=5
    )
    
    output = []
    for result in results:
        output.append(f"File: {result['filename']}\nContent Preview: {result['content'][:200]}...\n")
        
    return "\n---\n".join(output)


if __name__ == "__main__":
    mcp.run()

