import asyncio
import logging
import sys
import os
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# ----------------- CONFIGURATION FROM ENV -----------------
BOT_TOKEN = os.getenv("BOT_TOKEN")      
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))  
# ---------------------------------------------------------

if not BOT_TOKEN or not ADMIN_ID:
    logging.error("Environment variables BOT_TOKEN or ADMIN_ID are missing!")
    sys.exit(1)

class DepositStates(StatesGroup):
    awaiting_username = State()
    awaiting_ss = State()
    awaiting_txid = State()

dp = Dispatcher()
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))

def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="💰 ငွေဖြည့်ရန်")]],
        resize_keyboard=True
    )

@dp.message(CommandStart())
@dp.message(F.text == "💰 ငွေဖြည့်ရန်")
async def start_handler(message: Message, state: FSMContext):
    await state.set_state(DepositStates.awaiting_username)
    await message.answer(
        "👋 ဟုတ်ကဲ့၊ မင်္ဂလာပါ။\n\n📝 ကျေးဇူးပြု၍ သင့် Website ရဲ့ **Username** ကို ရိုက်ပို့ပေးပါခင်ဗျာ။\n\n/cancel နှိပ်၍ ပြန်ထွက်နိုင်ပါသည်။",
        reply_markup=get_main_keyboard()
    )

@dp.message(Command("cancel"))
@dp.message(F.text.lower() == "cancel")
async def cancel_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ လုပ်ဆောင်ချက်ကို ပယ်ဖျက်လိုက်ပါပြီ။ 💰 ငွေဖြည့်ရန် ခလုတ်ကို နှိပ်ပြီး ပြန်စနိုင်ပါသည်။", reply_markup=get_main_keyboard())

@dp.message(DepositStates.awaiting_username, F.text)
async def process_username(message: Message, state: FSMContext):
    await state.update_data(username=message.text)
    await state.set_state(DepositStates.awaiting_ss)
    
    payment_text = (
        "💳 **ငွေလွှဲရန် အချက်အလက်**\n\n"
        "🖤 **K Pay**\n09xxxxxxxxx\n(ကိုမင်းမင်း)\n\n"
        "🤍 **Wave Pay**\n09xxxxxxxxx\n(ကိုမင်းမင်း)\n\n"
        "⚠️ **လုပ်ဆောင်ရမည့်အဆင့်များ**\n"
        "1. အထက်ပါ အကောင့်သို့ ငွေလွှဲပါ။\n"
        "2. ငွေလွှဲပြီးလျှင် **ငွေလွှဲပြေစာ (Screenshot)** ကို ဤနေရာတွင် ပို့ပေးပါ။"
    )
    await message.answer(payment_text)

