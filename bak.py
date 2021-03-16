from pyrogram import Client, Filters
import time
import os

# conf
mysql_localhost = "localhost"
mysql_username = "USERNAME"
mysql_password = "PASSWORD"

world_db = "acore_world"
char_db = "acore_characters"
auth_db = "acore_auth"

zip_password = "db_zipped"

app = Client(
  "TELEGRAM_USERNAME",
  api_id=1234567,
  api_hash="1234d401234d401234d401234d40"
)

# --no-tablespaces is required for mysql 8.0.21 based on the user privileges (https://dba.stackexchange.com/questions/271981/access-denied-you-need-at-least-one-of-the-process-privileges-for-this-ope)

with app:
  os.system("mysqldump --no-tablespaces --column-statistics=0 -h " + mysql_localhost + " -u " + mysql_username + " -p'" + mysql_password + "' " + world_db + " > world.sql")
  os.system("mysqldump --no-tablespaces --column-statistics=0 -h " + mysql_localhost + " -u " + mysql_username + " -p'" + mysql_password + "' " + char_db + " > characters.sql")
  os.system("mysqldump --no-tablespaces --column-statistics=0 -h " + mysql_localhost + " -u " + mysql_username + " -p'" + mysql_password + "' " + auth_db + " > auth.sql")
  os.system("zip -P " + zip_password + " db.zip world.sql characters.sql auth.sql")

  time.sleep(1)

  app.send_document("me", "db.zip") # replace "me" with a chat_id or username to change the chat

  os.remove("world.sql")
  os.remove("characters.sql")
  os.remove("auth.sql")
  os.remove("db.zip")

  app.stop()
  exit(0) # exit from script

app.run()
