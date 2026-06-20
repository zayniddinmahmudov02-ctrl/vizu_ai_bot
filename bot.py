import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message,
    CallbackQuery,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from config import *
from database import *
from flask import Flask
from threading import Thread
bot = Bot(BOT_TOKEN)
dp = Dispatcher()

app = Flask(__name__)

@app.route("/")
def home():
    return "VIZU AI BOT ishlayapti!"
# =========================
# MENYU
# =========================
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(
                text="🏆 O'quvchilar reytingi"
            )
        ],
        [
            KeyboardButton(
                text="📤 Vazifa yuborish"
            )
        ],
        [
            KeyboardButton(
                text="👤 Mening profilim"
            )
        ]
    ],
    resize_keyboard=True
)

# =========================
# FSM STATES
# =========================
class RegisterState(StatesGroup):
    full_name = State()

class TaskState(StatesGroup):
    lesson = State()
    file = State()

class ProfileState(StatesGroup):
    rename = State()
# =========================
# START
# =========================
@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    user = await get_user(message.from_user.id)

    if user:
        await message.answer(
            f"Xush kelibsiz, {user[1]}!",
            reply_markup=main_menu
        )
        return

    await message.answer(
        "👋 Assalomu alaykum!\n\n"
        "Botdan foydalanish uchun ism va familiyangizni to'liq kiriting.\n\n"
        "Masalan:\n"
        "Zayniddinkhuja Makhmudov"
    )

    await state.set_state(RegisterState.full_name)

# =========================
# REGISTER
# =========================
@dp.message(RegisterState.full_name)
async def save_name(message: Message, state: FSMContext):
    full_name = message.text.strip()

    await add_user(
        message.from_user.id,
        full_name
    )

    await message.answer(
        "✅ Ma'lumot saqlandi.",
        reply_markup=main_menu
    )

    await state.clear()

# =========================
# TASK MENU
# =========================
@dp.message(F.text == "📤 Vazifa yuborish")
async def task_menu(message: Message, state: FSMContext):
    await message.answer(
        "📚 Qaysi dars vazifasini yubormoqchisiz?\n\n"
        "Masalan:\n"
        "1\n"
        "5\n"
        "12"
    )

    await state.set_state(TaskState.lesson)

# =========================
# LESSON NUMBER
# =========================
@dp.message(TaskState.lesson)
async def get_lesson(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer(
            "Faqat dars raqamini yuboring."
        )
        return

    lesson = int(message.text)

    await state.update_data(
        lesson=lesson
    )

    await message.answer(
        f"📤 {lesson}-dars uchun vazifangizni yuboring.\n\n"
        "Rasm, audio, video yoki fayl yuborishingiz mumkin."
    )

    await state.set_state(TaskState.file)

# =========================
# RECEIVE FILE
# =========================
@dp.message(
    TaskState.file,
    F.document |
    F.photo |
    F.video |
    F.voice |
    F.audio
)
async def receive_task(
    message: Message,
    state: FSMContext
):
    data = await state.get_data()

    lesson_number = data["lesson"]

    if message.document:
        file_id = message.document.file_id
        file_type = "document"

    elif message.photo:
        file_id = message.photo[-1].file_id
        file_type = "photo"

    elif message.video:
        file_id = message.video.file_id
        file_type = "video"

    elif message.voice:
        file_id = message.voice.file_id
        file_type = "voice"

    else:
        file_id = message.audio.file_id
        file_type = "audio"

    submission_id = await add_submission(
        message.from_user.id,
        message.from_user.full_name,
        lesson_number,
        file_id,
        file_type
    )

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⭐1",
                    callback_data=f"grade:{submission_id}:1"
                ),
                InlineKeyboardButton(
                    text="⭐2",
                    callback_data=f"grade:{submission_id}:2"
                ),
                InlineKeyboardButton(
                    text="⭐3",
                    callback_data=f"grade:{submission_id}:3"
                ),
                InlineKeyboardButton(
                    text="⭐4",
                    callback_data=f"grade:{submission_id}:4"
                ),
                InlineKeyboardButton(
                    text="⭐5",
                    callback_data=f"grade:{submission_id}:5"
                )
            ]
        ]
    )

    caption = (
        f"📥 Yangi vazifa\n\n"
        f"👤 {message.from_user.full_name}\n"
        f"🆔 {message.from_user.id}\n"
        f"📚 Dars: {lesson_number}\n"
        f"📄 ID: {submission_id}"
    )

    if file_type == "document":
        await bot.send_document(
            CHANNEL_ID,
            file_id,
            caption=caption,
            reply_markup=kb
        )

    elif file_type == "photo":
        await bot.send_photo(
            CHANNEL_ID,
            file_id,
            caption=caption,
            reply_markup=kb
        )

    elif file_type == "video":
        await bot.send_video(
            CHANNEL_ID,
            file_id,
            caption=caption,
            reply_markup=kb
        )

    elif file_type == "voice":
        await bot.send_voice(
            CHANNEL_ID,
            file_id,
            caption=caption,
            reply_markup=kb
        )

    else:
        await bot.send_audio(
            CHANNEL_ID,
            file_id,
            caption=caption,
            reply_markup=kb
        )

    await message.answer(
        "✅ Vazifa yuborildi.\n\nAdmin tekshiradi.",
        reply_markup=main_menu
    )

    await state.clear()
