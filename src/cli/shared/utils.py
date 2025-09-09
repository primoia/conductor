# src/cli/shared/utils.py

def confirm_action(prompt_message: str) -> bool:
    """
    Exibe um prompt de confirmação [y/N] para o usuário e retorna sua decisão.
    """
    full_prompt = f"{prompt_message} [y/N]: "
    while True:
        try:
            response = input(full_prompt).lower().strip()
            if response == 'y':
                return True
            elif response == 'n':
                return False
            else:
                print("Resposta inválida. Por favor, digite 'y' ou 'n'.")
        except (EOFError, KeyboardInterrupt):
            # Trata Ctrl+D ou Ctrl+C como um "Não"
            print("\nConfirmação cancelada.")
            return False