@dp.message(DepositStates.awaiting_ss, F.photo)
async def process_screenshot(message: Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    await state.update_data(photo_id=photo_id)
    await state.set_state(DepositStates.awaiting_txid)
    
    await message.answer("✅ ငွေလွှဲပြေစာ လက်ခံရရှိပါပြီ။\n\n🔢 လုပ်ငန်းစဉ်အမှတ် **Transaction ID (နောက်ဆုံး ဂဏန်း ၆ လုံး)** ကို စာသားဖြင့် ရိုက်ပို့ပေးပါခင်ဗျာ။\n\nဥပမာ - 123456")

@dp.message(DepositStates.awaiting_ss)
async def process_screenshot_invalid(message: Message):
    await message.answer("⚠️ ကျေးဇူးပြု၍ ငွေလွှဲပြေစာ ဓာတ်ပုံ (Screenshot) ကို ပို့ပေးပါရန်။")

@dp.message(DepositStates.awaiting_txid, F.text)
async def process_txid(message: Message, state: FSMContext):
    if len(message.text) < 6:
        await message.answer("⚠️ ကျေးဇူးပြု၍ နောက်ဆုံးဂဏန်း ၆ လုံးကို မှန်ကန်စွာ ရိုက်ထည့်ပေးပါရန်။")
        return

    user_data = await state.get_data()
    username = user_data['username']
    photo_id = user_data['photo_id']
    txid = message.text
    user_chat_id = message.chat.id

    await message.answer("🔄 သင့်ရဲ့ ငွေဖြည့်တောင်းဆိုမှုကို စစ်ဆေးနေပါပြီ။\nAdmin မှ စစ်ဆေးပြီးပါက Website ထဲသို့ ငွေထည့်သွင်းပေးပါမည်။ 🙏")

    
    admin_markup = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Approve (အောင်မြင်)", callback_data=f"approve_{user_chat_id}"),
            InlineKeyboardButton(text="❌ Reject (မအောင်မြင်)", callback_data=f"reject_{user_chat_id}")
        ]
    ])

    admin_caption = (
        f"🚨 **ငွေဖြည့်တောင်းဆိုမှုအသစ် ရောက်လာပါပြီ**\n\n"
        f"👤 **Website Username:** {username}\n"
        f"🔢 **Kpay TxID (၆ လုံး):** {txid}\n"
        f"🆔 **User Chat ID:** {user_chat_id}\n\n"
        f"အောက်က ခလုတ်ကို နှိပ်ပြီး အကြောင်းပြန်ပေးပါရန် 👇"
    )
    
    try:
        await bot.send_photo(chat_id=ADMIN_ID, photo=photo_id, caption=admin_caption, reply_markup=admin_markup)
    except Exception as e:
        logging.error(f"Failed to send to admin: {e}")

    await state.clear()

# ---
@dp.callback_query(F.data.startswith("approve_"))
async def admin_approve(callback: CallbackQuery):
    # 
    user_chat_id = int(callback.data.split("_")[1])
    
    #
    try:
        await bot.send_message(
            chat_id=user_chat_id, 
            text="🎉 **ငွေဖြည့်သွင်းခြင်း အောင်မြင်ပါသည်!**\n\nသင့်အကောင့်ထဲသို့ ငွေထည့်သွင်းပေးပြီးပါပြီ။ Website တွင် balance ကို ပြန်လည်စစ်ဆေးနိုင်ပါပြီ။ ကျေးဇူးတင်ပါသည်ခင်ဗျာ။ 💖"
        )
        # သင့် (Admin) ဆီက Message ကို စာသားပြောင်းလဲခြင်း
        await callback.message.edit_caption(
            caption=callback.message.caption + "\n\n🟢 **[အတည်ပြုပြီး - ငွေသွင်းအောင်မြင်ပါသည်]**",
            reply_markup=None # ခလုတ်ကို ဖျောက်လိုက်မယ်
        )
    except Exception as e:
        await callback.answer(f"Error: User ဆီ စာပို့လို့မရပါ (Bot ကို Block ထားတာ ဖြစ်နိုင်သည်)")

@dp.callback_query(F.data.startswith("reject_"))
async def admin_reject(callback: CallbackQuery):
    user_chat_id = int(callback.data.split("_")[1])
    
    try:
        await bot.send_message(
            chat_id=user_chat_id, 
            text="❌ **ငွေဖြည့်သွင်းခြင်း မအောင်မြင်ပါ။**\n\nသင်ပေးပို့လိုက်သော ငွေလွှဲပြေစာ သို့မဟုတ် အချက်အလက်များ မမှန်ကန်ပါ။ ကျေးဇူးပြု၍ အချက်အလက်များ ပြန်လည်စစ်ဆေးပြီး အသစ်ပြန်လည် တောင်းဆိုပေးပါရန်။"
        )
        await callback.message.edit_caption(
            caption=callback.message.caption + "\n\n🔴 **[ပယ်ဖျက်ပြီး - ငွေသွင်းမအောင်မြင်ပါ]**",
            reply_markup=None
        )
    except Exception as e:
        await callback.answer(f"Error: User ဆီ စာပို့လို့မရပါ")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
