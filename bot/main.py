import json
from datetime import datetime
from io import BytesIO
from random import randint
from PIL import Image

import requests
from sqlalchemy import desc
from sqlalchemy.orm import Session
from telebot import types, TeleBot
from telebot.types import Message

from database import engine
from scripts import save_dict_to_redis, save_to_redis, get_admins, get_promoters, get_ticket_checkers, calculate
from config import *
from models import Ticket, Event, Staff

from replices import *

import redis


class Bot(TeleBot):
	def __init__(self):
		super().__init__(token=BOT_TOKEN)


r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
bot = Bot()


# Старт
@bot.message_handler(commands=['start'])
def handle_start(message: Message):
	print(message)
	promoter = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None
	print(promoter)

	handle_start_page(message, promoter)


def handle_start_page(message: Message, promoter=None):
	markup = types.InlineKeyboardMarkup()
	buy_ticket = types.InlineKeyboardButton('Купити квиток 🎟️', callback_data=f'buy_ticket {promoter}')
	check_ticket_story = types.InlineKeyboardButton('История билетов 🖨', callback_data=f"check_ticket_story")

	markup.add(buy_ticket, check_ticket_story)

	with Session(engine) as session:
		try:
			event = session.query(Event).order_by(desc(Event.id)).first()
			if event:
				bot.send_message(message.chat.id, f"Paradise Seasons Bot"
												  f"\n"
												  f"\nНайближчий захід 🎉: {event.event_name}"
												  f"\nДата 🗓️: {event.event_date}"
												  f"\nТипова вартість 💵: {event.event_price_default}"
												  f"\n Місце проведення заходу: {event.event_place}"
												  f"\nВіп вартість 💸: {event.event_price_vip}",
								 reply_markup=markup)
			else:
				bot.send_message(message.chat.id, "Заходів поки немає 🙅‍♀️")
		except Exception as e:
			print(e)


# Вызов админки
@bot.message_handler(commands=['admin'])
def handle_admin(message: Message):
	admins = get_admins()
	if message.from_user.username in admins:
		handle_admin_page(message)


def handle_admin_page(message: Message):
	markup = types.InlineKeyboardMarkup(row_width=1)
	add_event = types.InlineKeyboardButton('Додати подію 📆', callback_data='add_event')
	check_tickets = types.InlineKeyboardButton('Перевірити квитки 🎟', callback_data='check_tickets')
	check_ticket_buy_request = types.InlineKeyboardButton('Перевірте 🧐 заявки на купівлю квитка 🎟 ',
														  callback_data='check_ticket_buy_request')
	show_rules = types.InlineKeyboardButton('Правила 📝', callback_data='show_rules')
	staff_menu = types.InlineKeyboardButton('Керування персоналом 🧑‍💼', callback_data='staff_menu')
	calculate_profit = types.InlineKeyboardButton('Розрахувати прибуток 🧮', callback_data='calculate_profit')

	markup.add(add_event, check_tickets, check_ticket_buy_request, show_rules, staff_menu, calculate_profit)
	bot.send_message(message.chat.id, "Адмін панель 👑", reply_markup=markup)


@bot.message_handler(commands=['promoter'])
def handle_promoter(message: Message):
	promoters = get_promoters()
	admins = get_admins()
	if message.from_user.username in promoters or message.from_user.username in admins:
		handle_promoter_page(message)


def handle_promoter_page(message: Message):
	markup = types.InlineKeyboardMarkup(row_width=1)
	check_tickets = types.InlineKeyboardButton('Перевірити квитки 🎟', callback_data='check_tickets')
	show_rules = types.InlineKeyboardButton('Правила 📝', callback_data='show_rules')
	give_prom_link = types.InlineKeyboardButton('Отримати промоутерське посилання🌐', callback_data='give_prom_link')

	markup.add(check_tickets, show_rules, give_prom_link)
	bot.send_message(message.chat.id, "Панель промоутера 👑", reply_markup=markup)


