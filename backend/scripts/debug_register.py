import sys
import os
import traceback

# Ensure project root is on sys.path so `app` package can be imported
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

payload = {"email": "frontend_test@example.com", "password": "TestPass123!", "full_name": "Frontend Test"}

try:
    resp = client.post('/auth/register', json=payload)
    print('STATUS', resp.status_code)
    try:
        print('BODY', resp.json())
    except Exception:
        print('BODY_TEXT', resp.text)
except Exception as e:
    print('EXCEPTION')
    traceback.print_exc()
