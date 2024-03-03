import secrets

from sqlalchemy import Column, Integer, String, MetaData, Table, Boolean, BigInteger, Time, Null

from bot.database import metadata, Base

class Ticket(Base):
	__tablename__ = 'tickets'

	id = Column(Integer, primary_key=True)
	ticket_id = Column(Integer)
	date = Column(String)
	bank_card = Column(String)
	price = Column(Integer)
	user_id = Column(BigInteger)
	promoter = Column(String, nullable=True)
	username = Column(String)
	full_name = Column(String)
	passed = Column(Boolean, default=False, nullable=False)
	confirmed = Column(Boolean, nullable=True)

class Event(Base):
	__tablename__ = 'events'

	id = Column(Integer, primary_key=True)
	event_name = Column(String)
	event_date = Column(String)
	event_price_default = Column(Integer)
	event_price_vip = Column(Integer)
	event_price_deadline = Column(Integer)