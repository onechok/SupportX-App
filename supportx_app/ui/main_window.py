from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
import webbrowser
from pathlib import Path

import requests
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QStatusBar,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parents[2]))

try:
    from ..config import AppConfig, normalize_url
    from ..theme import stylesheet_for
    from ..updates import UpdateInfo, UpdateService
    from ..web.overlay_view import OverlayWebView
except ImportError:
    from supportx_app.config import AppConfig, normalize_url
    from supportx_app.theme import stylesheet_for
    from supportx_app.updates import UpdateInfo, UpdateService
    from supportx_app.web.overlay_view import OverlayWebView


class MainWindow(QMainWindow):
    def __init__(self, app_dir: Path) -> None:
        super().__init__()
        self.app_dir = app_dir
        self.config_path = app_dir / "config.json"
        self.config = AppConfig.load(self.config_path)
        self._pending_update: UpdateInfo | None = None

        self.setWindowTitle(f"{self.config.app_name} - v{self.config.app_version}")
        self.resize(1360, 840)
        self.setMinimumSize(1100, 720)

        self._build_ui()
        self.apply_theme(self.config.theme)

        if self.config.auto_update:
            QTimer.singleShot(1200, lambda: self.check_for_updates(manual=False))

    def _build_ui(self) -> None:
        self.status = QStatusBar()
        self.setStatusBar(self.status)

        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        content = QWidget()
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        content_layout.addWidget(self._build_sidebar())

        self.stack = QStackedWidget()
        self.stack.setObjectName("contentStack")
        self.web_page = self._build_web_page()
        self.anydesk_page = self._build_anydesk_page()
        self.settings_page = self._build_settings_page()
        self.about_page = self._build_about_page()

        self.stack.addWidget(self.web_page)
        self.stack.addWidget(self.anydesk_page)
        self.stack.addWidget(self.settings_page)
        self.stack.addWidget(self.about_page)
        content_layout.addWidget(self.stack, 1)

        root_layout.addWidget(content, 1)
        self.setCentralWidget(root)

        self.menuBar().hide()
        self.status.showMessage(f"Pret • {self.config.app_name} • Version {self.config.app_version}")
        self._set_active_page(0)

    def _build_sidebar(self) -> QWidget:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(250)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        app_title = QLabel(self.config.app_name)
        app_title.setObjectName("sidebarTitle")
        app_version = QLabel(f"v{self.config.app_version}")
        app_version.setObjectName("sidebarSubtitle")
        layout.addWidget(app_title)
        layout.addWidget(app_version)

        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)

        for index, label in enumerate(["SupportX Web", "AnyDesk", "Parametres", "A propos"]):
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setObjectName("navButton")
            btn.clicked.connect(lambda checked=False, i=index: self._set_active_page(i))
            self.nav_group.addButton(btn, index)
            layout.addWidget(btn)

        layout.addStretch(1)

        quick_open = QPushButton("Ouvrir dans le navigateur")
        quick_open.setObjectName("secondaryButton")
        quick_open.clicked.connect(self.open_in_browser)
        layout.addWidget(quick_open)
        return sidebar

    def _set_active_page(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        button = self.nav_group.button(index)
        if button:
            button.setChecked(True)

    def _build_web_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        self.web_widget = OverlayWebView(self.config.supportx_url, self.status.showMessage)
        layout.addWidget(self.web_widget)
        return page

    def _build_anydesk_page(self) -> QWidget:
        page = QWidget()
        layout = QGridLayout(page)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(12)

        info_card = self._card("Installation AnyDesk")
        info = info_card.layout()
        info_text = QLabel(
            "Telechargez puis installez AnyDesk directement depuis cette page. "
            "Le mot de passe administrateur peut etre requis pendant l'installation."
        )
        info_text.setWordWrap(True)
        info_text.setObjectName("cardHeadline")
        info.addWidget(info_text)

        self.anydesk_status = QLabel("Statut: pret")
        self.anydesk_status.setWordWrap(True)
        self.anydesk_status.setObjectName("mutedLabel")
        info.addWidget(self.anydesk_status)

        actions_card = self._card("Actions")
        actions = actions_card.layout()

        btn_download = QPushButton("Telecharger AnyDesk")
        btn_download.clicked.connect(self.download_anydesk)

        btn_install = QPushButton("Installer AnyDesk")
        btn_install.clicked.connect(self.install_anydesk)

        btn_open_site = QPushButton("Ouvrir le site officiel")
        btn_open_site.clicked.connect(lambda: webbrowser.open("https://anydesk.com/fr/downloads/linux"))

        actions.addWidget(btn_download)
        actions.addWidget(btn_install)
        actions.addWidget(btn_open_site)

        layout.addWidget(info_card, 0, 0)
        layout.addWidget(actions_card, 0, 1)
        layout.setColumnStretch(0, 3)
        layout.setColumnStretch(1, 2)
        return page

    def _build_settings_page(self) -> QWidget:
        page = QWidget()
        layout = QGridLayout(page)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(12)

        appearance = self._card("Apparence")
        ap = appearance.layout()
        ap.addWidget(QLabel("Mode de theme"))

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["system", "light", "dark"])
        self.theme_combo.setCurrentText(self.config.theme)
        self.theme_combo.currentTextChanged.connect(self.change_theme)
        ap.addWidget(self.theme_combo)

        updates = self._card("Mises a jour")
        up = updates.layout()
        self.auto_update_check = QCheckBox("Verifier automatiquement les mises a jour")
        self.auto_update_check.setChecked(self.config.auto_update)
        self.auto_update_check.toggled.connect(self.save_auto_update_setting)

        self.simulate_check = QCheckBox("Activer le mode simulation")
        self.simulate_check.setChecked(self.config.simulate_updates)
        self.simulate_check.toggled.connect(self.save_simulate_setting)

        self.check_update_btn = QPushButton("Verifier maintenant")
        self.check_update_btn.clicked.connect(lambda: self.check_for_updates(manual=True))

        self.install_update_btn = QPushButton("Installer la mise a jour")
        self.install_update_btn.setEnabled(False)
        self.install_update_btn.clicked.connect(self.install_pending_update)

        up.addWidget(self.auto_update_check)
        up.addWidget(self.simulate_check)
        up.addWidget(self.check_update_btn)
        up.addWidget(self.install_update_btn)

        self.update_status_label = QLabel("Derniere verification: jamais")
        self.update_status_label.setWordWrap(True)
        self.update_status_label.setObjectName("mutedLabel")
        up.addWidget(self.update_status_label)

        actions = self._card("Navigation Web")
        ac = actions.layout()
        web_reload = QPushButton("Recharger SupportX")
        web_reload.clicked.connect(self.web_widget.web.reload)
        open_external = QPushButton("Ouvrir page courante dans le navigateur")
        open_external.clicked.connect(self.web_widget.open_external)
        ac.addWidget(web_reload)
        ac.addWidget(open_external)

        layout.addWidget(appearance, 0, 0)
        layout.addWidget(updates, 0, 1)
        layout.addWidget(actions, 1, 0, 1, 2)
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)
        return page

    def _build_about_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        title = QLabel("SupportX App")
        title.setObjectName("heroTitle")
        subtitle = QLabel(f"Version {self.config.app_version}")
        subtitle.setObjectName("cardHeadline")

        details = QTextEdit()
        details.setReadOnly(True)
        details.setPlainText(
            "Architecture modulaire:\n\n"
            "- supportx_app/config.py: configuration\n"
            "- supportx_app/updates.py: verification et orchestration updater\n"
            "- supportx_app/updater/: sous-application de mise a jour\n"
            "- supportx_app/web/: composant navigateur integre\n"
            "- supportx_app/ui/main_window.py: interface principale\n"
        )

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(details)
        return page

    def _card(self, title: str) -> QFrame:
        frame = QFrame()
        frame.setObjectName("card")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        header = QLabel(title)
        header.setObjectName("cardTitle")
        layout.addWidget(header)
        return frame

    def apply_theme(self, mode: str) -> None:
        self.setStyleSheet(stylesheet_for(mode))

    def change_theme(self, value: str) -> None:
        self.config.theme = value
        self.config.save(self.config_path)
        self.apply_theme(value)
        self.status.showMessage("Theme applique")

    def save_auto_update_setting(self, state: bool) -> None:
        self.config.auto_update = bool(state)
        self.config.save(self.config_path)
        self.status.showMessage("Mises a jour automatiques sauvegardees")

    def save_simulate_setting(self, state: bool) -> None:
        self.config.simulate_updates = bool(state)
        self.config.save(self.config_path)
        self.status.showMessage("Mode simulation mis a jour")

    def open_in_browser(self) -> None:
        url = self.web_widget.web.url().toString() or self.config.supportx_url
        webbrowser.open(normalize_url(url, self.config.supportx_url))

    def check_for_updates(self, manual: bool) -> None:
        self.update_status_label.setText("Verification des mises a jour en cours...")
        self.status.showMessage("Verification des mises a jour...")

        service = UpdateService(self.config)
        try:
            update = service.check()
        except Exception as exc:
            self._pending_update = None
            self.install_update_btn.setEnabled(False)
            self.update_status_label.setText("Echec de la verification des mises a jour")
            self.status.showMessage("Erreur de verification")
            if manual:
                QMessageBox.warning(self, "Mises a jour", f"Impossible de verifier les mises a jour.\n\n{exc}")
            return

        if update.has_update:
            self._pending_update = update
            self.install_update_btn.setEnabled(True)
            self.update_status_label.setText(f"Nouvelle version disponible: {update.latest_version}")
            self.status.showMessage(f"Version {update.latest_version} disponible")

            if manual:
                answer = QMessageBox.question(
                    self,
                    "Mise a jour disponible",
                    f"Version {update.latest_version} disponible.\n\nNotes:\n{update.notes}\n\n"
                    "Lancer l'installation maintenant ?",
                )
                if answer == QMessageBox.StandardButton.Yes:
                    self.install_pending_update()
            else:
                # Auto-update mode: launch updater silently then close this app.
                self.install_pending_update(silent=True)
        else:
            self._pending_update = None
            self.install_update_btn.setEnabled(False)
            self.update_status_label.setText(f"Vous etes a jour (v{self.config.app_version})")
            self.status.showMessage("Application a jour")
            if manual:
                QMessageBox.information(self, "Mises a jour", "Vous utilisez deja la derniere version.")

    def install_pending_update(self, silent: bool = False) -> None:
        if not self._pending_update:
            QMessageBox.information(self, "Mises a jour", "Aucune mise a jour en attente.")
            return

        service = UpdateService(self.config)
        entrypoint = self.app_dir / "launcher.py"
        ok, message = service.launch_updater(
            update=self._pending_update,
            app_dir=self.app_dir,
            config_path=self.config_path,
            entrypoint_path=entrypoint,
            parent_pid=os.getpid(),
        )

        if not ok:
            if not silent:
                QMessageBox.warning(self, "Updater", message)
            self.status.showMessage("Impossible de lancer Updater")
            return

        self.status.showMessage("Updater lance, fermeture de l'application...")
        if not silent:
            QMessageBox.information(
                self,
                "Updater",
                "Le module Updater va installer la nouvelle version puis redemarrer SupportX.",
            )
        QTimer.singleShot(300, QApplication.instance().quit)

    def _anydesk_deb_path(self) -> Path:
        downloads_dir = Path.home() / "Downloads"
        downloads_dir.mkdir(parents=True, exist_ok=True)
        return downloads_dir / "anydesk_amd64.deb"

    def download_anydesk(self) -> None:
        if platform.system() != "Linux":
            QMessageBox.warning(self, "AnyDesk", "Cette installation automatique est disponible sur Linux.")
            return

        url = "https://download.anydesk.com/linux/anydesk_amd64.deb"
        target = self._anydesk_deb_path()
        self.anydesk_status.setText(f"Statut: telechargement en cours vers {target}")
        self.status.showMessage("Telechargement AnyDesk en cours...")

        try:
            response = requests.get(url, stream=True, timeout=60)
            response.raise_for_status()
            with open(target, "wb") as handle:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        handle.write(chunk)
            self.anydesk_status.setText(f"Statut: telechargement termine ({target})")
            self.status.showMessage("Telechargement AnyDesk termine")
        except Exception as exc:
            self.anydesk_status.setText("Statut: echec du telechargement")
            QMessageBox.warning(self, "AnyDesk", f"Impossible de telecharger AnyDesk.\n\n{exc}")

    def install_anydesk(self) -> None:
        target = self._anydesk_deb_path()
        if not target.exists():
            QMessageBox.information(self, "AnyDesk", "Le paquet n'est pas present. Lancez d'abord le telechargement.")
            return

        self.anydesk_status.setText("Statut: preparation de l'installation...")
        command = f"sudo apt install -y '{target}'"

        if shutil.which("pkexec"):
            try:
                subprocess.Popen(["pkexec", "apt", "install", "-y", str(target)])
                self.anydesk_status.setText("Statut: installation lancee (pkexec)")
                self.status.showMessage("Installation AnyDesk lancee")
                return
            except Exception:
                pass

        terminal = shutil.which("x-terminal-emulator") or shutil.which("gnome-terminal") or shutil.which("konsole")
        if terminal:
            try:
                if "konsole" in terminal:
                    subprocess.Popen([terminal, "-e", f"bash -lc \"{command}; echo; read -n 1 -s -r -p 'Appuyez sur une touche...'\""])
                else:
                    subprocess.Popen([terminal, "-e", "bash", "-lc", f"{command}; echo; read -n 1 -s -r -p 'Appuyez sur une touche...'"])
                self.anydesk_status.setText("Statut: installation lancee dans le terminal")
                self.status.showMessage("Installation AnyDesk lancee")
                return
            except Exception:
                pass

        self.anydesk_status.setText("Statut: installation manuelle requise")
        QMessageBox.information(
            self,
            "AnyDesk",
            "Impossible de lancer l'installation automatiquement.\n\n"
            f"Executez cette commande:\n{command}",
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app_dir = Path(__file__).resolve().parents[2]
    window = MainWindow(app_dir)
    window.show()
    raise SystemExit(app.exec())
