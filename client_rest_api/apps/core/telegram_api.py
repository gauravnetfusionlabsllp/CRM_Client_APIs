# your_app/utils/telegram_api.py

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import requests

class TelegramAPI:
    def __init__(self) -> None:
        self.telSession = self.TelegramSession()

    def TelegramSession(self):
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)

        session = requests.Session()
        session.mount("https://", adapter)
        session.mount("http://", adapter)

        return session
    
    def send_telegram_message(self, api_details, text):
        for chat_id in api_details.get("chat_ids", []):
            try:
                print(self.telSession, "=====================")
                print(api_details['api_key'], chat_id)
                self.telSession.post(
                    f"https://api.telegram.org/bot{api_details['api_key']}/sendMessage",
                    data={
                        "chat_id": chat_id,
                        "text": text,
                        "parse_mode": "markdown"
                    }
                )
            except Exception as e:
                print("Error sending telegram message:", e)
