import json
from rich.prompt import Prompt

def export_results(console, history):
    if not history:
        console.print("[yellow]Aucun résultat à exporter.[/yellow]")
        return
    fmt = Prompt.ask("Format d'export [json/csv]", choices=["json", "csv"], default="json")
    fname = Prompt.ask("Nom du fichier", default="diagnostic_export")
    if fmt == "json":
        with open(fname + ".json", "w") as f:
            json.dump(history, f, indent=2)
        console.print(f"[green]Exporté vers {fname}.json[/green]")
    else:
        import csv
        with open(fname + ".csv", "w", newline='') as f:
            writer = csv.writer(f)
            for entry in history:
                writer.writerow([str(entry)])
        console.print(f"[green]Exporté vers {fname}.csv[/green]")
