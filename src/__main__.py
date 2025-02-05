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

    try:
        if updater.check_update():
            print("🔍 Nova versão disponível!")
            if updater.perform_update():
                print("Reiniciando aplicação...")
                updater.restart()

        # Só executa o main() se não houve atualização
        main()

    except KeyboardInterrupt:
        print("\n🛑 Aplicação encerrada pelo usuário")