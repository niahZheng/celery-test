import time
import requests
import threading

class ConfigCache:
    def __init__(self, endpoint, polling_interval=60):
        self.endpoint = endpoint
        self.config = None
        self.polling_interval = polling_interval
        self.last_updated = 0
        self._start_polling()

    def _fetch_config(self):
        try:
            response = requests.get(self.endpoint)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to fetch configuration. Status code: {response.status_code}")
        except Exception as e:
            print(f"Error fetching configuration: {e}")
        return None

    def _update_config(self):
        while True:
            config = self._fetch_config()
            if config:
                self.config = config
                self.last_updated = time.time()
            time.sleep(self.polling_interval)

    def _start_polling(self):
        polling_thread = threading.Thread(target=self._update_config, daemon=True)
        polling_thread.start()

    def get_config(self):
        return self.config
