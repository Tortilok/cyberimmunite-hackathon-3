import os
import json
import threading

from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from uuid import uuid4
from confluent_kafka import Consumer, OFFSET_BEGINNING

from .producer import proceed_to_deliver

DATABASE_URL = 'sqlite:///clients.db'
engine = create_engine(DATABASE_URL, echo=True)
Base = declarative_base()

TARIFF = ["min", "hour"]
MODULE_NAME: str = os.getenv("MODULE_NAME")


# Модель для хранения поездок клиентов
class Client(Base):
    __tablename__ = 'clients'
    id = Column(Integer, primary_key=True)
    client_name = Column(String(100), nullable=False)
    experience = Column(Integer, nullable=False)
    car = Column(String(100))
    prepayment = Column(Integer)
    prepayment_status = Column(String(100))
    tariff = Column(String(100))
    elapsed_time = Column(Float)


def initialize_database():
    # Создаем таблицы в базе данных
    Base.metadata.create_all(engine)


def send_to_com_mobile(id, details):
    details["deliver_to"] = "com-mobile"
    proceed_to_deliver(id, details)


def send_to_manage_drive(id, details):
    details["deliver_to"] = "manage-drive"
    proceed_to_deliver(id, details)


def send_to_bank_pay(id, details):
    details["deliver_to"] = "bank-pay"
    proceed_to_deliver(id, details)


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


def select_car(session, data):
    name = data[0]
    experience = data[1]
    tariff = data[2]
    brand = data[3]
    query = session.query(Client)
    client = query.filter_by(client_name=name).one_or_none()
    if client is None:
        client = Client(client_name=name, experience=experience)
        session.add(client)
        session.commit()
    client.car = brand
    client.tariff = tariff
    session.commit()
    return brand


def prepayment(session, car):
    amount = counter_prepayment(car)
    query = session.query(Client)
    brand = car['brand']
    client = query.filter_by(car=brand).one_or_none()
    if client:
        client.prepayment = amount
        name = client.client_name
        session.commit()
        return [name, amount]
    else:
        return []


def confirm_prepayment(session, name, status):
    query = session.query(Client)
    client = query.filter_by(client_name=name).one_or_none()
    if client:
        client.prepayment_status = status
        session.commit()


def return_car(session, name, trip_time):
    query = session.query(Client)
    client = query.filter_by(client_name=name).one_or_none()
    if client:
        client.elapsed_time = trip_time
        name = client.client_name
        session.commit()
        amount = counter_payment(trip_time, client.tariff, client.experience)
        return [name, amount]


def access(session, name):
    query = session.query(Client)
    client = query.filter_by(client_name=name).one_or_none()
    if client:
        if client.prepayment_status == 'paid':
            print(f"Доступ разрешен {name} до {client.car}")
            return {'access': True, 'tariff': client.tariff, 'car': client.car, 'name': name}


def final_receipt(session, receipt, name):
    query = session.query(Client)
    client = query.filter_by(client_name=name).one_or_none()
    if client:
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
        session.commit()
        return final_receipt


def handle_event(id, details_str):
    """ Обработчик входящих в модуль задач. """
    Session = sessionmaker(bind=engine)
    session = Session()

    details = json.loads(details_str)

    source: str = details.get("source")
    deliver_to: str = details.get("deliver_to")
    data: str = details.get("data")
    operation: str = details.get("operation")

    print(f"[info] handling event {id}, "
          f"{source}->{deliver_to}: {operation}")

    if operation == "get_tariff":
        details["data"] = TARIFF
        return send_to_com_mobile(id, details)
    elif operation == "get_cars":
        return send_to_manage_drive(id, details)
    elif operation == "answer_cars":
        return send_to_com_mobile(id, details)
    elif operation == "select_car":
        details["data"] = select_car(session, data)
        details["operation"] = "get_status"
        return send_to_manage_drive(id, details)
    elif operation == "answer_status":
        details["data"] = prepayment(session, data)
        details["operation"] = "get_prepayment_id"
        return send_to_bank_pay(id, details)
    elif operation == "get_prepayment_id":
        return send_to_com_mobile(id, details)
    elif operation == "confirm_prepayment":
        name = details.get("name")
        status = details.get("status")
        confirm_prepayment(session, name, status)
    elif operation == "access":
        details["access"] = access(session, details["name"])
        details["operation"] = "confirm_access"
        return send_to_manage_drive(id, details)
    elif operation == "return":
        details["data"] = return_car(session, details["name"], details["trip_time"])
        details["operation"] = "get_payment_id"
        return send_to_bank_pay(id, details)
    elif operation == "get_payment_id":
        return send_to_com_mobile(id, details)
    elif operation == "confirm_payment":
        details["data"] = final_receipt(session, details["receipt"], details["name"])
        details["operation"] = "final_receipt"
        return send_to_com_mobile(id, details)


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
    initialize_database()
    print(f'{MODULE_NAME}_consumer started')
    threading.Thread(target=lambda: consumer_job(args, config)).start()