import requests
import threading
import time
import os
import zipfile
import shutil
from tkinter import messagebox, filedialog

class UpdateManager:
    def __init__(self, app, config):
        self.app = app
        self.config = config
        self.current_version = config['app_version']
        self.update_server_url = config['update_server_url']
        self.latest_update_data = None
        self.stop_download = threading.Event()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def check_for_updates(self, manual=False):
        """Vérifie les mises à jour seulement si autorisé"""
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
        """Effectue la vérification des mises à jour via JSON"""
        time.sleep(2)
        
        simulate_mode = self.config.get("simulate_updates", False)
        
        if simulate_mode:
            self.latest_update_data = {
                "version": "1.3.0",
                "url": "https://example.com/update_1.3.0.zip",
                "notes": "Version simulée - Corrections de bugs",
                "forceUpdate": False
            }
            latest_version = self.latest_update_data["version"]
            if self._is_newer_version(latest_version):
                self.app.root.after(0, lambda: self._show_update_available(manual))
            else:
                self.app.root.after(0, lambda: self._show_no_update(manual))
        else:
            try:
                json_url = self.update_server_url
                if not json_url.endswith('.json'):
                    json_url = f"{json_url.rstrip('/')}/version.json"
                
                response = self.session.get(json_url, timeout=10)
                response.raise_for_status()
                
                self.latest_update_data = response.json()
                latest_version = self.latest_update_data["version"]
                
                if self._is_newer_version(latest_version):
                    self.app.root.after(0, lambda: self._show_update_available(manual))
                else:
                    self.app.root.after(0, lambda: self._show_no_update(manual))
                    
            except requests.exceptions.RequestException as e:
                error_msg = f"Erreur réseau: {str(e)}"
                self.app.root.after(0, lambda msg=error_msg: self._show_update_error(manual, msg))
            except (KeyError, ValueError) as e:
                error_msg = f"Données JSON invalides: {str(e)}"
                self.app.root.after(0, lambda msg=error_msg: self._show_update_error(manual, msg))
            except Exception as e:
                error_msg = f"Erreur inattendue: {str(e)}"
                self.app.root.after(0, lambda msg=error_msg: self._show_update_error(manual, msg))

    def _is_newer_version(self, latest_version):
        """Vérifie si la version est plus récente"""
        try:
            current = [int(x) for x in self.current_version.split(".")]
            latest = [int(x) for x in latest_version.split(".")]
            
            for c, l in zip(current, latest):
                if l > c:
                    return True
                if l < c:
                    return False
            return len(latest) > len(current)
            
        except (ValueError, TypeError):
            return latest_version > self.current_version

    def _show_update_available(self, manual):
        if not self.latest_update_data:
            return
            
        latest_version = self.latest_update_data["version"]
        notes = self.latest_update_data.get("notes", "Aucune information disponible")
        
        self.app.update_status.config(text=f"Mise à jour {latest_version} disponible!")
        self.app.status_bar.config(text=f"Version {latest_version} disponible - Prêt à télécharger")
        
        message = (
            f"Version {latest_version} disponible.\n\n"
            f"Notes de mise à jour:\n{notes}\n\n"
            f"Voulez-vous télécharger et installer la mise à jour maintenant?"
        )
        
        if manual or messagebox.askyesno("Mise à jour disponible", message):
            filename = os.path.basename(self.latest_update_data["url"]) or f"update_{latest_version}.zip"
                
            save_path = filedialog.asksaveasfilename(
                defaultextension=".zip",
                filetypes=[("ZIP files", "*.zip")],
                initialfile=filename,
                title="Choisir l'emplacement pour sauvegarder la mise à jour"
            )
            
            if save_path:
                self.app.root.after(0, lambda: self.app.progress.config(value=0))
                
                self.stop_download.clear()
                threading.Thread(
                    target=self.download_and_extract_update,
                    args=(self.latest_update_data["url"], save_path, latest_version),
                    daemon=True
                ).start()
            else:
                self.app.update_status.config(text="Téléchargement annulé")
                self.app.status_bar.config(text="Téléchargement annulé par l'utilisateur")

    def _show_no_update(self, manual):
        current_time = time.strftime("%H:%M:%S")
        self.app.update_status.config(text=f"Vous avez la dernière version ({self.current_version})")
        self.app.status_bar.config(text=f"À jour - Dernière vérification: {current_time}")
        if manual:
            messagebox.showinfo("Mise à jour", "Vous utilisez la dernière version disponible.")

    def _show_update_error(self, manual, error=""):
        self.app.update_status.config(text="Échec de la vérification")
        self.app.status_bar.config(text="Erreur lors de la vérification des mises à jour")
        if manual:
            messagebox.showerror("Erreur", f"Impossible de vérifier les mises à jour:\n{error}")

    def download_and_extract_update(self, update_url, save_path, latest_version):
        try:
            # Téléchargement
            self.app.root.after(0, lambda: self.app.update_status.config(text="Téléchargement en cours..."))
            self.app.root.after(0, lambda: self.app.status_bar.config(text="Téléchargement de la mise à jour..."))
            self.app.root.after(0, lambda: self.app.progress.config(value=0))
            
            response = self.session.get(
                update_url,
                stream=True,
                timeout=30,
                headers={
                    'Referer': self.update_server_url,
                    'Accept': 'application/octet-stream'
                }
            )
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            chunk_size = 8192
            
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if self.stop_download.is_set():
                        self.app.root.after(0, lambda: self.app.status_bar.config(text="Téléchargement annulé"))
                        return
                        
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        if total_size > 0:
                            progress = min(100, (downloaded_size / total_size) * 100)
                            self.app.root.after(0, lambda p=progress: self._update_progress(p))
            
            # Extraction
            self.app.root.after(0, lambda: self.app.update_status.config(text="Extraction en cours..."))
            self.app.root.after(0, lambda: self.app.status_bar.config(text="Extraction des fichiers..."))
            
            # Créer le dossier Supportx si besoin
            extract_dir = os.path.join(os.path.dirname(save_path), "Supportx")
            if not os.path.exists(extract_dir):
                os.makedirs(extract_dir)
                self.app.root.after(0, lambda: self.app.status_bar.config(
                    text=f"Dossier créé: {extract_dir}"))
            
            # Extraire le fichier ZIP
            with zipfile.ZipFile(save_path, 'r') as zip_ref:
                # Calculer la progression d'extraction
                total_files = len(zip_ref.infolist())
                extracted_count = 0
                
                for file in zip_ref.infolist():
                    zip_ref.extract(file, extract_dir)
                    extracted_count += 1
                    progress = (extracted_count / total_files) * 100
                    self.app.root.after(0, lambda p=progress: self._update_extraction_progress(p))
            
            # Nettoyer le fichier ZIP après extraction
            os.remove(save_path)
            
            self.app.root.after(0, lambda: self._show_extraction_success(extract_dir, latest_version))
            
        except Exception as e:
            error_msg = str(e)
            if hasattr(e, 'response') and e.response is not None:
                error_msg = f"{error_msg} (HTTP {e.response.status_code})"
            self.app.root.after(0, lambda msg=error_msg: self._show_download_error(msg))

    def _update_progress(self, progress):
        self.app.progress["value"] = progress
        self.app.update_status.config(text=f"Téléchargement... {progress:.1f}%")
        self.app.progress.update_idletasks()

    def _update_extraction_progress(self, progress):
        self.app.progress["value"] = progress
        self.app.update_status.config(text=f"Extraction... {progress:.1f}%")
        self.app.progress.update_idletasks()

    def _show_extraction_success(self, extract_dir, version):
        self.app.progress["value"] = 100
        self.app.update_status.config(text="Installation terminée!")
        self.app.status_bar.config(text=f"Mise à jour {version} installée avec succès")
        
        messagebox.showinfo(
            "Succès",
            f"Mise à jour {version} installée avec succès!\n\n"
            f"Les fichiers ont été extraits dans :\n{extract_dir}\n\n"
            "L'application va redémarrer pour appliquer les changements."
        )
        
        # Redémarrer l'application
        self.app.restart_application()

    def _show_download_error(self, error):
        self.app.update_status.config(text="Échec de l'installation")
        self.app.status_bar.config(text="Échec de l'installation de la mise à jour")
        self.app.progress["value"] = 0
        messagebox.showerror("Erreur", f"Échec de l'installation :\n{error}")
        
    def cancel_download(self):
        self.stop_download.set()