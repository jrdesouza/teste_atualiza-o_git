import os
import sys
import time
import subprocess

def restart():
    """Reinicia a aplicação corretamente."""
    python = sys.executable
    script = sys.argv[0]  # Obtém o nome do script atual

    print("🔄 Reiniciando a aplicação...")
    time.sleep(1)

    # Inicia um novo processo e encerra o atual
    subprocess.Popen([python, script], close_fds=True, shell=True)
    os._exit(0)  # Encerra o processo atual

if __name__ == "__main__":
    restart()
