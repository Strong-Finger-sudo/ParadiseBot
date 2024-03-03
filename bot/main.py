import json
from datetime import datetime
from random import randint

from sqlalchemy import desc
from sqlalchemy.orm import Session
from telebot import types, TeleBot
from telebot.types import Message

from bot.database import engine
from bot.scripts import save_dict_to_redis, save_to_redis
from config import BOT_TOKEN, ADMINS, PROMOTERS
from bot.models import Ticket, Event

import redis


class Bot(TeleBot):
	def __init__(self):
		super().__init__(token=BOT_TOKEN)


bot = Bot()
r = redis.Redis(host='localhost', port=6379, db=0)


# Старт
@bot.message_handler(commands=['start'])
def handle_start(message: Message):
	promoter = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None

	markup = types.InlineKeyboardMarkup()
	buy_ticket = types.InlineKeyboardButton('Купить билет', callback_data=f'buy_ticket {promoter}')
	check_event = types.InlineKeyboardButton('Ближайшее мероприятие', callback_data='check_event')

	markup.add(buy_ticket, check_event)
	bot.send_message(message.chat.id, "Привет, я бот для проверки билетов на мероприятия", reply_markup=markup)


# Вызов админки
@bot.message_handler(commands=['admin'])
def handle_admin(message: Message):
	if message.from_user.id in ADMINS:
		markup = types.InlineKeyboardMarkup()
		add_event = types.InlineKeyboardButton('Добавить мероприятие', callback_data='add_event')
		check_tickets = types.InlineKeyboardButton('Проверить билеты', callback_data='check_tickets')
		check_ticket_buy_request = types.InlineKeyboardButton('Проверить запросы на покупку билетов',
															  callback_data='check_ticket_buy_request')

		markup.add(add_event, check_tickets, check_ticket_buy_request)
		bot.send_message(message.chat.id, "Добавить мероприятие", reply_markup=markup)