@bot.message_handler(commands=['ticket_checker'])
def handle_ticket_checker(message: Message):
	ticket_checkers = get_ticket_checkers()
	admins = get_admins()
	if message.from_user.username in ticket_checkers or message.from_user.username in admins:
		handle_ticket_checker_page(message)


def handle_ticket_checker_page(message: Message):
	markup = types.InlineKeyboardMarkup(row_width=1)
	check_tickets = types.InlineKeyboardButton('Перевірити квитки 🎟', callback_data='check_tickets')
	show_rules = types.InlineKeyboardButton('Правила 📝', callback_data='show_rules')

	markup.add(check_tickets, show_rules)
	bot.send_message(message.chat.id, "Панель перевіряючого квитків 👑", reply_markup=markup)


# Обработчик кнопок
@bot.callback_query_handler(func=lambda call: True)
def keyboard_listener(call: types.CallbackQuery):
	data = call.data.split(' ')

	if call.data == 'add_event':
		bot.edit_message_text(message_id=call.message.id, chat_id=call.message.chat.id, text=f"Введіть назву події 🎤")
		bot.register_next_step_handler(call.message, handle_event_name_input)

	elif call.data == 'check_ticket_story':
		markup = types.InlineKeyboardMarkup()
		back = types.InlineKeyboardButton('Назад 🔙', callback_data='back_menu')

		markup.add(back)
		with Session(engine) as session:
			tickets = session.query(Ticket).filter(Ticket.user_id == call.from_user.id).all()

		if tickets:
			for ticket in tickets:
				bot.send_message(call.message.chat.id, f"ID: {ticket.ticket_id}"
													   f"\nUser ID: {ticket.user_id}"
													   f"\nUsername: {ticket.username}"
													   f"\nFull name: {ticket.full_name}"
													   f"\nDate: {ticket.date}"
													   f"\nBank card: {ticket.bank_card}"
													   f"\nPrice: {ticket.default_price if ticket.ticket_type == 'default' else ticket.vip_price}"
													   f"\nTicket type: {ticket.ticket_type}")

			bot.send_message(call.message.chat.id, "Ваші квитки 🎟️ ⬆", reply_markup=markup)

		else:
			bot.send_message(call.message.chat.id, "У вас ще нема квитків 🙅‍♀️", reply_markup=markup)

	elif call.data == 'show_rules':
		bot.edit_message_text(message_id=call.message.id, chat_id=call.message.chat.id, text=f"Правила бота 📝")
		bot.send_message(call.message.chat.id, RULES)

		with Session(engine) as session:
			staff = session.query(Staff).filter(Staff.staff_username == call.from_user.username).first()
			print(staff)
		if staff.staff_type == 'admin':
			handle_admin_page(call.message)
		elif staff.staff_type == 'promoter':
			handle_promoter_page(call.message)
		elif staff.staff_type == 'ticket_checker':
			handle_ticket_checker_page(call.message)

	elif call.data == 'back_menu':
		handle_start_page(call.message)

	elif call.data == 'back_menu_ticker_type':
		r.delete(f'ticket_{call.from_user.id}')
		handle_start_page(call.message)

	elif data[0] == 'buy_ticket' or call.data == 'buy_ticket':
		print(data)
		ticket_type(call=call, data=data[1])

	elif call.data == 'promoter':
		print(call.from_user.id)
		staff_data_r = r.get(f'staff_{call.from_user.id}')
		staff_data = json.loads(staff_data_r)

		staff_data['staff_type'] = 'promoter'

		bot.send_message(call.message.chat.id, "Введіть юзернейм персоналу 🧑‍💼")

		bot.register_next_step_handler(call.message, handle_staff_username_input, staff_data)

	elif call.data == 'ticket_checker':
		staff_data_r = r.get(f'staff_{call.from_user.id}')
		staff_data = json.loads(staff_data_r)

		staff_data['staff_type'] = 'ticket_checker'

		bot.send_message(call.message.chat.id, "Введіть юзернейм персоналу 🧑‍💼")

		bot.register_next_step_handler(call.message, handle_staff_username_input, staff_data)

	elif call.data == 'admin':
		staff_data_r = r.get(f'staff_{call.from_user.id}')
		staff_data = json.loads(staff_data_r)

		staff_data['staff_type'] = 'admin'

		bot.send_message(call.message.chat.id, "Введіть юзернейм персоналу 🧑‍💼")

		bot.register_next_step_handler(call.message, handle_staff_username_input, staff_data)

	elif call.data == 'ticket_type_default':
		try:
			ticket_r = r.get(f'ticket_{call.from_user.id}')
			saved_dict = json.loads(ticket_r)
			saved_dict['ticket_type'] = 'default'
			bot.edit_message_text(chat_id=call.message.chat.id,
								  text=f"Перекажіть кошти на банківську карту 💳 5375 4114 1943 2245"
									   f"\nПотім напишіть номер картки💳, з якої були перераховані кошти, у форматі XXXX XXXX XXXX XXXX",
								  message_id=call.message.id)

			bot.register_next_step_handler(call.message, bank_card_input, saved_dict)

			r.delete(f'ticket_{call.from_user.id}')
		except Exception as e:
			print(e)
			bot.send_message(call.message.chat.id, "Будь ласка, спробуйте ще раз")
			handle_start_page(call.message)

	elif call.data == 'ticket_type_vip':
		try:
			ticket_r = r.get(f'ticket_{call.from_user.id}')
			saved_dict = json.loads(ticket_r)
			saved_dict['ticket_type'] = 'vip'
			bot.edit_message_text(chat_id=call.message.chat.id,
								  text=f"Перекажіть кошти на банківську карту 💳 5375 4114 1943 2245"
									   f"\nПотім напишіть номер картки💳, з якої були перераховані кошти, у форматі XXXX XXXX XXXX XXXX",
								  message_id=call.message.id)

			bot.register_next_step_handler(call.message, bank_card_input, saved_dict)

			r.delete(f'ticket_{call.from_user.id}')
		except Exception as e:
			print(e)
			bot.send_message(call.message.chat.id, "Будь ласка, спробуйте ще раз")
			handle_start_page(call.message)

	elif call.data == 'check_tickets':
		bot.edit_message_text(message_id=call.message.id, chat_id=call.message.chat.id,

							  text=f"Введіть 🆔 квитка")
		bot.register_next_step_handler(call.message, check_ticket)

	elif call.data == 'accept':
		try:
			ticket_id_r = r.get(f'ticket_id_{call.from_user.id}')
			decoded_ticket_id_r = ticket_id_r.decode('utf-8')

			with Session(engine) as session:
				ticket = session.query(Ticket).filter(Ticket.ticket_id == decoded_ticket_id_r).first()
				ticket.passed = True
				session.commit()
			r.delete(f'ticket_id_{call.from_user.id}')
			bot.edit_message_text(chat_id=call.message.chat.id, text="Квиток 🎟️ успішно прийнятий ✅",
								  message_id=call.message.id)

			with Session(engine) as session:
				staff = session.query(Staff).filter(Staff.staff_username == call.from_user.username).first()
				print(staff)
			if staff.staff_type == 'admin':
				handle_admin_page(call.message)
			elif staff.staff_type == 'promoter':
				handle_promoter_page(call.message)
			elif staff.staff_type == 'ticket_checker':
				handle_ticket_checker_page(call.message)

		except Exception as e:
			print(e)
			bot.send_message(call.message.chat.id, "Помилка ❌при прийманні квитка🎟️")

	elif call.data == 'decline':
		try:
			ticket_id_r = r.get(f'ticket_id_{call.from_user.id}')
			decoded_ticket_id_r = ticket_id_r.decode('utf-8')

			with Session(engine) as session:
				ticket = session.query(Ticket).filter(Ticket.ticket_id == decoded_ticket_id_r).first()
				ticket.passed = False
				session.commit()
			r.delete(f'ticket_id_{call.from_user.id}')
			bot.edit_message_text(chat_id=call.message.chat.id, text="Квиток 🎟️ відхилен ",
								  message_id=call.message.id)

			with Session(engine) as session:
				staff = session.query(Staff).filter(Staff.staff_username == call.from_user.username).first()
				print(staff)
			if staff.staff_type == 'admin':
				handle_admin_page(call.message)
			elif staff.staff_type == 'promoter':
				handle_promoter_page(call.message)
			elif staff.staff_type == 'ticket_checker':
				handle_ticket_checker_page(call.message)

		except Exception as e:
			print(e)
			bot.send_message(call.message.chat.id, "Помилка ❌при відхиленні квитка🎟️")

	elif call.data == 'create_event':
		try:
			saved_dict_json = r.get(f'event_data_{call.from_user.id}')
			saved_dict = json.loads(saved_dict_json)

			with Session(engine) as session:
				session.add(Event(**saved_dict))
				session.commit()
			r.delete(f'event_data_{call.from_user.id}')
			bot.send_message(call.message.chat.id, "Захід добавлено🪩 ✅")

			handle_admin_page(call.message)
		except Exception as e:
			print(e)
			bot.send_message(call.message.chat.id, "Помилка при додаванні заходу ❌")

	elif call.data == 'eject_create_event':
		r.delete(f'event_data_{call.from_user.id}')

		bot.send_message(call.message.chat.id, "Створення заходу відхилено ❌")

		handle_admin_page(call.message)

	elif call.data == 'check_ticket_buy_request':
		with Session(engine) as session:
			tickets = session.query(Ticket).filter(Ticket.confirmed.is_(None)).all()
			if tickets:
				for ticket in tickets:
					markup = types.InlineKeyboardMarkup()
					confirm_ticket = types.InlineKeyboardButton('✔', callback_data=f'confirmTicket_{ticket.ticket_id}')
					eject_ticket = types.InlineKeyboardButton('❌', callback_data=f'ejectTicket_{ticket.ticket_id}')

					markup.add(confirm_ticket, eject_ticket)

					with Session(engine) as session:
						event = session.query(Event).filter(Event.id == ticket.event_id).first()

					response = requests.get(ticket.photo_url)

					if response.status_code == 200:

						image = Image.open(BytesIO(response.content))

						with BytesIO() as output:
							image.save(output, format='JPEG')
							output.seek(0)
							bot.send_photo(call.message.chat.id, output, f"ID: {ticket.ticket_id}"
																		 f"\nUser ID: {ticket.user_id}"
																		 f"\nUsername: {ticket.username}"
																		 f"\nFull name: {ticket.full_name}"
																		 f"\nDate: {ticket.date}"
																		 f"\nBank card: {ticket.bank_card}"
																		 f"\nPrice: {ticket.default_price if ticket.ticket_type == 'default' else ticket.vip_price}"
																		 f"\nTicket type: {ticket.ticket_type}"
																		 f"\nEvent Name: {event.event_name}", reply_markup=markup)
					else:
						bot.send_message(call.message.chat.id, f"ID: {ticket.ticket_id}"
															   f"\nUser ID: {ticket.user_id}"
															   f"\nUsername: {ticket.username}"
															   f"\nFull name: {ticket.full_name}"
															   f"\nDate: {ticket.date}"
															   f"\nBank card: {ticket.bank_card}"
															   f"\nPrice: {ticket.default_price if ticket.ticket_type == 'default' else ticket.vip_price}"
															   f"\nTicket type: {ticket.ticket_type}"
															   f"\nEvent Name: {event.event_name}", reply_markup=markup)
			else:
				bot.send_message(call.message.chat.id, "Нема запитів на купівлю квитка 🧐")
		session.commit()
		handle_admin_page(call.message)

	elif call.data.startswith('confirmTicket'):
		try:
			with Session(engine) as session:
				ticket = session.query(Ticket).filter(Ticket.ticket_id == call.data[14:]).first()

				ticket.confirmed = True
				session.commit()
				bot.send_message(call.message.chat.id, f"Квиток {ticket.ticket_id} прийнятий ✅")
				bot.delete_message(call.message.chat.id, call.message.message_id)
		except Exception as e:
			print(e)
			bot.send_message(call.message.chat.id, f"Помилка при підтвердженні квитка ❌")

	elif call.data.startswith('ejectTicket'):
		try:
			with Session(engine) as session:
				ticket = session.query(Ticket).filter(Ticket.ticket_id == call.data[12:]).first()

				ticket.confirmed = False
				session.commit()
				bot.send_message(call.message.chat.id, f"Квиток {ticket.ticket_id} відхилен ✅")
				bot.delete_message(call.message.chat.id, call.message.message_id)
		except Exception as e:
			print(e)
			bot.send_message(call.message.chat.id, f"Помилка при відхиленні квитка ❌")

	elif call.data == 'give_prom_link':
		promoters = get_promoters()
		if call.from_user.username in promoters:
			bot.send_message(call.message.chat.id, f"Ваше посилання промоутеру:"
												   f"\nhttps://t.me/ParadiseTicketBot?start={call.from_user.username}")

	elif call.data == 'staff_menu':
		markup = types.InlineKeyboardMarkup(row_width=2)

		add_staff = types.InlineKeyboardButton('Додати персонал 🧑‍💼', callback_data='add_staff')
		check_staff = types.InlineKeyboardButton('Перевірити персонал 🧑‍💼', callback_data='check_staff')
		delete_staff = types.InlineKeyboardButton('Видалити персонал 🧑‍💼', callback_data='delete_staff')

		markup.add(add_staff, check_staff, delete_staff)
		bot.send_message(call.message.chat.id, "Оберіть дію з персоналом", reply_markup=markup)

	elif call.data == 'add_staff':
		bot.edit_message_text(message_id=call.message.id, chat_id=call.message.chat.id, text=f"Введіть ім'я персонала 🧑‍💼")
		bot.register_next_step_handler(call.message, handle_staff_name_input)

	elif call.data == 'check_staff':
		markup = types.InlineKeyboardMarkup(row_width=2)

		promoters_list = types.InlineKeyboardButton('Список промоутерів 🧑‍💼', callback_data='staff_check promoters')
		admins_list = types.InlineKeyboardButton('Список адмінів 🧑‍💼', callback_data='staff_check admins')
		ticket_checkers_list = types.InlineKeyboardButton('Список перевіряючих квитків 🧑‍💼',
														  callback_data='staff_check ticket_checkers')

		markup.add(promoters_list, admins_list, ticket_checkers_list)

		bot.send_message(call.message.chat.id, "Оберіть тип персоналу", reply_markup=markup)

	elif call.data == 'delete_staff':
		bot.edit_message_text(message_id=call.message.id, chat_id=call.message.chat.id,
							  text=f"Введіть юзернейм персонала 🧑‍💼")
		bot.register_next_step_handler(call.message, handle_staff_delete_username_input)

	elif call.data.startswith('staff_check'):
		data = call.data.split()[1]
		try:
			with Session(engine) as session:
				if data == 'promoters':
					staff = session.query(Staff).filter(Staff.staff_type == 'promoter').all()
				elif data == 'admins':
					staff = session.query(Staff).filter(Staff.staff_type == 'admin').all()
				elif data == 'ticket_checkers':
					staff = session.query(Staff).filter(Staff.staff_type == 'ticket_checker').all()
		except Exception as e:
			print(e)
			bot.send_message(call.message.chat.id, "Помилка при отриманні персоналу ❌")
		if staff:
			bot.edit_message_text(message_id=call.message.id, chat_id=call.message.chat.id, text=f"Персонал {data}:")
			for staff in staff:
				bot.send_message(call.message.chat.id, f"ID: {staff.id}"
													 f"\nUsername: {staff.staff_username}"
													 f"\nFull name: {staff.staff_name}")
		else:
			bot.send_message(call.message.chat.id, "Персонал не знайдений ❌")

	elif call.data == 'calculate_profit':
		handle_calculate_profit(call.message)


