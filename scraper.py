
import os
import sys
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

def scrape(url, output_dir, visited):
    if url in visited:
        return
    visited.add(url)

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return

    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Create a valid filename for the URL
    parsed_url = urlparse(url)
    path = parsed_url.path
    if path.endswith('/'):
        path += 'index.html'
    
    # Handle case where path is empty (root URL)
    if not path or path == '/':
        path = '/index.html'

    filename = os.path.join(output_dir, parsed_url.netloc, path.lstrip('/'))
    
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    with open(filename, 'wb') as f:
        f.write(response.content)
    print(f"Saved {url} to {filename}")

    for link in soup.find_all('a', href=True):
        href = link['href']
        joined_url = urljoin(url, href)
        parsed_joined_url = urlparse(joined_url)

        if parsed_joined_url.netloc == parsed_url.netloc:
            scrape(joined_url, output_dir, visited)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scraper.py <URL>")
        sys.exit(1)
    
    start_url = sys.argv[1]
    output_directory = "juliaconfecciones_scrape"
    
    visited_urls = set()
    scrape(start_url, output_directory, visited_urls)
