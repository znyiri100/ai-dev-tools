import os
import requests
import zipfile
import io
import minsearch

def download_and_extract():
    url = "https://github.com/jlowin/fastmcp/archive/refs/heads/main.zip"
    zip_path = "fastmcp-main.zip"
    
    if not os.path.exists(zip_path):
        print("Downloading zip...")
        response = requests.get(url)
        with open(zip_path, "wb") as f:
            f.write(response.content)
    else:
        print("Zip already exists.")
        
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
            # e.g. fastmcp-main/docs/welcome.mdx -> docs/welcome.mdx
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

def main():
    documents = get_documents()
    print(f"Indexed {len(documents)} documents.")
    
    index = build_index(documents)
    
    query = "demo"
    results = index.search(
        query=query,
        filter_dict={},
        boost_dict={"filename": 1, "content": 1},
        num_results=5
    )
    
    print("\nSearch results for 'demo':")
    for i, result in enumerate(results):
        print(f"{i+1}. {result['filename']}")
        # print(result['content'][:100])
        
    if results:
        print(f"\nFirst result: {results[0]['filename']}")

if __name__ == "__main__":
    main()
