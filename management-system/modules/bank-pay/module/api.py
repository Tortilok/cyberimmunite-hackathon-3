import os
import time
import json
import threading
import multiprocessing
import requests
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


def send_to_profile_client(details):
    if not details:
        abort(400)

    details["deliver_to"] = "profile-client"
    details["source"] = MODULE_NAME
    details["id"] = uuid4().__str__()

    try:
        _requests_queue.put(details)
        print(f"{MODULE_NAME} update event: {details}")
    except Exception as e:
        print("[BANK-PAY_DEBUG] malformed request", e)
        abort(400)


# Handler for payment system
@app.route('/confirm_prepayment/<string:name>', methods=['POST'])
def confirm_prepayment(name):
    details_to_send = {
        "operation": "confirm_prepayment",
        "status": request.json['status'],
        "name": name
    }
    send_to_profile_client(details_to_send)
    print(f'Потверждена предоплата: {request.json}')
    return jsonify(request.json)


# Handler for payment system
@app.route('/confirm_payment/<string:name>', methods=['POST'])
def confirm_payment(name):
    print(f'Потверждена оплата: {request.json}')
    response = requests.get(f'{PAYMENT_URL}/invoices/{request.json['id']}/receipt')
    if response.status_code == 200:
        receipt = response.json()['receipt']
        details_to_send = {"operation": "confirm_payment", "receipt": receipt, "name": name}
        send_to_profile_client(details_to_send)
        return "ok"




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
