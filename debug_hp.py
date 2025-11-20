import requests
import json

def fetch_itunes(query):
    base_url = "https://itunes.apple.com/search"
    params = {"term": query, "media": "ebook", "limit": 10, "country": "TR"}
    try:
        response = requests.get(base_url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"--- iTunes Results for '{query}' ---")
            if "results" in data:
                for item in data["results"]:
                    print(f"Title: {item.get('trackName')}")
                    print(f"Artist: {item.get('artistName')}")
                    print(f"Kind: {item.get('kind')}")
                    print("-" * 10)
            else:
                print("No results found.")
    except Exception as e:
        print(f"iTunes Exception: {e}")

def fetch_google(query):
    base_url = "https://www.googleapis.com/books/v1/volumes"
    params = {"q": query, "maxResults": 10}
    try:
        response = requests.get(base_url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"--- Google Results for '{query}' ---")
            if "items" in data:
                for item in data["items"]:
                    info = item.get("volumeInfo", {})
                    print(f"Title: {info.get('title')}")
                    print(f"Authors: {info.get('authors')}")
                    print(f"PageCount: {info.get('pageCount')}")
                    print("-" * 10)
    except Exception as e:
        print(f"Google Exception: {e}")

fetch_itunes("Harry Potter")
fetch_google("Harry Potter")
