import os
import time
import json
import threading
import multiprocessing

from uuid import uuid4
from flask import Flask, request, jsonify, abort
from werkzeug.exceptions import HTTPException


# Константы
PAYMENT_URL = 'http://payment_system:8000'
HOST: str = "0.0.0.0"
PORT: int = int(os.getenv("MODULE_PORT"))
MODULE_NAME: str = os.getenv("MODULE_NAME")


# Очереди задач и ответов
_requests_queue: multiprocessing.Queue = None
_response_queue: multiprocessing.Queue = None


app = Flask(__name__)


def counter_prepayment(car):
    counter = 0
    if car['has_air_conditioner']:
        counter += 7
    if car['has_heater']:
        counter += 5
    if car['has_navigator']:
        counter += 10
    return counter


def counter_payment(trip_time, tariff, experience):
    tariff_min = 2
    tariff_hours = 80
    counter = 0
    if tariff == 'min':
        if experience < 1:
            counter += round(trip_time * tariff_min*2, 2)
        else:
            counter += round(trip_time * tariff_min/experience, 2)
    elif tariff == 'hour':
        if experience < 1:
            counter += round(trip_time * tariff_hours*2, 2)
        else:
            counter += round(trip_time / 10 * tariff_hours/experience, 2) 
    return counter


@app.get("/")
def index():
    print("Connected to", HOST, PORT)
    return {"message": "ok"}

'''# Handler for payment system
@app.route('/confirm_prepayment/<string:name>', methods=['POST'])
def confirm_prepayment(name):
    if client:
        client.prepayment_status = request.json['status']
        db.session.commit()
        print(f'Потверждена предоплата: {request.json}')
        return jsonify(request.json)
'''

'''# Handler for payment system
@app.route('/confirm_payment/<string:name>', methods=['POST'])
def confirm_payment(name):
    client = Client.query.filter_by(client_name=name).one_or_none()
    if client:
        print(f'Потверждена оплата: {request.json}')
        response = requests.get(f'{PAYMENT_URL}/invoices/{request.json['id']}/receipt')
        if response.status_code == 200:
            receipt = response.json()['receipt']
            final_amount = receipt['amount'] + client.prepayment
            created_at = receipt['created_at']
            final_receipt = {
                'car': client.car,
                'name': client.client_name,
                'final_amount': final_amount,
                'created_at': created_at,
                'elapsed_time': client.elapsed_time,
                'tarif': client.tariff,

            }
            client.car = ''
            client.prepayment = ''
            client.prepayment_status = ''
            client.tariff = ''
            client.elapsed_time = 0
            db.session.commit()
        print(f'Финальный чек: {final_receipt}')
        return jsonify(final_receipt)'''




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
