import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
PROMPT_PATH = os.path.join(ROOT_DIR, 'prompt', 'translate.txt')
TRADITIONAL_ONLY = set(
    '體簡變這個國學書電腦車馬魚鳥龍愛後來東長萬當樂業經機轉動傳統繁體'
    '說話語詞讀寫聽見會還過進開關門問題點線時間現實世界廣場風雲氣無為與'
    '從讓對邊還沒應該發現選擇請謝謝歡迎買賣賣東西臺灣台灣區縣號碼歲數親'
    '師範醫藥頭臉腳髮聲音顏色紅綠藍黃網絡網路軟體資訊資料處理圖片畫圖'
    '範圍類別組織機構環境應用程式使用者帳號權限管理資料庫網際網路瀏覽器'
    '輸出輸入轉換匯總統計優點缺點問題解決方案簡單複雜變化變更設計測試'
    '開發部署維護連線設定檔案記錄標籤標題內容備註編輯儲存刪除還原復原'
    '確認翻譯語言偵測偵測語系繁體中文簡體中文傳統簡化選項來源目標對照'
)
SIMPLIFIED_ONLY = set(
    '体简变这个国学书电脑车马鱼鸟龙爱后来东长万当乐业经机转动传统繁体'
    '说话语词读写听见会还过进开关门问题点线时间现实世界广场风云气无为与'
    '从让对边还没应该发现选择请谢谢欢迎买卖卖东西台台湾区县号码岁数亲'
    '师范医药头脸脚发声音颜色红绿蓝黄网络软件资讯资料处理图片画图'
    '范围类别组织机构环境应用程序使用者账号权限管理数据库互联网浏览器'
    '输出输入转换汇总统计优点缺点问题解决方案简单复杂变化变更设计测试'
    '开发部署维护连接设置档案记录标签标题内容备注编辑储存删除还原复原'
    '确认翻译语言检测语系繁体中文简体中文传统简化选项来源目标对照'
)
CHINESE_LANGUAGE_LABELS = (
    'chinese', '中文', 'zh-', 'zh_', '繁體', '繁体', '简體', '简体',
)


def normalize_detected_language(detected_language: str, title: str, content: str) -> str:
    normalized = detected_language.strip().casefold()
    if not any(label in normalized for label in CHINESE_LANGUAGE_LABELS):
        return detected_language

    source_text = title + '\n' + content
    traditional_count = sum(character in TRADITIONAL_ONLY for character in source_text)
    simplified_count = sum(character in SIMPLIFIED_ONLY for character in source_text)
    if traditional_count > simplified_count:
        return 'Traditional Chinese (繁體中文)'
    if simplified_count > traditional_count:
        return 'Simplified Chinese (简体中文)'
    return detected_language


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
        'detected_language': normalize_detected_language(detected_language, title, content),
        'title': translated_title,
        'content': translated_content,
    }