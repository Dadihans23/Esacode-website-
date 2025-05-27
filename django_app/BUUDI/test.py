import requests

url = "https://panel.smsing.app/smsAPI"
params = {
    "sendsms": "true",
    "apikey": "HL6UNLEaP8UASb5xDVurPDNbHPbPlFWm",
    "apitoken": "FzkA1748105614",
    "type": "sms",
    "from": "OTP",
    "to": "0151655248",
    "text": "hello"
}
headers = {
    "User-Agent": "Mozilla/5.0"
}

try:
    response = requests.get(url, params=params, headers=headers, timeout=10)
    print(response.status_code)
    print(response.text)
except requests.exceptions.RequestException as e:
    print("Erreur de requête :", e)
