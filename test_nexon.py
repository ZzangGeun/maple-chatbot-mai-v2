# test_nexon.py
import urllib.request
import urllib.error
import json

url = 'http://127.0.0.1:8000/api/v1/character/search/?name=%EB%AC%B4%EB%8B%B9%ED%96%B5%EC%8A%A4%ED%84%B0'
print(f"Requesting URL: {url}")

try:
    resp = urllib.request.urlopen(url)
    print("SUCCESS STATUS:", resp.status)
    print("BODY:", json.loads(resp.read().decode('utf-8')))
except urllib.error.HTTPError as e:
    print("HTTP ERROR CODE:", e.code)
    try:
        body = e.read().decode('utf-8')
        print("HTTP ERROR BODY:", json.loads(body))
    except Exception as ex:
        print("Failed to read/parse body:", ex)
        print("Raw body was:", body if 'body' in locals() else 'None')
except Exception as e:
    print("OTHER ERROR:", e)
