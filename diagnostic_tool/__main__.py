import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))

from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table
from rich.progress import track
import sys
import json
import os
import diagnostic_tool.system as system
import diagnostic_tool.network as network
import diagnostic_tool.scanner as scanner
import diagnostic_tool.security as security
import diagnostic_tool.utils as utils

console = Console()
history = []

def main_menu():
    while True:
        console.print("[bold cyan]Outil de Diagnostic Système & Réseau[/bold cyan]")
        console.print("1. Analyse système")
        console.print("2. Analyse réseau")
        console.print("3. Scan de ports")
        console.print("4. Scan réseau local")
        console.print("5. Analyse sécurité")
        console.print("6. Exporter les résultats")
        console.print("7. Quitter")
        choice = Prompt.ask("Choix", choices=[str(i) for i in range(1,8)])
        if choice == "1":
            res = system.analyse_systeme(console)
            history.append({"system": res})
        elif choice == "2":
            res = network.analyse_reseau(console)
            history.append({"network": res})
        elif choice == "3":
            res = scanner.scan_ports_menu(console)
            history.append({"ports": res})
        elif choice == "4":
            res = scanner.scan_reseau_local(console)
            history.append({"lan": res})
        elif choice == "5":
            res = security.analyse_securite(console)
            history.append({"security": res})
        elif choice == "6":
            utils.export_results(console, history)
        elif choice == "7":
            console.print("[bold green]Au revoir ![/bold green]")
            break

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        console.print("\n[red]Interruption utilisateur.[/red]")
