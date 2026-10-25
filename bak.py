import asyncio
import glob
import os
import subprocess
import time
from datetime import datetime
from typing import Any

# Pyrogram 2.0.106 calls asyncio.get_event_loop() at import time; Python 3.14 no
# longer creates a loop implicitly, so one must exist before the import.
asyncio.set_event_loop(asyncio.new_event_loop())
import sys

from pyrogram import Client
from pyrogram.errors import FloodWait, RPCError

# how to extract: 7z x db-YYYYMMDD-world.7z.001

# --------------------
# START CONF
# --------------------
# database connection config
mysql_localhost = "localhost"
mysql_port = 3306
mysql_username = "USERNAME"
mysql_password = "PASSWORD"

world_db = "acore_world"
char_db = "acore_characters"
auth_db = "acore_auth"

# (database, short name used for its archive)
databases = [
    (world_db, "world"),
    (char_db, "characters"),
    (auth_db, "auth"),
]

# archive config: every run produces db-YYYYMMDD* files; an archive larger than
# volume_size is split in parts of at most that size (Telegram refuses uploads above 2 GB)
archive_password = "db_zipped"
archive_prefix = (
    f"db-{datetime.now():%Y%m%d}"  # this will result in a string like "db-20211231"
)
volume_size = "1400m"

# replace "me" with a chat_id or username to change the chat
chat_id = "me"
# Telegram client config
username = ""
api_id = ""
api_hash = ""

# Telegram uploads fail now and then (network drops, FloodWait): every archive is
# retried until Telegram confirms it, waiting retry_wait_seconds after a failure
# (doubled each time, up to 10 minutes). Archives still unsent after send_attempts
# tries stay on disk.
send_attempts = 20
retry_wait_seconds = 30

# --------------------
# END CONF
# --------------------

app = Client(username, api_id=api_id, api_hash=api_hash)

# --no-tablespaces is required for mysql 8.0.21 based on the user privileges (https://dba.stackexchange.com/questions/271981/access-denied-you-need-at-least-one-of-the-process-privileges-for-this-ope)


def sh(cmd):
    """Run a shell pipeline; abort the backup if any stage of it fails."""
    if (
        subprocess.run(
            "set -o pipefail; " + cmd, shell=True, executable="/bin/bash", check=False
        ).returncode
        != 0
    ):
        raise SystemExit("command failed, backup aborted")


def dump(db, name):
    # --single-transaction: one consistent InnoDB snapshot without locking the live tables.
    # The dump is streamed into 7z (-mx=1: fast LZMA2, -mhe=on: encrypted headers),
    # so no uncompressed .sql ever touches the disk.
    sh(
        f"mysqldump --single-transaction --no-tablespaces --column-statistics=0 -h {mysql_localhost} -P {mysql_port} -u {mysql_username} -p'{mysql_password}' {db} | 7z a -si{name}.sql -mx=1 -v{volume_size} -p'{archive_password}' -mhe=on {archive_prefix}-{name}.7z"
    )


def sync(result: Any) -> Any:
    """Return a pyrogram call result as is.

    Pyrogram runs Client coroutines synchronously outside asyncio (pyrogram/sync.py);
    type checkers only see the async signatures, so results pass through here untyped.
    """
    return result


def send(file_path):
    """Upload one archive; True once Telegram reports a document of the same size."""
    size = os.path.getsize(file_path)
    wait = retry_wait_seconds
    for attempt in range(1, send_attempts + 1):
        print(
            f"sending {file_path} ({size / 1024 / 1024:.0f} MB), attempt {attempt}/{send_attempts}"
        )
        try:
            message = sync(app.send_document(chat_id, file_path))
        except FloodWait as e:
            # FloodWait carries the seconds to wait; fall back to the normal pause otherwise
            flood_wait = e.value if isinstance(e.value, int) else retry_wait_seconds
            print(f"  Telegram asks to wait {flood_wait} s")
            time.sleep(flood_wait + 1)
            continue
        except (RPCError, OSError, TimeoutError) as e:
            print(f"  failed: {e!r}")
        else:
            if message and message.document and message.document.file_size == size:
                return True
            print("  Telegram did not confirm the upload")
        time.sleep(wait)
        wait = min(wait * 2, 600)
    return False


# leftovers of a previous run
for leftover in glob.glob("db-*.7z.*"):
    os.remove(leftover)

with app:
    # A session file starts with no known peers and Telegram refuses unknown ones
    # (PEER_ID_INVALID): listing the dialogs loads every chat this account has
    # talked to, then the check fails fast before spending minutes on dumps.
    for _ in sync(app.get_dialogs()):
        pass
    sync(app.resolve_peer(chat_id))

    for db, name in databases:
        dump(db, name)

    files_to_send = sorted(glob.glob(archive_prefix + "*"))
    if not files_to_send:
        raise SystemExit("no archive produced, nothing to send")

    unsent = []
    for file_path in files_to_send:
        if send(file_path):
            os.remove(file_path)
        else:
            unsent.append(file_path)
        time.sleep(1)

    sync(app.stop())

    if unsent:
        raise SystemExit("kept on disk, not sent: " + ", ".join(unsent))

    sys.exit(0)  # exit from script

app.run()
