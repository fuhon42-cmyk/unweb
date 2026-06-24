import httpx
from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse
from typing import Optional


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:134.0) Gecko/20100101 Firefox/134.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
]

_robot_parsers: dict[str, tuple[RobotFileParser, bool]] = {}


def _get_robots_parser(base_url: str) -> RobotFileParser:
    parsed = urlparse(base_url)
    key = f"{parsed.scheme}://{parsed.netloc}"
    if key not in _robot_parsers:
        rp = RobotFileParser()
        rp.set_url(f"{key}/robots.txt")
        try:
            rp.read()
            ok = True
        except Exception:
            ok = False
        _robot_parsers[key] = (rp, ok)
    return _robot_parsers[key][0]


def _can_fetch(url: str, user_agent: str) -> bool:
    rp = _get_robots_parser(url)
    return rp.can_fetch(user_agent, url)


async def fetch_url(url: str, user_agent_index: int = 0) -> dict:
    """Fetch a URL asynchronously with User-Agent rotation and robots.txt respect.

    Args:
        url: The target URL to fetch.
        user_agent_index: Index into USER_AGENTS list for rotation.

    Returns:
        A dict with keys:
            - html (str): The response text.
            - status_code (int): HTTP status code (0 if request failed).
            - content_type (str): Content-Type header value.
            - final_url (str): The final URL after redirects.
    """
    user_agent = USER_AGENTS[user_agent_index % len(USER_AGENTS)]

    if not _can_fetch(url, user_agent):
        return {
            "html": "",
            "status_code": -1,
            "content_type": "",
            "final_url": url,
        }

    headers = {"User-Agent": user_agent}
    transport = httpx.AsyncHTTPTransport(retries=1)
    async with httpx.AsyncClient(transport=transport, timeout=15.0, follow_redirects=True) as client:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return {
                "html": response.text,
                "status_code": response.status_code,
                "content_type": response.headers.get("content-type", ""),
                "final_url": str(response.url),
            }
        except httpx.TimeoutException:
            return {
                "html": "",
                "status_code": 0,
                "content_type": "",
                "final_url": url,
            }
        except httpx.HTTPStatusError as e:
            return {
                "html": "",
                "status_code": e.response.status_code,
                "content_type": e.response.headers.get("content-type", ""),
                "final_url": str(e.response.url),
            }
        except httpx.ConnectError:
            return {
                "html": "",
                "status_code": 0,
                "content_type": "",
                "final_url": url,
            }


