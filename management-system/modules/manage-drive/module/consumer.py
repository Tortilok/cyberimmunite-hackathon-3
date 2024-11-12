import os
import json
import threading

from uuid import uuid4
from confluent_kafka import Consumer, OFFSET_BEGINNING

from .producer import proceed_to_deliver


MODULE_NAME: str = os.getenv("MODULE_NAME")


def send_to_verify(id, details):
    details["deliver_to"] = "verify"
    proceed_to_deliver(id, details)


def send_to_profile_client(id, details):
    details["deliver_to"] = "profile-client"
    proceed_to_deliver(id, details)


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
        return send_to_verify(id, details)
    elif operation == "answer_cars":
        details["data"] = [car['brand'] for car in data if car['occupied_by'] is None]
        return send_to_profile_client(id, details)
    elif operation == "get_status":
        return send_to_verify(id, details)
    elif operation == "answer_status":
        return send_to_profile_client(id, details)
    elif operation == "access":
        return send_to_profile_client(id, details)
    elif operation == "confirm_access":
        return send_to_verify(id, details)
    elif operation == "return":
        return send_to_profile_client(id, details)
    elif operation == "telemetry":
        speed = data.get('speed')
        coordinates = data.get('coordinates')
        print(f"{details["car"]} Скорость: {speed:.2f} км/ч, Координаты: {coordinates}")


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