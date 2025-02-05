import os
import sys
import json
import requests
import subprocess
from pathlib import Path


class AutoUpdater:
    def __init__(self):
        self.repo_path = Path(__file__).parent.parent
        self.config = self._load_config()

    def _load_config(self):
        config_path = self.repo_path / "config.json"
        with open(config_path, 'r') as f:
            return json.load(f)

    def _get_local_version(self):
        version_path = self.repo_path / "version.txt"
        return version_path.read_text().strip()

    def _get_remote_version(self):
        headers = {'Authorization': f'token {self.config["GITHUB_TOKEN"]}'}
        url = f"{self.config['REPO_API_URL']}/version.txt"

        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return response.json()['content'].strip()
        except Exception as e:
            print(f"Erro ao verificar atualizações: {e}")
        return None

    def check_update(self):
        local_version = self._get_local_version()
        remote_version = self._get_remote_version()
        return remote_version and (remote_version != local_version)

    def perform_update(self):
        try:
            # Atualiza via Git
            subprocess.run(
                ['git', 'pull', 'origin', self.config['BRANCH']],
                cwd=self.repo_path,
                check=True
            )
            print("✅ Atualização concluída")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Falha na atualização: {e}")
            return False

    def restart(self):
        os.execv(sys.executable, ['python'] + sys.argv)