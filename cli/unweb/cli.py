import sys
import subprocess
from pathlib import Path
from typing import Optional

import click
import httpx
from rich import print as rprint
from rich.console import Console
import json
from rich.table import Table
from rich.panel import Panel

console = Console()

API_URL = "http://localhost:8000"


@click.group()
@click.option("--api-url", "-a", default=API_URL, help="Base URL for the API")
@click.option("--api-key", "-k", envvar="UNWEB_API_KEY", help="API key")
@click.pass_context
def cli(ctx, api_url: str, api_key: Optional[str]):
    ctx.ensure_object(dict)
    ctx.obj["api_url"] = api_url.rstrip("/")
    ctx.obj["api_key"] = api_key


def _headers(ctx) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    key = ctx.obj.get("api_key")
    if key:
        headers["X-API-Key"] = key
    return headers


def _client(ctx) -> httpx.Client:
    return httpx.Client(
        base_url=ctx.obj["api_url"],
        headers=_headers(ctx),
        timeout=60,
    )


@cli.command()
@click.argument("url")
@click.pass_context
def extract(ctx, url: str):
    """Extract structured content from a URL."""
    with _client(ctx) as client:
        try:
            resp = client.post("/api/v1/extract", json={"url": url})
        except httpx.ConnectError:
            console.print("[red]Could not connect to API server.[/]")
            raise click.Abort()
    if resp.is_error:
        _error(resp)
        raise click.Abort()

    data = resp.json()
    panel = Panel(
        json.dumps(data, indent=2),
        title=f"[bold]{data.get('title', 'Untitled')}[/]",
        subtitle=url,
    )
    console.print(panel)


@cli.command()
@click.argument("url")
@click.option(
    "--content", "-c",
    help="Content body (omit to read from stdin)",
)
@click.option("--name", "-n", help="Site name (defaults to domain)")
@click.pass_context
def publish(ctx, url: str, content: Optional[str], name: Optional[str]):
    """Publish structured content for a URL as an LLMS site."""
    if not content:
        console.print("[dim]Reading content from stdin...[/]")
        content = sys.stdin.read()

    if not name:
        from urllib.parse import urlparse
        name = urlparse(url).netloc or "untitled"

    with _client(ctx) as client:
        try:
            resp = client.post(
                "/api/v1/publish",
                json={"url": url, "content": content, "site_name": name},
            )
        except httpx.ConnectError:
            console.print("[red]Could not connect to API server.[/]")
            raise click.Abort()
    if resp.is_error:
        _error(resp)
        raise click.Abort()

    data = resp.json()
    table = Table(title="Published")
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="green")
    for k, v in data.items():
        table.add_row(k, str(v))
    console.print(table)


@cli.command()
@click.pass_context
def serve(ctx):
    """Start the Unweb backend server."""
    backend_path = Path(__file__).resolve().parent.parent.parent / "backend"
    if not (backend_path / "main.py").exists():
        console.print("[red]backend/main.py not found.[/]")
        raise click.Abort()
    cmd = [
        sys.executable, "-m", "uvicorn", "backend.main:app",
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8000",
    ]
    console.print("[dim]Starting Unweb API server...[/]")
    subprocess.run(cmd, cwd=backend_path.parent)


@cli.command()
@click.pass_context
def status(ctx):
    """Check API server health."""
    with _client(ctx) as client:
        try:
            resp = client.get("/api/v1/health")
        except httpx.ConnectError:
            console.print("[red]API server is not reachable.[/]")
            raise click.Abort()
    if resp.is_error:
        _error(resp)
        raise click.Abort()

    data = resp.json()
    table = Table(show_header=False)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    for k, v in data.items():
        table.add_row(k, str(v))
    console.print(table)


def _error(resp: httpx.Response):
    try:
        detail = resp.json().get("detail", resp.text)
    except Exception:
        detail = resp.text
    console.print(f"[red]Error {resp.status_code}:[/] {detail}")


@click.command("search")
@click.argument("query")
@click.option("--max-results", "-n", default=3, help="Number of results")
@click.pass_context
def search_cmd(ctx, query: str, max_results: int):
    """Search the web and get a summarized report."""
    with _client(ctx) as client:
        console.print(f"[dim]Searching: {query}...[/]")
        try:
            resp = client.post("/api/v1/search", json={"query": query, "max_results": max_results})
        except httpx.ConnectError:
            console.print("[red]API server is not reachable.[/]")
            raise click.Abort()
    if resp.is_error:
        _error(resp)
        raise click.Abort()

    data = resp.json()
    console.print(Panel(data["summary"], title=f"[bold]🔍 {query}[/]", border_style="green"))
    if data["key_points"]:
        console.print("\n[bold]Key Points:[/]")
        for pt in data["key_points"]:
            console.print(f"  • {pt}")
    if data["sources"]:
        console.print("\n[bold]Sources:[/]")
        for s in data["sources"]:
            console.print(f"  [{s.get('relevance','?')}] {s['title']}")

cli.add_command(search_cmd)


@click.command("proxy")
@click.option("--port", "-p", default=8080, help="Proxy port")
@click.pass_context
def proxy_cmd(ctx, port: int):
    """Start local proxy — auto-structure all web traffic for AI agents."""
    from .proxy import main as proxy_main
    import sys
    sys.argv = ["unweb-proxy", "--port", str(port)]
    proxy_main()

cli.add_command(proxy_cmd)


main = cli
