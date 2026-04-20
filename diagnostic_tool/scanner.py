import socket
import psutil
from rich.table import Table
from rich.progress import track

COMMON_PORTS = [21, 22, 23, 80, 443, 3389]

def scan_ports_menu(console, auto_all=False):
    if auto_all:
        host = "127.0.0.1"
        ports = COMMON_PORTS
    else:
        host = console.input("IP à scanner (laisser vide pour localhost): ") or "127.0.0.1"
        mode = console.input("Mode [r]apide (ports courants) ou [c]complet (1-65535)? [r/c]: ").lower()
        if mode == "c":
            ports = range(1, 65536)
        else:
            ports = COMMON_PORTS
    results = []
    table = Table(title=f"Scan de ports sur {host}")
    table.add_column("Port")
    table.add_column("Etat")
    for port in track(ports, description="Scan des ports..."):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            try:
                s.connect((host, port))
                table.add_row(str(port), "[green]OUVERT[/green]")
                results.append(port)
            except Exception:
                table.add_row(str(port), "[red]FERME[/red]")
    console.print(table)
    return {"host": host, "open_ports": results}

def scan_reseau_local(console, auto_all=False):
    import ipaddress, subprocess
    if auto_all:
        local_ip = "127.0.0.1"
    else:
        local_ip = psutil.net_if_addrs()['lo'][0].address if 'lo' in psutil.net_if_addrs() else "127.0.0.1"
    net = ipaddress.ip_network(local_ip + '/24', strict=False)
    table = Table(title="Scan réseau local")
    table.add_column("IP")
    table.add_column("Etat")
    for ip in track(net.hosts(), description="Scan IP..."):
        ip_str = str(ip)
        try:
            subprocess.check_output(["ping", "-c", "1", "-W", "1", ip_str], stderr=subprocess.DEVNULL)
            table.add_row(ip_str, "[green]Actif[/green]")
        except Exception:
            pass
    console.print(table)
    return {"scanned_net": str(net)}
