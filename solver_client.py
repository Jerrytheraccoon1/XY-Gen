import requests
import time
import random
import json
from urllib.parse import urlparse

with open('input/config.json', 'r') as cfg_file:
    KEY_STORE = json.load(cfg_file)
    AUTH_TOKEN = KEY_STORE['data']['solver_api_key']

class Solver:
    def __init__(self, url, sitekey, rqdata="", user_agent="", proxy=None):
        self.target_url = url
        self.key = sitekey
        self.data_payload = rqdata
        self.ua_string = user_agent
        self.proxy_str = proxy
        self.endpoint = "https://solve.xgen.ink"

    def _extract_network_configs(self):
        if not self.proxy_str:
            return {}

        address = self.proxy_str if "://" in self.proxy_str else f"http://{self.proxy_str}"
        
        try:
            parsed = urlparse(address)
            net_info = {}
            
            if parsed.hostname and parsed.port:
                net_info["srv"] = f"{parsed.hostname}:{parsed.port}"
            if parsed.username:
                net_info["usr"] = parsed.username
            if parsed.password:
                net_info["pw"] = parsed.password
                
            return net_info
        except Exception:
            return {}

    def solve(self, timeout=300, poll_interval=1):
        query_data = {
            "url": self.target_url,
            "sitekey": self.key,
            "rqdata": self.data_payload,
            "user_agent": self.ua_string,
        }
        
        query_data.update(self._extract_network_configs())

        http_client = requests.Session()
        
        headers = {"X-API-Key": AUTH_TOKEN}
        if self.ua_string:
            headers["User-Agent"] = self.ua_string
        http_client.headers.update(headers)

        try:
            init_call = http_client.get(f"{self.endpoint}/solve", params=query_data, timeout=30)
            init_call.raise_for_status()
            job_id = init_call.json().get("taskid")
        except Exception:
            return None, None

        if not job_id:
            return None, None

        expiry = time.time() + timeout
        while time.time() < expiry:
            try:
                check = http_client.get(f"{self.endpoint}/task/{job_id}", timeout=30)
                if check.status_code == 200:
                    result = check.json()
                    state = result.get("status")
                    
                    if state == "success":
                        return result.get("uuid")
                    
                    if state in {"failed", "error", "not_found"}:
                        break
            except Exception:
                pass
            
            time.sleep(poll_interval + random.uniform(0, 0.5))

        return None, None
