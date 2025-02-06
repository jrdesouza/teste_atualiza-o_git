import os
import sys
import json
import requests
import base64
import subprocess
from pathlib import Path


class AutoUpdater:
    def __init__(self):
        self.repo_path = Path(__file__).parent.parent
        self.config = self._load_config()
        self.is_admin = self.config.get("IS_ADMIN", False)
        self.local_version = self._get_local_version()

    def _load_config(self):
        config_path = self.repo_path / "config.json"
        with open(config_path, 'r') as f:
            return json.load(f)

    def _get_local_version(self):
        try:
            with open(self.repo_path / 'version.txt', 'r') as f:
                return f.read().strip()
        except FileNotFoundError:
            return "0.0.0"

    def _get_remote_version(self):
        headers = {'Authorization': f'token {self.config["GITHUB_TOKEN"]}'}
        try:
            response = requests.get(f"{self.config['REPO_API_URL']}/version.txt", headers=headers)
            if response.status_code == 200:
                content = base64.b64decode(response.json()['content']).decode('utf-8')
                return content.strip()
            return None
        except Exception as e:
            print(f"Erro ao verificar versão remota: {e}")
            return None

    def _restart(self):
        """Chama o script de reinício externo."""
        python = sys.executable
        restart_script = os.path.join(os.path.dirname(__file__), "restart.py")

        print("🔄 Chamando script de reinício externo...")
        subprocess.Popen([python, restart_script], close_fds=True, shell=True)
        os._exit(0)

    def _download_file(self, file_path):
        headers = {'Authorization': f'token {self.config["GITHUB_TOKEN"]}'}
        response = requests.get(f"{self.config['REPO_API_URL']}/{file_path}", headers=headers)

        if response.status_code == 200:
            try:
                content = base64.b64decode(response.json()['content'])
                full_path = self.repo_path / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)

                with open(full_path, 'wb') as f:
                    f.write(content)
                return True
            except Exception as e:
                print(f"❌ Erro ao baixar {file_path}: {e}")
                return False
        return False

    def _update_files(self):
        headers = {'Authorization': f'token {self.config["GITHUB_TOKEN"]}'}
        response = requests.get(self.config['REPO_API_URL'], headers=headers)

        if response.status_code != 200:
            print("❌ Erro ao listar arquivos do repositório.")
            return False

        remote_files = response.json()

        for item in remote_files:
            if item['type'] == 'file' and item['name'] != 'config.json':
                remote_path = item['path']
                local_path = self.repo_path / remote_path

                if not self._is_file_updated(local_path, item['sha']):
                    print(f"🔄 Atualizando arquivo: {remote_path}")
                    if not self._download_file(remote_path):
                        return False
        return True

    def _is_file_updated(self, local_path, remote_sha):
        if not local_path.exists():
            return False

        try:
            import hashlib
            sha = hashlib.sha1()
            with open(local_path, 'rb') as f:
                while chunk := f.read(8192):
                    sha.update(chunk)
            local_sha = sha.hexdigest()

            return local_sha == remote_sha
        except Exception as e:
            print(f"❌ Erro ao verificar arquivo {local_path}: {e}")
            return False

    def check_and_apply_updates(self):
        remote_version = self._get_remote_version()
        if remote_version and remote_version != self.local_version:
            print(f"🔍 Nova versão encontrada: {remote_version}")
            if self._update_files():
                with open(self.repo_path / 'version.txt', 'w') as f:
                    f.write(remote_version)
                print("🔄 Reiniciando para aplicar atualizações...")
                self._restart()

    def push_update(self, commit_message="Auto-update"):
        if not self.is_admin:
            print("❌ Apenas a máquina admin pode fazer push!")
            return

        try:
            current_version = self._get_local_version()
            major, minor, patch = map(int, current_version.split('.'))
            new_version = f"{major}.{minor}.{patch + 1}"
            with open(self.repo_path / 'version.txt', 'w') as f:
                f.write(new_version)

            subprocess.run(['git', 'add', '.'], cwd=self.repo_path, check=True)
            subprocess.run(['git', 'commit', '-m', commit_message], cwd=self.repo_path, check=True)
            subprocess.run(['git', 'push', 'origin', 'main'], cwd=self.repo_path, check=True)
            print(f"✅ Versão {new_version} publicada!")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Erro no push: {e}")
            return False


from app import teste

def main():
    updater = AutoUpdater()

    updater.check_and_apply_updates()

    print("Aplicação em execução...")
    teste()


if __name__ == "__main__":
    if '--push' in sys.argv:
        AutoUpdater().push_update()
    else:
        main()
