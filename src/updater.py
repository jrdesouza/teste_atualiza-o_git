import os
import sys
import json
import requests
import subprocess
from pathlib import Path
import base64

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
                # Decodifica o conteúdo base64
                content_base64 = response.json()['content']
                content_decoded = base64.b64decode(content_base64).decode('utf-8').strip()
                return content_decoded
        except Exception as e:
            print(f"Erro ao verificar atualizações: {e}")
        return None

    def check_update(self):
        local_version = self._get_local_version()
        remote_version = self._get_remote_version()
        return remote_version and (remote_version != local_version)


    def perform_update(self):
        try:
            result = subprocess.run(
                ['git', 'pull', 'origin', self.config['BRANCH']],
                cwd=self.repo_path,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            print("✅ Atualização concluída")
            print(result.stdout)
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Falha na atualização:\n{e.stderr}")
            return False


    def restart(self):
        try:
            # Configuração multiplataforma robusta
            python = sys.executable
            args = [python, "-m", "src"]  # Executa como módulo

            # Flags específicas por SO
            kwargs = {}
            if os.name == 'nt':
                kwargs['creationflags'] = (
                        subprocess.CREATE_NEW_PROCESS_GROUP |
                        subprocess.DETACHED_PROCESS
                )
            else:
                kwargs['start_new_session'] = True

            # Inicia novo processo
            subprocess.Popen(args, **kwargs)

            # Encerra o processo atual
            sys.exit(0)

        except Exception as e:
            print(f"🚨 Erro crítico no reinício: {e}")
            sys.exit(1)