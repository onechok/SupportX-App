# SupportX App

Application desktop SupportX multi-OS (Linux, macOS, Windows).

## Installation en 3 clics

### 1. Ouvrir le dossier du projet
- Placez le dossier SupportX-App où vous voulez le conserver.

### 2. Lancer l'installateur (double-clic)
- Linux: `install-supportx.sh`
- macOS: `install-supportx.command`
- Windows: `install-supportx.bat`

L'installateur:
- crée/réutilise l'environnement Python local (`.venv`),
- installe les dépendances,
- crée un raccourci bureau,
- ajoute un raccourci application (menu système).

### 3. Ouvrir l'application via le raccourci
- Linux: `SupportX.desktop`
- macOS: `SupportX.command`
- Windows: `SupportX` (raccourci bureau/menu démarrer)

## Lancement manuel (optionnel)
- Linux/macOS: `start-supportx.sh` ou `start-supportx.command`
- Windows: `start-supportx.bat`

## Prérequis
- Python 3.10+
- Sur Linux Debian/Ubuntu: `python3-tk` peut être nécessaire.

## Release
- Les releases sont publiées automatiquement via GitHub Actions lors d'un push de tag `v*`.