# Ввод ююзернейма персонала для видалення
def handle_staff_delete_username_input(message: Message):
	if message.text.startswith("https://t.me/"):
		username = message.text[13:]
	elif message.text.startswith("@"):
		username = message.text[1:]
	else:
		username = message.text

	try:
		with Session(engine) as session:
			staff = session.query(Staff).filter(Staff.staff_username == username).first()
			if staff:
				session.delete(staff)
				session.commit()
				bot.send_message(message.chat.id, "Персонал видалений ✅")
			else:
				bot.send_message(message.chat.id, "Персонал не знайдений ❌")
	except Exception as e:
		print(e)
		bot.send_message(message.chat.id, "Помилка при видаленні персонала ❌")
	handle_admin_page(message)


# Ввод логина
def handle_staff_username_input(message: Message, staff_data: dict):
	if message.text.startswith("https://t.me/"):
		staff_data['staff_username'] = message.text[13:]
	elif message.text.startswith("@"):
		staff_data['staff_username'] = message.text[1:]
	else:
		staff_data['staff_username'] = message.text

	save_staff(message, staff_data)


# Ввод имени
def handle_staff_name_input(message: Message):
	markup = types.InlineKeyboardMarkup(row_width=2)

	staff_data = {
		"staff_name": message.text,
	}

	promoter = types.InlineKeyboardButton('Промоутер', callback_data='promoter')
	admin = types.InlineKeyboardButton('Адмін', callback_data='admin')
	ticket_checker = types.InlineKeyboardButton('Перевіряючий квитків', callback_data='ticket_checker')

	markup.add(promoter, admin, ticket_checker)

	bot.send_message(message.chat.id, "Виберіть роль", reply_markup=markup)

	save_dict_to_redis(r, f"staff_{message.from_user.id}", staff_data)


