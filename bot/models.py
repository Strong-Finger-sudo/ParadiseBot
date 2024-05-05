import secrets

from sqlalchemy import Column, Integer, String, MetaData, Table, Boolean, BigInteger, Time, Null, ForeignKey, DateTime, \
	Date

from database import metadata, Base

class Ticket(Base):
	__tablename__ = 'tickets'
	__table_args__ = {'extend_existing': True}

	id = Column(Integer, primary_key=True)
	ticket_id = Column(Integer, nullable=False)
	date = Column(DateTime, nullable=False)
	bank_card = Column(String, nullable=False)
	default_price = Column(Integer, nullable=False)
	vip_price = Column(Integer, nullable=False)
	deadline_price = Column(Integer, nullable=False)
	event_id = Column(Integer, ForeignKey('events.id'), nullable=False)
	ticket_type = Column(String, nullable=False)
	user_id = Column(BigInteger, nullable=False)
	promoter = Column(String, nullable=True)
	username = Column(String, nullable=False)
	full_name = Column(String, nullable=False)
	passed = Column(Boolean, default=False, nullable=False)
	confirmed = Column(Boolean, nullable=True)
	photo_url = Column(String, nullable=False)


class Staff(Base):
	__tablename__ = 'staff'
	__table_args__ = {'extend_existing': True}

	id = Column(Integer, primary_key=True)
	staff_type = Column(String)
	staff_name = Column(String)
	staff_username = Column(String)


class Event(Base):
	__tablename__ = 'events'
	__table_args__ = {'extend_existing': True}

	id = Column(Integer, primary_key=True)
	event_place = Column(String)
	event_name = Column(String)
	event_date = Column(Date)
	event_price_default = Column(Integer)
	event_price_vip = Column(Integer)
	event_price_deadline = Column(Integer)
