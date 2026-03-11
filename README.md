# FiberHome Remote Wi-Fi Control

A standalone Python library to control FiberHome HG6145D2 routers. This library allows you to programmatically change Wi-Fi SSIDs and Passwords by interacting directly with the router's AJAX backend.

## Features
- **Direct Backend Interaction**: Bypasses the web UI for faster execution.
- **AES-128 Encryption**: Implements the router's custom `fhencrypt` logic (AES-CBC with PKCS7 padding).
- **Session Persistence**: Handles session token refreshes automatically to ensure settings are saved.
- **Band Support**: Works for both 2.4GHz and 5GHz Wi-Fi bands.

## Technical Details
The router uses a challenge-response mechanism. It provides an `acs_random` string which is used to derive the AES key:
`Key = acs_random[6:-7]`
The same string is used as the Initialization Vector (IV).
All sensitive data (SSID and PreSharedKey) must be encrypted and sent as an **UPPERCASE HEXADECIMAL** string.

## Installation
```bash
pip install -r requirements.txt
```

## Usage
Edit `example.py` with your router's IP and credentials, then run:
```bash
python example.py
```

## Security Note
This tool handles router credentials and Wi-Fi passwords. Ensure your `.env` files or hardcoded credentials are not pushed to public repositories.
