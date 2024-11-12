import requests
import time


MOBILE_URL = 'http://0.0.0.0:8002'
client = {"name": "Иван Иванов", "experience": 1}

# Тест базового сценария поездки клиента от аренды до завершения поездки
def test_full_func():
    prepayment = requests.post(f'{MOBILE_URL}/cars', json=client)
    time.sleep(2)
    response = requests.post(f'{MOBILE_URL}/prepayment', json=prepayment.json())
    time.sleep(2)
    car = requests.post(f'{MOBILE_URL}/start_drive', json=client)
    time.sleep(5)  # Сколько времени будет длиться поездка
    invoice = requests.post(f'{MOBILE_URL}/stop_drive', json=client)
    time.sleep(2)
    response = requests.post(f'{MOBILE_URL}/final_pay', json=invoice.json())
    time.sleep(2)
    assert response.status_code == 200
    data = response.json()
    assert 'car' in data
    assert 'created_at' in data
    assert 'elapsed_time' in data
    assert 'name' in data
    assert 'final_amount' in data
    assert 'tarif' in data
