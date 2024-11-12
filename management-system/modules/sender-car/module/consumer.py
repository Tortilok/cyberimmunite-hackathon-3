import os
import json
import threading
import requests

from uuid import uuid4
from confluent_kafka import Consumer, OFFSET_BEGINNING

from .producer import proceed_to_deliver

CARS_URL = 'http://cars:8000'

MODULE_NAME: str = os.getenv("MODULE_NAME")


def get_cars():
    requests.get(f'{CARS_URL}/car/status/all')
    return None


def confirm_access(access):
    name = access["name"]
    requests.post(f'{CARS_URL}/access/{name}', json=access)
    return None


def get_status_car(car):
    requests.get(f'{CARS_URL}/car/status/{car}')
    return None


def stop_car(car):
    requests.get(f'{CARS_URL}/emergency/{car}')
    return None


def handle_event(id, details_str):
    """ Обработчик входящих в модуль задач. """
    details = json.loads(details_str)

    source: str = details.get("source")
    deliver_to: str = details.get("deliver_to")
    data: str = details.get("data")
    operation: str = details.get("operation")

    print(f"[info] handling event {id}, "
          f"{source}->{deliver_to}: {operation}")

    if operation == "get_cars":
        return get_cars()
    if operation == "get_status":
        return get_status_car(data)
    if operation == "confirm_access":
        return confirm_access(details["access"])
    if operation == "stop":
        return stop_car(details["car"])

def consumer_job(args, config):
    consumer = Consumer(config)

    def reset_offset(verifier_consumer, partitions):
        if not args.reset:
            return

        for p in partitions:
            p.offset = OFFSET_BEGINNING
        verifier_consumer.assign(partitions)

    topic = MODULE_NAME
    consumer.subscribe([topic], on_assign=reset_offset)

    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                pass
            elif msg.error():
                print(f"[error] {msg.error()}")
            else:
                try:
                    id = msg.key().decode('utf-8')
                    details_str = msg.value().decode('utf-8')
                    handle_event(id, details_str)
                except Exception as e:
                    print(f"[error] Malformed event received from " \
                          f"topic {topic}: {msg.value()}. {e}")
    except KeyboardInterrupt:
        pass

    finally:
        consumer.close()

def start_consumer(args, config):
    print(f'{MODULE_NAME}_consumer started')
    threading.Thread(target=lambda: consumer_job(args, config)).start()