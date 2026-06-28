import os
from dotenv import load_dotenv

load_dotenv()

import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
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
from aiogram.exceptions import TelegramBadRequest

bot = Bot(BOT_TOKEN)
dp = Dispatcher()
# =========================================================
# FLASK WEB SERVER
# =========================================================
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
        port=port,
        debug=False,
        use_reloader=False
    )
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
# ADMIN MENU
# =========================

admin_menu = ReplyKeyboardMarkup(
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
# ADMIN PANEL
# =========================

@dp.message(Command("admin"))
async def admin_panel(
    message: Message
):

    if message.from_user.id != MAIN_ADMIN_ID:
        return

    users = await get_users_count()
    tasks = await get_tasks_count()

    text = (
        "📊 Admin Panel\n\n"
        f"👥 Foydalanuvchilar: {users}\n"
        f"📚 Vazifalar: {tasks}\n\n"
        "⚙️ Admin rejimi faol"
    )

    await message.answer(text)

# =========================
# CHECK SUBSCRIPTION
# =========================

async def check_subscription(
    user_id: int
):

    try:

        member = await bot.get_chat_member(
            CHANNEL_USERNAME,
            user_id
        )

        return member.status in [
            "member",
            "administrator",
            "creator"
        ]

    except TelegramBadRequest:
        return False
# =========================
# CHECK SUB CALLBACK
# =========================
@dp.callback_query(
    F.data == "check_sub"
)
async def check_sub_callback(
    callback: CallbackQuery
):

    subscribed = await check_subscription(
        callback.from_user.id
    )

    if subscribed:

        await callback.message.delete()

        await callback.message.answer(
            "✅ Obuna tasdiqlandi.\n\n/start yuboring."
        )

    else:

        await callback.answer(
            "❌ Hali kanalga a'zo bo'lmagansiz.",
            show_alert=True
        )
# =========================
# FSM STATES
# =========================
class RegisterState(StatesGroup):
    full_name = State()

class TaskState(StatesGroup):
    lesson = State()
    task = State()
    file = State()

class ProfileState(StatesGroup):
    rename = State()

# =========================
# START
# =========================
@dp.message(CommandStart())
async def start(
    message: Message,
    state: FSMContext
):

    subscribed = await check_subscription(
        message.from_user.id
    )

    if not subscribed:

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📢 Kanalga kirish",
                        url=f"https://t.me/{CHANNEL_USERNAME.replace('@','')}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="✅ Tekshirish",
                        callback_data="check_sub"
                    )
                ]
            ]
        )

        await message.answer(
            "📢 Botdan foydalanish uchun kanalga obuna bo'ling.",
            reply_markup=kb
        )

        return

    user = await get_user(
        message.from_user.id
    )

    if user:
        if message.from_user.id == MAIN_ADMIN_ID:
            await message.answer(
                f"👑 Xush kelibsiz, {user['full_name']}!\n\n"
                "Admin panel uchun /admin yozing.",
                reply_markup=main_menu
            )
        else:
            await message.answer(
                f"Xush kelibsiz, {user['full_name']}!",
                reply_markup=main_menu
            )

        return

    await message.answer(
        "👋 Assalomu alaykum!\n\n"
        "Botdan foydalanish uchun ism va familiyangizni to'liq kiriting.\n\n"
        "Masalan:\n"
        "Zayniddinkhuja Makhmudov"
    )

    await state.set_state(
        RegisterState.full_name
    )
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
async def task_menu(
    message: Message,
    state: FSMContext
):

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="⬅️ Orqaga"
                )
            ]
        ],
        resize_keyboard=True
    )

    await message.answer(
        "📚 Qaysi dars vazifasini yubormoqchisiz?\n\n"
        "Masalan:\n"
        "1\n"
        "5\n"
        "12",
        reply_markup=kb
    )

    await state.set_state(
        TaskState.lesson
    )

# =========================
# LESSON NUMBER
# =========================
@dp.message(TaskState.lesson)
async def get_lesson(
    message: Message,
    state: FSMContext
):

    if message.text == "⬅️ Orqaga":

        await state.clear()

        await message.answer(
            "🏠 Asosiy menyu",
            reply_markup=main_menu
        )

        return

    if not message.text.isdigit():

        await message.answer(
            "❌ Faqat dars raqamini yuboring.\n\n"
            "Masalan: 1, 5, 12"
        )

        return

    lesson = int(message.text)

    await state.update_data(
        lesson=lesson
    )

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="⬅️ Orqaga"
                )
            ]
        ],
        resize_keyboard=True
    )

    await message.answer(
        f"📚 {lesson}-dars tanlandi.\n\n"
        "📝 Endi topshiriq raqamini kiriting.\n\n"
        "Masalan:\n"
        "1\n"
        "2\n"
        "3",
        reply_markup=kb
    )

    await state.set_state(
        TaskState.task
    )
