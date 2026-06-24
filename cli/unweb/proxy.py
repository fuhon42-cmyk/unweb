"""Unweb local proxy — transparently structures web content for AI agents.

Start with: unweb proxy
AI agents configure: HTTP_PROXY=http://localhost:8080
All HTML responses are automatically converted to structured JSON.
"""

import asyncio
import json
import os
import sys
from urllib.parse import urlparse

import httpx


class UnwebProxy:
    """HTTP proxy that intercepts web requests and returns Unweb-structured JSON."""

    def __init__(self, api_url: str = "https://unweb-production-6f69.up.railway.app", api_key: str = "any"):
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key

    async def handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        try:
            request_line = await asyncio.wait_for(reader.readline(), timeout=30)
            if not request_line:
                writer.close()
                return

            line = request_line.decode()
            parts = line.split()
            if len(parts) < 2:
                writer.close()
                return
            method, url = parts[0], parts[1]

            # Only intercept GET requests to http/https URLs
            if method != "GET" or not (url.startswith("http://") or url.startswith("https://")):
                await self._passthrough(reader, writer, method, url)
                return

            parsed = urlparse(url)

            # Skip non-HTML resources
            path = parsed.path.lower()
            if any(path.endswith(ext) for ext in ['.js', '.css', '.png', '.jpg', '.ico', '.woff2', '.svg', '.json']):
                await self._passthrough(reader, writer, request_line, method, url)
                return

            # Call Unweb API to structure this URL
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.post(
                        f"{self.api_url}/api/v1/extract",
                        json={"url": url},
                        headers={"X-API-Key": self.api_key},
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        # Wrap in markdown-like format that agents understand
                        structured = self._format_for_agent(data)
                        await self._send_response(writer, structured, "application/json")
                        return
            except Exception:
                pass

            # Fallback: pass through
            await self._passthrough(reader, writer, request_line, method, url)

        except Exception:
            pass
        finally:
            try:
                writer.close()
            except Exception:
                pass

    def _format_for_agent(self, data: dict) -> str:
        """Format extracted data as agent-friendly text."""
        llm = data.get("structured_data", {}).get("llm", {})
        parts = [
            f"# {data.get('title', 'Untitled')}",
            f"",
            f"**URL:** {data.get('metadata', {}).get('url', '')}",
            f"",
        ]
        if llm.get("summary"):
            parts.append(f"## Summary\n{llm['summary']}")
            parts.append("")
        parts.append(f"## Content\n{data.get('content', '')[:5000]}")
        parts.append("")
        if data.get("actions"):
            parts.append(f"## Actions\n" + "\n".join(f"- {a}" for a in data["actions"]))
        return json.dumps({"text": "\n".join(parts), "structured": data})

    async def _send_response(self, writer, body: str, content_type: str = "text/plain"):
        encoded = body.encode()
        response = (
            f"HTTP/1.1 200 OK\r\n"
            f"Content-Type: {content_type}\r\n"
            f"Content-Length: {len(encoded)}\r\n"
            f"X-Unweb: structured\r\n"
            f"\r\n"
        ).encode() + encoded
        writer.write(response)
        await writer.drain()

    async def _passthrough(self, reader, writer, request_line, method, url):
        """Read remaining headers and return a redirect/error."""
        while True:
            line = await reader.readline()
            if line in (b"\r\n", b"\n", b""):
                break
        body = json.dumps({"error": "passthrough", "url": url.decode()})
        await self._send_response(writer, body)

    async def start(self, host: str = "127.0.0.1", port: int = 8080):
        server = await asyncio.start_server(self.handle, host, port)
        print(f"🔌 Unweb proxy running on {host}:{port}")
        print(f"   Configure AI agents: HTTP_PROXY=http://{host}:{port}")
        print(f"   All web requests will be auto-structured.")
        print(f"   Press Ctrl+C to stop.")
        async with server:
            await server.serve_forever()


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Unweb Proxy — transparent AI-ready web access")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--api-url", default=os.environ.get("UNWEB_API_URL", "https://unweb-production-6f69.up.railway.app"))
    parser.add_argument("--api-key", default=os.environ.get("UNWEB_API_KEY", "any"))
    args = parser.parse_args()

    proxy = UnwebProxy(api_url=args.api_url, api_key=args.api_key)
    try:
        asyncio.run(proxy.start(args.host, args.port))
    except KeyboardInterrupt:
        print("\n👋 Proxy stopped.")


if __name__ == "__main__":
    main()
