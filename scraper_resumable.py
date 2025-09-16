import os
import sys
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time

VISITED_FILE = "visited_urls.txt"
QUEUE_FILE = "queue.txt"
OUTPUT_DIR = "juliaconfecciones_scrape"

def load_set_from_file(filename):
    if os.path.exists(filename):
        with open(filename, "r", encoding="latin-1") as f:
            return set(line.strip() for line in f)
    return set()

def load_list_from_file(filename):
    if os.path.exists(filename):
        with open(filename, "r", encoding="latin-1") as f:
            return [line.strip() for line in f]
    return []

def save_to_file(data, filename):
    with open(filename, "w", encoding="utf-8") as f:
        if isinstance(data, set) or isinstance(data, list):
            for item in sorted(list(data)):
                f.write(f"{item}\n")

def scrape(start_url):
    processed_for_links = load_set_from_file(VISITED_FILE)
    queue = load_list_from_file(QUEUE_FILE)

    if not queue:
        queue = [start_url]

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    save_interval = 10
    count = 0

    try:
        while queue:
            url = queue.pop(0)

            if url in processed_for_links:
                continue

            print(f"Processing: {url}")

            parsed_url = urlparse(url)
            path = parsed_url.path
            if not path or path.endswith('/'):
                path += 'index.html'
            
            filename = os.path.join(OUTPUT_DIR, parsed_url.netloc, path.lstrip('/'))

            html_content = None
            if os.path.exists(filename):
                print(f"  - File exists, reading from disk.")
                with open(filename, 'rb') as f:
                    html_content = f.read()
            else:
                try:
                    print(f"  - Downloading...")
                    response = requests.get(url, timeout=10)
                    response.raise_for_status()
                    html_content = response.content
                    os.makedirs(os.path.dirname(filename), exist_ok=True)
                    with open(filename, 'wb') as f:
                        f.write(html_content)
                except requests.RequestException as e:
                    print(f"  - Error fetching {url}: {e}")
                    processed_for_links.add(url) # Mark as processed to avoid retrying
                    continue
            
            if html_content:
                soup = BeautifulSoup(html_content, 'html.parser')
                found_new_link = False
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    joined_url = urljoin(url, href)
                    parsed_joined_url = urlparse(joined_url)

                    if parsed_joined_url.netloc == parsed_url.netloc and joined_url not in processed_for_links and joined_url not in queue:
                        queue.append(joined_url)
                        found_new_link = True
                if found_new_link:
                    print("  - Found new links to follow.")
            
            processed_for_links.add(url)
            count += 1
            if count % save_interval == 0:
                print("Saving progress...")
                save_to_file(processed_for_links, VISITED_FILE)
                save_to_file(queue, QUEUE_FILE)

    finally:
        print("Scraping finished or interrupted. Saving final progress.")
        save_to_file(processed_for_links, VISITED_FILE)
        save_to_file(queue, QUEUE_FILE)
        if not queue and os.path.exists(QUEUE_FILE):
            os.remove(QUEUE_FILE)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scraper_resumable.py <URL>")
        sys.exit(1)
    
    start_url = sys.argv[1]
    # I will first re-parse all existing files to build a complete queue
    # This is the most robust way to do it.
    print("Pre-processing existing files to build a complete queue...")
    all_html_files = []
    for root, dirs, files in os.walk(OUTPUT_DIR):
        for file in files:
            if file.endswith(".html"):
                all_html_files.append(os.path.join(root, file))
    
    processed_for_links = load_set_from_file(VISITED_FILE)
    queue = load_list_from_file(QUEUE_FILE)
    
    for html_file in all_html_files:
        # reconstruct url from file path
        relative_path = os.path.relpath(html_file, OUTPUT_DIR)
        url_path = relative_path.replace("\\", "/")
        parts = url_path.split('/')
        domain = parts[0]
        rest_of_path = '/'.join(parts[1:])
        if rest_of_path.endswith("index.html"):
            rest_of_path = rest_of_path[:-10]
        url = f"http://{domain}/{rest_of_path}"

        if url not in processed_for_links:
            print(f"Re-parsing {url} for links...")
            with open(html_file, 'rb') as f:
                content = f.read()
            soup = BeautifulSoup(content, 'html.parser')
            parsed_url = urlparse(url)
            for link in soup.find_all('a', href=True):
                href = link['href']
                joined_url = urljoin(url, href)
                parsed_joined_url = urlparse(joined_url)
                if parsed_joined_url.netloc == parsed_url.netloc and joined_url not in processed_for_links and joined_url not in queue:
                    queue.append(joined_url)
            processed_for_links.add(url)

    save_to_file(queue, QUEUE_FILE)
    save_to_file(processed_for_links, VISITED_FILE)
    print("Pre-processing finished.")

    scrape(start_url)
