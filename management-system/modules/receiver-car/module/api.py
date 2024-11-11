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

'''# Handler for telemtry car
@app.route('/telemetry/<string:brand>', methods=['POST'])
def telemetry(brand):
    data = request.json['status']
    speed = data.get('speed')
    coordinates = data.get('coordinates')
    print(f'f"{brand} Скорость: {speed:.2f} км/ч, Координаты: {coordinates}"')
    return jsonify(None)'''

'''# Handler for return car
@app.route('/return/<string:name>', methods=['POST'])
def return_car(name):
    client = Client.query.filter_by(client_name=name).one_or_none()
    if client:
        data = request.json
        trip_time = data.get('status')['trip_time']
        client.elapsed_time = trip_time
        db.session.commit()
        amount = counter_payment(trip_time, client.tariff, client.experience)
        response = requests.post(f'{PAYMENT_URL}/clients', json={'name': name})
        if response.status_code == 201 or 200:
            response = requests.post(f'{PAYMENT_URL}/invoices', json={'client_id': response.json()[0]['id'], 'amount': amount})
            invoice = response.json()
            return jsonify(invoice)
        else:
            print('Нет связи с банком')
        return jsonify({'error': True}), 404
    else:
        print(f"Такой клиент{name} не арендовал машину.")
        return jsonify({'error': True}), 404
    
# Handler for access car
@app.route('/access/<string:name>', methods=['POST'])
def access(name):
    client = Client.query.filter_by(client_name=name).one_or_none()
    if client:
        if client.prepayment_status == 'paid':
            print(f"Доступ разрешен {name}")
            return jsonify({'access': True, 'tariff': client.tariff, 'car': client.car})
        else:
            print(f"Доступ запрещён {name}")
            return jsonify({'access': False}), 405
    else:
        print(f"Доступ запрещён {name}")
        return jsonify({'access': False}), 404'''


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
