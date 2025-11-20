import requests
import concurrent.futures
from bs4 import BeautifulSoup
import difflib
import re

def fetch_google_books(query):
    """
    Fetches book metadata from Google Books API.
    """
    base_url = "https://www.googleapis.com/books/v1/volumes"
    # Check if query is likely an ISBN
    clean_query = query.replace("-", "").replace(" ", "")
    if clean_query.isdigit() and len(clean_query) in [10, 13]:
        params = {"q": f"isbn:{clean_query}"}
    else:
        params = {
            "q": query,
            "maxResults": 40,
            "printType": "books",
            "orderBy": "relevance"
        }
    
    try:
        # 1. Standard Search
        response = requests.get(base_url, params=params, timeout=5)
        results = []
        
        if response.status_code == 200:
            data = response.json()
            if "items" in data:
                for item in data["items"]:
                    parsed = parse_google_book(item)
                    if parsed:
                        results.append(parsed)

        # 2. Author Search (to catch translations like "Kendinizin CEO'su olun")
        # Only if query looks like a name (no numbers, reasonable length)
        if not any(char.isdigit() for char in query) and len(query.split()) < 5:
            params_author = params.copy()
            params_author["q"] = f"inauthor:{query}"
            try:
                response_author = requests.get(base_url, params=params_author, timeout=5)
                if response_author.status_code == 200:
                    data_author = response_author.json()
                    if "items" in data_author:
                        for item in data_author["items"]:
                            # Avoid duplicates
                            parsed = parse_google_book(item)
                            if parsed and not any(r["title"] == parsed["title"] and r["author"] == parsed["author"] for r in results):
                                results.append(parsed)
            except Exception as e:
                print(f"Google Books Author Search Error: {e}")

    except Exception as e:
        print(f"Google Books Error: {e}")
        return []
        
    return results

def parse_google_book(item):
    book = item.get("volumeInfo", {})
    
    title = book.get("title")
    authors_list = book.get("authors")
    publisher = book.get("publisher", "Bilinmeyen Yayınevi")
    
    if not title:
        return None
    
    # Allow books without authors, but label them
    authors = ", ".join(authors_list) if authors_list else "Bilinmeyen Yazar"
    
    isbn = "Bilinmiyor"
    if "industryIdentifiers" in book:
        for identifier in book["industryIdentifiers"]:
            if identifier["type"] == "ISBN_13":
                isbn = identifier["identifier"]
                break
            elif identifier["type"] == "ISBN_10":
                isbn = identifier["identifier"]
    
    cover_url = ""
    if "imageLinks" in book:
        cover_url = book["imageLinks"].get("thumbnail", "")
    
    summary = book.get("description", "Özet bulunmuyor.")
    page_count = book.get("pageCount", 0)
    published_date = book.get("publishedDate", "")
    
    info_link = book.get("infoLink", "")
    if not info_link:
        info_link = book.get("canonicalVolumeLink", "")

    return {
        "title": title,
        "author": authors,
        "isbn": isbn,
        "cover_url": cover_url,
        "summary": summary,
        "page_count": page_count,
        "publisher": publisher,
        "published_date": published_date,
        "source": "Google Books",
        "link": info_link
    }

def fetch_open_library(query):
    """
    Fetches book metadata from Open Library API.
    """
    base_url = "https://openlibrary.org/search.json"
    
    # Check for ISBN
    clean_query = query.replace("-", "").replace(" ", "")
    if clean_query.isdigit() and len(clean_query) in [10, 13]:
         params = {"q": clean_query}
    else:
        params = {
            "q": query,
            "limit": 20
        }
    
    try:
        response = requests.get(base_url, params=params, timeout=5)
        results = []
        
        if response.status_code == 200:
            data = response.json()
            if "docs" in data:
                for item in data["docs"]:
                    title = item.get("title")
                    author_name = item.get("author_name", ["Bilinmeyen Yazar"])
                    
                    if not title:
                        continue
                        
                    authors = ", ".join(author_name) if isinstance(author_name, list) else author_name
                    
                    isbn = "Bilinmiyor"
                    if "isbn" in item and len(item["isbn"]) > 0:
                        isbn = item["isbn"][0]
                    
                    cover_url = ""
                    if "cover_i" in item:
                        cover_url = f"https://covers.openlibrary.org/b/id/{item['cover_i']}-M.jpg"
                    
                    summary = "Özet bulunmuyor."
                    page_count = item.get("number_of_pages_median", 0)
                    publisher = item.get("publisher", ["Bilinmeyen Yayınevi"])
                    if isinstance(publisher, list):
                        publisher = publisher[0]
                    
                    publish_date_list = item.get("publish_date", [])
                    published_date = publish_date_list[0] if isinstance(publish_date_list, list) and publish_date_list else ""

                    key = item.get("key", "")
                    link = f"https://openlibrary.org{key}" if key else ""

                    results.append({
                        "title": title,
                        "author": authors,
                        "isbn": isbn,
                        "cover_url": cover_url,
                        "summary": summary,
                        "page_count": page_count,
                        "publisher": publisher,
                        "published_date": published_date,
                        "source": "Open Library",
                        "link": link
                    })
    except Exception as e:
        print(f"Open Library Error: {e}")
        return []
        
    return results

