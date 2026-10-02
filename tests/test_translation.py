import io
import json
import os
import unittest
from unittest.mock import patch

from flask import Flask

from src.routes.translation import translation_bp
from src.services import translation


class TranslationRouteTests(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)
        app.register_blueprint(translation_bp, url_prefix='/api')
        self.client = app.test_client()

    def test_rejects_empty_note(self):
        response = self.client.post('/api/translate', json={
            'title': '  ',
            'content': '',
            'target_language': 'ja',
        })
        self.assertEqual(response.status_code, 400)

    def test_rejects_unsupported_language_without_calling_provider(self):
        with patch('src.routes.translation.translate_note') as translate_note:
            response = self.client.post('/api/translate', json={
                'title': 'Hello',
                'content': '',
                'target_language': ['ja'],
            })
        self.assertEqual(response.status_code, 400)
        translate_note.assert_not_called()

    def test_returns_translated_fields(self):
        expected = {
            'detected_language': 'English',
            'title': 'こんにちは',
            'content': '世界',
        }
        with patch('src.routes.translation.translate_note', return_value=expected) as translate_note:
            response = self.client.post('/api/translate', json={
                'title': 'Hello',
                'content': 'World',
                'target_language': 'ja',
            })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), expected)
        translate_note.assert_called_once_with('Hello', 'World', 'Japanese (日本語)')

    def test_accepts_english_as_target_language(self):
        with patch('src.routes.translation.translate_note', return_value={
            'detected_language': 'Japanese',
            'title': 'Hello',
            'content': 'World',
        }) as translate_note:
            response = self.client.post('/api/translate', json={
                'title': 'こんにちは',
                'content': '世界',
                'target_language': 'en',
            })
        self.assertEqual(response.status_code, 200)
        translate_note.assert_called_once_with('こんにちは', '世界', 'English')


class TranslationServiceTests(unittest.TestCase):
    def test_traditional_script_overrides_incorrect_simplified_detection(self):
        detected = translation.normalize_detected_language(
            'Simplified Chinese',
            '繁體中文翻譯',
            '請使用這個設定，將資料儲存到資料庫。',
        )
        self.assertEqual(detected, 'Traditional Chinese (繁體中文)')

    def test_simplified_script_overrides_incorrect_traditional_detection(self):
        detected = translation.normalize_detected_language(
            'Traditional Chinese',
            '简体中文翻译',
            '请使用这个设置，将数据保存到数据库。',
        )
        self.assertEqual(detected, 'Simplified Chinese (简体中文)')

    def test_ambiguous_chinese_text_keeps_model_detection(self):
        detected = translation.normalize_detected_language('Chinese', '你好', '中文')
        self.assertEqual(detected, 'Chinese')

    def test_missing_key_is_reported(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, 'OPEN_ROUTER_KEY'):
                translation.translate_note('Hello', '', 'Japanese')

    def test_reads_prompt_file_and_sends_structured_translation_request(self):
        prompt_text = 'Editable translation instructions'
        api_response = {
            'choices': [{
                'message': {'content': json.dumps({
                    'detected_language': 'English',
                    'title': 'こんにちは',
                    'content': '世界',
                })}
            }]
        }
        response_stream = io.BytesIO(json.dumps(api_response).encode('utf-8'))

        def fake_urlopen(request, timeout):
            self.assertEqual(timeout, 60)
            self.assertEqual(request.get_header('Authorization'), 'Bearer test-key')
            request_data = json.loads(request.data.decode('utf-8'))
            self.assertEqual(request_data['messages'][0]['content'], prompt_text)
            self.assertIn('Japanese', request_data['messages'][1]['content'])
            return response_stream

        with patch.object(translation, 'PROMPT_PATH', 'prompt/translate.txt'), \
                patch('builtins.open', unittest.mock.mock_open(read_data=prompt_text)), \
                patch.dict(os.environ, {'OPEN_ROUTER_KEY': 'test-key'}), \
                patch.object(translation, 'urlopen', side_effect=fake_urlopen):
            result = translation.translate_note('Hello', 'World', 'Japanese')

        self.assertEqual(result, {
            'detected_language': 'English',
            'title': 'こんにちは',
            'content': '世界',
        })


if __name__ == '__main__':
    unittest.main()