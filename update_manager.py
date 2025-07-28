import requests
import threading
import time
from tkinter import messagebox
import json

class UpdateManager:
    def __init__(self, app, config):
        self.app = app
        self.config = config
        self.current_version = config['app_version']
        self.update_server_url = config['update_server_url']

    def check_for_updates(self, manual=False):
        """Vérifie les mises à jour seulement si autorisé"""
        # Ne pas vérifier si ce n'est pas manuel et que auto_update est désactivé
        if not manual and not self.config.get("auto_update", True):
            return
            
        current_time = time.strftime("%H:%M:%S")
        self.app.status_bar.config(text=f"Vérification des mises à jour... ({current_time})")
        self.app.update_status.config(text="Vérification en cours...")
        
        try:
            threading.Thread(target=self._perform_update_check, args=(manual,), daemon=True).start()
        except Exception as e:
            self.app.update_status.config(text="Échec de vérification")
            self.app.status_bar.config(text="Échec de vérification des mises à jour")
            if manual:
                messagebox.showerror("Erreur", f"Impossible de vérifier les mises à jour: {str(e)}")

    def _perform_update_check(self, manual):
        """Effectue la vérification des mises à jour"""
        time.sleep(2)
        
        # Utiliser le paramètre de configuration pour la simulation
        simulate_mode = self.config.get("simulate_updates", True)
        
        if simulate_mode:
            latest_version = "1.3.0"
            update_available = self._is_newer_version(latest_version)
            if update_available:
                self.app.root.after(0, lambda: self._show_update_available(latest_version, manual))
            else:
                self.app.root.after(0, lambda: self._show_no_update(manual))
        else:
            # Logique réelle de vérification des mises à jour
            try:
                response = requests.get(f"{self.update_server_url}/version")
                if response.status_code == 200:
                    latest_version = response.text.strip()
                    if self._is_newer_version(latest_version):
                        self.app.root.after(0, lambda: self._show_update_available(latest_version, manual))
                    else:
                        self.app.root.after(0, lambda: self._show_no_update(manual))
                else:
                    self.app.root.after(0, lambda: self._show_update_error(manual))
            except Exception as e:
                self.app.root.after(0, lambda: self._show_update_error(manual, str(e)))

    def _is_newer_version(self, latest_version):
        """Vérifie si la version est plus récente"""
        current = [int(x) for x in self.current_version.split(".")]
        latest = [int(x) for x in latest_version.split(".")]
        return latest > current

    def _show_update_available(self, latest_version, manual):
        """Affiche qu'une mise à jour est disponible"""
        self.app.update_status.config(text=f"Mise à jour {latest_version} disponible!")
        self.app.status_bar.config(text=f"Version {latest_version} disponible - Prêt à installer")
        
        if manual or messagebox.askyesno("Mise à jour disponible", 
                                        f"Version {latest_version} disponible. Voulez-vous l'installer maintenant?"):
            threading.Thread(
                target=self.download_and_apply_update, 
                args=(f"{self.update_server_url}/update_{latest_version}.zip",),
                daemon=True
            ).start()

    def _show_no_update(self, manual):
        """Affiche qu'aucune mise à jour n'est disponible"""
        current_time = time.strftime("%H:%M:%S")
        self.app.update_status.config(text=f"Vous avez la dernière version ({self.current_version})")
        self.app.status_bar.config(text=f"À jour - Dernière vérification: {current_time}")
        if manual:
            messagebox.showinfo("Mise à jour", "Vous utilisez la dernière version disponible.")

    def _show_update_error(self, manual, error=""):
        """Affiche une erreur lors de la vérification des mises à jour"""
        self.app.update_status.config(text="Échec de la vérification")
        self.app.status_bar.config(text="Erreur lors de la vérification des mises à jour")
        if manual:
            messagebox.showerror("Erreur", f"Impossible de vérifier les mises à jour: {error}")

    def download_and_apply_update(self, update_url):
        """Télécharge et applique la mise à jour"""
        try:
            self.app.update_status.config(text="Téléchargement en cours...")
            self.app.status_bar.config(text="Téléchargement de la mise à jour...")
            self.app.progress["value"] = 0
            
            # Simulation de téléchargement
            for i in range(0, 101, 2):
                self.app.progress["value"] = i
                self.app.update_status.config(text=f"Téléchargement... {i}%")
                time.sleep(0.05)
                self.app.root.update()

            self.app.update_status.config(text="Application de la mise à jour...")
            self.app.status_bar.config(text="Installation de la mise à jour...")
            
            # Simulation d'installation
            for i in range(0, 101, 5):
                self.app.progress["value"] = i
                time.sleep(0.1)
                self.app.root.update()

            # Mise à jour de la version
            self.current_version = "1.3.0"
            self.app.version_label.config(text=self.current_version)
            
            self.app.update_status.config(text="Mise à jour terminée!")
            self.app.status_bar.config(text="Mise à jour installée avec succès - Redémarrage nécessaire")
            messagebox.showinfo("Mise à jour", "Mise à jour installée avec succès. Veuillez redémarrer l'application pour appliquer les changements.")
        except Exception as e:
            self.app.update_status.config(text="Échec de la mise à jour")
            self.app.status_bar.config(text="Échec de l'installation de la mise à jour")
            messagebox.showerror("Erreur", f"Échec de la mise à jour : {str(e)}")