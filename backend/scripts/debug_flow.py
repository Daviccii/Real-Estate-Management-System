import sys, os, traceback
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

email = 'frontend_test@example.com'
password = 'TestPass123!'

print('Registering user...')
try:
    r = client.post('/auth/register', json={'email':email,'password':password,'full_name':'Frontend Test'})
    print('REGISTER', r.status_code, r.text)
except Exception:
    traceback.print_exc()

print('Logging in...')
try:
    r = client.post('/auth/login', json={'email':email,'password':password})
    print('LOGIN', r.status_code, r.text)
    data = r.json() if r.status_code==200 else None
    if data and 'access_token' in data:
        token = data['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        print('GET /users/me')
        r2 = client.get('/users/me', headers=headers)
        print('ME', r2.status_code, r2.text)

        print('Testing /auth/refresh')
        r3 = client.post('/auth/refresh')
        print('REFRESH', r3.status_code, r3.text)
except Exception:
    traceback.print_exc()
