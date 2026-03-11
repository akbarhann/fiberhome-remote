import requests
import random
import time
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

class FiberHomeRouter:
    """
    Standalone controller for FiberHome HG6145D2 routers.
    Supports login, encryption, and changing Wi-Fi settings.
    """
    def __init__(self, ip, username, password):
        self.router_url = f"http://{ip}"
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.sessionid = ""
        self.acs_random = ""
        
        # Standard headers to match browser behavior
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest"
        })

    def login(self):
        """Authenticates with the router using AES challenge-response."""
        ajax_url = f"{self.router_url}/cgi-bin/ajax"
        
        # 1. Get ACS Random Challenge
        resp = self.session.get(ajax_url, params={"ajaxmethod": "get_acs_random", "_": random.random()})
        data = resp.json()
        self.sessionid = data.get("sessionid", "")
        self.acs_random = data.get("acsRandom", "")
        
        if not (self.acs_random and self.sessionid):
            return False
            
        # 2. Key derivation: acs_random[6:-7] and IV = Key
        key = self.acs_random[6:-7].encode('utf-8')
        cipher = AES.new(key, AES.MODE_CBC, key)
        padded_password = pad(self.password.encode('utf-8'), AES.block_size)
        loginpd_hash = cipher.encrypt(padded_password).hex().upper()
        
        # 3. Submit Login
        payload = {
            "username": self.username,
            "loginpd": loginpd_hash,
            "port": "0",
            "sessionid": self.sessionid,
            "ajaxmethod": "do_login"
        }
        login_resp = self.session.post(ajax_url, data=payload)
        
        if '"login_result":0' in login_resp.text:
            self.session.headers.update({"Referer": f"{self.router_url}/html/index.html"})
            return True
        return False

    def fh_encrypt(self, text):
        """Encrypts data for router (SSID, PSK) returning UPPERCASE HEX."""
        if not self.acs_random: self.login()
        key = self.acs_random[6:-7].encode('utf-8')
        cipher = AES.new(key, AES.MODE_CBC, key)
        padded = pad(text.encode('utf-8'), AES.block_size)
        return cipher.encrypt(padded).hex().upper()

    def fh_decrypt(self, hex_str):
        """Decrypts HEX string from router back to plain text."""
        if not self.acs_random or not hex_str: return ""
        key = self.acs_random[6:-7].encode('utf-8')
        cipher = AES.new(key, AES.MODE_CBC, key)
        try:
            return unpad(cipher.decrypt(bytes.fromhex(hex_str)), AES.block_size).decode('utf-8')
        except:
            return hex_str

    def send_request(self, payload_method, method="POST"):
        """Sends AJAX request with session refresh for POST commands."""
        ajax_url = f"{self.router_url}/cgi-bin/ajax"
        if not self.sessionid: self.login()
        
        final_payload = payload_method.copy()
        
        if method.upper() == "POST":
            # Refresh sessionid first (Crucial for persistence)
            try:
                refresh_resp = self.session.get(f"{ajax_url}?ajaxmethod=get_refresh_sessionid&sessionid={self.sessionid}&_={random.random()}")
                new_sid = refresh_resp.json().get("sessionid")
                if new_sid: self.sessionid = new_sid
            except: pass
            
            final_payload["sessionid"] = self.sessionid
            final_payload["_"] = str(random.random())
            
            headers = {
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Referer": f"{self.router_url}/html/index.html",
                "Origin": self.router_url
            }
            resp = self.session.post(f"{ajax_url}?sessionid={self.sessionid}", data=final_payload, headers=headers)
        else:
            final_payload["sessionid"] = self.sessionid
            final_payload["_"] = str(random.random())
            resp = self.session.get(ajax_url, params=final_payload)
            
        try:
            if resp.text.strip() == "{}": return {"status": "ok"}
            return resp.json()
        except:
            return resp.text

    def get_wifi_status(self, band="5g"):
        """Helper to get SSID and Password for a specific band."""
        ajax_get = "get_wifi_status_5G" if band == "5g" else "get_wifi_status_2G"
        resp = self.send_request({"ajaxmethod": ajax_get}, method="GET")
        wifi_key = "wifi_status5g" if band == "5g" else "wifi_status2g"
        data = resp.get(wifi_key, [{}])[0]
        return {
            "ssid": self.fh_decrypt(data.get("SSID", "")),
            "password": self.fh_decrypt(data.get("PreSharedKey", "")),
            "raw": data
        }
