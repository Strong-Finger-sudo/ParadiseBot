from dotenv import load_dotenv
import os

load_dotenv()

# BOT CONFIG
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = 2559708
API_HASH = "379589fd8763fdfa87a3bb8f78953277"

# TEST_BOT
TEST_BOT_TOKEN = "6966859884:AAHS0VQ-euYD5vYqZz8FTtd_W6jMK2bZAwY"
TEST_API_ID = 2559708
TEST_API_HASH = "379589fd8763fdfa87a3bb8f78953277"

# ADMIN LIST
ADMINS = [651910998, 1068622041, 876255386, 737729515]

# DB POSTGRES
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_PORT = os.getenv("DB_PORT")
DB_PASS = os.getenv("DB_PASS")
DB_USER = os.getenv("DB_USER")

# TEST DB POSTGRES
TEST_DB_HOST = os.getenv("TEST_DB_HOST")
TEST_DB_NAME = os.getenv("TEST_DB_NAME")
TEST_DB_PORT = os.getenv("TEST_DB_PORT")
TEST_DB_PASS = os.getenv("TEST_DB_PASS")
TEST_DB_USER = os.getenv("TEST_DB_USER")

# REDIS DB
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")

# TEST REDIS DB
TEST_REDIS_HOST = os.getenv("TEST_REDIS_HOST")
TEST_REDIS_PORT = os.getenv("TEST_REDIS_PORT")

# PROMOTERS
PROMOTERS = [
	'dianaaaa_yaa', 'allvrnaa', 'Ksenichhhka', 'ieeslyss', 'evdants'
]
