import json


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