def fetch_itunes_books(query):
    """
    Fetches book metadata from iTunes Search API (Apple Books).
    """
    base_url = "https://itunes.apple.com/search"
    params = {
        "term": query,
        "media": "ebook",
        "limit": 20,
        "country": "TR" # Search in Turkish store
    }
    
    try:
        response = requests.get(base_url, params=params, timeout=5)
        results = []
        
        if response.status_code == 200:
            data = response.json()
            if "results" in data:
                for item in data["results"]:
                    title = item.get("trackName")
                    author_name = item.get("artistName")
                    
                    if not title:
                        continue
                    
                    authors = author_name if author_name else "Bilinmeyen Yazar"
                        
                    isbn = "Bilinmiyor"
                    cover_url = item.get("artworkUrl100", "").replace("100x100", "600x600")
                    summary = item.get("description", "Özet bulunmuyor.")
                    page_count = 0
                    publisher = item.get("artistName", "Apple Books")
                    link = item.get("trackViewUrl", "")
                    published_date = item.get("releaseDate", "")[:10]

                    results.append({
                        "title": title,
                        "author": authors,
                        "isbn": isbn,
                        "cover_url": cover_url,
                        "summary": summary,
                        "page_count": page_count,
                        "publisher": publisher,
                        "published_date": published_date,
                        "source": "Apple Books",
                        "link": link
                    })
    except Exception as e:
        print(f"iTunes Error: {e}")
        return []
        
    return results