# Выбор типа билета
def ticket_type(call, data):
	markup = types.InlineKeyboardMarkup(row_width=2)

	with Session(engine) as session:
		event = session.query(Event).order_by(desc(Event.id)).first()

	promoters = get_promoters()
	print(promoters)
	print(data)

	if event:
		ticket_data = {
			"date": f"{datetime.now().replace(microsecond=0)}",
			"ticket_id": randint(100000, 999999),
			"user_id": call.from_user.id,
			"username": call.from_user.username,
			"promoter": data if data in promoters else None,
			'default_price': event.event_price_default,
			'vip_price': event.event_price_vip,
			'deadline_price': event.event_price_deadline,
			'event_id': event.id,
		}

		default = types.InlineKeyboardButton('Open Door 🎟️', callback_data='ticket_type_default')
		vip = types.InlineKeyboardButton('Vip 💎', callback_data='ticket_type_vip')
		back = types.InlineKeyboardButton('🔙', callback_data='back_menu_ticker_type')

		markup.add(default, vip, back)

		bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text="Оберіть тип квитка 🎟️",
							  reply_markup=markup)

		save_dict_to_redis(r, f'ticket_{call.from_user.id}', ticket_data)

	else:
		bot.send_message(call.message.chat.id, "Заходів поки немає 🙅‍♀️")


