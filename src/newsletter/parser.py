from bs4 import BeautifulSoup
import re

# drop the end/footer part of the email
FOOTER_MARKERS = [
    "unsubscribe",
    "manage your preferences",
    "update your preferences",
    "privacy policy",
]

NOISE_PATTERNS =[
    r"^newsletter logo$",
    r"^sponsor logo$",
    r"^illustration of",
    r"^image of",
    r"^photo of",
    r"^click here$",
    r"^view in browser$",
]

def remove_html_noise(soup):
    for tag in soup([
        "script",
        "style",
        "head",
        "noscript",
        "svg",
    ]):
        tag.decompose()

    for img in soup.find_all("img"):
        parent = img.parent
        if parent and parent.name == "a":
            parent.decompose()
        else:
            img.decompose()
    return soup

def clean_lines(text):
    cleaned = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        line = re.sub(r"\s+", " ", line)

        if any(re.match(pattern, line, re.IGNORECASE) for pattern in NOISE_PATTERNS):
            continue

        cleaned.append(line)
    return cleaned

def remove_footer(lines):
    for i, line in enumerate(lines):
        lower = line.lower()
        if any(marker in lower for marker in FOOTER_MARKERS):
            return lines[:i]
        
    return lines

def html_to_text(html):
    soup = BeautifulSoup(html, "html.parser")
    soup = remove_html_noise(soup)

    text = soup.get_text(separator="\n")

    lines = clean_lines(text)
    lines = remove_footer(lines)
    return "\n".join(lines)

def clean_plain_text(text):
    lines = clean_lines(text)
    lines = remove_footer(lines)
    
    return "\n".join(lines)