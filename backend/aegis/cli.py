"""Interface en ligne de commande d'AegisLLM."""
from __future__ import annotations

import asyncio

import typer
from rich.console import Console

from .attacks.loader import available_categories, load_probes
from .attacks.runner import run_scan
from .config import DEFAULT_CONCURRENCY, DEFAULT_MAX_TOKENS, DEFAULT_TEMPERATURE
from .connectors import build_connector
from .connectors.ollama import OllamaConnector
from .reporting import print_report, save_json

app = typer.Typer(add_completion=False, help="AegisLLM — test de sécurité automatisé des LLM.")
console = Console()


@app.command()
def scan(
    target: str = typer.Option(..., "--target", "-t", help="Cible, p.ex. ollama:llama3:8b"),
    only: str = typer.Option("", "--only", help="Catégories séparées par des virgules (LLM01,jailbreak)"),
    judge: str = typer.Option("", "--judge", help="Modèle juge, p.ex. ollama:llama3:8b"),
    concurrency: int = typer.Option(DEFAULT_CONCURRENCY, "--concurrency", "-c"),
    max_tokens: int = typer.Option(DEFAULT_MAX_TOKENS, "--max-tokens"),
    no_json: bool = typer.Option(False, "--no-json", help="Ne pas écrire le rapport JSON"),
) -> None:
    """Lance une campagne d'attaques sur la cible et affiche le score."""
    only_set = {c.strip() for c in only.split(",") if c.strip()} or None
    probes = load_probes(only=only_set)
    if not probes:
        console.print("[red]Aucune attaque chargée (vérifie --only).[/red]")
        raise typer.Exit(1)

    console.print(
        f"[bold]AegisLLM[/bold] — scan de [cyan]{target}[/cyan] : "
        f"{len(probes)} attaques"
        + (f", juge [cyan]{judge}[/cyan]" if judge else "")
    )

    report = asyncio.run(_run(target, probes, judge, concurrency, max_tokens))

    print_report(report, console)
    if not no_json:
        path = save_json(report)
        console.print(f"\nRapport JSON : [green]{path}[/green]")


async def _run(target, probes, judge, concurrency, max_tokens):
    target_conn = build_connector(target)
    judge_conn = build_connector(judge) if judge else None
    total = sum(len(p.mutations or ["identity"]) for p in probes)

    def on_progress(result, done, _total):
        mark = "[red]✗ vuln[/red]" if result.success else "[green]✓ ok[/green]"
        if result.error:
            mark = "[yellow]! err[/yellow]"
        console.print(f"  [{done}/{total}] {result.owasp} {result.probe_id}/{result.mutation} … {mark}")

    try:
        return await run_scan(
            target_conn, probes, judge=judge_conn, concurrency=concurrency,
            temperature=DEFAULT_TEMPERATURE, max_tokens=max_tokens, on_progress=on_progress,
        )
    finally:
        await target_conn.aclose()
        if judge_conn:
            await judge_conn.aclose()


@app.command()
def models() -> None:
    """Liste les modèles Ollama disponibles en local."""
    try:
        names = asyncio.run(OllamaConnector.list_models())
    except Exception as exc:  # noqa: BLE001
        console.print(f"[red]Ollama injoignable : {exc}[/red]")
        raise typer.Exit(1)
    if not names:
        console.print("Aucun modèle. Essaie : [cyan]ollama pull llama3:8b[/cyan]")
        return
    console.print("[bold]Modèles Ollama locaux :[/bold]")
    for n in names:
        console.print(f"  • {n}")


@app.command()
def categories() -> None:
    """Liste les catégories d'attaques disponibles."""
    for cat in available_categories():
        console.print(f"  • {cat}")


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", "--host"),
    port: int = typer.Option(8000, "--port"),
    reload: bool = typer.Option(False, "--reload"),
    open_browser: bool = typer.Option(True, "--open/--no-open", help="Ouvrir le navigateur"),
) -> None:
    """Démarre AegisLLM : interface web + API (une seule commande)."""
    import uvicorn

    from .config import PROJECT_DIR

    url = f"http://{host}:{port}"
    dist = PROJECT_DIR / "frontend" / "dist"
    if dist.exists():
        console.print(f"[bold]AegisLLM[/bold] — interface + API : [green]{url}[/green]")
    else:
        console.print(f"[bold]AegisLLM[/bold] — API : [green]{url}[/green] (docs : /docs)")
        console.print("[yellow]Interface non construite.[/yellow] Lance une fois : "
                      "[cyan]cd frontend && npm install && npm run build[/cyan]")
    if open_browser and not reload:
        import threading
        import webbrowser
        threading.Timer(1.5, lambda: webbrowser.open(url)).start()
    uvicorn.run("aegis.api.app:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    app()
