import os
import json
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
from flask import Flask, send_from_directory
from flask_cors import CORS
from src.models.user import db
from src.routes.user import user_bp
from src.routes.note import note_bp
from src.routes.translation import translation_bp
from src.models.note import Note

ROOT_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
load_dotenv(os.path.join(ROOT_DIR, '.env'))


def llm_generate(user_prompt: str) -> str:
    api_key = os.getenv('OPEN_ROUTER_KEY')
    if not api_key:
        raise RuntimeError('OPEN_ROUTER_KEY is not set in the environment or .env file')

    request_body = {
        'model': os.getenv('OPEN_ROUTER_MODEL', 'openai/gpt-4o-mini'),
        'messages': [
            {
                'role': 'system',
                'content': (
                    'You are a professional translator. Translate the user input into '
                    'Traditional Chinese (繁體中文). Preserve the original meaning, tone, '
                    'and formatting. Return only the translation.'
                ),
            },
            {'role': 'user', 'content': user_prompt},
        ],
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
        detail = error.read().decode('utf-8', errors='replace')
        raise RuntimeError(f'OpenRouter request failed ({error.code}): {detail}') from error
    except URLError as error:
        raise RuntimeError(f'Could not connect to OpenRouter: {error.reason}') from error

    try:
        return result['choices'][0]['message']['content'].strip()
    except (KeyError, IndexError, TypeError, AttributeError) as error:
        raise RuntimeError('OpenRouter returned an unexpected response format') from error


app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'

# Enable CORS for all routes
CORS(app)

# register blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(note_bp, url_prefix='/api')
app.register_blueprint(translation_bp, url_prefix='/api')
# configure database to use repository-root `database/app.db`
DB_PATH = os.path.join(ROOT_DIR, 'database', 'app.db')
# ensure database directory exists
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{DB_PATH}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
with app.app_context():
    db.create_all()

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
