MAX_FILE_SIZE_BYTES: int = 5 * 1024 * 1024  # 5 МБ

ERROR_API_KEY_API_HOST_MISSING: str = 'Ошибка: Не заданы параметры подключения (API_KEY, API_HOST).'
ERROR_ENV_VARIABLES_YUML_MISSING: str = 'Ошибка: нет config.yaml/переменных окружения\n'
ERROR_REQUEST_INTERRRUPTED: str = '\nЗапрос прерван\n'
ERROR_FILE_NOT_FOUND: str = '\nФайл не найден\n'
ERROR_EXCEED_FILE_SIZE_LIMIT: str = '\nОшибка: лимит загрузки файла 5 МБ\n'
API_ERROR: str = '\nОшибка от сервера: '
FILE_READING_ERROR: str = '\nОшибка чтения файла'

GET_FILE_INPUT_TEXT = '\nВведите путь до файла:\n'
GET_PROMPT_INPUT_TEXT: str = '\nВведите промпт:\n'
PROCESS_PROMPT_TEXT: str = '\nНачинаю обработку промпта\n'
PROCESS_PROMPT_ENDED_TEXT: str = '\nОбработка файла завершена\n'
GET_COMMAND_INPUT_TEXT: str = '\n\nВведите команду:\n'
CONTEXT_CLEARED_TEXT: str = '\nКонтекст очищен\n'
GREETING_COMMANDS_TEXT: str = (
    'Команды:\n'
    r"'\q' - выход из приложения"
    '\n/reset - очищает контекст'
)
LLM_AUTHOR_STR: str = '\nLLM: '
INSTRUCTIONS_STR: str = (
    '\nнажмите enter для продолжения, '
    r'\q для выхода'
)

SYSTEM_ROLE_STR: str = 'system'
USER_ROLE_STR: str = 'user'
LLM_ROLE_STR: str = 'assistant'
YAML_FILENAME: str = 'config.yaml'

CHUNK_MODE_COMMAND: str = '/file_chunk'
RESET_COMMAND: str = '/reset'
QUIT_COMMAND: str = r'\q'

PARAGRAPH_CHUNK_TYPE: str = 'paragraph'
CHARS_CHUNK_TYPE: str = 'len'

ROLE_KEY = 'role'
CONTENT_KEY = 'content'

API_KEY_STR = 'api_key'
API_HOST_STR = 'api_host'


# enum для цветного текста в консоли
class Colors:
    reset = '\033[0m'
    red = '\033[31m'
    green = '\033[32m'
    yellow = '\033[33m'
    blue = '\033[34m'
    cyan = '\033[36m'
