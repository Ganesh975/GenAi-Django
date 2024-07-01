import io
import fitz  # PyMuPDF
import requests
from PIL import Image
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime

def extract_text(page):
    try:
        text = page.get_text()
        return text
    except Exception as e:
        print(f"Error extracting text: {e}")
        return ""

def extract_images(pdf_document, page):
    images = []
    try:
        image_list = page.get_images(full=True)
        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = pdf_document.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            image = Image.open(io.BytesIO(image_bytes))
            images.append((img_index + 1, image_ext, image))
    except Exception as e:
        print(f"Error extracting images: {e}")
    return images

def extract_links(page):
    try:
        links = page.get_links()
        link_info = [link.get('uri') for link in links]
        return link_info
    except Exception as e:
        print(f"Error extracting links: {e}")
        return []
    
    
import re

def filter_links_by_pattern(url, links):
  """Filters links based on a pattern match with the main URL's domain.

  Args:
      url (str): The main URL.
      links (list): A list of links to be filtered.

  Returns:
      list: A new list containing only links that match the pattern.
  """

  # Extract the domain name from the main URL
  domain_pattern = r'^[^/]*://([^/]+)'  # Matches protocol and domain (e.g., https://www.example.com)
  domain_match = re.match(domain_pattern, url)
  if not domain_match:
    raise ValueError("Failed to extract domain name from main URL")
  domain_name = domain_match.group(1)

  # Create the regular expression pattern to match links with the same domain
  pattern = r'\b' + re.escape(domain_name) + r'\b'  # Matches exact domain name boundaries

  # Filter links based on the pattern
  filtered_links = []
  for link in links:
    if re.search(pattern, link):
      filtered_links.append(link)

  return filtered_links


import re
def fetch_data_from_url(url,visited_urls_list=None, visited_urls=None, depth=0, max_depth=3):
    if visited_urls is None:
        visited_urls = []
    if visited_urls_list is None:
        visited_urls_list =[]

    if depth > max_depth:
        visited_urls_list.append(url)
        visited_urls.append({
            "id": len(visited_urls) + 1,
            "status": "not processed",
            "status_message": None,
            "url": url,
            "title": None,
            "filename_original": None,
            "retrain_initiated_at": None,
            "characters": 0,
            "text": None,
            "chunks_count": 0,
            "created_at": datetime.now().isoformat()
        })

        return "Max depth reached", visited_urls

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        visited_urls_list.append(url)
        visited_urls.append({
            "id": len(visited_urls) + 1,
            "status": "not processed",
            "status_message": str(e),
            "url": url,
            "title": None,
            "filename_original": None,
            "retrain_initiated_at": None,
            "characters": 0,
            "text": None,
            "chunks_count": 0,
            "created_at": datetime.now().isoformat()
        })

        print(f"Error fetching {url}: {e}")
        return f"Error fetching {url}: {e}", visited_urls

    html_content = response.text
    soup = BeautifulSoup(html_content, 'html.parser')

    title = soup.title.string if soup.title else "No title"
    text = soup.get_text()
    characters = len(text)
    chunks_count = characters // 1000  # Assuming 1000 characters per chunk as an example
    visited_urls_list.append(url)
    visited_urls.append({
        "id": len(visited_urls) + 1,
        "status": "processed",
        "status_message": None,
        "url": url,
        "title": title,
        "filename_original": None,
        "retrain_initiated_at": None,
        "characters": characters,
        "text": None,
        "chunks_count": chunks_count,
        "created_at": datetime.now().isoformat()
    })


    images = [urljoin(url, img_tag.get('src')) for img_tag in soup.find_all('img') if img_tag.get('src')]
    links = [urljoin(url, link_tag['href']) for link_tag in soup.find_all('a', href=True)]

    
    links = filter_links_by_pattern(url, links)
    
    content = f"\nText from {url}:\n{text}"
    if images:
        content += "\nImages:\n" + "\n".join(images)
    if links:
        content += "\nLinks:\n" + "\n".join(links)

    for link in links:
        
        if (link not in visited_urls_list) :
                nested_content, visited_urls = fetch_data_from_url(link,visited_urls_list, visited_urls, depth + 1, max_depth)
                content += f"\n\nThe content in the link {link} is:\n{nested_content}"
    print(visited_urls_list)
    return content, visited_urls

def select_and_read_pdf(pdf_file):
    try:
        pdf_document = fitz.open(stream=pdf_file.read(), filetype="pdf")
        print(f"Reading PDF")

        pdf_content = ""

        for page_num in range(pdf_document.page_count):
            page = pdf_document.load_page(page_num)
            pdf_content += f"\n--- Page {page_num + 1} ---\n"

            text = extract_text(page)
            pdf_content += "\nText:\n" + text

            links = extract_links(page)
            if links:
                pdf_content += "\nLinks:\n"
                for link in links:
                    pdf_content += f"Link: {link}\n"
                    fetched_data, _ = fetch_data_from_url(link)
                    if fetched_data:
                        pdf_content += fetched_data + "\n"
        return pdf_content
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return None
from nltk.tokenize import sent_tokenize, word_tokenize

def split_text(description, max_tokens):
    sentences = sent_tokenize(description)
    parts = []
    current_part = []
    current_part_token_count = 0
    
    for sentence in sentences:
        words = word_tokenize(sentence)
        word_count = len(words)
        
        if current_part_token_count + word_count > max_tokens:
            parts.append(' '.join(current_part))
            current_part = words
            current_part_token_count = word_count
        else:
            current_part.extend(words)
            current_part_token_count += word_count
    
    # Add the last part
    if current_part:
        parts.append(' '.join(current_part))
    
    return parts