# Добавление нового співробітника
def save_staff(message: Message, staff_data):
	try:
		with Session(engine) as session:
			session.add(Staff(**staff_data))
			session.commit()
		bot.send_message(message.chat.id, "Новий співробітник додан ✅")
	except Exception as e:
		print(e)
		bot.send_message(message.chat.id, f"Помилка при додаванні нового співробітника ❌")


# Проверка билета
def check_ticket(message: Message):
		try:
			with Session(engine) as session:
				ticket = session.query(Ticket).filter(Ticket.ticket_id == message.text).first()
				event = session.query(Event).filter(Event.id == ticket.event_id).first()

				if ticket:
					markup = types.InlineKeyboardMarkup()
					add_event = types.InlineKeyboardButton('✔', callback_data=f'accept')
					check_tickets = types.InlineKeyboardButton('❌', callback_data=f'decline')

					markup.add(add_event, check_tickets)
					if ticket.confirmed is True:
						bot.send_message(message.chat.id, f"ID: {ticket.ticket_id}"
														  f"\nUser ID: {ticket.user_id}"
														  f"\nUsername: {ticket.username}"
														  f"\nFull name: {ticket.full_name}"
														  f"\nDate: {ticket.date}"
														  f"\nBank card: {ticket.bank_card}"
														  f"\nPrice: {ticket.default_price if ticket.ticket_type == 'default' else ticket.vip_price}"
														  f"\nTicket type: {ticket.ticket_type}"
														  f"\nPassed: {ticket.passed}"
														  f"\nConfirmed: {ticket.confirmed}"
														  f"\nEvent Name: {event.event_name}", reply_markup=markup)

						save_to_redis(r, f'ticket_id_{message.from_user.id}', ticket.ticket_id)
					else:
						bot.send_message(message.chat.id, f"Квиток був відхилен або не прийнят адміністратором ❌")
				else:
					bot.send_message(message.chat.id, "Квитки не знайдени 🙅‍♀️")
		except Exception as e:
			print(e)
			bot.send_message(message.chat.id, "Помилка при отриманні квитка ❌")


