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
                "text": f"🔴 *Django Error Log:*\n\n```\n{log_entry}\n```",
                "parse_mode": "Markdown"
            }
            requests.post(self.url, json=payload)
        except Exception as e:
            print(f"Ошибка отправки лога в Telegram: {e}")
