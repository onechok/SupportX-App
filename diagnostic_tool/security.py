from .scanner import COMMON_PORTS
import psutil
from rich.console import Console

def analyse_securite(console: Console):
    alerts = []
    # Ports sensibles ouverts
    open_ports = []
    for conn in psutil.net_connections():
        if conn.status == psutil.CONN_LISTEN and conn.laddr.port in COMMON_PORTS:
            open_ports.append(conn.laddr.port)
    if open_ports:
        alerts.append(f"Ports sensibles ouverts: {open_ports}")
    # Connexions suspectes (exemple: ports élevés, IP inconnues)
    for conn in psutil.net_connections():
        if conn.status == psutil.CONN_ESTABLISHED and conn.raddr and conn.raddr.ip not in ("127.0.0.1",):
            alerts.append(f"Connexion suspecte: {conn.raddr.ip}:{conn.raddr.port}")
    if not alerts:
        console.print("[green]Aucun risque détecté.[/green]")
    else:
        for alert in alerts:
            console.print(f"[red]{alert}[/red]")
    return {"alerts": alerts}