# =========================
# TASK NUMBER
# =========================
@dp.message(TaskState.task)
async def get_task_number(
    message: Message,
    state: FSMContext
):

    if message.text == "⬅️ Orqaga":

        await state.set_state(
            TaskState.lesson
        )

        await message.answer(
            "📚 Dars raqamini kiriting."
        )

        return

    if not message.text.isdigit():

        await message.answer(
            "❌ Faqat topshiriq raqamini kiriting."
        )

        return

    task = int(message.text)

    await state.update_data(
        task=task
    )

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="⬅️ Orqaga"
                )
            ]
        ],
        resize_keyboard=True
    )

    await message.answer(
        f"📝 {task}-topshiriq tanlandi.\n\n"
        "📎 Endi vazifangizni yuboring.\n\n"
        "✅ Audio\n"
        "✅ Rasm\n"
        "✅ Video\n"
        "✅ Matn\n"
        "✅ Fayl",
        reply_markup=kb
    )

    await state.set_state(
        TaskState.file
    )
# =========================
# BACK FROM FILE
# =========================
@dp.message(
    TaskState.file,
    F.text == "⬅️ Orqaga"
)
async def back_from_file(
    message: Message,
    state: FSMContext
):

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="⬅️ Orqaga"
                )
            ]
        ],
        resize_keyboard=True
    )

    await message.answer(
        "📝 Topshiriq raqamini kiriting.",
        reply_markup=kb
    )

    await state.set_state(
        TaskState.task
    )
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
    try:

        data = await state.get_data()

        lesson_number = data.get("lesson")
        task_number = data.get("task")

        if not lesson_number:

            await message.answer(
                "❌ Dars raqami topilmadi."
            )

            await state.clear()
            return

        # 2-dars uchun qayta topshirishga ruxsat
        passed = await lesson_already_passed(
            message.from_user.id,
            lesson_number
        )

        if lesson_number != 2 and passed:

            await message.answer(
                f"✅ {lesson_number}-dars avval qabul qilingan.\n\n"
                "Qayta yuborish mumkin emas.",
                reply_markup=main_menu
            )

            await state.clear()
            return

        user = await get_user(
            message.from_user.id
        )

        if user:
            full_name = user["full_name"]
        else:
            full_name = (
                message.from_user.full_name
                or "Noma'lum"
            )

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

        elif message.audio:
            file_id = message.audio.file_id
            file_type = "audio"

        else:

            await message.answer(
                "❌ Fayl turi qo'llab-quvvatlanmaydi."
            )
            return

        # MUHIM O'ZGARISH
        submission_id = await add_submission(
            message.from_user.id,
            full_name,
            lesson_number,
            task_number,
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
            f"👤 O'quvchi: {full_name}\n"
            f"🆔 Telegram ID: {message.from_user.id}\n"
            f"📚 Dars: {lesson_number}\n"
            f"📝 Topshiriq: {task_number}\n"
            f"📄 Submission ID: {submission_id}"
        )

        sent_message = None

        if file_type == "document":

            sent_message = await bot.send_document(
                CHANNEL_ID,
                file_id,
                caption=caption,
                reply_markup=kb
            )

        elif file_type == "photo":

            sent_message = await bot.send_photo(
                CHANNEL_ID,
                file_id,
                caption=caption,
                reply_markup=kb
            )

        elif file_type == "video":

            sent_message = await bot.send_video(
                CHANNEL_ID,
                file_id,
                caption=caption,
                reply_markup=kb
            )

        elif file_type == "voice":

            sent_message = await bot.send_voice(
                CHANNEL_ID,
                file_id,
                caption=caption,
                reply_markup=kb
            )

        elif file_type == "audio":

            sent_message = await bot.send_audio(
                CHANNEL_ID,
                file_id,
                caption=caption,
                reply_markup=kb
            )

        print(
            f"CHANNEL MESSAGE ID: "
            f"{sent_message.message_id}"
        )

        await save_channel_message_id(
            submission_id,
            sent_message.message_id
        )

        await message.answer(
            "✅ Vazifa muvaffaqiyatli yuborildi.\n\n"
            "📚 Lehrer/in tekshiradi.",
            reply_markup=main_menu
        )

        await state.clear()

    except Exception as e:

        print(
            f"RECEIVE TASK ERROR: {e}"
        )

        await message.answer(
            f"❌ Xatolik:\n{e}"
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
    try:
        _, submission_id, score = callback.data.split(":")
        submission_id = int(submission_id)
        score = int(score)

        submission = await get_submission(
            submission_id
        )

        if not submission:
            await callback.answer(
                "❌ Vazifa topilmadi.",
                show_alert=True
            )
            return

        if submission["status"] != "pending":
            await callback.answer(
                "✅ Bu vazifa allaqachon baholangan.",
                show_alert=True
            )
            return

        status = (
            "accepted"
            if score >= 4
            else "rejected"
        )

        success = await update_score(
            submission_id,
            score,
            status
        )

        if not success:
            await callback.answer(
                "❌ Baholashda xatolik.",
                show_alert=True
            )
            return
        # =====================
        # AUTO COMMENT
        # =====================
        if score == 1:
            comment = (
                "❌ Vazifa qabul qilinmadi.\n\n"
                "⚠️ Mavzu hali yaxshi o'zlashtirilmagan.\n"
                "Darsni qayta ko'rib chiqing."
            )
        elif score == 2:
            comment = (
                "❌ Vazifa qabul qilinmadi.\n\n"
                "📖 Harakat bor, ammo ko'proq mashq qilish kerak."
            )
        elif score == 3:
            comment = (
                "❌ Vazifa qabul qilinmadi.\n\n"
                "👍 Yaxshi natija, lekin hali qabul qilish uchun yetarli emas.\n"
                "Xatolar ustida ishlang."
            )
        elif score == 4:
            comment = (
                "✅ Vazifa qabul qilindi.\n\n"
                "🌟 Juda yaxshi natija.\n"
                "Davom eting!"
            )
        else:
            comment = (
                "🏆 Vazifa qabul qilindi.\n\n"
                "Ajoyib! Vazifa mukammal bajarilgan."
            )

        # =====================
        # USERGA XABAR
        # =====================
        try:
            await bot.send_message(
                chat_id=int(
                    submission["user_id"]
                ),
                text=f"📚 {submission['lesson_number']}-dars tekshirildi.\n\n"
                     f"⭐ Baho: {score}/5\n\n"
                     f"{comment}"
            )
        except Exception as e:
            print(
                f"USER SEND ERROR: {e}"
            )

        # =====================
        # TUGMALARNI O'CHIRISH
        # =====================
        try:
            await callback.message.edit_reply_markup(
                reply_markup=None
            )
        except Exception as e:
            print(
                f"REMOVE BUTTON ERROR: {e}"
            )

    except Exception as e:
        print(
            f"GRADE TASK ERROR: {e}"
        )
        await callback.answer(
            f"❌ Xatolik: {e}",
            show_alert=True
        )
    # =====================
    # POSTNI TAHRIRLASH
    # =====================
    try:

        new_text = (
            f"{comment}\n\n"
            f"👤 {submission['full_name']}\n"
            f"🆔 {submission['user_id']}\n"
            f"📚 Dars: {submission['lesson_number']}\n"
            f"📄 ID: {submission_id}\n\n"
            f"⭐ Baho: {score}/5"
        )

        # captionli media
        if callback.message.caption:

            await callback.message.edit_caption(
                caption=new_text
            )

        # voice/audio va boshqa holatlar
        else:

            await bot.send_message(
                chat_id=CHANNEL_ID,
                reply_to_message_id=
                callback.message.message_id,
                text=new_text
            )

    except Exception as e:

        print(
            f"EDIT POST ERROR: {e}"
        )

    await callback.answer(
        f"⭐ {score}/5 qo'yildi"
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
        f"👤 Ism: {user['full_name']}\n\n"
        f"⭐ Jami ball: {user['total_score']}\n"
        f"✅ Qabul qilingan: {user['accepted_tasks']}\n"
        f"❌ Qaytarilgan: {user['rejected_tasks']}\n\n"
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

    if not users:
        await message.answer(
            "🏆 Reyting hozircha bo'sh."
        )
        return

    text = "🏆 O'quvchilar reytingi (TOP-100)\n\n"

    for i, user in enumerate(users):

        if i == 0:
            prefix = "🥇"

        elif i == 1:
            prefix = "🥈"

        elif i == 2:
            prefix = "🥉"

        else:
            prefix = f"#{i+1}"

        text += (
            f"{prefix} "
            f"{user['full_name']} — "
            f"{user['total_score']} ball\n"
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
    if message.from_user.id == MAIN_ADMIN_ID:

        await message.answer(
            "Asosiy menyu",
            reply_markup=main_menu
        )
    else:

        await message.answer(
            "Asosiy menyu",
            reply_markup=main_menu
        )
# =========================
# MAIN
# =========================
async def main():

    await init_db()

    await bot.delete_webhook(
        drop_pending_updates=True
    )

    me = await bot.get_me()

    print(
        f"STARTED BOT: @{me.username}"
    )

    print(
        f"BOT ID: {me.id}"
    )

    Thread(
        target=run_web,
        daemon=True
    ).start()

    print("Bot ishga tushdi...")

    await dp.start_polling(
        bot,
        allowed_updates=dp.resolve_used_update_types()
    )

if __name__ == "__main__":
    asyncio.run(main())