# Обработчик кнопок
@bot.callback_query_handler(func=lambda call: True)
def keyboard_listener(call: types.CallbackQuery):
	data = call.data.split(' ')

	if call.data == 'add_event':
		bot.send_message(call.message.chat.id, "Введите название мероприятия")
		bot.register_next_step_handler(call.message, handle_event_name_input)

	elif call.data == 'check_event':
		markup = types.InlineKeyboardMarkup()
		buy_ticket = types.InlineKeyboardButton('Купить билет', callback_data='buy_ticket')

		markup.add(buy_ticket)
		with Session(engine) as session:
			try:
				event = session.query(Event).order_by(desc(Event.id)).first()
				if event:
					bot.send_message(call.message.chat.id, f"Ближайшее мероприятие: {event.event_name}"
														   f"\nДата: {event.event_date}"
														   f"\nЦена по умолчанию: {event.event_price_default}"
														   f"\nЦена VIP: {event.event_price_vip}"
														   f"\nЦена дедлайна: {event.event_price_deadline}", reply_markup=markup)
				else:
					bot.send_message(call.message.chat.id, "Мероприятий еще нет")
			except Exception as e:
				print(e)
				bot.send_message(call.message.chat.id, "Ошибка при получении ближайшего мероприятия")

	elif data[0] == 'buy_ticket' or call.data == 'buy_ticket':
		bot.send_message(call.message.chat.id,
						 "Перечислите деньги на банковскую карту XXXX XXXX XXXX XXXX\nПосле напишите номер карты, с которой были перечисленны средства, в формате XXXX XXXX XXXX XXXX")
		bot.register_next_step_handler(call.message, bank_card_input, data[1] if len(data) > 1 else None)

	elif call.data == 'check_tickets':
		bot.send_message(call.message.chat.id, "Введите ID билета")
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
			bot.send_message(call.message.chat.id, "Билет успешно принят")

		except Exception as e:
			print(e)
			bot.send_message(call.message.chat.id, "Ошибка при принятии билета")

		finally:
			handle_admin(call.message)

	elif call.data == 'decline':
		r.delete(f'ticket_id_{call.from_user.id}')
		bot.send_message(call.message.chat.id, "Билет отклонен")
		handle_admin(call.message)

	elif call.data == 'create_event':
		try:
			saved_dict_json = r.get(f'event_data_{call.from_user.id}')
			saved_dict = json.loads(saved_dict_json)

			with Session(engine) as session:
				session.add(Event(**saved_dict))
				session.commit()
			r.delete(f'event_data_{call.from_user.id}')
			bot.send_message(call.message.chat.id, "Мероприятие добавлено")
		except Exception as e:
			print(e)
			bot.send_message(call.message.chat.id, "Ошибка при добавлении мероприятия")

	elif call.data == 'eject_create_event':
		r.delete(f'event_data_{call.from_user.id}')

		bot.send_message(call.message.chat.id, "Создание мероприятие отменено")

	elif call.data == 'check_ticket_buy_request':
		with Session(engine) as session:
			tickets = session.query(Ticket).filter(Ticket.confirmed.is_(None)).all()
			if tickets:
				for ticket in tickets:
					markup = types.InlineKeyboardMarkup()
					confirm_ticket = types.InlineKeyboardButton('✔', callback_data=f'confirmTicket_{ticket.ticket_id}')
					eject_ticket = types.InlineKeyboardButton('❌', callback_data=f'ejectTicket_{ticket.ticket_id}')

					markup.add(confirm_ticket, eject_ticket)

					bot.send_message(call.message.chat.id, f"ID билета: {ticket.ticket_id}"
														   f"\nUser ID: {ticket.user_id}"
														   f"\nUsername: {ticket.username}"
														   f"\nFull name: {ticket.full_name}"
														   f"\nDate: {ticket.date}"
														   f"\nBank card: {ticket.bank_card}"
														   f"\nPrice: {ticket.price}", reply_markup=markup)

			else:
				bot.send_message(call.message.chat.id, "Нету запросов на покупку билетов")
			session.commit()
			handle_admin(call.message)

	elif call.data.startswith('confirmTicket'):
		try:
			with Session(engine) as session:
				ticket = session.query(Ticket).filter(Ticket.ticket_id == call.data[14:]).first()

				ticket.confirmed = True
				session.commit()
				bot.send_message(call.message.chat.id, f"Билет {ticket.ticket_id} успешно подтвержден")
				bot.delete_message(call.message.chat.id, call.message.message_id)
		except Exception as e:
			print(e)
			bot.send_message(call.message.chat.id, f"Ошибка при подтверждении билета {ticket.ticket_id}")

	elif call.data.startswith('ejectTicket'):
		try:
			with Session(engine) as session:
				ticket = session.query(Ticket).filter(Ticket.ticket_id == call.data[12:]).first()

				ticket.confirmed = False
				session.commit()
				bot.send_message(call.message.chat.id, f"Билет {ticket.ticket_id} успешно отклонен")
				bot.delete_message(call.message.chat.id, call.message.message_id)
		except Exception as e:
			print(e)
			bot.send_message(call.message.chat.id, f"Ошибка при отклонении билета {ticket.ticket_id}")


# Проверка билета
def check_ticket(message: Message):
	with Session(engine) as session:
		ticket = session.query(Ticket).filter(Ticket.ticket_id == message.text).first()
		if ticket:
			markup = types.InlineKeyboardMarkup()
			add_event = types.InlineKeyboardButton('✔', callback_data=f'accept')
			check_tickets = types.InlineKeyboardButton('❌', callback_data=f'decline')

			markup.add(add_event, check_tickets)
			if ticket.confirmed is True:
				save_to_redis(r, f'ticket_id_{message.from_user.id}', ticket.ticket_id)
				bot.send_message(message.chat.id, f"ID билета: {ticket.ticket_id}"
												  f"\nUser ID: {ticket.user_id}"
												  f"\nUsername: {ticket.username}"
												  f"\nFull name: {ticket.full_name}"
												  f"\nDate: {ticket.date}"
												  f"\nBank card: {ticket.bank_card}"
												  f"\nPrice: {ticket.price}"
												  f"\nConfirmed: {ticket.confirmed}", reply_markup=markup)
			else:
				bot.send_message(message.chat.id, f"Билет был отклонён или не подтвержён админом")
		else:
			bot.send_message(message.chat.id, "Билеты не найдены")


