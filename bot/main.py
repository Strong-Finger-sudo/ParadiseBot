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
from scripts import save_dict_to_redis, save_to_redis
from config import BOT_TOKEN, ADMINS, PROMOTERS, TEST_BOT_TOKEN
from models import Ticket, Event

import redis


class Bot(TeleBot):
	def __init__(self):
		super().__init__(token=BOT_TOKEN)


bot = Bot()

# Старт
@bot.message_handler(commands=['start'])
def handle_start(message: Message):
	promoter = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None

	handle_start_page(message, promoter)


def handle_start_page(message: Message, promoter=None):

	markup = types.InlineKeyboardMarkup()
	buy_ticket = types.InlineKeyboardButton('Купити квиток 🎟️', callback_data=f'buy_ticket {promoter}')
	check_ticket_story = types.InlineKeyboardButton('История билетов 🖨', callback_data=f"check_ticket_story")

	markup.add(buy_ticket, check_ticket_story)

	with Session(engine) as session:
			event = session.query(Event).order_by(desc(Event.id)).first()
			if event:
				bot.send_message(message.chat.id, f"Paradise Seasons Bot"
												  f"\n"
												  f"\nНайближчий захід 🎉: {event.event_name}"
												  f"\nДата 🗓️: {event.event_date}"
												  f"\nТипова вартість 💵: {event.event_price_default}"
												  f"\nВіп вартість 💸: {event.event_price_vip}"
												  f"\nЦіна кінцевого терміну 💵: {event.event_price_deadline}",
								 				  reply_markup=markup)
			else:
				bot.send_message(message.chat.id, "Заходів поки немає 🙅‍♀️")

# Вызов админки
@bot.message_handler(commands=['admin'])
def handle_admin(message: Message):
	if message.from_user.id in ADMINS:
		markup = types.InlineKeyboardMarkup()
		add_event = types.InlineKeyboardButton('Додати подію 📆', callback_data='add_event')
		check_tickets = types.InlineKeyboardButton('Перевірити квитки 🎟', callback_data='check_tickets')
		check_ticket_buy_request = types.InlineKeyboardButton('Перевірте 🧐 заявки на купівлю квитка 🎟 ',
															  callback_data='check_ticket_buy_request')

		markup.add(add_event, check_tickets, check_ticket_buy_request)
		bot.send_message(message.chat.id, "Адмін панель 👑", reply_markup=markup)


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

	elif call.data == 'back_menu':
		handle_start_page(call.message)

	elif data[0] == 'buy_ticket' or call.data == 'buy_ticket':

		markup = types.InlineKeyboardMarkup()

		with Session(engine) as session:
			event = session.query(Event).order_by(desc(Event.id)).first()

		ticket_data = {
			"date": f"{datetime.now().replace(microsecond=0)}",
			"ticket_id": randint(100000, 999999),
			"user_id": call.from_user.id,
			"username": call.from_user.username,
			"promoter": data[1] if data[1] in PROMOTERS else None,
			'default_price': event.event_price_default,
			'vip_price': event.event_price_vip,
			'deadline_price': event.event_price_deadline,
			'event_id': event.id,
		}

		default = types.InlineKeyboardButton('🎟️', callback_data='ticket_type_default')
		vip = types.InlineKeyboardButton('💎', callback_data='ticket_type_vip')

		markup.add(default, vip)

		bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text="Оберіть тип квитка 🎟️", reply_markup=markup)

		save_dict_to_redis(r, f'ticket_{call.from_user.id}', ticket_data)

	elif call.data == 'ticket_type_default':
		ticket_r = r.get(f'ticket_{call.from_user.id}')
		saved_dict = json.loads(ticket_r)
		saved_dict['ticket_type'] = 'default'
		bot.send_message(call.message.chat.id, f"Перекажіть кошти на банківську карту 💳 XXXX XXXX XXXX XXXX"
											   f"\nПотім напишіть номер картки💳, з якої були перераховані кошти, у форматі XXXXXX XXXXX XXXX XXXX")
		bot.register_next_step_handler(call.message, bank_card_input, saved_dict)

		r.delete(f'ticket_{call.from_user.id}')

	elif call.data == 'ticket_type_vip':
		ticket_r = r.get(f'ticket_{call.from_user.id}')
		saved_dict = json.loads(ticket_r)
		saved_dict['ticket_type'] = 'vip'
		bot.send_message(call.message.chat.id, f"Перекажіть кошти на банківську карту 💳 XXXX XXXX XXXX XXXX"
											   f"\nПотім напишіть номер картки💳, з якої були перераховані кошти, у форматі XXXXXX XXXXX XXXX XXXX")

		bot.register_next_step_handler(call.message, bank_card_input, saved_dict)

		r.delete(f'ticket_{call.from_user.id}')

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

			handle_admin(call.message)

		except Exception as e:
			print(e)
			bot.send_message(call.message.chat.id, "Помилка ❌при прийманні квитка🎟️")

	elif call.data == 'decline':
		r.delete(f'ticket_id_{call.from_user.id}')
		bot.edit_message_text(chat_id=call.message.chat.id, text="Квиток відхилен 💀", message_id=call.message.id)

		handle_admin(call.message)

	elif call.data == 'create_event':
		try:
			saved_dict_json = r.get(f'event_data_{call.from_user.id}')
			saved_dict = json.loads(saved_dict_json)

			with Session(engine) as session:
				session.add(Event(**saved_dict))
				session.commit()
			r.delete(f'event_data_{call.from_user.id}')
			bot.send_message(call.message.chat.id, "Захід добавлено🪩 ✅")
		except Exception as e:
			print(e)
			bot.send_message(call.message.chat.id, "Помилка при додаванні заходу ❌")

	elif call.data == 'eject_create_event':
		r.delete(f'event_data_{call.from_user.id}')

		bot.send_message(call.message.chat.id, "Створення заходу відхилено ❌")

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
						bot.send_message(call.message.chat.id, f"При отриманні квитка виникла помилка ❌")
			else:
				bot.send_message(call.message.chat.id, "Нема запитів на купівлю квитка 🧐")
			session.commit()
			handle_admin(call.message)

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
			bot.send_message(call.message.chat.id, f"Помилка при підтвердженні квитка {ticket.ticket_id} ❌")

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
			bot.send_message(call.message.chat.id, f"Помилка при выдхиленні квитка {ticket.ticket_id} ❌")


