import requests
import json

def fetch_google_books(query):
    base_url = "https://www.googleapis.com/books/v1/volumes"
    params = {
        "q": query,
        "maxResults": 40,
        "printType": "books",
        "orderBy": "relevance"
    }
    try:
        response = requests.get(base_url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"--- Google Books Results for '{query}' (Max 40) ---")
            if "items" in data:
                for item in data["items"]:
                    info = item.get("volumeInfo", {})
                    print(f"Title: {info.get('title')}, Authors: {info.get('authors')}")
            else:
                print("No items found.")
        else:
            print(f"Google Books Error: {response.status_code}")
    except Exception as e:
        print(f"Google Books Exception: {e}")

def check_openlibrary_isbn(isbn):
    url = f"https://openlibrary.org/isbn/{isbn}.json"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print("Found in Open Library by ISBN!")
            print(response.json())
        else:
            print(f"Not found in Open Library by ISBN: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")

check_openlibrary_isbn("9786055422950")





