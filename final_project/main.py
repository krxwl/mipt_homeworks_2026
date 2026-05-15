import os
import sys
import re
import yaml
from typing import Any
from openai import OpenAI

import settings
from helpers import clear_screen, print_colored, get_file_content


def get_yaml_configuration() -> dict[str, Any]:
    config: dict[str, Any] = {}
    if os.path.exists(settings.YAML_FILENAME):
        with open(settings.YAML_FILENAME, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file) or {}
    return config


def fill_config(config: dict[str, Any], res: dict[str, Any]) -> None:
    res['model'] = os.environ.get('MODEL_NAME', config.get('model'))
    env_limit_message: int = os.environ.get('LIMIT_MESSAGE')
    res['limit_message'] = int(env_limit_message or config.get('limit_message') or 0) or None
    env_chars: int = int(os.environ.get('LIMIT_CHARS'))
    res['limit_chars'] = int(env_chars or config.get('limit_chars') or 0) or None
    env_temperature: float = float(os.environ.get('TEMPERATURE'))
    res['temperature'] = float(env_temperature or config.get('temperature', 0.7))
    res['system_prompt'] = config.get('system_prompt')


def crop_if_limit_exceeded(new_text: str, limit_chars: int | None) -> None:
    if limit_chars and len(new_text) > limit_chars:
        new_text = new_text[-limit_chars:]


def parse_chunk_args(command: str) -> tuple[str, int, bool]:
    """парсит аргументы команды /file_chunk"""
    args: list[str] = command.split()
    chunk_type: str = settings.PARAGRAPH_CHUNK_TYPE
    chunk_value: int = 1

    for arg in args:
        if arg.startswith(f'{settings.PARAGRAPH_CHUNK_TYPE}='):
            chunk_type = settings.PARAGRAPH_CHUNK_TYPE
            chunk_value = int(arg.split('=')[1])
        elif arg.startswith('len='):
            chunk_type = settings.CHARS_CHUNK_TYPE
            chunk_value = int(arg.split('=')[1])

    return chunk_type, chunk_value, '-y' in args


def prepare_chunks(content: str, chunk_type: str, chunk_value: int) -> list[str]:
    """разбивает текст на куски в зависимости от типа"""

    if chunk_type == settings.PARAGRAPH_CHUNK_TYPE:
        paragraphs: list[str] = re.split('\n\n', content)
        paragraphs = [p for p in paragraphs if p.strip()]
        return [
            '\n'.join(paragraphs[i : i + chunk_value])
            for i in range(0, len(paragraphs), chunk_value)
        ]
    else:
        chunks: list[str] = []
        for i in range(0, len(content), chunk_value):
            chunks.append(content[i : i + chunk_value])
        return chunks


def request_chunk_inputs() -> tuple[str, str] | None:
    """запрашивает у пользователя путь к файлу и промпт"""

    print_colored(settings.GET_FILE_INPUT_TEXT, settings.Colors.blue)
    filepath: str = input().strip()

    if not os.path.exists(filepath):
        print_colored(settings.ERROR_FILE_NOT_FOUND, settings.Colors.yellow)
        return None

    print_colored(settings.GET_PROMPT_INPUT_TEXT, settings.Colors.blue)
    user_prompt: str = input()
    return filepath, user_prompt


def interrupt_chunks_processing(auto_yes: bool) -> bool:
    if auto_yes:
        return False

    print_colored(settings.INSTRUCTIONS_STR, settings.Colors.BLUE)
    return input().strip() == settings.QUIT_COMMAND


def process_exceeding_file_limit(path: str) -> bool:
    if os.path.getsize(path) > settings.MAX_FILE_SIZE_BYTES:
        print_colored(settings.ERROR_EXCEED_FILE_SIZE_LIMIT, settings.Colors.yellow)
        return True
    return False


def process_file_not_found(path: str) -> bool:
    if not os.path.exists(path):
        print_colored(settings.ERROR_FILE_NOT_FOUND, settings.Colors.yellow)
        return True
    return False


def process_response(response: Any) -> str:
    """обрабатывает ответ от модели, выводит текст и собирает результат"""
    reply: list[str] = []

    for chunk in response:
        if not chunk.choices:
            continue

        content = chunk.choices[0].delta.content
        if not content:
            continue

        print(content, end='', flush=True)
        reply.append(content)

    print(flush=True)
    return ''.join(reply)


