import os
import sys
import json
import requests
import base64
from pathlib import Path
from programa.app import teste
import subprocess

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
                content = base64.b64decode(response.json()['content']).decode('utf-8-sig')
                return content.strip()
            return None
        except Exception as e:
            print(f"Erro ao verificar versão remota: {e}")
            return None

    def _is_file_updated(self, local_path, remote_sha):
        """Verifica se o arquivo local está atualizado comparando o SHA."""
        if not local_path.exists():
            return False  # Arquivo não existe localmente

        try:
            # Calcula o SHA do arquivo local
            import hashlib
            sha = hashlib.sha1()
            with open(local_path, 'rb') as f:
                while chunk := f.read(8192):
                    sha.update(chunk)
            local_sha = sha.hexdigest()

            # Compara com o SHA remoto
            return local_sha == remote_sha
        except Exception as e:
            print(f"❌ Erro ao verificar arquivo {local_path}: {e}")
            return False

    def _download_file(self, file_path):
        headers = {'Authorization': f'token {self.config["GITHUB_TOKEN"]}'}
        response = requests.get(f"{self.config['REPO_API_URL']}/{file_path}", headers=headers)

        if response.status_code == 200:
            try:
                # Decodifica o conteúdo base64
                content = base64.b64decode(response.json()['content'])

                # Cria os diretórios necessários
                full_path = self.repo_path / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)

                # Escreve o arquivo (binário ou texto)
                if isinstance(content, bytes):
                    with open(full_path, 'wb') as f:
                        f.write(content)
                else:
                    with open(full_path, 'w', encoding='utf-8') as f:
                        f.write(content.decode('utf-8-sig'))
                return True
            except Exception as e:
                print(f"❌ Erro ao baixar {file_path}: {e}")
                return False
        return False

    def _fetch_files_recursive(self, path=""):
        """Busca arquivos de forma recursiva no repositório do GitHub"""
        headers = {'Authorization': f'token {self.config["GITHUB_TOKEN"]}'}
        response = requests.get(f"{self.config['REPO_API_URL']}/{path}", headers=headers)

        if response.status_code != 200:
            print(f"❌ Erro ao buscar {path}: {response.status_code}")
            return []

        files = response.json()
        all_files = []

        for item in files:
            if item['type'] == 'file' and item['name'] != 'config.json':
                all_files.append(item)
            elif item['type'] == 'dir':  # Se for uma pasta, buscar recursivamente
                all_files.extend(self._fetch_files_recursive(item['path']))

        return all_files

    def _update_files(self):
        """Atualiza todos os arquivos, incluindo os que estão dentro de subpastas"""
        remote_files = self._fetch_files_recursive()

        for item in remote_files:
            remote_path = item['path']
            local_path = self.repo_path / remote_path

            # 🔹 Garantir que subpastas existem antes de salvar
            local_path.parent.mkdir(parents=True, exist_ok=True)

            # Verifica se o arquivo local está atualizado
            if not self._is_file_updated(local_path, item['sha']):
                print(f"🔄 Atualizando arquivo: {remote_path}")
                if not self._download_file(remote_path):
                    return False
        return True

    def _restart(self):
        """Reinicia o script atual de forma confiável no Windows"""
        try:
            print("🔄 Reiniciando aplicação...")

            python = sys.executable
            args = sys.argv[:]

            # Para Windows: iniciar novo processo e encerrar o atual
            if sys.platform.startswith('win'):
                subprocess.Popen([python] + args, creationflags=subprocess.CREATE_NEW_CONSOLE)
                os._exit(0)  # Força o encerramento do processo atual

            # Para Linux/macOS
            else:
                os.execv(python, [python] + args)

        except Exception as e:
            print(f"❌ Falha crítica ao reiniciar: {e}")
            print("⏳ Tente reiniciar manualmente o aplicativo.")
            sys.exit(1)

    def check_and_apply_updates(self):
        remote_version = self._get_remote_version()
        if remote_version and remote_version != self.local_version:
            print(f"🔍 Nova versão encontrada: {remote_version}")
            if self._update_files():
                with open(self.repo_path / 'version.txt', 'w') as f:
                    f.write(remote_version)
                self._restart()

    def _install_requirements(self):
        """Instala as dependências do requirements.txt se existir"""
        requirements_path = self.repo_path / 'requirements.txt'

        if not requirements_path.exists():
            print("⚠️ Arquivo requirements.txt não encontrado.")
            return True

        print("📦 Verificando dependências...")
        try:
            # Comando para instalar as dependências
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', '-r', str(requirements_path)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Mostra o output limpo
            if result.stdout:
                print("Saída da instalação:")
                print(result.stdout)

            print("✅ Dependências instaladas/verificadas com sucesso!")
            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Erro ao instalar dependências: {e.stderr}")
            return False

    def check_and_apply_updates(self):
        remote_version = self._get_remote_version()
        if remote_version and remote_version != self.local_version:
            print(f"🔍 Nova versão encontrada: {remote_version}")
            if self._update_files():
                # Atualiza a versão local primeiro
                with open(self.repo_path / 'version.txt', 'w') as f:
                    f.write(remote_version)

                # Instala dependências antes de reiniciar
                if self._install_requirements():
                    self._restart()


def main():
    updater = AutoUpdater()
    updater.check_and_apply_updates()
    # Verifica dependências mesmo sem atualizações
    updater._install_requirements()

    # Seu código principal aqui
    print("Aplicação em execução...")
    teste()
    # (ex: loop principal, interface gráfica, etc.)


if __name__ == "__main__":
    # Se o argumento --push for passado, tenta fazer push (apenas admin)
    if '--push' in sys.argv:
        AutoUpdater().push_update()
    else:
        main()