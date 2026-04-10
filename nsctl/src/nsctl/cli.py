"""nsctl CLI — identity namespace management."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    name="nsctl",
    help="Manage isolated identity namespaces.",
    no_args_is_help=True,
)
console = Console(stderr=True)

# Device subcommand group
device_app = typer.Typer(help="Manage per-device keys and deploy keys.")
app.add_typer(device_app, name="device")


@app.command("list")
def list_cmd(
    root: str | None = typer.Option(
        None, "--root", help="Override namespace root directory"
    ),
) -> None:
    """Show all namespaces."""
    from pathlib import Path

    from nsctl.namespace import list_namespaces

    r = Path(root) if root else None
    namespaces = list_namespaces(r)
    if not namespaces:
        console.print("[dim]No namespaces found.[/dim]")
        return
    table = Table(title="Namespaces")
    table.add_column("Name", style="bold")
    table.add_column("Status")
    table.add_column("Created")
    table.add_column("GPG Fingerprint")
    for ns in namespaces:
        status = "[red]disabled[/red]" if ns.disabled else "[green]active[/green]"
        fpr = (
            ns.keystone_gpg_fingerprint[:16] + "..."
            if len(ns.keystone_gpg_fingerprint) > 16
            else ns.keystone_gpg_fingerprint
        )
        table.add_row(ns.name, status, str(ns.created_at.date()), fpr)
    console.print(table)


@app.command()
def current() -> None:
    """Print the active namespace from $DOTFILES_ID."""
    import os

    ns = os.environ.get("DOTFILES_ID", "")
    if ns:
        typer.echo(ns)
    else:
        console.print("[dim]No active namespace[/dim]")
        raise typer.Exit(1) from None


@app.command()
def new(
    name: str = typer.Argument(..., help="Namespace name"),
    description: str = typer.Option("", help="Description"),
    prompt_color: str = typer.Option(
        "green", "--prompt-color", help="PS1 prompt color"
    ),
    root: str | None = typer.Option(
        None, "--root", help="Override namespace root directory"
    ),
) -> None:
    """Create a new namespace."""
    from pathlib import Path

    from nsctl.namespace import create_namespace

    r = Path(root) if root else None
    try:
        repo_dir = create_namespace(
            name, root=r, description=description, prompt_color=prompt_color
        )
        console.print(f"[green]Created namespace:[/green] {name}")
        console.print(f"  repo: {repo_dir}")
    except FileExistsError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from None


@app.command()
def switch(
    name: str = typer.Argument(..., help="Namespace to activate"),
    root: str | None = typer.Option(
        None, "--root", help="Override namespace root directory"
    ),
) -> None:
    """Print env-var exports for eval by shell wrapper."""
    from pathlib import Path

    from nsctl.switch import generate_switch_env

    r = Path(root) if root else None
    try:
        # Print to stdout (not stderr/console) so eval works
        typer.echo(generate_switch_env(name, root=r))
    except (FileNotFoundError, RuntimeError) as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from None


@app.command()
def deactivate() -> None:
    """Print env-var restores for eval by shell wrapper."""
    from nsctl.switch import generate_deactivate_env

    typer.echo(generate_deactivate_env())


@app.command()
def remove(
    name: str = typer.Argument(..., help="Namespace to remove"),
    force: bool = typer.Option(False, "--force", help="Skip safety checks"),
    root: str | None = typer.Option(
        None, "--root", help="Override namespace root directory"
    ),
) -> None:
    """Remove a namespace and its directories."""
    from pathlib import Path

    from nsctl.namespace import remove_namespace

    r = Path(root) if root else None
    try:
        remove_namespace(name, root=r, force=force)
        console.print(f"[green]Removed namespace:[/green] {name}")
    except (FileNotFoundError, RuntimeError) as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from None


@app.command()
def disable(
    name: str = typer.Argument(...),
    root: str | None = typer.Option(None, "--root"),
) -> None:
    """Disable a namespace (keep files, mark inactive)."""
    from pathlib import Path

    from nsctl.namespace import disable_namespace

    r = Path(root) if root else None
    disable_namespace(name, root=r)
    console.print(f"[yellow]Disabled:[/yellow] {name}")


@app.command()
def enable(
    name: str = typer.Argument(...),
    root: str | None = typer.Option(None, "--root"),
) -> None:
    """Enable a previously disabled namespace."""
    from pathlib import Path

    from nsctl.namespace import enable_namespace

    r = Path(root) if root else None
    enable_namespace(name, root=r)
    console.print(f"[green]Enabled:[/green] {name}")


@app.command()
def sync(
    name: str | None = typer.Argument(
        None, help="Namespace to sync (default: all enabled)"
    ),
    root: str | None = typer.Option(None, "--root"),
) -> None:
    """Sync namespace (git pull --ff-only + audit log)."""
    from pathlib import Path

    from nsctl.namespace import list_namespaces
    from nsctl.sync import sync_namespace

    r = Path(root) if root else None
    if name:
        names = [name]
    else:
        names = [ns.name for ns in list_namespaces(r) if not ns.disabled]
    for n in names:
        try:
            entry = sync_namespace(n, root=r)
            note = f" ({entry.note})" if entry.note else ""
            console.print(f"[green]Synced:[/green] {n}{note}")
        except Exception as e:
            console.print(f"[red]Sync failed for {n}:[/red] {e}")


@app.command()
def doctor(
    root: str | None = typer.Option(None, "--root"),
) -> None:
    """Sanity-check all enabled namespaces."""
    from pathlib import Path

    from nsctl.doctor import run_doctor

    r = Path(root) if root else None
    results = run_doctor(r)
    if not results:
        console.print("[dim]No enabled namespaces to check.[/dim]")
        return
    for health in results:
        icon = {
            "pass": "[green]OK[/green]",
            "warn": "[yellow]WARN[/yellow]",
            "fail": "[red]FAIL[/red]",
        }
        console.print(f"\n[bold]{health.namespace}[/bold] — {icon[health.worst]}")
        for check in health.checks:
            status_str = {
                "pass": "[green]\u2713[/green]",
                "warn": "[yellow]![/yellow]",
                "fail": "[red]\u2717[/red]",
            }
            console.print(f"  {status_str[check.status]} {check.name}: {check.message}")


# --- Stubs for v0.2+ commands ---


@app.command()
def add(name: str = typer.Argument(...)) -> None:
    """Clone an existing namespace onto this device. [v0.2]"""
    console.print(
        "[yellow]nsctl add is not implemented yet (planned for v0.2)[/yellow]"
    )
    raise typer.Exit(1)


@app.command()
def rotate(name: str = typer.Argument(...)) -> None:
    """Rotate keys in a namespace. [v0.2]"""
    console.print(
        "[yellow]nsctl rotate is not implemented yet (planned for v0.2)[/yellow]"
    )
    raise typer.Exit(1)


@app.command()
def lock(name: str = typer.Argument(...)) -> None:
    """Wipe unlocked namespace material from disk. [v0.3]"""
    console.print(
        "[yellow]nsctl lock is not implemented yet (planned for v0.3)[/yellow]"
    )
    raise typer.Exit(1)


@app.command()
def unlock(name: str = typer.Argument(...)) -> None:
    """Re-decrypt namespace material. [v0.3]"""
    console.print(
        "[yellow]nsctl unlock is not implemented yet (planned for v0.3)[/yellow]"
    )
    raise typer.Exit(1)


@device_app.command("add")
def device_add(name: str = typer.Argument(...)) -> None:
    """Add this device to a namespace. [v0.2]"""
    console.print(
        "[yellow]nsctl device add is not implemented yet (planned for v0.2)[/yellow]"
    )
    raise typer.Exit(1)


@device_app.command("remove")
def device_remove(name: str = typer.Argument(...)) -> None:
    """Remove a device from a namespace. [v0.2]"""
    console.print(
        "[yellow]nsctl device remove is not implemented yet (planned for v0.2)[/yellow]"
    )
    raise typer.Exit(1)


@app.command("export")
def export_cmd(name: str = typer.Argument(...)) -> None:
    """Export namespace as encrypted bundle. [v0.4]"""
    console.print(
        "[yellow]nsctl export is not implemented yet (planned for v0.4)[/yellow]"
    )
    raise typer.Exit(1)


@app.command("import")
def import_cmd(name: str = typer.Argument(...)) -> None:
    """Import namespace from encrypted bundle. [v0.4]"""
    console.print(
        "[yellow]nsctl import is not implemented yet (planned for v0.4)[/yellow]"
    )
    raise typer.Exit(1)


@app.command()
def search(term: str = typer.Argument(...)) -> None:
    """Search across all namespace pass entries. [v0.4]"""
    console.print(
        "[yellow]nsctl search is not implemented yet (planned for v0.4)[/yellow]"
    )
    raise typer.Exit(1)


@app.command()
def audit(name: str = typer.Argument(...)) -> None:
    """Show key inventory and rotation status. [v0.3]"""
    console.print(
        "[yellow]nsctl audit is not implemented yet (planned for v0.3)[/yellow]"
    )
    raise typer.Exit(1)


@app.command()
def kill(name: str = typer.Argument(...)) -> None:
    """Emergency: revoke all keys and destroy namespace. [v0.4]"""
    console.print(
        "[yellow]nsctl kill is not implemented yet (planned for v0.4)[/yellow]"
    )
    raise typer.Exit(1)
