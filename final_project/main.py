import os
import sys
import re
import yaml  # type: ignore
from typing import Any
from openai import OpenAI  # type: ignore
from itertools import batched

import settings
from services import clear_screen, print_colored, get_file_content


def get_yaml_configuration() -> dict[str, Any]:
    config: dict[str, Any] = {}
    if os.path.exists(settings.YAML_FILENAME):
        with open(settings.YAML_FILENAME, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file) or {}
    return config


def fill_config(config: dict[str, Any], res: dict[str, Any]) -> None:
    env_limit_message: str | None = os.environ.get('LIMIT_MESSAGE')
    raw_limit_message = int(env_limit_message or config.get('limit_message') or 0)
    res['limit_message'] = raw_limit_message or None

    env_chars_raw: str | None = os.environ.get('LIMIT_CHARS')
    if env_chars_raw is None:
        env_chars_raw = str(config.get('limit_chars') or 0)
    res['limit_chars'] = int(env_chars_raw) or None

    env_temperature_raw: str | None = os.environ.get('TEMPERATURE')
    if env_temperature_raw is None:
        env_temperature_raw = str(config.get('temperature', 0.7))
    res['temperature'] = float(env_temperature_raw)

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
        return ['\n'.join(batch) for batch in batched(paragraphs, chunk_value)]
    else:
        chunks: list[str] = []
        for batch in batched(content, chunk_value):
            chunks.append(''.join(batch))
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

    print_colored(settings.INSTRUCTIONS_STR, settings.Colors.blue)
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


def prepare_api_messages(agent: 'AIAgent') -> list[dict[str, str]]:
    api_messages = []
    if agent.system_prompt:
        api_messages.append(
            {
                settings.ROLE_KEY: settings.SYSTEM_ROLE_STR,
                settings.CONTENT_KEY: agent.system_prompt,
            }
        )
    api_messages.extend(agent.history)
    return api_messages


def handle_command(agent: 'AIAgent', command: str) -> bool:
    """обрабатывает команды решвет продолжать ли цикл"""
    if command == settings.QUIT_COMMAND:
        return False

    if command == settings.RESET_COMMAND:
        agent.history.clear()
        clear_screen()
        print(settings.CONTEXT_CLEARED_TEXT)
        return True

    if command.startswith(settings.CHUNK_MODE_COMMAND):
        agent.chunk_mode(command)
        return True

    return True


def print_reply(agent: 'AIAgent', reply: str | None) -> None:
    if reply:
        print_colored(f'{reply}\n', settings.Colors.cyan)
        agent.history.append(
            {settings.ROLE_KEY: settings.LLM_ROLE_STR, settings.CONTENT_KEY: reply}
        )
    elif agent.history:
        agent.history.pop()


def process_single_command(agent: 'AIAgent', command: str) -> bool:
    """обрабатывает одну команду возвращает False если цикл приложения нужно завершить"""
    if command.startswith(('/', settings.QUIT_COMMAND)):
        return handle_command(agent, command)

    processed_text = agent.process_inline_files(command)
    agent.follow_context_limits(processed_text)
    print_reply(agent, agent.get_llm_response(prepare_api_messages(agent)))
    return True


def delete_exceeded_limit_messages(history: list[dict[str, str]], limit: int | None) -> None:
    """удаляет старые сообщения если превышен лимит на их количество"""
    if limit:
        while len(history) > limit:
            history.pop(0)


def delete_exceeded_char_messages(history: list[dict[str, str]], limit_chars: int | None) -> None:
    """удаляет старые сообщения если суммарное количество символов превышает лимит"""
    if limit_chars:
        while sum(len(msg['content']) for msg in history) > limit_chars:
            if len(history) <= 1:
                break
            history.pop(0)


def load_config() -> dict[str, Any]:
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


class AIAgent:
    def __init__(self) -> None:
        self.config: dict[str, Any] = load_config()

        api_host = self.config['api_host']
        api_key = self.config['api_key']

        self.client = OpenAI(base_url=api_host, api_key=api_key)
        self.history: list[dict[str, str]] = []
        self.system_prompt: str | None = self.config.get('system_prompt')

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
        delete_exceeded_limit_messages(self.history, limit_message)
        delete_exceeded_char_messages(self.history, limit_chars)

    def process_inline_files(self, text: str) -> str:
        """находит файлы в формате @::filepath:: и заменяет их содержимым"""
        files_paths = re.findall(r'@::(.*?)::', text)

        for path in files_paths:
            correct_path = path.strip()
            if process_file_not_found(correct_path) or process_exceeding_file_limit(correct_path):
                continue

            try:
                text = text.replace(f'@::{path}::', f'\n{get_file_content(correct_path)}\n')
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

    def run(self) -> None:
        """основной цикл приложения"""
        while True:
            print(settings.GREETING_COMMANDS_TEXT, settings.Colors.blue)
            print_colored(settings.GET_COMMAND_INPUT_TEXT, settings.Colors.blue)
            user_input = input()
            command = user_input.strip()

            if not command:
                continue

            if not process_single_command(self, command):
                break


if __name__ == '__main__':
    bot = AIAgent()
    bot.run()
