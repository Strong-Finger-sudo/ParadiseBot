#Schemas
from datetime import datetime
from random import randint

from telebot.types import Message

from config import PROMOTERS


class TicketConstruct:
	def __init__(self, promoter, prices: dict, message: Message, event_date):
		self.ticket_id = randint(100000, 999999)
		self._date = datetime.now().replace(microsecond=0)
		self.bank_card = None
		self.price_default = prices['default']
		self.price_vip = prices['vip']
		self.price_deadline = prices['deadline']
		self._user_id = message.from_user.id
		self._promoter = promoter if promoter in PROMOTERS else None
		self._username = message.from_user.username
		self._event_date = event_date
		self._ticket_type = None
		self.full_name = None
		self._passed = None
		self._confirmed = None
		self._photo_url = None

	def set_fullname(self, full_name):
		self.full_name = full_name

	def set_passed(self, passed):
		self._passed = passed

	def set_confirmed(self, confirmed):
		self._confirmed = confirmed

	def set_photo_url(self, photo_url):
		self._photo_url = photo_url

	def set_bank_card(self, bank_card):
		self.bank_card = bank_card

	def set_ticket_type(self, ticket_type):
		self._ticket_type = ticket_type

	def to_dict(self):
		return {
			'ticket_id': self.ticket_id,
			'date': self._date,
			'bank_card': self.bank_card,
			'price_default': self.price_default,
			'price_vip': self.price_vip,
			'price_deadline': self.price_deadline,
			'user_id': self._user_id,
			'promoter': self._promoter,
			'username': self._username,
			'full_name': self.full_name,
			'passed': self._passed,
			'confirmed': self._confirmed,
			'photo_url': self._photo_url,
			'ticket_type': self._ticket_type,
			'event_date': self._event_date
		}