from main import fetch_page_markdown

def solve_q4():
    url = "https://datatalks.club/"
    print(f"Scraping {url}...")
    content = fetch_page_markdown(url)
    
    # "Count how many times the word 'data' appears"
    # The search should probably be case-insensitive or exact? Usually "word" implies checking for the string.
    # The prompt says "word 'data'", usually implying substrings or exact matches. 
    # Let's count the substring "data" (case-insensitive is safer usually, but let's try exact lower case first or just count occurrences).
    # "Count how many times the word "data" appears"
    
    count = content.lower().count("data")
    print(f"Occurrences of 'data' (case-insensitive): {count}")

if __name__ == "__main__":
    solve_q4()
