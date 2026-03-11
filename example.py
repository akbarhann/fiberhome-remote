from router_utils import FiberHomeRouter
import time
import json

# --- CONFIGURATION ---
ROUTER_IP = "192.168.1.1"
USER = "user"
PASS = "user1234"

def main():
    router = FiberHomeRouter(ROUTER_IP, USER, PASS)
    
    print(f"[*] Connecting to router at {ROUTER_IP}...")
    if not router.login():
        print("[!] Login failed. Check credentials.")
        return

    print("[SUCCESS] Logged in.")

    # 1. Get current status
    print("\n[*] Fetching current 5G Wi-Fi status...")
    status = router.get_wifi_status(band="5g")
    print(f"    Current SSID: {status['ssid']}")
    print(f"    Current Pwd : {status['password']}")

    # 2. Change Settings
    new_ssid = "FiberHome_Remote"
    new_pass = "sasukeee_123"

    print(f"\n[*] Changing Wi-Fi to:")
    print(f"    New SSID: {new_ssid}")
    print(f"    New Pwd : {new_pass}")

    # Build payload using current data as template
    main_wifi = status['raw']
    payload = {
        "wifiIndex": main_wifi.get("index", 5),
        "Enable": main_wifi.get("Enable", "1"),
        "SSID": router.fh_encrypt(new_ssid),
        "X_FH_SSIDHide": main_wifi.get("X_FH_SSIDHide", "0"),
        "BeaconType": main_wifi.get("BeaconType", "WPA/WPA2"),
        "WPAEncryptionModes": main_wifi.get("WPAEncryptionModes", "TKIPandAESEncryption"),
        "PreSharedKey": router.fh_encrypt(new_pass),
        "X_FH_WPARekeyInterval": main_wifi.get("X_FH_WPARekeyInterval", "86400"),
        "device_type": "HG6145D2",
        "ajaxmethod": "setWlanAdvancedCfg_5G"
    }

    resp = router.send_request(payload, method="POST")
    if resp and resp.get("status") == "ok":
        print("[SUCCESS] Settings accepted by router.")
        print("[*] Waiting 5 seconds for router to apply changes...")
        time.sleep(5)
        
        # 3. Verify
        print("[*] Verifying new settings...")
        final_status = router.get_wifi_status(band="5g")
        if final_status['ssid'] == new_ssid and final_status['password'] == new_pass:
            print("[VERIFIED] Changes are persistent!")
        else:
            print("[WARNING] Verification failed. Settings might not have saved.")
            print(f"    Found SSID: {final_status['ssid']}")
    else:
        print(f"[!] Router rejected the request: {resp}")

if __name__ == "__main__":
    main()
