from updater import AutoUpdater
import time


def main():
    print("\n=== MEU SCRIPT ===")

    # Lógica principal do seu script
    while True:
        print("Executando tarefas importantes...")
        time.sleep(5)


if __name__ == "__main__":
    updater = AutoUpdater()

    if updater.check_update():
        print("🔍 Nova versão disponível!")
        if updater.perform_update():
            updater.restart()

    main()