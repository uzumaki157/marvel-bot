import asyncio
import os
import asyncpg
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = os.getenv("BOT_TOKEN")
KANAL = "@iPageUz"
DATABASE_URL = os.getenv("DATABASE_URL")

bot = Bot(token=TOKEN)
dp = Dispatcher()
db_pool = None

KOMIKSLAR = {
    "Ajoyib Fantaziya #15": "BQACAgIAAxkBAAMEah_Eg5PHnK_cnGidT_Ag0RTFsegAAnmgAAK8XZFI9UR38GVcbsU7BA",
    "O'rgimchak-odam va Supermen #1": "BQACAgIAAxkBAAPEaiT5TbIEuW95Im0gvp_KUvy43jAAAtOlAALA_CBJIgkZSFGwK5I7BA",
    "DUM YILNOMALARI #1": "BQACAgIAAxkBAAIDXGovvvll2q4WO83WfVMFJJ1JDPs9AALHpgACFkmASWBwHYQ3MpT8PAQ",
"DUM YILNOMALARI #2": "BQACAgIAAxkBAAIHR2pPfC1p8plSFdzHiXl7foEgXCiiAAKvoQACvUyASjTl25ZKtOn5PAQ","Deadpool Marvel olamini o'ldiradi #1": "BQACAgIAAxkBAAIE-2pCUtI1xClzfDV9IDdkvYIuPurRAAIHlwACdA4RSh2erBP3HHlTPAQ",
"Deadpool Marvel olamini o'ldiradi #2": "BQACAgIAAxkBAAIIWWpUcpLweNMyeCXfoubwCvx6oKviAAKnnwACMmSRSigYEpXP1My1PAQ"
},
"QORA QIROL #1": "BQACAgIAAxkBAAIL9mpoZ-SzPCBYXyL5sOmQbMOchmafAAJFqQACbMFAS5P7n-ONKQnNPQQ"


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

async def obuna_tekshir(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(KANAL, user_id)
        return member.status not in ["left", "kicked", "restricted"]
    except:
        return False

def komiks_menyusi() -> InlineKeyboardMarkup:
    tugmalar = []
    for nom in KOMIKSLAR:
        tugmalar.append([InlineKeyboardButton(text=nom, callback_data=f"komiks:{nom}")])
    return InlineKeyboardMarkup(inline_keyboard=tugmalar)

def obuna_tugmasi() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Kanalga obuna bo'lish", url="https://t.me/iPageUz")],
        [InlineKeyboardButton(text="✅ Obunani tekshirish", callback_data="tekshir")]
    ])

def qaytish_tugmasi() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Ro'yxatga qaytish", callback_data="royxat")]
    ])

@dp.message(CommandStart())
async def start(message: types.Message):
    await foydalanuvchi_saqlash(message.from_user.id, message.from_user.username)
    if await obuna_tekshir(message.from_user.id):
        await message.answer("👋 Salom! Qaysi komiksni o'qimoqchisiz?", reply_markup=komiks_menyusi())
    else:
        await message.answer(
            "👋 Salom!\n\n📚 Marvel komikslarini o'zbek tilida o'qish uchun avval kanalimizga obuna bo'ling.\n\nObuna bo'lgach '✅ Obunani tekshirish' tugmasini bosing.",
            reply_markup=obuna_tugmasi()
        )

@dp.message(F.text == "/stats")
async def stats(message: types.Message):
    son = await foydalanuvchilar_soni()
    await message.answer(f"📊 Jami foydalanuvchilar: {son} ta")

@dp.callback_query(F.data == "tekshir")
async def obuna_tekshirish(callback: types.CallbackQuery):
    if await obuna_tekshir(callback.from_user.id):
        await callback.message.edit_text("✅ Rahmat! Endi komikslarni o'qishingiz mumkin.", reply_markup=komiks_menyusi())
    else:
        await callback.answer("❌ Siz hali obuna bo'lmadingiz!", show_alert=True)

@dp.callback_query(F.data == "royxat")
async def royxatga_qaytish(callback: types.CallbackQuery):
    await callback.message.answer("📚 Qaysi komiksni o'qimoqchisiz?", reply_markup=komiks_menyusi())
    await callback.answer()
@dp.callback_query(F.data.startswith("komiks:"))
async def komiks_yuborish(callback: types.CallbackQuery):
    if not await obuna_tekshir(callback.from_user.id):
        await callback.answer("❌ Avval kanalga obuna bo'ling!", show_alert=True)
        return
    nom = callback.data.split("komiks:")[1]
    fayl_id = KOMIKSLAR.get(nom)
    if fayl_id is None and nom in KOMIKSLAR:
        await callback.message.answer(
            f"⏳ *{nom}* hali tarjima qilinmoqda.\n\nTez orada tayyor bo'ladi — kanalimizni kuzatib boring!",
            parse_mode="Markdown",
            reply_markup=qaytish_tugmasi()
        )
        await callback.answer()
    elif fayl_id:
        await callback.message.answer_document(fayl_id, caption=f"📖 {nom}", protect_content=True, reply_markup=qaytish_tugmasi())
        await callback.answer()
    else:
        await callback.answer("❌ Komiks topilmadi", show_alert=True)

async def main():
    await db_connect()
    print("Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
