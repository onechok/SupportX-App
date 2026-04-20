import platform
import psutil
from rich.table import Table

def analyse_systeme(console):
    table = Table(title="Analyse Système")
    table.add_column("Propriété")
    table.add_column("Valeur")

    uname = platform.uname()
    table.add_row("OS", f"{uname.system} {uname.release} ({uname.version})")
    table.add_row("Noyau", uname.version)
    table.add_row("Machine", uname.machine)
    table.add_row("Processeur", uname.processor)
    table.add_row("Cœurs physiques", str(psutil.cpu_count(logical=False)))
    table.add_row("Cœurs logiques", str(psutil.cpu_count(logical=True)))
    table.add_row("Utilisation CPU (%)", f"{psutil.cpu_percent(interval=1)}%")
    svmem = psutil.virtual_memory()
    table.add_row("RAM totale", f"{svmem.total // (1024**2)} Mo")
    table.add_row("RAM utilisée", f"{svmem.used // (1024**2)} Mo")
    table.add_row("RAM libre", f"{svmem.available // (1024**2)} Mo")
    for i, disk in enumerate(psutil.disk_partitions()):
        usage = psutil.disk_usage(disk.mountpoint)
        table.add_row(f"Disque {disk.device}", f"{usage.used // (1024**3)} Go / {usage.total // (1024**3)} Go ({usage.percent}%)")
    # Processus actifs
    proc_count = len(psutil.pids())
    table.add_row("Processus actifs", str(proc_count))
    # Services (Windows) ou daemons (Linux)
    try:
        if platform.system() == "Windows":
            import wmi
            c = wmi.WMI()
            services = [s.Name for s in c.Win32_Service() if s.State == "Running"]
        else:
            services = [s.name() for s in psutil.process_iter(['name']) if 'd' in s.name()]
        table.add_row("Services actifs", str(len(services)))
    except Exception:
        table.add_row("Services actifs", "Non disponible")
    console.print(table)
    return dict(OS=uname.system, CPU=uname.processor, RAM=svmem.total, Disks=[d.device for d in psutil.disk_partitions()])
