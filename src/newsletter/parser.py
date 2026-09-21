from bs4 import BeautifulSoup
import re

def is_image_artifact(line):
    lower = line.lower().strip()
    if lower in {
        "newsletter logo",
        "sponsor logo",
    }:
        return True
    if lower.startswith("sponsor logo:"):
        return True

    image_starts = [
        "illustration of ",
        "image of ",
        "photo of ",
    ]

    if any(lower.startswith(prefix) for prefix in image_starts):
        return True
    
    if lower in {
        "unsplash", 
        "getty images",
        "shutterstock",
        "reuters",
        "associated press",
    }:
        return True
    return False

def html_to_text(html):
    if not html:
        return ""
    
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup([
        "script",
        "style",
        "head",
        "noscript",
        "svg",
    ]):
        tag.decompose()

    for img in soup.find_all("img"):
        img.decompose()
    
    text = soup.get_text(separator="\n")
    return clean_text(text)

def clean_plain_text(text):
    if not text:
        return ""
    
    if(
        "<html" in text.lower() 
        or "<body" in text.lower()
        or "<a" in text.lower() 
        or "<img " in text.lower()
    ):
        return html_to_text(text)

    return clean_text(text)

def clean_text(text):
    lines =[]
    for line in text.splitlines():
        line = re.sub(r"\s+", " ", line).strip()
        if not line:
            continue
        if is_image_artifact(line):
            continue
        lines.append(line)
    return "\n".join(lines)