# Вибір типа квитка
def choose_kind_of_ticket(message: Message):
	bot.send_message(chat_id=message.chat.id, text=f"Переказ грошей на банківську карту 💳 XXXX XXXX XXXX XXXX"
												   f"\nПотім напишіть номер картки💳, з якої були перераховані кошти, у форматі XXXX XXXX XXXX XXXX")

	bot.register_next_step_handler(message, bank_card_input)


# Ввод карты при покупки
def bank_card_input(message: Message, ticket_data):
	ticket_data['bank_card'] = message.text

	bot.send_message(message.chat.id, "Введіть своє повне ім'я...")

	bot.register_next_step_handler(message, full_name_input, ticket_data)


# Ввод полного имени при покупки
def full_name_input(message: Message, ticket_data):
	full_name = message.text

	ticket_data['full_name'] = full_name

	bot.send_message(message.chat.id, f"Відправте знімок екрану з оплатою")
	bot.register_next_step_handler(message, send_screen_shot, ticket_data)


# Отправка скриншота оплаты
def send_screen_shot(message: Message, ticket_data):
	try:
		photo_id = message.photo[-1].file_id

		photo_file = bot.get_file(photo_id)
		photo_url = f"https://api.telegram.org/file/bot{bot.token}/{photo_file.file_path}"

		ticket_data['photo_url'] = photo_url

		markup = types.InlineKeyboardMarkup()
		back_menu = types.InlineKeyboardButton('🔙 Назад', callback_data='back_menu')

		markup.add(back_menu)

		try:
			with Session(engine) as session:
				session.add(Ticket(**ticket_data))
				session.commit()
			bot.send_message(message.chat.id, f"Придбання вашого квитка було зареєстрованно!"
											  f"\nВаш квиток буде нижче ⬇⬇⬇")
			ticket_type = ticket_data['ticket_type']
			bot.send_message(message.chat.id, f"Вартість квитка 💸: {str(ticket_data[f'{ticket_type}_price'])}"
											  f"\nДата 📅: {ticket_data['date']}"
											  f"\nТип квитка 🎫: {ticket_type}"
											  f"\nБанковська картка 💳: {ticket_data['bank_card']}"
											  f"\nПовне ім'я 📄: {ticket_data['full_name']}"
											  f"\nID: {ticket_data['ticket_id']}", reply_markup=markup)
		except Exception as e:
			print(e)
			bot.send_message(message.chat.id, "При додаванні квитків виникла помилка ❌")
			handle_start_page(message)

	except Exception as e:
		print(e)
		bot.send_message(message.chat.id, "Відправте знімок екрану з оплатою")
		bot.register_next_step_handler(message, send_screen_shot, ticket_data)


