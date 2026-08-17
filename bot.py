import asyncio
import os
import asyncpg
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = os.getenv("BOT_TOKEN")
KANAL = "@iPageUz"
DATABASE_URL = os.getenv("DATABASE_URL")
ADMIN_ID = 1369800095

bot = Bot(token=TOKEN)
dp = Dispatcher()
db_pool = None

KOMIKSLAR = {
    "Ajoyib Fantaziya": {
        "#15": "BQACAgIAAxkBAAMEah_Eg5PHnK_cnGidT_Ag0RTFsegAAnmgAAK8XZFI9UR38GVcbsU7BA",
    },
    "O'rgimchak-odam va Supermen": {
        "#1": "BQACAgIAAxkBAAPEaiT5TbIEuW95Im0gvp_KUvy43jAAAtOlAALA_CBJIgkZSFGwK5I7BA",
    },
    "Dum Yilnomalari": {
        "1-qism": "BQACAgIAAxkBAAIDXGovvvll2q4WO83WfVMFJJ1JDPs9AALHpgACFkmASWBwHYQ3MpT8PAQ",
        "2-qism": "BQACAgIAAxkBAAIHR2pPfC1p8plSFdzHiXl7foEgXCiiAAKvoQACvUyASjTl25ZKtOn5PAQ",
        "3-qism": "BQACAgIAAxkBAAIM8WprMuUNRa-mdVwwJDtV8Rk7-C0sAALspgAC6R9RS_SG0Gq7MU1lPQQ",
    },
    "Deadpool Marvel olamini o'ldiradi": {
        "1-qism": "BQACAgIAAxkBAAIE-2pCUtI1xClzfDV9IDdkvYIuPurRAAIHlwACdA4RSh2erBP3HHlTPAQ",
        "2-qism": "BQACAgIAAxkBAAIIWWpUcpLweNMyeCXfoubwCvx6oKviAAKnnwACMmSRSigYEpXP1My1PAQ",
        "3-qism": "BQACAgIAAxkBAAIOFWpvcnXRNSalrBniHXxa_Bk4Lu36AAJ7rAACGjtwS6Oa5tEiaO0ePQQ",
        "4-qism": "BQACAgIAAxkBAAIQump0hoU8dWR0ivuufxz05kd--M01AALOpwACBbahS-MoQAcfcPxyPQQ",
    },
    "Qora Qirol": {
        "1-qism": "BQACAgIAAxkBAAIL9mpoZ-SzPCBYXyL5sOmQbMOchmafAAJFqQACbMFAS5P7n-ONKQnNPQQ",
        "2-qism": "BQACAgIAAxkBAAIVrWp9TLFyI2hfBAWlHmot2oQ9f-_4AAK9pgACcy3gS4R0UjJaHW_7PQQ",
"3-qism": "BQACAgIAAxkBAAIYqWqCikOjIEqn4ZtH-G1E6bPYgj1jAALapwAC6FMJSH98bnsa4YrnPQQ",
    },
    "Fuqarolar Urushi": {
        "1-qism": "BQACAgIAAxkBAAIWzWqASoZgNUiQyjvPVEYr9N7zIOZ0AAKFsAAClvgISNBOqLJdJpdaPQQ",
    },
}

SAHIFA_HAJMI = 5

def seriya_sahifasini_topish(seriya_nomi: str) -> int:
    seriyalar = list(KOMIKSLAR.keys())
    if seriya_nomi in seriyalar:
        return seriyalar.index(seriya_nomi) // SAHIFA_HAJMI
    return 0

