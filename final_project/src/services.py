import os
from final_project.src.settings import Colors


def clear_screen() -> None:
    """очистка консоли"""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_colored(text: str, color: str, end: str = '\n', flush: bool = False) -> None:
    """печатает текст выбранным цветом"""
    print(f'{color}{text}{Colors.reset}', end=end, flush=flush)


def get_file_content(file_path: str) -> str:
    """читает содержимое файла"""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()
