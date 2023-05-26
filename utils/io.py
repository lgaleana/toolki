def print_system(message) -> str:
    print(f"\033[0;0m{message}")
    return message


def print_assistant(message) -> str:
    print(f"\033[92m{message}")
    return message


def user_input(message: str = "") -> str:
    return input(f"\033[1;34m{message}")