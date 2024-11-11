import requests
import random
import time
import os
from flask import Flask, jsonify, request
import threading
from werkzeug.exceptions import HTTPException

HOST = '0.0.0.0'
PORT = 8000
MODULE_NAME = os.getenv('MODULE_NAME')
app = Flask(__name__)

MANAGMENT_URL = 'http://management_system:8000'
PAYMENT_URL = 'http://payment_system:8000'
CARS_URL = 'http://cars:8000'


# Выбор и запрос авто (автоматически выбирает из свободных машин и выбирает тариф)
@app.route('/cars', methods=['POST'])
def get_cars():
    data = request.json
    name = data.get('name')
    experience = data.get('experience')
    cars = get_car()
    while len(cars) == 0:
            cars = get_car()
            time.sleep(1)
    tariff = get_tariff()
    selected_auto = cars[random.randint(0, len(cars)-1)]
    selected_tariff = tariff[random.randint(0, len(tariff)-1)]
    print(f"Выбранный автомобиль {selected_auto} и тариф {selected_tariff}")
    prepayment = select_auto_and_prepayment(name, experience, selected_auto, selected_tariff)

    return jsonify(prepayment)

# Начало поездки
@app.route('/start_drive', methods=['POST'])
def start_drive():
    data = request.json
    name = data.get('name')
    client_access = access(name)
    if client_access['access']:
        response = start_travel(client_access['car'])
        return jsonify(response)
    else:
        return jsonify({"error": "Доступ на данную операцию не разрешён"}), 404


@app.route('/stop_drive', methods=['POST'])
def stop_drive():
    data = request.json
    name = data.get('name')
    client_access = access(name)
    if client_access['access']:
        invoice = stop_travel(client_access['car'])
        return jsonify(invoice)
    else:
        return jsonify({"error": "Доступ на данную операцию не разрешён"}), 404


@app.route('/prepayment', methods=['POST'])
def prepayment():
    data = request.json
    prepayment_id = data.get('id')
    prepayment = confirm_prepayment(prepayment_id)
    if prepayment.status_code == 200:
        return jsonify(prepayment.json())
    else:
        return jsonify(prepayment.json()), 404


@app.route('/final_pay', methods=['POST'])
def final_pay():
    data = request.json
    invoice_id = data.get('invoice_id')
    final_receipt = confirm_payment(invoice_id)
    if final_receipt.status_code == 200:
        return jsonify(final_receipt.json()['final_receipt'])
    else:
        return jsonify(final_receipt.json()), 404

def get_car():
    response = requests.get(f'{MANAGMENT_URL}/cars')
    if response.status_code == 200:
        print("Информация о доступных автомобилях:", response.json())
        return response.json()
    else:
        print("Ошибка при получении доступных автомобилей:", response.json())


def get_tariff():
    response = requests.get(f'{MANAGMENT_URL}/tariff')
    if response.status_code == 200:
        print("Информация о доступных тарифах:", response.json())
        return response.json()
    else:
        print("Ошибка при получении доступных тарифов:", response.json())

def select_auto_and_prepayment(name, experience, brand, tariff):
    response = requests.post(f'{MANAGMENT_URL}/select/car/{brand}', json={'client_name': name, 'experience': experience, 'tariff': tariff})
    if response.status_code == 200:
        print("Информация о предоплате:", response.json())
        return response.json()
    else:
        print("Ошибка при получении информации о предоплате:", response.json())

def confirm_prepayment(prepayment_id):
    response = requests.post(f'{PAYMENT_URL}/prepayment/{prepayment_id}/confirm')
    if response.status_code == 200:
        print("Предоплата подтверждена:", response.json())
        return response
    else:
        print("Ошибка при подтверждении предоплаты:", response.json())
        return response

def confirm_payment(invoice_id: int):
    response = requests.post(f'{PAYMENT_URL}/invoices/{invoice_id}/confirm')
    if response.status_code == 200:
        print("Оплата потверждена:", response.json())
        print("Финальный чек:", response.json()['final_receipt'])
        return response
    else:
        print("Ошибка при подтверждении оплаты:", response.json())
        return response

def access(name):
    response = requests.post(f'{CARS_URL}/car/occupy/{name}')
    if response.status_code == 200:
        print(response.json()['message'])
        return response.json()
    else:
        print(response.json()['message'])
        return response.json()

def start_travel(brand):
    response = requests.post(f'{CARS_URL}/car/start/{brand}')
    if response.status_code == 200:
        print(response.json()['message'])
        return response.json()
    else:
        print(response.json()['message'])
        return response.json()


def stop_travel(brand):
    response = requests.post(f'{CARS_URL}/car/stop/{brand}')
    if response.status_code == 200:
        print(response.json()['message'])
        return response.json()
    else:
        print(response.json()['message'])


@app.errorhandler(HTTPException)
def handle_exception(e):
    response = e.get_response()
    return jsonify({
        "status": e.code,
        "name": e.name,
    }), e.code


def start_web():
    threading.Thread(target=lambda: app.run(
        host=HOST, port=PORT, debug=True, use_reloader=False
    )).start()