# Проверка билета
def check_ticket(message: Message):
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
		handle_admin(message)


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

		print(ticket_data)

		try:
			with Session(engine) as session:
				session.add(Ticket(**ticket_data))
				session.commit()
			bot.send_message(message.chat.id, f"Придбання вашого квитка була зареєстрованна!"
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
	if message.from_user.id in ADMINS:
		event_data = {
			'event_name': message.text
		}
		bot.send_message(message.chat.id, "Введіть дату захода у форматі DD.MM.YYYY 📆")
		bot.register_next_step_handler(message, handle_date_input, event_data)


# Ввод даты события
def handle_date_input(message: Message, event_data):
	if message.from_user.id in ADMINS:
		bot.send_message(message.chat.id, "Введіть звичайну вартість квитка 💵")
		event_data['event_date'] = message.text
		bot.register_next_step_handler(message, handle_price_default_input, event_data)


# Ввод цены при регистрации события для обычного клиента
def handle_price_default_input(message: Message, event_data):
	if message.from_user.id in ADMINS:
		bot.send_message(message.chat.id, "Введіть вартість VIP квитка 💰")
		event_data['event_price_default'] = message.text
		bot.register_next_step_handler(message, handle_price_vip_input, event_data)


# Ввод цены при регистрации события для VIP билета
def handle_price_vip_input(message: Message, event_data):
	if message.from_user.id in ADMINS:
		event_data['event_price_vip'] = message.text
		bot.send_message(message.chat.id, "Введіть вартість дедлайн билета 📅")
		bot.register_next_step_handler(message, handle_price_deadline_input, event_data)


# Ввод цены при регистрации события для дедлайн билета
def handle_price_deadline_input(message: Message, event_data):
	if message.from_user.id in ADMINS:
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
										  f"\n Ціна кінцевого терміну 💵: {event_data['event_price_deadline']}",
						 reply_markup=markup)

		handle_admin(message)


if __name__ == '__main__':
	r = redis.Redis(host='redis_app', port=5370, db=0)
	bot.polling()
