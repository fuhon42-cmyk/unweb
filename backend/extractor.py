import json
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from backend.schemas import ExtractResponse


def _clean_text(text: str) -> str:
    return re.sub(r'\s+', ' ', text).strip()


def _remove_unwanted(soup: BeautifulSoup) -> None:
    for selector in ['script', 'style', 'nav', 'footer', 'header', 'aside',
                     'noscript', 'iframe', 'svg', 'form',
                     '[class*="ad"]', '[class*="sidebar"]', '[class*="comment"]',
                     '[id*="ad"]', '[id*="sidebar"]', '[id*="comment"]']:
        for tag in soup.select(selector):
            tag.decompose()


def _extract_title(soup: BeautifulSoup) -> str:
    og = soup.select_one('meta[property="og:title"]')
    if og and og.get('content'):
        return _clean_text(og['content'])
    tag = soup.select_one('title')
    if tag and tag.string:
        return _clean_text(tag.string)
    h1 = soup.select_one('h1')
    if h1:
        return _clean_text(h1.get_text())
    return ''


def _extract_description(soup: BeautifulSoup) -> str:
    og = soup.select_one('meta[property="og:description"]')
    if og and og.get('content'):
        return _clean_text(og['content'])
    meta = soup.select_one('meta[name="description"]')
    if meta and meta.get('content'):
        return _clean_text(meta['content'])
    return ''


def _extract_main_content(soup: BeautifulSoup) -> str:
    for selector in ['article', 'main', '[role="main"]', 'body']:
        container = soup.select_one(selector)
        if container:
            texts = [t for t in container.stripped_strings]
            if texts:
                return '\n\n'.join(texts)
    return _clean_text(soup.get_text())


def _extract_opengraph(soup: BeautifulSoup) -> dict:
    og_data = {}
    for meta in soup.select('meta[property^="og:"]'):
        prop = meta.get('property')
        content = meta.get('content')
        if prop and content:
            og_data[prop] = content
    return og_data


def _extract_jsonld(soup: BeautifulSoup) -> list:
    results = []
    for script in soup.select('script[type="application/ld+json"]'):
        try:
            data = json.loads(script.string)
            results.append(data if isinstance(data, list) else [data])
        except (json.JSONDecodeError, TypeError):
            pass
    return [item for sublist in results for item in sublist]


def _extract_schema_org(soup: BeautifulSoup) -> list:
    results = []
    for item in soup.select('[itemscope][itemtype]'):
        item_type = item.get('itemtype', '')
        props = {}
        for prop in item.select('[itemprop]'):
            name = prop.get('itemprop', '')
            val = prop.get('content') or prop.get('src') or prop.get('href') or _clean_text(prop.get_text())
            if name:
                props[name] = val
        if item_type:
            results.append({'@type': item_type, 'properties': props})
    return results


def _detect_actions(soup: BeautifulSoup, base_url: str) -> list[str]:
    actions = []
    login_patterns = re.compile(r'log\s*in|sign\s*in|login|登入|登录', re.IGNORECASE)
    for a in soup.select('a[href]'):
        href = a.get('href', '')
        text = a.get_text()
        if login_patterns.search(text) or login_patterns.search(href):
            full_url = urljoin(base_url, href)
            actions.append(f'login: {full_url}')
    for form in soup.select('form'):
        method = form.get('method', 'get').upper()
        action = form.get('action', '')
        full_url = urljoin(base_url, action)
        actions.append(f'search_form: {method} {full_url}')
    cta_pattern = re.compile(r'\b(btn|cta)\b', re.IGNORECASE)
    for el in soup.select('[class*="btn"], [class*="cta"], a[class*="btn"], a[class*="cta"], button[class*="btn"], button[class*="cta"]'):
        class_str = ' '.join(el.get('class', []))
        if cta_pattern.search(class_str):
            text = _clean_text(el.get_text())
            if text:
                href = el.get('href', '') if isinstance(el, Tag) and el.name == 'a' else ''
                full_url = urljoin(base_url, href) if href else ''
                actions.append(f'cta: {text} -> {full_url}' if full_url else f'cta: {text}')
    return actions


async def extract_content(html: str, url: str) -> ExtractResponse:
    soup = BeautifulSoup(html, 'html.parser')

    _remove_unwanted(soup)

    title = _extract_title(soup)
    description = _extract_description(soup)
    content = _extract_main_content(soup)

    og_data = _extract_opengraph(soup)
    jsonld = _extract_jsonld(soup)
    schema_org = _extract_schema_org(soup)

    structured_data = {
        'opengraph': og_data,
        'jsonld': jsonld,
        'schema_org': schema_org,
    }

    actions = _detect_actions(soup, url)

    word_count = len(content.split())

    metadata = {
        'url': url,
        'word_count': word_count,
        'og_image': og_data.get('og:image', ''),
    }

    return ExtractResponse(
        title=title,
        description=description,
        content=content,
        structured_data=structured_data,
        actions=actions,
        metadata=metadata,
    )