# Ввод карты при покупки
def bank_card_input(message: Message, promoter):
	bot.send_message(message.chat.id, "Введите своё полное имя")

	ticket_data = {
		"date": f"{datetime.now().replace(microsecond=0)}",
		"ticket_id": randint(100000, 999999),
		"bank_card": message.text,
		"price": 250,
		"user_id": message.from_user.id,
		"username": message.from_user.username,
		"promoter": promoter if promoter in PROMOTERS else None,
	}

	bot.register_next_step_handler(message, full_name_input, ticket_data)


# Ввод полного имени при покупки
def full_name_input(message: Message, ticket_data):
	full_name = message.text

	ticket_data['full_name'] = full_name

	with Session(engine) as session:
		session.add(Ticket(**ticket_data))
		session.commit()

	bot.send_message(message.chat.id, f"Покупка вашего билета была зарегестрирована, спасибо за покупку!"
									  f"\nВаш билет будет ниже")
	bot.send_message(message.chat.id, f"Цена: {str(ticket_data['price'])}"
									  f"\nБанковская карта: {ticket_data['bank_card']}"
									  f"\nПолное имя: {ticket_data['full_name']}"
									  f"\nID билета: {ticket_data['ticket_id']}")

	handle_start(message)


# Ввод названия события
def handle_event_name_input(message: Message):
	if message.from_user.id in ADMINS:
		event_data = {
			'event_name': message.text
		}
		bot.send_message(message.chat.id, "Введите дату события в формате DD.MM.YYYY")
		bot.register_next_step_handler(message, handle_date_input, event_data)


# Ввод даты события
def handle_date_input(message: Message, event_data):
	if message.from_user.id in ADMINS:
		bot.send_message(message.chat.id, "Введите обычную цену билета")
		event_data['event_date'] = message.text
		bot.register_next_step_handler(message, handle_price_default_input, event_data)


# Ввод цены при регистрации события для обычного клиента
def handle_price_default_input(message: Message, event_data):
	if message.from_user.id in ADMINS:
		bot.send_message(message.chat.id, "Введите цену VIP билета")
		event_data['event_price_default'] = message.text
		bot.register_next_step_handler(message, handle_price_vip_input, event_data)


# Ввод цены при регистрации события для VIP билета
def handle_price_vip_input(message: Message, event_data):
	if message.from_user.id in ADMINS:
		event_data['event_price_vip'] = message.text
		bot.send_message(message.chat.id, "Введите цену дедлайн билета")
		bot.register_next_step_handler(message, handle_price_deadline_input, event_data)


# Ввод цены при регистрации события для дедлайн билета
def handle_price_deadline_input(message: Message, event_data):
	if message.from_user.id in ADMINS:
		event_data['event_price_deadline'] = message.text

		bot.send_message(message.chat.id, "Проверьте данные события и подтвердите сохранение")

		markup = types.InlineKeyboardMarkup()
		create_event = types.InlineKeyboardButton('✔', callback_data=f'create_event')
		delete_data = types.InlineKeyboardButton('❌', callback_data=f'eject_create_event')

		save_dict_to_redis(r, f'event_data_{message.from_user.id}', event_data)

		markup.add(create_event, delete_data)
		bot.send_message(message.chat.id, f"Название события: {event_data['event_name']}"
										  f"\n Дата события: {event_data['event_date']}"
										  f"\n Обычная цена билета: {event_data['event_price_default']}"
										  f"\n Цена VIP билета: {event_data['event_price_vip']}"
										  f"\n Цена дедлайна билета: {event_data['event_price_deadline']}",
						 reply_markup=markup)

		handle_admin(message)


if __name__ == '__main__':
	bot.polling()
