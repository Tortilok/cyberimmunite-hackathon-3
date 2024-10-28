import requests

MOBILE_URL = 'http://0.0.0.0:8002'
client = {"name": "Иван Иванов", "experience": 3}

def test_get_prepayment():
    response = requests.post(f'{MOBILE_URL}/cars', json=client)
    assert response.status_code == 200
    data = response.json()
    assert 'id' in data

def test_start_car():
    response = requests.post(f'{MOBILE_URL}/start_drive', json=client)
    assert response.status_code == 404
    assert response.json()["error"] == "Доступ на данную операцию не разрешён"

def test_stop_car():
    response = requests.post(f'{MOBILE_URL}/stop_drive', json=client)
    assert response.status_code == 404
    assert response.json()["error"] == "Доступ на данную операцию не разрешён"

def test_pay_prepayment():
    prepayment = requests.post(f'{MOBILE_URL}/cars', json=client)
    response = requests.post(f'{MOBILE_URL}/prepayment', json=prepayment.json())
    assert response.status_code == 200
    data = response.json()
    assert 'status' in data
    assert data['status'] == 'paid'

def test_final_pay():
    response = requests.post(f'{MOBILE_URL}/final_pay', json={"invoice_id": 1000})
    assert response.status_code == 404
    assert response.json()["name"] == "Not Found"