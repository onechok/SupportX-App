# SupportX App

Application desktop SupportX multi-OS (Linux, macOS, Windows).

## Installation en 3 clics

### Option recommandee Windows (installateur .exe)
1. Telechargez `SupportX-Setup-vX.Y.Z.exe` depuis la release GitHub.
2. Lancez l'installeur puis suivez l'assistant.
3. Ouvrez `SupportX App` depuis le Bureau ou le menu Demarrer.

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
- sur Windows, vérifie Python et tente son installation automatique via winget si nécessaire.

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

## Windows: parcours recommandé
1. Clic droit sur `install-supportx.bat` puis Exécuter en tant qu'administrateur (recommandé).
2. L'installeur vérifie Python puis:
	- utilise Python existant si disponible,
	- sinon tente l'installation via winget.
3. Installe uniquement les dépendances nécessaires (PySide6 + requests), sans pywebview/pythonnet.
4. Une fois terminé, utilisez le raccourci `SupportX` créé sur le bureau.

Si Windows SmartScreen bloque le script:
- cliquer sur Informations complémentaires,
- puis Exécuter quand même.

Si l'installation pip échoue:
- l'installeur s'arrête immédiatement,
- corrigez l'erreur affichée puis relancez `install-supportx.bat`.

## Release
- Les releases sont publiées automatiquement via GitHub Actions lors d'un push de tag `v*`.
