import os
import sys
import time
from datetime import datetime

from pyrogram import Client

# --------------------
# START CONF
# --------------------
# database connection config
mysql_localhost = "localhost"
mysql_username = "USERNAME"
mysql_password = "PASSWORD"

world_db = "acore_world"
char_db = "acore_characters"
auth_db = "acore_auth"

# zip config
zip_password = "db_zipped"
zip_name = f"db-{datetime.now():%Y%m%d}.zip"  # this will result in a string like "db-20211231.zip"

# replace "me" with a chat_id or username to change the chat
chat_id = "me"
# Telegram client config
username = "TELEGRAM_USERNAME"
api_id = 1234567
api_hash = "1234d401234d401234d401234d40"

# --------------------
# END CONF
# --------------------

app = Client(username, api_id=api_id, api_hash=api_hash)

# --no-tablespaces is required for mysql 8.0.21 based on the user privileges (https://dba.stackexchange.com/questions/271981/access-denied-you-need-at-least-one-of-the-process-privileges-for-this-ope)

# Pyrogram runs Client coroutines synchronously outside asyncio (pyrogram/sync.py);
# type checkers only see the async signatures, hence the ty ignores below.
with app:
    os.system(
        f"./dump-tables-mysql.sh {mysql_localhost} {mysql_username} {mysql_password} {world_db} world"
    )
    os.system(
        f"./dump-tables-mysql.sh {mysql_localhost} {mysql_username} {mysql_password} {char_db} characters"
    )
    os.system(
        f"./dump-tables-mysql.sh {mysql_localhost} {mysql_username} {mysql_password} {auth_db} auth"
    )
    os.system(f"zip -P {zip_password} -r {zip_name} world characters auth")

    time.sleep(1)

    app.send_document(chat_id, zip_name)  # ty: ignore[unused-awaitable]

    os.system("rm -rf world")
    os.system("rm -rf characters")
    os.system("rm -rf auth")
    os.remove(zip_name)

    app.stop()  # ty: ignore[unused-awaitable]
    sys.exit(0)  # exit from script

app.run()
