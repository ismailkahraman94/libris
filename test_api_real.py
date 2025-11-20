import api
import time

print("Testing api.get_book_metadata...")
results = api.get_book_metadata("Harry Potter ve Felsefe Taşı")
print(f"Found {len(results)} results.")

for r in results:
    if r['source'] == 'Kitapyurdu':
        print(f"Title: {r['title']}")
        print(f"Summary: {r['summary'][:50]}...")
        print(f"Link: {r['link']}")
        print("-" * 20)