class AIAgent:
    def __init__(self) -> None:
        self.config: dict[str, Any] = self.load_config()

        api_host = self.config['api_host']
        api_key = self.config['api_key']

        self.client = OpenAI(base_url=api_host, api_key=api_key)
        self.history: list[dict[str, str]] = []
        self.system_prompt: str | None = self.config.get('system_prompt')

    def load_config(self) -> dict[str, Any]:
        """загрузка конфигурации из yaml и переменных окружения"""
        config: dict[str, Any] = get_yaml_configuration()

        res: dict[str, Any] = {
            settings.API_KEY_STR: os.environ.get('API_KEY', config.get('api_key')),
            settings.API_HOST_STR: os.environ.get('API_HOST', config.get('api_host')),
        }

        if not res[settings.API_KEY_STR] and not res[settings.API_HOST_STR]:
            print_colored(settings.ERROR_API_KEY_API_HOST_MISSING, settings.Colors.red)
            print_colored(settings.ERROR_ENV_VARIABLES_YUML_MISSING, settings.Colors.red)
            sys.exit(1)

        fill_config(config, res)

        return res

    def print_reply(self, reply: str | None) -> None:
        if reply:
            print_colored(f'{reply}\n', settings.Colors.cyan)
            self.history.append(
                {settings.ROLE_KEY: settings.LLM_ROLE_STR, settings.CONTENT_KEY: reply}
            )
        elif self.history:
            self.history.pop()

    def prepare_api_messages(self) -> list[dict[str, str]]:
        api_messages = []
        if self.system_prompt:
            api_messages.append(
                {
                    settings.ROLE_KEY: settings.SYSTEM_ROLE_STR,
                    settings.CONTENT_KEY: self.system_prompt,
                }
            )
        api_messages.extend(self.history)
        return api_messages

    def execute_chunk_processing(self, chunks: list[str], user_prompt: str, auto_yes: bool) -> None:
        """отправляет чанки в LLM и обрабатывает паузы пользователя"""
        for chunk in chunks:
            if not chunk.strip():
                continue

            messages: list[dict[str, str]] = [
                {
                    settings.ROLE_KEY: settings.USER_ROLE_STR,
                    settings.CONTENT_KEY: f'{user_prompt}\n\n{chunk}',
                }
            ]
            print_colored(settings.LLM_AUTHOR_STR, settings.Colors.cyan)
            self.get_llm_response(messages)

            if interrupt_chunks_processing(auto_yes):
                break

    def follow_context_limits(self, new_text: str) -> None:
        """обрезает сообщения и удаляет старые по лимитам"""
        limit_chars = self.config['limit_chars']
        limit_message = self.config['limit_message']

        if limit_chars and len(new_text) > limit_chars:
            new_text = new_text[-limit_chars:]

        self.history.append(
            {settings.ROLE_KEY: settings.USER_ROLE_STR, settings.CONTENT_KEY: new_text}
        )

        if limit_message:
            while len(self.history) > limit_message:
                self.history.pop(0)

        if limit_chars:
            while sum(len(msg['content']) for msg in self.history) > limit_chars:
                if len(self.history) <= 1:
                    break
                self.history.pop(0)

    def process_inline_files(self, text: str) -> str:
        """находит файлы в формате @::filepath:: и заменяет их содержимым"""
        files_paths = re.findall(r'@::(.*?)::', text)

        for path in files_paths:
            correct_path = path.strip()
            if process_file_not_found(correct_path) or process_exceeding_file_limit(correct_path):
                continue

            try:
                content = get_file_content(correct_path)
                text = text.replace(f'@::{path}::', f'\n{content}\n')
            except Exception as e:
                print_colored(
                    f'\n{settings.FILE_READING_ERROR} {correct_path}: {e}', settings.Colors.yellow
                )

        return text

    def get_llm_response(self, messages: list[dict[str, str]]) -> str | None:
        """отправка запроса к модели"""
        try:
            response = self.client.chat.completions.create(
                model=self.config['model'],
                messages=messages,
                temperature=self.config['temperature'],
                stream=True,
            )
        except KeyboardInterrupt:
            print_colored(settings.ERROR_REQUEST_INTERRRUPTED, settings.Colors.yellow)
            return None
        except Exception as e:
            print_colored(f'{settings.API_ERROR} {e}', settings.Colors.yellow)
            return None

        return process_response(response)

    def chunk_mode(self, command: str) -> None:
        chunk_type, chunk_value, auto_yes = parse_chunk_args(command)

        inputs = request_chunk_inputs()
        if inputs is None:
            return

        print_colored(settings.PROCESS_PROMPT_TEXT, settings.Colors.green)

        content = get_file_content(inputs[0])

        self.execute_chunk_processing(
            prepare_chunks(content, chunk_type, chunk_value), inputs[1], auto_yes
        )
        print_colored(settings.PROCESS_PROMPT_ENDED_TEXT, settings.Colors.green)

    def handle_command(self, command: str) -> bool:
        """обрабатывает команды"""
        if command == settings.QUIT_COMMAND:
            return False

        if command == settings.RESET_COMMAND:
            self.history.clear()
            clear_screen()
            print(settings.CONTEXT_CLEARED_TEXT)
            return True

        if command.startswith(settings.CHUNK_MODE_COMMAND):
            self.chunk_mode(command)
            return True

        return True

    def run(self) -> None:
        """основной цикл приложения"""
        while True:
            print(settings.GREETING_COMMANDS_TEXT, settings.Colors.BLUE)
            print_colored(settings.GET_COMMAND_INPUT_TEXT, settings.Colors.BLUE)
            user_input = input()
            command = user_input.strip()

            if not command:
                continue

            if command.startswith(('/', settings.QUIT_COMMAND)):
                if not self.handle_command(command):
                    break
                continue

            processed_text = self.process_inline_files(command)
            self.follow_context_limits(processed_text)
            self.print_reply(self.get_llm_response(self.prepare_api_messages()))


if __name__ == '__main__':
    bot = AIAgent()
    bot.run()