def fetch_kitapyurdu(query):
    """
    Fetches book metadata from Kitapyurdu.
    """
    base_url = "https://www.kitapyurdu.com/index.php"
    params = {
        "route": "product/search",
        "filter_name": query
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    results = []
    try:
        response = requests.get(base_url, params=params, headers=headers, timeout=8)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            products = soup.select('.product-cr')[:5] # Limit to top 5
            
            for product in products:
                try:
                    name_tag = product.select_one('.name span')
                    title = name_tag.text.strip() if name_tag else "Bilinmeyen Kitap"
                    
                    link_tag = product.select_one('.name a')
                    link = link_tag['href'] if link_tag else ""
                    
                    img_tag = product.select_one('.image img')
                    cover_url = img_tag['src'] if img_tag else ""
                    
                    # Author
                    author_tag = product.select_one('.author span a span')
                    author = author_tag.text.strip() if author_tag else "Bilinmeyen Yazar"
                    
                    # Publisher
                    publisher_tag = product.select_one('.publisher span a span')
                    publisher = publisher_tag.text.strip() if publisher_tag else "Bilinmeyen Yayınevi"
                    
                    # Fetch details
                    summary = "Özet bulunmuyor."
                    page_count = 0
                    isbn = "Bilinmiyor"
                    
                    if link:
                        try:
                            detail_resp = requests.get(link, headers=headers, timeout=5)
                            if detail_resp.status_code == 200:
                                detail_soup = BeautifulSoup(detail_resp.text, 'html.parser')
                                
                                # Summary - Try multiple selectors
                                desc_tag = detail_soup.select_one('#description_text')
                                if not desc_tag:
                                    desc_tag = detail_soup.select_one('.info__text')
                                if not desc_tag:
                                    desc_tag = detail_soup.select_one('.product-info-text')
                                
                                # Fallback to meta description
                                if not desc_tag:
                                    meta_desc = detail_soup.find('meta', attrs={'name': 'description'})
                                    if meta_desc:
                                        summary = meta_desc.get('content', '')

                                if desc_tag:
                                    summary = desc_tag.get_text(strip=True)
                                
                                # Clean up summary and check for bad data
                                if summary:
                                    # Check for the specific error string reported by user
                                    if "Kitapyurdu'ndan bulundu" in summary or "bulundu" in summary.lower() and len(summary) < 50:
                                        summary = "Özet bulunmuyor."
                                    
                                    # If summary is still empty or default
                                    if not summary or summary == "Özet bulunmuyor.":
                                         # Try to get from meta description if we haven't already
                                         meta_desc = detail_soup.find('meta', attrs={'name': 'description'})
                                         if meta_desc:
                                             summary = meta_desc.get('content', '')

                                
                                # Attributes
                                attr_rows = detail_soup.select('.attributes table tr')
                                for row in attr_rows:
                                    cols = row.select('td')
                                    if len(cols) == 2:
                                        key = cols[0].get_text(strip=True)
                                        val = cols[1].get_text(strip=True)
                                        if "Sayfa Sayısı" in key:
                                            try: page_count = int(val)
                                            except: pass
                                        elif "ISBN" in key:
                                            isbn = val.replace("-", "")
                        except Exception as e:
                            print(f"Detail fetch error: {e}")

                    results.append({
                        "title": title,
                        "author": author,
                        "isbn": isbn,
                        "cover_url": cover_url,
                        "summary": summary,
                        "page_count": page_count,
                        "publisher": publisher,
                        "published_date": "",
                        "source": "Kitapyurdu",
                        "link": link
                    })
                except Exception as e:
                    print(f"Error parsing kitapyurdu item: {e}")
                    continue
                    
    except Exception as e:
        print(f"Kitapyurdu Error: {e}")
        
    return results

def get_book_metadata(query):
    """
    Fetches book metadata from multiple sources in parallel.
    Uses a scoring system to rank results instead of strict filtering.
    """
    results = []
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_google = executor.submit(fetch_google_books, query)
        future_openlib = executor.submit(fetch_open_library, query)
        future_itunes = executor.submit(fetch_itunes_books, query)
        future_kitapyurdu = executor.submit(fetch_kitapyurdu, query)
        
        for future in concurrent.futures.as_completed([future_google, future_openlib, future_itunes, future_kitapyurdu]):
            try:
                data = future.result()
                results.extend(data)
            except Exception as e:
                print(f"API Error: {e}")

    # Scoring and Deduplication
    scored_results = []
    seen_keys = set()
    
    query_lower = query.lower()
    query_words = [w for w in query_lower.split() if len(w) > 1]
    
    for book in results:
        title = book["title"]
        author = book["author"]
        publisher = book["publisher"]
        
        # Deduplication Key
        key = (title.lower(), author.lower())
        if key in seen_keys:
            continue
        seen_keys.add(key)
        
        # Calculate Score
        score = 0
        title_lower = title.lower()
        author_lower = author.lower()
        
        # Filter out bad results
        # 1. Corporate Authors
        bad_authors = ["inc", "corp", "ltd", "studio", "staff", "entertainment", "warner bros"]
        if any(bad in author_lower for bad in bad_authors):
            score -= 100 # Heavy penalty
            
        # 2. Zero Page Count (unless it's a very strong match otherwise)
        if book["page_count"] == 0:
            score -= 20
        else:
            score += 10 # Bonus for having page count
            
        # 3. Fuzzy Similarity Score (Replaces exact/word match)
        # Calculates how similar the query is to the title (0-100 points)
        similarity = difflib.SequenceMatcher(None, query_lower, title_lower).ratio() * 100
        score += similarity
        
        # Extra bonus if it starts with the query
        if title_lower.startswith(query_lower):
            score += 20

        # 4. Cover Image Bonus
        if book["cover_url"]:
            score += 10

        # 4. Turkish Character Bonus (to further prioritize local content)
        tr_chars = ['ç', 'ğ', 'ı', 'ö', 'ş', 'ü', 'Ç', 'Ğ', 'I', 'Ö', 'Ş', 'Ü']
        if any(char in title for char in tr_chars) or any(char in author for char in tr_chars):
            score += 20
            
        # 5. Source Bonus (Kitapyurdu is usually better for Turkish books)
        if book["source"] == "Kitapyurdu":
            score += 30

        # 6. Non-Book Item Penalty (Generic filter for all searches)
        # Filters out coloring books, movie guides, calendars, summaries, etc.
        non_book_keywords = [
            "boyama", "film", "rehber", "ajanda", "takvim", "poster", "çıkartma", 
            "dehlizi", "popüler kültür", "özet", "notlar", "sınav", "hazırlık", 
            "analiz", "inceleme", "kılavuz"
        ]
        if any(keyword in title_lower for keyword in non_book_keywords):
            score -= 40

        # 7. Generic Author Quality Check
        # Penalize generic or corporate authors
        generic_authors = ["kolektif", "komisyon", "editör", "staff", "unknown", "bilinmeyen", "inc", "corp"]
        if any(gen in author_lower for gen in generic_authors):
            score -= 15
            
        # Store score
        book["score"] = score
        scored_results.append(book)
    
    # Sort by score descending
    scored_results.sort(key=lambda x: x["score"], reverse=True)
    
    # Filter out very low scores
    final_results = [b for b in scored_results if b["score"] > 0]
    
    return final_results
