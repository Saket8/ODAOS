import sys
import json
from fastapi.testclient import TestClient
from src.api.main import app
from src.api.middleware.auth import verify_admin

app.dependency_overrides[verify_admin] = lambda: 'admin'

def test_prompts():
    print('Testing brm-payment-002: Payment Method Distribution...')
    with TestClient(app) as client:
        response = client.post(
            '/api/prompts/brm-payment-002/execute',
            json={'parameters': {}}
        )
        if response.status_code == 200:
            for line in response.iter_lines():
                if b'chart' in line:
                    event = json.loads(line.decode('utf-8').replace('data: ', ''))
                    data = event['data']
                    print(f"  -> Chart Title: {data.get('title')}")
                    print(f"  -> Chart Type: {data.get('type')}")
                    print(f"  -> Data Example: {data.get('data')[0] if data.get('data') else 'Empty'}")
                    
test_prompts()
