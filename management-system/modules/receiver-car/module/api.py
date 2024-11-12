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


def send_to_control_drive(details):
    if not details:
        abort(400)

    details["deliver_to"] = "control-drive"
    details["source"] = MODULE_NAME
    details["id"] = uuid4().__str__()

    try:
        _requests_queue.put(details)
        print(f"{MODULE_NAME} update event: {details}")
    except Exception as e:
        print("[RECEIVER_CAR_DEBUG] malformed request", e)
        abort(400)


# Handler for telemtry car
@app.route('/telemetry/<string:brand>', methods=['POST'])
def telemetry(brand):
    data = request.json['status']
    details_to_send = {"data": data,
                       "operation": "telemetry",
                       "car": brand}
    send_to_control_drive(details_to_send)
    return jsonify("ok")


@app.route('/car/status/all', methods=['POST'])
def cars():
    data = request.json
    cars = data.get("cars")
    details_to_send = {"data": cars,
                       "operation": "answer_cars"}
    send_to_control_drive(details_to_send)
    return jsonify("ok")


@app.route('/car/status', methods=['POST'])
def status():
    data = request.json
    status = data.get("status")
    details_to_send = {"data": status,
                       "operation": "answer_status"}
    send_to_control_drive(details_to_send)
    return jsonify("ok")


# Handler for return car
@app.route('/return/<string:name>', methods=['POST'])
def return_car(name):
    data = request.json
    trip_time = data.get('status')['trip_time']
    details_to_send = {"data": data,
                       "trip_time": trip_time,
                       "name": name,
                       "operation": "return"}
    send_to_control_drive(details_to_send)
    return jsonify("ok")


# Handler for access car
@app.route('/access/<string:name>', methods=['POST'])
def access(name):
    details_to_send = {"operation": "access",
                       "name": name}
    send_to_control_drive(details_to_send)
    return jsonify("ok")


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
