#Schemas
from datetime import datetime
from random import randint
from typing import Type, Optional

from telebot.types import CallbackQuery, Message

from bot.models import Event


class TicketOrderConstruct:
	def __init__(self):
		self._bank_card = None
		self._ticket_type = None
		self._full_name = None
		self._photo_url = None
		self._tickets_quantity = None
		self._promoter = None

	@property
	def promoter(self):
		return self._promoter

	@promoter.setter
	def promoter(self, value):
		self._promoter = value

	@property
	def bank_card(self):
		return self._bank_card

	@bank_card.setter
	def bank_card(self, bank_card):
		self._bank_card = bank_card

	@property
	def ticket_type(self):
		return self._ticket_type

	@ticket_type.setter
	def ticket_type(self, ticket_type):
		self._ticket_type = ticket_type

	@property
	def full_name(self):
		return self._full_name

	@full_name.setter
	def full_name(self, full_name):
		self._full_name = full_name

	@property
	def photo_url(self):
		return self._photo_url

	@photo_url.setter
	def photo_url(self, photo_url):
		self._photo_url = photo_url

	@property
	def tickets_quantity(self):
		return self._tickets_quantity

	@tickets_quantity.setter
	def tickets_quantity(self, quantity):
		self._tickets_quantity = quantity


class TicketConstruct:
	def __init__(self, promoter, message: Message, event: Optional[Type[Event]], order_cls: TicketOrderConstruct):
		self.ticket_id = randint(100000, 999999)
		self._date = datetime.now().replace(microsecond=0)
		self.bank_card = order_cls.bank_card
		self.default_price = event.event_price_default
		self.vip_price = event.event_price_vip
		self.deadline_price = event.event_price_deadline
		self._user_id = message.from_user.id
		self._promoter = promoter
		self._username = message.from_user.username
		self._event_id = event.id
		self._ticket_type = order_cls.ticket_type
		self.full_name = order_cls.full_name
		self._passed = None
		self._confirmed = None
		self._photo_url = order_cls.photo_url

	@property
	def ticket_type(self):
		return self._ticket_type

	@ticket_type.setter
	def ticket_type(self, ticket_type):
		self._ticket_type = ticket_type

	def to_dict(self):
		return {
			'ticket_id': self.ticket_id,
			'date': self._date,
			'bank_card': self.bank_card,
			'default_price': self.default_price,
			'vip_price': self.vip_price,
			'deadline_price': self.deadline_price,
			'user_id': self._user_id,
			'promoter': self._promoter,
			'username': self._username,
			'full_name': self.full_name,
			'passed': self._passed,
			'confirmed': self._confirmed,
			'photo_url': self._photo_url,
			'ticket_type': self._ticket_type,
			'event_id': self._event_id
		}
