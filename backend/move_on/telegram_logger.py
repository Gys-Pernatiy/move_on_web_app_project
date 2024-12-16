import logging
import requests

class TelegramHandler(logging.Handler):
    """
    Кастомный обработчик для отправки логов уровня ERROR и CRITICAL в Telegram.
    """
    def __init__(self, bot_token, chat_id):
        super().__init__(level=logging.ERROR)
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    def emit(self, record):
        try:
            log_entry = self.format(record)
            payload = {
                "chat_id": self.chat_id,
                "text": f"🔴 <b>Django Error Log:</b>\n<pre>{log_entry}</pre>",
                "parse_mode": "HTML"
            }
            response = requests.post(self.url, json=payload)
            if not response.ok:
                print(f"Ошибка отправки лога в Telegram: {response.text}")
        except Exception as e:
            print(f"Ошибка отправки лога в Telegram: {e}")
