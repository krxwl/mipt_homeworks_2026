import os
import re
from settings import Colors, MAX_FILE_SIZE_BYTES, PARAGRAPH_CHUNK_TYPE, CHARS_CHUNK_TYPE
from settings import ERROR_FILE_NOT_FOUND, ERROR_EXCEED_FILE_SIZE_LIMIT


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


def parse_chunk_args(command: str) -> tuple[str, int, bool]:
    """парсит аргументы команды /file_chunk"""
    args: list[str] = command.split()
    chunk_type: str = PARAGRAPH_CHUNK_TYPE
    chunk_value: int = 1

    for arg in args:
        if arg.startswith(f'{PARAGRAPH_CHUNK_TYPE}='):
            chunk_type = PARAGRAPH_CHUNK_TYPE
            chunk_value = int(arg.split('=')[1])
        elif arg.startswith('len='):
            chunk_type = CHARS_CHUNK_TYPE
            chunk_value = int(arg.split('=')[1])

    return chunk_type, chunk_value, '-y' in args


def prepare_chunks(content: str, chunk_type: str, chunk_value: int) -> list[str]:
    """разбивает текст на куски в зависимости от типа разбиения"""
    content = content.replace('\r\n', '\n')

    if chunk_type == PARAGRAPH_CHUNK_TYPE:
        paragraphs: list[str] = re.split(r'\n{2,}', content)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        return [
            '\n\n'.join(paragraphs[i : i + chunk_value])
            for i in range(0, len(paragraphs), chunk_value)
        ]
    else:
        return [content[i : i + chunk_value] for i in range(0, len(content), chunk_value)]


def is_file_valid(path: str) -> bool:
    """проверяет файл на существование и размер до 5 мб"""
    if not os.path.exists(path):
        print_colored(ERROR_FILE_NOT_FOUND, Colors.yellow)
        return False
    if os.path.getsize(path) > MAX_FILE_SIZE_BYTES:
        print_colored(ERROR_EXCEED_FILE_SIZE_LIMIT, Colors.yellow)
        return False
    return True