# =========================
# ADMIN GRADING
# =========================
@dp.callback_query(
    F.data.startswith("grade:")
)
async def grade_task(
    callback: CallbackQuery
):
    if callback.from_user.id not in ADMIN_IDS:
        return

    _, submission_id, score = callback.data.split(":")

    submission_id = int(submission_id)
    score = int(score)

    data = await get_submission(
        submission_id
    )

    if not data:
        return

    user_id = data[1]
    lesson_number = data[3]

    if score >= 4:
        status = "accepted"

        await bot.send_message(
            user_id,
            f"✅ {lesson_number}-dars vazifasi qabul qilindi.\n\n"
            f"⭐ Baho: {score}/5"
        )
    else:
        status = "rejected"

        await bot.send_message(
            user_id,
            f"❌ {lesson_number}-dars vazifasi qabul qilinmadi.\n\n"
            f"⭐ Baho: {score}/5\n\n"
            f"Qayta yuborishingiz mumkin."
        )

    await update_score(
        submission_id,
        score,
        status
    )

    await callback.answer(
        f"{score} baho qo'yildi"
    )

# =========================
# PROFILE
# =========================
@dp.message(
    F.text == "👤 Mening profilim"
)
async def my_profile(
    message: Message
):
    user = await get_user(
        message.from_user.id
    )

    if not user:
        return

    rank = await get_user_rank(
        message.from_user.id
    )

    text = (
        f"👤 Ism: {user[1]}\n\n"
        f"⭐ Jami ball: {user[2]}\n"
        f"✅ Qabul qilingan: {user[3]}\n"
        f"❌ Qaytarilgan: {user[4]}\n\n"
        f"🏆 Reyting: #{rank}"
    )

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="✏️ Ismni o'zgartirish"
                )
            ],
            [
                KeyboardButton(
                    text="⬅️ Orqaga"
                )
            ]
        ],
        resize_keyboard=True
    )

    await message.answer(
        text,
        reply_markup=kb
    )

# =========================
# RENAME
# =========================
@dp.message(
    F.text == "✏️ Ismni o'zgartirish"
)
async def rename_start(
    message: Message,
    state: FSMContext
):
    await message.answer(
        "Yangi ism-familiyangizni kiriting."
    )

    await state.set_state(
        ProfileState.rename
    )

@dp.message(ProfileState.rename)
async def rename_save(
    message: Message,
    state: FSMContext
):
    await update_name(
        message.from_user.id,
        message.text
    )

    await message.answer(
        "✅ Ism yangilandi.",
        reply_markup=main_menu
    )

    await state.clear()

# =========================
# RATING
# =========================
@dp.message(
    F.text == "🏆 O'quvchilar reytingi"
)
async def leaderboard(
    message: Message
):
    users = await get_top_users()

    text = "🏆 O'quvchilar reytingi\n\n"

    medal = [
        "🥇",
        "🥈",
        "🥉"
    ]

    for i, user in enumerate(users):

        if i < 3:
            prefix = medal[i]
        else:
            prefix = f"{i+1}."

        text += (
            f"{prefix} "
            f"{user[0]} — "
            f"{user[1]} ball\n"
        )

    await message.answer(text)

# =========================
# BACK
# =========================
@dp.message(
    F.text == "⬅️ Orqaga"
)
async def back_menu(
    message: Message
):
    await message.answer(
        "Asosiy menyu",
        reply_markup=main_menu
    )
# =========================
# FLASK WEB SERVER
# =========================
from flask import Flask
from threading import Thread
import os

app = Flask(__name__)

@app.route("/")
def home():
    return "VIZU AI BOT ishlayapti!"

def run_web():
    port = int(
        os.environ.get(
            "PORT",
            10000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port
    )

# =========================
# MAIN
# =========================
async def main():

    await init_db()

    Thread(
        target=run_web,
        daemon=True
    ).start()

    print("Bot ishga tushdi...")

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())