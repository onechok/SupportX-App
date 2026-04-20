import psutil
import socket
import requests
from rich.table import Table

def get_public_ip():
    try:
        return requests.get('https://api.ipify.org').text
    except Exception:
        return "Non disponible"

def analyse_reseau(console):
    table = Table(title="Analyse Réseau")
    table.add_column("Propriété")
    table.add_column("Valeur")
    # IP locale
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    table.add_row("Nom d'hôte", hostname)
    table.add_row("IP locale", local_ip)
    table.add_row("IP publique", get_public_ip())
    # Interfaces
    for name, iface in psutil.net_if_addrs().items():
        ips = ", ".join([i.address for i in iface if i.family == socket.AF_INET])
        table.add_row(f"Interface {name}", ips)
    # Connexions actives
    conns = psutil.net_connections()
    table.add_row("Connexions actives", str(len(conns)))
    # Bande passante (approx)
    io = psutil.net_io_counters()
    table.add_row("Octets envoyés", str(io.bytes_sent))
    table.add_row("Octets reçus", str(io.bytes_recv))
    # Ping google
    import subprocess
    try:
        output = subprocess.check_output(["ping", "-c", "1", "8.8.8.8"], universal_newlines=True)
        latency = [l for l in output.splitlines() if "time=" in l]
        table.add_row("Latence Google", latency[0].split("time=")[-1] if latency else "N/A")
    except Exception:
        table.add_row("Latence Google", "Erreur")
    console.print(table)
    return dict(local_ip=local_ip, public_ip=get_public_ip())
