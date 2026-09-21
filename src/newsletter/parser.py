from bs4 import BeautifulSoup
import re

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
        lines.append(line)
    return "\n".join(lines)