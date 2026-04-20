import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))

from rich.console import Console
import diagnostic_tool.system as system
import diagnostic_tool.network as network
import diagnostic_tool.scanner as scanner
import diagnostic_tool.security as security
import diagnostic_tool.utils as utils

def run_full_diagnostic(console=None):
    """
    Exécute tous les diagnostics sans interaction utilisateur et retourne les résultats sous forme de texte.
    """
    if console is None:
        from rich.console import Console
        console = Console()
    output = []
    output.append("[bold cyan]Diagnostic Système[/bold cyan]")
    output.append(str(system.analyse_systeme(console)))
    output.append("\n[bold cyan]Diagnostic Réseau[/bold cyan]")
    output.append(str(network.analyse_reseau(console)))
    output.append("\n[bold cyan]Scan de ports[/bold cyan]")
    output.append(str(scanner.scan_ports_menu(console, auto_all=True)))
    output.append("\n[bold cyan]Scan réseau local[/bold cyan]")
    output.append(str(scanner.scan_reseau_local(console, auto_all=True)))
    output.append("\n[bold cyan]Analyse sécurité[/bold cyan]")
    output.append(str(security.analyse_securite(console)))
    return "\n".join(output)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--batch":
        console = Console()
        print(run_full_diagnostic(console))
    else:
        from diagnostic_tool.__main__ import main_menu
        main_menu()
