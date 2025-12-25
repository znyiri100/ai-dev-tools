from main import fetch_page_markdown

def test_scraper():
    url = "https://github.com/alexeygrigorev/minsearch"
    print(f"Scraping {url}...")
    content = fetch_page_markdown(url)

    print(f"Content length: {len(content)}")
    # Print the first 100 characters to verify
    print("Beginning of content:")
    print(content[:100])

if __name__ == "__main__":
    test_scraper()
