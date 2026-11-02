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

def remove_footer(text):
    # remove footers
    footer_markers=[
        "brew's best",
        "share the brew",
        "referrals get rewarded",
        "a note from chase",
        "get smarter in just 5 minutes",
        "take the brew to work",
        "interested in podcasts?",
        "was this email forwarded to you?",
    ]
    lines=text.splitlines()
    cleaned_lines=[]
    for line in lines:
        lower = line.lower().strip()
        if any(marker in lower for marker in footer_markers):
            break
        cleaned_lines.append(line)
    return "\n".join(cleaned_lines)

# change html text/script to plain text
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
    
    if any(
        marker in text.lower() for marker in ["<html", "<body", "<a", "<img "]
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
    text= "\n".join(lines)
    return remove_footer(text)