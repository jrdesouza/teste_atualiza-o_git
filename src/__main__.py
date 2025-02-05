import sys

from updater import AutoUpdater
import time


def main():
    print("\n=== MEU SCRIPT ===")

    # Lógica principal do seu script
    while True:
        print("Executando tarefas importanttes...")
        time.sleep(5)


if __name__ == "__main__":
    updater = AutoUpdater()

    try:
        # Instala dependências mesmo sem atualizações
        updater.install_dependencies()

        if updater.check_update():
            print("🔍 Nova versão disponível!")
            if updater.perform_update():
                print("🔄 Reiniciando aplicação...")
                updater.restart()

        main()

    except KeyboardInterrupt:
        print("\n🛑 Aplicação encerrada pelo usuário")
    except Exception as e:
        print(f"🚨 Erro não tratado: {e}")
        sys.exit(1)