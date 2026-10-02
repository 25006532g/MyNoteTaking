import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
PROMPT_PATH = os.path.join(ROOT_DIR, 'prompt', 'translate.txt')


def translate_note(title: str, content: str, target_language: str) -> dict[str, str]:
    api_key = os.getenv('OPEN_ROUTER_KEY')
    if not api_key:
        raise RuntimeError('OPEN_ROUTER_KEY is not set in the environment or .env file')

    try:
        with open(PROMPT_PATH, encoding='utf-8') as prompt_file:
            system_prompt = prompt_file.read().strip()
    except OSError as error:
        raise RuntimeError('Translation prompt file prompt/translate.txt could not be read') from error
    if not system_prompt:
        raise RuntimeError('Translation prompt file prompt/translate.txt is empty')

    user_message = json.dumps({
        'target_language': target_language,
        'title': title,
        'content': content,
    }, ensure_ascii=False)
    request_body = {
        'model': os.getenv('OPEN_ROUTER_MODEL', 'openai/gpt-4o-mini'),
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_message},
        ],
        'response_format': {'type': 'json_object'},
    }
    request = Request(
        'https://openrouter.ai/api/v1/chat/completions',
        data=json.dumps(request_body).encode('utf-8'),
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        },
        method='POST',
    )

    try:
        with urlopen(request, timeout=60) as response:
            result = json.loads(response.read().decode('utf-8'))
    except HTTPError as error:
        raise RuntimeError(f'OpenRouter request failed with status {error.code}') from error
    except URLError as error:
        raise RuntimeError('Could not connect to OpenRouter') from error

    try:
        translated = json.loads(result['choices'][0]['message']['content'])
        detected_language = translated['detected_language']
        translated_title = translated['title']
        translated_content = translated['content']
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as error:
        raise RuntimeError('OpenRouter returned an unexpected translation format') from error

    if (not isinstance(detected_language, str) or not detected_language.strip()
            or not isinstance(translated_title, str) or not isinstance(translated_content, str)):
        raise RuntimeError('OpenRouter returned an unexpected translation format')
    return {
        'detected_language': detected_language,
        'title': translated_title,
        'content': translated_content,
    }