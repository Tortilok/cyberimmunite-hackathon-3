import os
import time
import json
import threading
import multiprocessing

from uuid import uuid4
from flask import Flask, request, jsonify, abort
from werkzeug.exceptions import HTTPException


# Константы
HOST: str = "0.0.0.0"
PORT: int = int(os.getenv("MODULE_PORT"))
MODULE_NAME: str = os.getenv("MODULE_NAME")


# Очереди задач и ответов
_requests_queue: multiprocessing.Queue = None
_response_queue: multiprocessing.Queue = None


app = Flask(__name__)


@app.get("/")
def index():
    print("Connected to", HOST, PORT)
    return {"message": "ok"}

'''# List all avaible cars
@app.route('/cars', methods=['GET'])
def get_all_cars():
    response = requests.get(f'{CARS_URL}/car/status/all')
    if response.status_code == 200:
        cars = response.json()
        avaible_cars = [car['brand'] for car in cars if car['occupied_by'] is None]
        return jsonify(avaible_cars)
    else:
        return jsonify([])

# List all avaible tariff
@app.route('/tariff', methods=['GET'])
def get_tariff():
    return jsonify(TARIFF)


# Select car and prepayment calculation
@app.route('/select/car/<string:brand>', methods=['POST'])
def select_car(brand):
    data = request.json
    name = data.get('client_name')
    experience = data.get('experience')
    tariff = data.get('tariff')
    response = requests.post(f'{PAYMENT_URL}/clients', json={'name': name})
    if response.status_code == 201 or 200:
        client = Client.query.filter_by(client_name=name).one_or_none()
        if client is None:
            client = Client(client_name=name, experience=experience)
            db.session.add(client)
            db.session.commit()
        client.car = brand
        client.tariff = tariff
        car = requests.get(f'{CARS_URL}/car/status/{client.car}').json()
        amount = counter_prepayment(car)
        client.prepayment = amount
        db.session.commit()
        print(f'Сформирована предоплата: {client.prepayment}')
        response = requests.post(f'{PAYMENT_URL}/clients/{response.json()[0]['id']}/prepayment', json={'amount': client.prepayment})

        return jsonify(response.json())
    else:
        print("Ошибка при создании клиента:", client.json())
        return None
'''

# Обработчик ошибок
@app.errorhandler(HTTPException)
def handle_exception(e):
    return jsonify({
        "status": e.code,
        "name": e.name,
    }), e.code


def start_web(requests_queue, response_queue):
    global _requests_queue
    global _response_queue

    _requests_queue = requests_queue
    _response_queue = response_queue

    threading.Thread(target=lambda: app.run(
        host=HOST, port=PORT, debug=True, use_reloader=False
    )).start()
