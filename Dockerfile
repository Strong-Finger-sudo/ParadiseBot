FROM python:3.8

RUN mkdir /bot

WORKDIR /bot

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

RUN chmod a+x docker/*.sh

RUN alembic upgrade head

WORKDIR bot

CMD python3 main.py