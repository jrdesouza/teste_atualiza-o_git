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
        self._validate_config()  # Nova verificação
        self._verify_git_config()

    def _validate_config(self):
        required_keys = ['REPO_OWNER', 'REPO_NAME', 'BRANCH', 'GITHUB_TOKEN']
        missing = [key for key in required_keys if key not in self.config]

        if missing:
            print(f"🚨 Configuração incompleta. Chaves faltando: {', '.join(missing)}")
            print("Por favor atualize o arquivo config.json")
            sys.exit(1)

    def install_dependencies(self):
        """Instala/atualiza dependências do requirements.txt"""
        requirements_path = self.repo_path / 'requirements.txt'

        if not requirements_path.exists():
            print("⚠️ Arquivo requirements.txt não encontrado")
            return False

        try:
            print("📦 Instalando/atualizando dependências...")
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'],
                cwd=self.repo_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            print("✅ Dependências instaladas com sucesso")
            print(result.stdout)
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Erro na instalação das dependências:\n{e.stderr}")
            return False


    def _verify_git_config(self):
        try:
            # Verifica se o remote 'origin' existe
            result = subprocess.run(
                ['git', 'remote', 'get-url', 'origin'],
                cwd=self.repo_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            if result.returncode != 0:
                print("⚠️ Configurando repositório Git...")
                self._setup_git_repo()

        except Exception as e:
            print(f"Erro na verificação do Git: {e}")

    def _setup_git_repo(self):
        try:
            # Verifica se todas as chaves necessárias existem
            required_keys = ['REPO_OWNER', 'REPO_NAME', 'GITHUB_TOKEN']
            for key in required_keys:
                if key not in self.config:
                    raise ValueError(f"Chave de configuração faltando: {key}")

            # Configuração do repositório
            repo_url = f"https://{self.config['GITHUB_TOKEN']}@github.com/{self.config['REPO_OWNER']}/{self.config['REPO_NAME']}.git"

            # Resto do código permanece igual
            if not (self.repo_path / ".git").exists():
                subprocess.run(['git', 'init'], cwd=self.repo_path, check=True)

            subprocess.run(
                ['git', 'remote', 'add', 'origin', repo_url],
                cwd=self.repo_path,
                check=True
            )

        except Exception as e:
            print(f"🚨 Erro na configuração do Git: {str(e)}")
            sys.exit(1)

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
            # Passo 1: Remove todas as mudanças locais
            subprocess.run(
                ['git', 'reset', '--hard', 'HEAD'],
                cwd=self.repo_path,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Passo 2: Limpa arquivos não rastreados e ignorados
            subprocess.run(
                ['git', 'clean', '-fdx'],  # -f: force, -d: directories, -x: inclui arquivos ignorados
                cwd=self.repo_path,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Passo 3: Atualiza do repositório remoto
            result = subprocess.run(
                ['git', 'pull', 'origin', self.config['BRANCH']],
                cwd=self.repo_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )

            print("✅ Atualização concluída com sucesso")
            print(result.stdout)
            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Falha crítica na atualização:\n{e.stderr}")
            print("Tentando reparar o repositório...")
            self._force_repair_repo()
            return False

    def _force_repair_repo(self):
        try:
            print("⚙️ Executando reparo emergencial...")
            # Remove o repositório local e reclona
            subprocess.run(['rm', '-rf', '.git'], cwd=self.repo_path, check=True)
            subprocess.run(
                ['git', 'clone', self.config['REPO_URL'], '.'],
                cwd=self.repo_path,
                check=True
            )
            print("🔁 Repositório reconstruído com sucesso")
            return True
        except Exception as e:
            print(f"🚨 Reparo falhou: {str(e)}")
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