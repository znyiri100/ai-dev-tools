import os
import requests
import sys

proxy = os.getenv("HTTP_PROXY")
# Mask password for printing
if proxy and "@" in proxy:
    user_pass, host = proxy.split("@")
    print(f"Proxy from env: ...@{host}")
else:
    print(f"Proxy from env: {proxy}")

proxies = None # Rely on environment variables

try:
    print("Attempting request to https://www.google.com ...")
    resp = requests.get("https://www.google.com", proxies=proxies, timeout=10)
    print(f"Success: {resp.status_code}")
except Exception as e:
    print(f"Error: {e}")
