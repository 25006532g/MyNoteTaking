from flask import Blueprint, jsonify, request

from src.services.translation import translate_note


translation_bp = Blueprint('translation', __name__)

SUPPORTED_LANGUAGES = {
    'en': 'English',
    'zh-TW': 'Traditional Chinese (繁體中文)',
    'zh-CN': 'Simplified Chinese (简体中文)',
    'ja': 'Japanese (日本語)',
    'ko': 'Korean (한국어)',
    'es': 'Spanish',
    'fr': 'French',
    'de': 'German',
    'it': 'Italian',
    'pt': 'Portuguese',
    'ru': 'Russian',
    'ar': 'Arabic',
    'hi': 'Hindi',
}


@translation_bp.route('/translate', methods=['POST'])
def translate():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'error': 'A JSON request body is required'}), 400

    title = data.get('title', '')
    content = data.get('content', '')
    language_code = data.get('target_language')
    if not isinstance(title, str) or not isinstance(content, str):
        return jsonify({'error': 'Title and content must be text'}), 400
    if not (title.strip() or content.strip()):
        return jsonify({'error': 'Enter a title or note content to translate'}), 400
    if not isinstance(language_code, str) or language_code not in SUPPORTED_LANGUAGES:
        return jsonify({'error': 'Choose a supported target language'}), 400

    try:
        translation = translate_note(title, content, SUPPORTED_LANGUAGES[language_code])
    except RuntimeError as error:
        return jsonify({'error': str(error)}), 503
    return jsonify(translation)