# Ввод названия события
def handle_event_name_input(message: Message):
	event_data = {
		'event_name': message.text
	}
	bot.send_message(message.chat.id, "Введіть місце проведення заходу")
	bot.register_next_step_handler(message, handle_event_place_input, event_data)


# Ввод місця проведення заходу
def handle_event_place_input(message: Message, event_data):
	event_data['event_place'] = message.text

	bot.send_message(message.chat.id, "Введіть дату захода у форматі DD.MM.YYYY 📆")
	bot.register_next_step_handler(message, handle_date_input, event_data)


# Ввод даты события
def handle_date_input(message: Message, event_data):
	bot.send_message(message.chat.id, "Введіть звичайну вартість квитка 💵")
	event_data['event_date'] = message.text
	bot.register_next_step_handler(message, handle_price_default_input, event_data)


# Ввод цены при регистрации события для обычного клиента
def handle_price_default_input(message: Message, event_data):
	bot.send_message(message.chat.id, "Введіть вартість VIP квитка 💰")
	event_data['event_price_default'] = message.text
	bot.register_next_step_handler(message, handle_price_vip_input, event_data)


# Ввод цены при регистрации события для VIP билета
def handle_price_vip_input(message: Message, event_data):
	event_data['event_price_vip'] = message.text
	bot.send_message(message.chat.id, "Введіть вартість дедлайн билета 📅")
	bot.register_next_step_handler(message, handle_price_deadline_input, event_data)


