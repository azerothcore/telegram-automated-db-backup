from pyrogram import Client
from datetime import datetime
import time
import os

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
zip_name = "db{:%Y%m%d}.zip".format(datetime.now()) # this will result in a string like "db20211231.zip"

# replace "me" with a chat_id or username to change the chat
char_id = "me"
# Telegram client config
username = "TELEGRAM_USERNAME"
api_id=1234567
api_hash="1234d401234d401234d401234d40"

# --------------------
# END CONF
# --------------------

app = Client(
    username,
    api_id=api_id,
    api_hash=api_hash
)

# --no-tablespaces is required for mysql 8.0.21 based on the user privileges (https://dba.stackexchange.com/questions/271981/access-denied-you-need-at-least-one-of-the-process-privileges-for-this-ope)

with app:
    os.system("mysqldump --no-tablespaces --column-statistics=0 -h {} -u {} -p'{}' {} > world.sql".format(
        mysql_localhost,
        mysql_username,
        mysql_password,
        world_db
    ))
    os.system("mysqldump --no-tablespaces --column-statistics=0 -h {} -u {} -p'{}' {} > characters.sql".format(
        mysql_localhost,
        mysql_username,
        mysql_password,
        char_db
    ))
    os.system("mysqldump --no-tablespaces --column-statistics=0 -h {} -u {} -p'{}' {} > auth.sql".format(
        mysql_localhost,
        mysql_username,
        mysql_password,
        auth_db
    ))
    os.system("zip -P {} {} world.sql characters.sql auth.sql".format(
        zip_password,
        zip_name
    ))

    time.sleep(1)

    app.send_document(
        char_id,
        zip_name
        )

    os.remove("world.sql")
    os.remove("characters.sql")
    os.remove("auth.sql")
    os.remove(zip_name)

    app.stop()
    exit(0) # exit from script

app.run()
