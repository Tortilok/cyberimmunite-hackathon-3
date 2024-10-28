from flask import Flask, jsonify
from pathlib import Path
import json
import random
import time
import requests
import os
import threading
from werkzeug.exceptions import HTTPException

MANAGMENT_URL = 'http://management_system:8000'

HOST = '0.0.0.0'
PORT = 8000
MODULE_NAME = os.getenv('MODULE_NAME')
app = Flask(__name__)


class Car:
    def __init__(self, brand, has_air_conditioner=False, has_heater=False, has_navigator=False):
        self.speed = 0
        self.coordinates = (0, 0)
        self.occupied_by = None
        self.start_time = None
        self.brand = brand
        self.has_air_conditioner = has_air_conditioner
        self.has_heater = has_heater
        self.has_navigator = has_navigator
        self.is_running = False
        self.tariff = None

    def start(self):
        if not self.is_running:
            self.is_running = True
            self.start_time = time.time()
            return f"{self.brand} поездка началась."
        else:
            return f"{self.brand} поездка ещё идет."

    def stop(self):
        if self.is_running:
            self.is_running = False
            self.speed = 0
            self.occupied_by = None
            return f"{self.brand} поездка завершена."
        else:
            return f"{self.brand} на парковке."

    def get_status(self):
        elapsed_time = 0
        if self.start_time is not None and self.is_running:
            elapsed_time = round(time.time() - self.start_time, 2)  # Время в секундах
        return {
            "brand": self.brand,
            "is_running": self.is_running,
            "speed": self.speed,
            "coordinates": self.coordinates,
            "occupied_by": self.occupied_by,
            "trip_time": elapsed_time,
            "has_air_conditioner": self.has_air_conditioner,
            "has_heater": self.has_heater,
            "has_navigator": self.has_navigator,
            "tariff ": self.tariff
        }

    def update_coordinates(self, x, y):
        self.coordinates = (x, y)

    def set_speed(self, speed):
        if self.is_running:
            self.speed = speed
            return f"Скорость {self.brand} изменена на {self.speed} км/ч."
        else:
            return f"{self.brand} не парковке, скорость не может быть изменена."

    def occupy(self, person, tarif):
        self.occupied_by = person
        self.tariff = tarif
        return f"{self.brand} арендован {self.occupied_by}."


def simulate_drive(car):
    while car.is_running:
        new_speed = random.randint(10, 100)
        car.set_speed(new_speed)

        x_change = random.uniform(-2, 2)
        y_change = random.uniform(-2, 2)
        current_coordinates = car.coordinates
        new_coordinates = (current_coordinates[0] + x_change, current_coordinates[1] + y_change)
        car.update_coordinates(*new_coordinates)

        print(f"{car.brand} Скорость: {car.speed:.2f} км/ч, Координаты: {car.coordinates}")
        status = car.get_status()
        requests.post(f'{MANAGMENT_URL}/telemetry/{car.brand}', json={'status': status})
        time.sleep(1)


# Функция для загрузки автомобилей из JSON файла
def load_cars_from_json(file_path):
    with open(file_path, 'r') as file:
        cars_data = json.load(file)
        return [Car(**car) for car in cars_data]


BASE_DIR = Path(__file__).resolve().parent.parent
# Загружаем список автомобилей из файла
cars = load_cars_from_json(f'{BASE_DIR}/data/cars.json')


@app.route('/car/status/all', methods=['GET'])
def get_all_car_statuses():
    statuses = [car.get_status() for car in cars]
    return jsonify(statuses)


@app.route('/car/start/<string:brand>', methods=['POST'])
def start_car(brand):
    car = next((car for car in cars if car.brand.lower() == brand.lower()), None)
    if car:
        message = car.start()
        thread = threading.Thread(target=simulate_drive, args=(car,))
        thread.start()
        return jsonify({"message": message})
    else:
        return jsonify({"error": "Автомобиль не найден."}), 404


@app.route('/car/stop/<string:brand>', methods=['POST'])
def stop_car(brand):
    car = next((car for car in cars if car.brand.lower() == brand.lower()), None)
    if car:
        status = car.get_status()
        invoice_id = requests.post(f'{MANAGMENT_URL}/return/{car.occupied_by}', json={'status': status})
        if invoice_id.status_code == 200:
            invoice_id = invoice_id.json()['id']
            message = car.stop()
            return jsonify({"message": message, 'invoice_id': invoice_id})
        else:
            message = car.stop()
            return jsonify({"message": message}), 404
    else:
        return jsonify({"error": "Автомобиль не найден."}), 404


@app.route('/car/status/<string:brand>', methods=['GET'])
def get_car_status(brand):
    car = next((car for car in cars if car.brand.lower() == brand.lower()), None)
    if car:
        status = car.get_status()
        return jsonify(status)
    else:
        return jsonify({"error": "Автомобиль не найден."}), 404


@app.route('/car/occupy/<string:person>', methods=['POST'])
def occupy_car(person):
    response = requests.post(f'{MANAGMENT_URL}/access/{person}')
    if response.status_code == 200:
        brand = response.json()['car']
        car = next((car for car in cars if car.brand.lower() == brand.lower()), None)
        if car and person is not None:
            tariff = response.json()['tariff']
            message = car.occupy(person, tariff)
            return jsonify({"access": True, "car": car.brand, "message": message})
        else:
            return jsonify({"access": False, "message": "Автомобиль не найден или не указан клиент."}), 404
    else:
        return jsonify({"access": False, "message": "Доступ до автомобиля не разрешен."}), 404


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
