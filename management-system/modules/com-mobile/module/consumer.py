import os
import json
import threading
import multiprocessing
import requests
from confluent_kafka import Consumer, OFFSET_BEGINNING

from .producer import proceed_to_deliver
MOBILE_URL = 'http://mobile-client:8000'

_response_queue: multiprocessing.Queue = None
MODULE_NAME = os.getenv("MODULE_NAME")


def payment(data):
    requests.post(f'{MOBILE_URL}/payment', json=data)
    return None


def final(data):
    requests.post(f'{MOBILE_URL}/final', json=data)
    return None


def handle_event(id, details_str):
    global _response_queue

    """ Обработчик входящих в модуль задач. """
    details = json.loads(details_str)

    source: str = details.get("source")
    deliver_to: str = details.get("deliver_to")
    data: str = details.get("data")
    operation: str = details.get("operation")

    print(f"[info] handling event {id}, "
          f"{source}->{deliver_to}: {operation}")
   
    if operation == "get_tariff":
        print("[COM_MOBILE_DEBUG] catched new send:", details)
        _response_queue.put(details)
    elif operation == "answer_cars":
        print("[COM_MOBILE_DEBUG] catched new send:", details)
        _response_queue.put(details)
    elif operation == "get_prepayment_id":
        print("[COM_MOBILE_DEBUG] catched new send:", details)
        _response_queue.put(details)
    elif operation == "get_payment_id":
        print("[COM_MOBILE_DEBUG] catched new send:", details)
        return payment(data)
    elif operation == "final_receipt":
        print("[COM_MOBILE_DEBUG] catched new send:", details)
        return final(data)


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


def start_consumer(args, config, response_queue):
    global _response_queue
    _response_queue = response_queue

    print(f'{MODULE_NAME}_consumer started')

    threading.Thread(target=lambda: consumer_job(args, config)).start()