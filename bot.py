import asyncio

import os

from aiogram import Bot, Dispatcher, types, F

from aiogram.filters import CommandStart

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = os.getenv("BOT_TOKEN")

KANAL = "@SpideyUz"

bot = Bot(token=TOKEN)

dp = Dispatcher()

KOMIKSLAR = {

    "Ajoyib Fantaziya #15": "BQACAgIAAxkBAAP6ahyE7lXh3Pm0J0UMNuvRd_ew114AAnmgAAK8XZFIZhsIIMA_b887BA",

}

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

        [InlineKeyboardButton(text="📢 Kanalga obuna bo'lish", url="https://t.me/SpideyUz")],

        [InlineKeyboardButton(text="✅ Obunani tekshirish", callback_data="tekshir")]

    ])

@dp.message(CommandStart())

async def start(message: types.Message):

    if await obuna_tekshir(message.from_user.id):

        await message.answer("👋 Salom! Qaysi komiksni o'qimoqchisiz?", reply_markup=komiks_menyusi())

    else:

        await message.answer(

            "👋 Salom!\n\n📚 Marvel komikslarini o'zbek tilida o'qish uchun avval kanalimizga obuna bo'ling.\n\nObuna bo'lgach '✅ Obunani tekshirish' tugmasini bosing.",

            reply_markup=obuna_tugmasi()

        )

@dp.message(F.document)

async def fayl_id_olish(message: types.Message):

    await message.answer(f"Fayl ID: {message.document.file_id}")

@dp.callback_query(F.data == "tekshir")

async def obuna_tekshirish(callback: types.CallbackQuery):

    if await obuna_tekshir(callback.from_user.id):

        await callback.message.edit_text("✅ Rahmat! Endi komikslarni o'qishingiz mumkin.", reply_markup=komiks_menyusi())

    else:

        await callback.answer("❌ Siz hali obuna bo'lmadingiz!", show_alert=True)

@dp.callback_query(F.data.startswith("komiks:"))

async def komiks_yuborish(callback: types.CallbackQuery):

    if not await obuna_tekshir(callback.from_user.id):

        await callback.answer("❌ Avval kanalga obuna bo'ling!", show_alert=True)

        return

    nom = callback.data.split("komiks:")[1]

    fayl_id = KOMIKSLAR.get(nom)

    if fayl_id:

       await callback.message.answer_document(fayl_id, caption=f"📖 {nom}", protect_content=True)

        await callback.answer()

    else:

        await callback.answer("❌ Komiks topilmadi", show_alert=True)

async def main():

    print("Bot ishga tushdi...")

    await dp.start_polling(bot)

if __name__ == "__main__":

    asyncio.run(main())