import re

def extract_website_name(url):
    # Remove protocol
    url = re.sub(r'^https?://', '', url)
    # Remove www.
    url = re.sub(r'^www\.', '', url)
    # Remove path, query, fragment
    url = url.split('/')[0]
    # Remove port
    url = url.split(':')[0]
    # Remove TLDs (handles .co.uk, .com, .org, etc.)
    parts = url.split('.')
    if len(parts) > 2:
        # e.g. sub.domain.com or domain.co.uk
        if parts[-2] in ['co', 'com', 'org', 'net', 'gov', 'edu']:
            name = parts[-3]
        else:
            name = parts[-2]
    else:
        name = parts[0]
    return name