# Ввод цены при регистрации события для дедлайн билета
def handle_price_deadline_input(message: Message, event_data):
	event_data['event_price_deadline'] = message.text

	bot.send_message(message.chat.id, "Перевірте введені дані та підтвердіть створення заходу ✅")

	markup = types.InlineKeyboardMarkup()
	create_event = types.InlineKeyboardButton('✔', callback_data=f'create_event')
	delete_data = types.InlineKeyboardButton('❌', callback_data=f'eject_create_event')

	save_dict_to_redis(r, f'event_data_{message.from_user.id}', event_data)

	markup.add(create_event, delete_data)
	bot.send_message(message.chat.id, f"Назва заходу 🖊: {event_data['event_name']}"
									  f"\n Дата 📆: {event_data['event_date']}"
									  f"\n Типова ціна 💵: {event_data['event_price_default']}"
									  f"\n Віп ціна 💸: {event_data['event_price_vip']}"
									  f"\n Місце проведення заходу: {event_data['event_place']}"
									  f"\n Ціна кінцевого терміну 💵: {event_data['event_price_deadline']}",
					 reply_markup=markup)


def handle_calculate_profit(message: Message):
	bot.send_message(message.chat.id, "Введіть назву заходу 🖊")
	bot.register_next_step_handler(message, handle_date_profit_input)


def handle_date_profit_input(message: Message):
	event_name = message.text
	try:
		with Session(engine) as session:
			event = session.query(Event).filter(Event.event_name == event_name).first()
			if event:
				event_id = event.id
				tickets = session.query(Ticket).filter(Ticket.event_id == event_id).all()

			else:
				bot.send_message(message.chat.id, "Такого заходу не знайдено ❌")

		profit_data = calculate(tickets)

		bot.send_message(message.chat.id, f"Рентабельність заходу: {profit_data['sum']} UAH"
										  f"\nКількість продаж звичайних квитків: {profit_data['default_ticket_quantity']}"
										  f"\nКількість продаж віп квитків: {profit_data['vip_ticket_quantity']}"
										  f"\nКількість продаж кінцевих квитків: {profit_data['deadline_ticket_quantity']}"
										  f"\nНижче буде зведена статистика з продаж квитків промоутерами")

		for promoter, promoter_profit in profit_data['promoters'].items():
			bot.send_message(message.chat.id, f"{promoter}: {promoter_profit} UAH")
	except Exception as e:
		print(e)
		bot.send_message(message.chat.id, "При розрахуванні рентабельності заходу виникла помилка ❌")


if __name__ == '__main__':
	bot.polling()
