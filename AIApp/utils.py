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

def fetch_data_from_url(url, visited_urls=None, depth=0, max_depth=5):
    if visited_urls is None:
        visited_urls = {}

    if depth > max_depth:
        visited_urls[url] = {
            "id": len(visited_urls) + 1,
            "status": "not processed",
            "url": url,
            "title": None,
            "characters": 0,
            "chunks_count": 0,
            "created_at": datetime.now().isoformat()
        }
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
        visited_urls[url] = {
            "id": len(visited_urls) + 1,
            "status": "not processed",
            "url": url,
            "title": None,
            "characters": 0,
            "chunks_count": 0,
            "created_at": datetime.now().isoformat()
        }
        print(f"Error fetching {url}: {e}")
        return f"Error fetching {url}: {e}", visited_urls

    html_content = response.text
    soup = BeautifulSoup(html_content, 'html.parser')

    title = soup.title.string if soup.title else "No title"
    text = soup.get_text()
    characters = len(text)
    chunks_count = characters // 1000  # Assuming 1000 characters per chunk as an example

    visited_urls[url] = {
        "id": len(visited_urls) + 1,
        "status": "processed",
        "url": url,
        "title": title,
        "characters": characters,
        "chunks_count": chunks_count,
        "created_at": datetime.now().isoformat()
    }

    images = [urljoin(url, img_tag.get('src')) for img_tag in soup.find_all('img') if img_tag.get('src')]
    links = [urljoin(url, link_tag['href']) for link_tag in soup.find_all('a', href=True)]

    content = f"\nText from {url}:\n{text}"
    if images:
        content += "\nImages:\n" + "\n".join(images)
    if links:
        content += "\nLinks:\n" + "\n".join(links)

    for link in links:
        if link not in visited_urls:
            nested_content, visited_urls = fetch_data_from_url(link, visited_urls, depth + 1, max_depth)
            content += f"\n\nThe content in the link {link} is:\n{nested_content}"

    print(content)
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