async def db_connect():
    global db_pool
    db_pool = await asyncpg.create_pool(DATABASE_URL)
    await db_pool.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            username TEXT,
            joined_at TIMESTAMP DEFAULT NOW()
        )
    """)

async def foydalanuvchi_saqlash(user_id: int, username: str):
    await db_pool.execute("""
        INSERT INTO users (user_id, username) VALUES ($1, $2)
        ON CONFLICT (user_id) DO NOTHING
    """, user_id, username)

async def foydalanuvchilar_soni() -> int:
    return await db_pool.fetchval("SELECT COUNT(*) FROM users")

async def barcha_foydalanuvchilar():
    return await db_pool.fetch("SELECT user_id FROM users")

async def obuna_tekshir(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(KANAL, user_id)
        return member.status not in ["left", "kicked", "restricted"]
    except:
        return False

def seriya_menyusi(sahifa: int = 0) -> InlineKeyboardMarkup:
    seriyalar = list(KOMIKSLAR.keys())
    boshlash = sahifa * SAHIFA_HAJMI
    tugash = boshlash + SAHIFA_HAJMI
    sahifadagi = seriyalar[boshlash:tugash]

    tugmalar = []
    for nom in sahifadagi:
        tugmalar.append([InlineKeyboardButton(text=f"{nom}", callback_data=f"seriya:{nom}:{sahifa}")])

    navigatsiya = []
    if sahifa > 0:
        navigatsiya.append(InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"sahifa:{sahifa-1}"))
    if tugash < len(seriyalar):
        navigatsiya.append(InlineKeyboardButton(text="Keyingisi ➡️", callback_data=f"sahifa:{sahifa+1}"))
    if navigatsiya:
        tugmalar.append(navigatsiya)

    return InlineKeyboardMarkup(inline_keyboard=tugmalar)

def qismlar_menyusi(seriya_nomi: str, sahifa: int) -> InlineKeyboardMarkup:
    qismlar = KOMIKSLAR.get(seriya_nomi, {})
    tugmalar = []
    for qism, fayl_id in qismlar.items():
        matn = f"✅ {qism}" if fayl_id else f"⏳ {qism}"
        tugmalar.append([InlineKeyboardButton(text=matn, callback_data=f"qism:{seriya_nomi}|{qism}|{sahifa}")])
    tugmalar.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data=f"sahifa:{sahifa}")])
    return InlineKeyboardMarkup(inline_keyboard=tugmalar)

def obuna_tugmasi() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Kanalga obuna bo'lish", url="https://t.me/iPageUz")],
        [InlineKeyboardButton(text="✅ Obunani tekshirish", callback_data="tekshir")]
    ])

def qaytish_tugmasi(sahifa: int = 0) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Ro'yxatga qaytish", callback_data=f"sahifa:{sahifa}")]
    ])

@dp.message(CommandStart())
async def start(message: types.Message):
    await foydalanuvchi_saqlash(message.from_user.id, message.from_user.username)
    if await obuna_tekshir(message.from_user.id):
        await message.answer("👋 Salom! Qaysi komiksni o'qimoqchisiz?", reply_markup=seriya_menyusi(0))
    else:
        await message.answer(
            "👋 Salom!\n\n📚 Marvel komikslarini o'zbek tilida o'qish uchun avval kanalimizga obuna bo'ling.\n\nObuna bo'lgach '✅ Obunani tekshirish' tugmasini bosing.",
            reply_markup=obuna_tugmasi()
        )

@dp.message(F.text == "/stats")
async def stats(message: types.Message):
    son = await foydalanuvchilar_soni()
    await message.answer(f"📊 Jami foydalanuvchilar: {son} ta")

@dp.message(Command("broadcast"))
async def broadcast(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    matn = message.text.replace("/broadcast", "").strip()
    if not matn:
        await message.answer("❌ Xabar matni kiriting.\nMisol: /broadcast Yangi komiks chiqdi!")
        return
    foydalanuvchilar = await barcha_foydalanuvchilar()
    yuborildi = 0
    xato = 0
    for foydalanuvchi in foydalanuvchilar:
        try:
            await bot.send_message(foydalanuvchi["user_id"], matn)
            yuborildi += 1
        except:
            xato += 1
    await message.answer(f"✅ Yuborildi: {yuborildi} ta\n❌ Xato: {xato} ta")

@dp.callback_query(F.data == "tekshir")
async def obuna_tekshirish(callback: types.CallbackQuery):
    if await obuna_tekshir(callback.from_user.id):
        await callback.message.edit_text("✅ Rahmat! Endi komikslarni o'qishingiz mumkin.", reply_markup=seriya_menyusi(0))
    else:
        await callback.answer("❌ Siz hali obuna bo'lmadingiz!", show_alert=True)

@dp.callback_query(F.data.startswith("sahifa:"))
async def sahifa_almashtirish(callback: types.CallbackQuery):
    sahifa = int(callback.data.split("sahifa:")[1])
    try:
        await callback.message.edit_text("📚 Qaysi komiksni o'qimoqchisiz?", reply_markup=seriya_menyusi(sahifa))
    except:
        await callback.message.answer("📚 Qaysi komiksni o'qimoqchisiz?", reply_markup=seriya_menyusi(sahifa))
    await callback.answer()

@dp.callback_query(F.data.startswith("seriya:"))
async def seriya_tanlash(callback: types.CallbackQuery):
    parts = callback.data.split("seriya:")[1].rsplit(":", 1)
    seriya_nomi = parts[0]
    sahifa = int(parts[1]) if len(parts) > 1 else 0
    await callback.message.edit_text(f"📖 *{seriya_nomi}* — qismni tanlang:", parse_mode="Markdown", reply_markup=qismlar_menyusi(seriya_nomi, sahifa))
    await callback.answer()

@dp.callback_query(F.data.startswith("qism:"))
async def qism_yuborish(callback: types.CallbackQuery):
    if not await obuna_tekshir(callback.from_user.id):
        await callback.answer("❌ Avval kanalga obuna bo'ling!", show_alert=True)
        return
    data = callback.data.split("qism:")[1]
    parts = data.rsplit("|", 1)
    seriya_qism = parts[0]
    sahifa = int(parts[1]) if len(parts) > 1 else 0
    seriya_nomi, qism = seriya_qism.split("|", 1)
    fayl_id = KOMIKSLAR.get(seriya_nomi, {}).get(qism)
    if fayl_id is None:
        await callback.message.answer(
            f"⏳ *{seriya_nomi} {qism}* hali tarjima qilinmoqda.\n\nTez orada tayyor bo'ladi!",
            parse_mode="Markdown",
            reply_markup=qaytish_tugmasi(sahifa)
        )
        await callback.answer()
    else:
        await callback.message.answer_document(fayl_id, caption=f"📖 {seriya_nomi} {qism}", protect_content=True)
        await callback.message.answer("👇 Ro'yxatga qaytish:", reply_markup=qaytish_tugmasi(sahifa))
        await callback.answer()

@dp.message(F.document)
async def fayl_id_olish(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer(f"Fayl ID: {message.document.file_id}")

async def main():
    await db_connect()
    print("Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
