import os
import sys
import re
import yaml
from typing import Any
from openai import OpenAI

from settings import *
from utils import clear_screen, print_colored, get_file_content

class AIAgent:
    def __init__(self):
        self.config = self.load_config()
        self.client = OpenAI(
            base_url=self.config['api_host'],
            api_key=self.config['api_key']
        )
        self.history = []
        self.system_prompt = self.config.get('system_prompt')

    # хэлперы
    def print_reply(self, reply: str | None) -> None:
        if reply:
            print_colored(f"{reply}\n", Colors.CYAN)
            self.history.append({"role": LLM_ROLE_STR, "content": reply})
        else:
            if self.history:
                self.history.pop()


    def prepare_api_messages(self) -> list[dict[str, str]]:
        api_messages = []
        if self.system_prompt:
            api_messages.append({"role": SYSTEM_ROLE_STR, "content": self.system_prompt})
        api_messages.extend(self.history)
        return api_messages


    def get_yaml_configuration(self) -> dict[str, Any]:
        config = {}
        if os.path.exists(YAML_FILENAME):
            with open(YAML_FILENAME, "r", encoding="utf-8") as file:
                config = yaml.safe_load(file) or {}
        return config


    def fill_config(self, config: dict[str, Any], res: dict) -> None:
        res['model'] = os.environ.get('MODEL_NAME', config.get('model'))

        res['limit_message'] = int(os.environ.get('LIMIT_MESSAGE') or config.get('limit_message') or 0) or None
        res['limit_chars'] = int(os.environ.get('LIMIT_CHARS') or config.get('limit_chars') or 0) or None

        res['temperature'] = float(os.environ.get('TEMPERATURE') or config.get('temperature', 0.7))
        res['system_prompt'] = config.get('system_prompt')


    def crop_if_limit_exceeded(self, new_text: str, limit_chars: int) -> None:
        if limit_chars and len(new_text) > limit_chars:
            new_text = new_text[-limit_chars:]


    def parse_chunk_args(self, command: str) -> tuple[str, int, bool]:
        """парсит аргументы команды /file_chunk"""
        args: list[str] = command.split()
        chunk_type: str = PARAGRAPH_CHUNK_TYPE
        chunk_value: int = 1

        for arg in args:
            if arg.startswith(f"{PARAGRAPH_CHUNK_TYPE}="):
                chunk_type = PARAGRAPH_CHUNK_TYPE
                chunk_value = int(arg.split("=")[1])
            elif arg.startswith("len="):
                chunk_type = CHARS_CHUNK_TYPE
                chunk_value = int(arg.split("=")[1])

        return chunk_type, chunk_value, "-y" in args


    def prepare_chunks(self, content: str, chunk_type: str, chunk_value: int) -> list[str]:
        """разбивает текст на куски в зависимости от типа"""

        if chunk_type == PARAGRAPH_CHUNK_TYPE:
            paragraphs: list[str] = re.split("\n\n", content)
            paragraphs = [p for p in paragraphs if p.strip()]
            return ["\n".join(paragraphs[i: i + chunk_value]) for i in range(0, len(paragraphs), chunk_value)]
        else:
            return [content[i:i + chunk_value] for i in range(0, len(content), chunk_value)]


    def request_chunk_inputs(self) -> tuple[str, str] | None:
        """запрашивает у пользователя путь к файлу и промпт"""

        print_colored(GET_FILE_INPUT_TEXT, Colors.BLUE)
        filepath: str = input().strip()

        if not os.path.exists(filepath):
            print_colored(ERROR_FILE_NOT_FOUND, Colors.YELLOW)
            return None

        print_colored(GET_PROMPT_INPUT_TEXT, Colors.BLUE)
        user_prompt: str = input()
        return filepath, user_prompt


    def execute_chunk_processing(self, chunks: list[str], user_prompt: str, auto_yes: bool) -> None:
        """отправляет чанки в LLM и обрабатывает паузы пользователя"""
        for chunk in chunks:
            if not chunk.strip():
                continue

            messages: list[dict[str, str]] = [{"role": USER_ROLE_STR, "content": f"{user_prompt}\n\n{chunk}"}]
            print_colored(LLM_AUTHOR_STR, Colors.CYAN)
            self.get_llm_response(messages)

            if not auto_yes:
                print_colored(INSTRUCTIONS_STR, Colors.BLUE)
                if input().strip() == QUIT_COMMAND:
                    break

    def process_exceeding_file_limit(self, path: str) -> bool:
        if os.path.getsize(path) > MAX_FILE_SIZE_BYTES:
            print_colored(ERROR_EXCEED_FILE_SIZE_LIMIT, Colors.YELLOW)
            return True
        return False

    def process_file_not_found(self, path: str) -> bool:
        if not os.path.exists(path):
            print_colored(ERROR_FILE_NOT_FOUND, Colors.YELLOW)
            return True
        return False

    # основной функционал
    def load_config(self):
        """загрузка конфигурации из yaml и переменных окружения"""
        config: dict[str, Any] = self.get_yaml_configuration()

        res: dict = {
            'api_key': os.environ.get('API_KEY', config.get('api_key')),
            'api_host': os.environ.get('API_HOST', config.get('api_host'))
        }

        if not res['api_key'] and not res['api_host']:
            print_colored(ERROR_API_KEY_API_HOST_MISSING, Colors.RED)
            print_colored(ERROR_ENV_VARIABLES_YUML_MISSING, Colors.RED)
            sys.exit(1)

        self.fill_config(config, res)

        return res


    def follow_context_limits(self, new_text):
        """обрезает соообщения и удаляет старые"""
        limit_chars = self.config['limit_chars']
        limit_message = self.config['limit_message']

        self.crop_if_limit_exceeded(new_text, limit_chars)
        self.history.append({"role": USER_ROLE_STR, "content": new_text})

        while True:
            chars_limit_exceeded = limit_chars and sum(len(msg["content"]) for msg in self.history) > limit_chars
            msgs_limit_exceeded = limit_message and len(self.history) > limit_message

            if not chars_limit_exceeded and not msgs_limit_exceeded:
                break

            if len(self.history) > 1:
                self.history.pop(0)
            else:
                break


    def process_inline_files(self, text: str):
        """находит файлы в формате @::filepath:: и заменяет их содержимым"""
        files_paths = re.findall(r'@::(.*?)::', text)

        for path in files_paths:
            correct_path = path.strip()
            if self.process_file_not_found(correct_path) or self.process_exceeding_file_limit(correct_path):
                continue

            try:
                content = get_file_content(correct_path)
                text = text.replace(f'@::{path}::', f'\n{content}\n')
            except Exception as e:
                print_colored(f"\n{FILE_READING_ERROR} {correct_path}: {e}", Colors.YELLOW)

        return text


    def get_llm_response(self, messages):
        """отправка запроса к модели"""
        try:
            response = self.client.chat.completions.create(
                model=self.config['model'],
                messages=messages,
                temperature=self.config['temperature'],
                stream=True,
            )
            reply: list[str] = []

            for chunk in response:
                if chunk.choices:
                    content = chunk.choices[0].delta.content
                    if content:
                        print(content, end="", flush=True)
                        reply.append(content)

            print(flush=True)
            return "".join(reply)
        except KeyboardInterrupt:
            print_colored(ERROR_REQUEST_INTERRRUPTED, Colors.YELLOW)
            return None
        except Exception as e:
            print_colored(f"{API_ERROR} {e}", Colors.YELLOW)
            return None


    def chunk_mode(self, command):
        chunk_type, chunk_value, auto_yes = self.parse_chunk_args(command)

        inputs = self.request_chunk_inputs()
        if inputs is None:
            return

        print_colored(PROCESS_PROMPT_TEXT, Colors.GREEN)

        content = get_file_content(inputs[0])

        self.execute_chunk_processing(self.prepare_chunks(content, chunk_type, chunk_value), inputs[1], auto_yes)
        print_colored(PROCESS_PROMPT_ENDED_TEXT, Colors.GREEN)


    def run(self):
        """основной цикл приложения"""
        while True:
            print(GREETING_COMMANDS_TEXT, Colors.BLUE)
            print_colored(GET_COMMAND_INPUT_TEXT, Colors.BLUE)
            user_input = input()

            command = user_input.strip()

            if command == QUIT_COMMAND:
                break
            elif command == RESET_COMMAND:
                self.history.clear()
                clear_screen()
                print(CONTEXT_CLEARED_TEXT)
                continue
            elif command.startswith(CHUNK_MODE_COMMAND):
                self.chunk_mode(command)
                continue
            elif not command:
                continue

            self.follow_context_limits(self.process_inline_files(command))
            self.print_reply(self.get_llm_response(self.prepare_api_messages()))


if __name__ == "__main__":
    bot = AIAgent()
    bot.run()