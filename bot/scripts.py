import json

from database import engine
from sqlalchemy.orm import Session
from models import Staff

import pickle


def save_class_to_redis(redis_conn, key, cls):
	serialized_obj = pickle.dumps(cls)

	redis_conn.set(key, serialized_obj)

def save_dict_to_redis(redis_conn, key, dictionary):
	"""
	Сохраняет словарь в Redis.

	Параметры:
	- redis_conn: подключение к Redis (объект redis.Redis)
	- key: ключ, под которым будет сохранен словарь
	- dictionary: словарь, который нужно сохранить
	"""
	# Преобразуем словарь в строку JSON
	json_str = json.dumps(dictionary)

	# Сохраняем JSON-строку в Redis под указанным ключом
	redis_conn.set(key, json_str)


def save_to_redis(redis_conn, key, value):
	"""
	Сохраняет значение в Redis.

	Параметры:
	- redis_conn: подключение к Redis (объект redis.Redis)
	- key: ключ, под которым будет сохранено значение
	- value: значение, которое нужно сохранить
	"""
	redis_conn.set(key, value)

def get_admins():
	with Session(engine) as session:
		admins = session.query(Staff).filter(Staff.staff_type == "admin").all()

		return [username.staff_username for username in admins]


def get_promoters():
	with Session(engine) as session:
		admins = session.query(Staff).filter(Staff.staff_type == "promoter").all()

		return [username.staff_username for username in admins]


def get_ticket_checkers():
	with Session(engine) as session:
		admins = session.query(Staff).filter(Staff.staff_type == "ticket_checker").all()

		return [username.staff_username for username in admins]


def calculate(tickets):

	profit_data = {
		 'sum': 0,
		 'default_ticket_quantity': 0,
		 'vip_ticket_quantity': 0,
		 'deadline_ticket_quantity': 0,
		 'promoters': {}
	}

	for ticket in tickets:
		price = 0
		if ticket.ticket_type == 'default':
			price += ticket.default_price
			profit_data['default_ticket_quantity'] += 1
		elif ticket.ticket_type == 'vip':
			price += ticket.vip_price
			profit_data['vip_ticket_quantity'] += 1
		elif ticket.ticket_type == 'deadline':
			price += ticket.deadline_price
			profit_data['deadline_ticket_quantity'] += 1

		profit_data['sum'] += price

		if ticket.promoter is not None:
			if ticket.promoter not in profit_data['promoters']:
				profit_data['promoters'][ticket.promoter] = price
			else:
				profit_data['promoters']['not_promoter'] += price

	return profit_data
