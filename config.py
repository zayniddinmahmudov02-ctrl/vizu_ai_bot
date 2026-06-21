import os

BOT_TOKEN = os.getenv("BOT_TOKEN")

CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME")

CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

MAIN_ADMIN_ID = int(os.getenv("MAIN_ADMIN_ID"))

ADMIN_IDS = [
    int(x.strip())
    for x in os.getenv(
        "ADMIN_IDS",
        ""
    ).split(",")
    if x.strip()
]
DATABASE_URL = os.getenv(
    "DATABASE_URL"
)
# =========================
# BOT NAME
# =========================

BOT_NAME = "vizu_homework"