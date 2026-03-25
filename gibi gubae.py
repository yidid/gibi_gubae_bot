import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import sqlite3
from datetime import datetime
import logging
import os

# ==================== CONFIGURATION ====================
# REPLACE THESE WITH YOUR ACTUAL VALUES
BOT_TOKEN = "8685046978:AAE4xWpRThE5qVjK-wNhhvugkjNcAB6DPVI"  # Get from @BotFather
ADMIN_IDS = [5140218347]  # Replace with your Telegram ID from @userinfobot

# ==================== SETUP ====================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(BOT_TOKEN)

# Store pending purchases
user_pending_tshirt = {}
user_pending_lottery = {}

# ==================== DATABASE SETUP ====================
def init_db():
    """Initialize SQLite database"""
    conn = sqlite3.connect('gubi_event.db')
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            phone TEXT,
            registered_date TIMESTAMP
        )
    ''')
    
    # RSVP table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rsvp (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            status TEXT,
            timestamp TIMESTAMP
        )
    ''')
    
    # T-shirt orders table with payment
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tshirt_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            size TEXT,
            quantity INTEGER,
            total_price INTEGER,
            screenshot_file_id TEXT,
            status TEXT DEFAULT 'pending',
            timestamp TIMESTAMP
        )
    ''')
    
    # Lottery purchases table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lottery_purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            quantity INTEGER,
            total_price INTEGER,
            screenshot_file_id TEXT,
            status TEXT DEFAULT 'pending',
            timestamp TIMESTAMP
        )
    ''')
    
    # Comments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            comment TEXT,
            timestamp TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ ዳታቤዝ ተዘጋጅቷል")

init_db()

# ==================== HELPER FUNCTIONS ====================
def register_user(message):
    """Register user in database"""
    conn = sqlite3.connect('gubi_event.db')
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT OR IGNORE INTO users (user_id, username, first_name, last_name, registered_date)
            VALUES (?, ?, ?, ?, ?)
        ''', (message.from_user.id, message.from_user.username, 
              message.from_user.first_name, message.from_user.last_name,
              datetime.now()))
        conn.commit()
    except Exception as e:
        logger.error(f"ስህተት: {e}")
    finally:
        conn.close()

def is_admin(user_id):
    """Check if user is admin"""
    return user_id in ADMIN_IDS

# ==================== USER MENU ====================
def user_menu():
    """ዋና ማውጫ"""
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(
        KeyboardButton("📝 ለጉባኤው ይመዝገቡ"),
        KeyboardButton("ℹ️ የጉባኤው መረጃ"),
        KeyboardButton("👕 ቲሸርት ይዘዙ"),
        KeyboardButton("🎫 ሎተሪ ይግዙ"),
        KeyboardButton("💬 አስተያየት ይስጡ"),
        KeyboardButton("📊 ሁኔታዎን ይመልከቱ")
    )
    return markup

# ==================== ADMIN MENU ====================
def admin_menu():
    """የአድሚን ማውጫ"""
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(
        KeyboardButton("📊 አጠቃላይ ስታቲስቲክስ"),
        KeyboardButton("📋 የተመዘገቡ ሰዎች"),
        KeyboardButton("👕 የቲሸርት ትዕዛዞች"),
        KeyboardButton("🎫 የሎተሪ ግዢዎች"),
        KeyboardButton("⏳ የተጠባባቂ ትዕዛዞች"),
        KeyboardButton("💬 የአስተያየቶች"),
        KeyboardButton("📤 ዳታቢውዝ አውጣ"),
        KeyboardButton("🔙 ወደ ተጠቃሚ ማውጫ")
    )
    return markup

# ==================== START COMMAND ====================
@bot.message_handler(commands=['start'])
def start(message):
    """የመጀመሪያ መልእክት"""
    register_user(message)
    
    welcome_text = """
🎉 **እንኳን ወደ 30ኛ አመት የጉቢ ጉባኤ ቦት በደህና መጡ!** 🎉

ይህ ቦት በሚከተሉት ነገሮች ይረዳዎታል:

✅ ለጉባኤው መመዝገብ
ℹ️ የጉባኤውን መረጃ ማግኘት
👕 ቲሸርት ማዘዝ (ከክፍያ ጋር)
🎫 ሎተሪ መግዛት (ከክፍያ ጋር)
💬 አስተያየት መስጠት
📊 ሁኔታዎን መመልከት

ለመጀመር ከታች ያሉትን ቁልፎች ይጫኑ 👇
    """
    
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=user_menu())

# ==================== EVENT INFORMATION ====================
@bot.message_handler(func=lambda message: message.text == "ℹ️ የጉባኤው መረጃ")
def event_info(message):
    """የጉባኤው መረጃ"""
    info = """
📅 **የ30ኛ አመት የጉቢ ጉባኤ** 📅

🎉 **ዝግጅት:** 30ኛ አመት የጉቢ ጉባኤ
📍 **ቦታ:** በአ.ሳ.ቴ.ዩ ጉቢ ጉባኤ አዳራሽ
📅 **ቀን:** ግንቦት 1-2, 2018 ዓ.ም
🕐 **ሰዓት:** ከጠዋቱ 2:00 - ምሽቱ 6:00

👕 **ቲሸርት:**
• ዋጋ: 350 ብር
• መጠኖች: S, M, L

🎫 **ሎተሪ:**
• ዋጋ: 100 ብር በአንድ ቲኬት
• ሽልማቶች:
  - 1ኛ እጣ: በገና
  - 2ኛ እጣ: መጽሐፍ ቅዱስ
  - 3ኛ እጣ: መንፈሳዊ መጽሐፍ

📞 **ለበለጠ መረጃ:** 0911-123456
    """
    
    bot.send_message(message.chat.id, info, parse_mode="Markdown", reply_markup=user_menu())

# ==================== RSVP ====================

# ==================== RSVP WITH UPDATE CAPABILITY ====================

@bot.message_handler(func=lambda message: message.text == "📝 ለጉባኤው ይመዝገቡ")
def rsvp_prompt(message):
    """ለጉባኤው መመዝገቢያ - Shows current status and options"""
    
    # Check if user already has an RSVP
    conn = sqlite3.connect('gubi_event.db')
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM rsvp WHERE user_id = ? ORDER BY timestamp DESC LIMIT 1", (message.from_user.id,))
    existing = cursor.fetchone()
    conn.close()
    
    # Create markup with options
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("✅ አዎ እገኛለሁ", callback_data="rsvp_yes"),
        InlineKeyboardButton("❌ አይ፣ መገኘት አልችልም", callback_data="rsvp_no")
    )
    markup.row(
        InlineKeyboardButton("🤔 እርግጠኛ አይደለሁም", callback_data="rsvp_maybe")
    )
    
    # Customize message based on existing RSVP
    if existing:
        current_status = existing[0]
        status_text = {
            "yes": "እንደሚገኙ 🎉",
            "no": "እንደማይገኙ ❌",
            "maybe": "እርግጠኛ እንዳልሆኑ 🤔"
        }.get(current_status, "አልተመዘገቡም")
        
        msg = f"📝 **አሁን ያለዎት ሁኔታ:** {status_text}\n\n"
        msg += "ምላሽዎን መለወጥ ይፈልጋሉ? ከታች ያሉትን አማራጮች ይምረጡ:"
    else:
        msg = "ለ30ኛ አመት የጉቢ ጉባኤ ይገኛሉ?"
    
    bot.send_message(message.chat.id, msg, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("rsvp_"))
def handle_rsvp(call):
    """የRSVP ምላሽ ማስተናገጃ - Updates existing RSVP"""
    status = call.data.split("_")[1]
    
    conn = sqlite3.connect('gubi_event.db')
    cursor = conn.cursor()
    
    # Check if user already has an RSVP
    cursor.execute("SELECT id, status FROM rsvp WHERE user_id = ? ORDER BY timestamp DESC LIMIT 1", (call.from_user.id,))
    existing = cursor.fetchone()
    
    if existing:
        old_status = existing[1]
        # Update existing RSVP
        cursor.execute('''
            UPDATE rsvp 
            SET status = ?, timestamp = ? 
            WHERE id = ?
        ''', (status, datetime.now(), existing[0]))
        action = "ተቀይሯል"
    else:
        # Insert new RSVP
        cursor.execute('''
            INSERT INTO rsvp (user_id, username, status, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (call.from_user.id, call.from_user.username, status, datetime.now()))
        action = "ተመዝግቧል"
        old_status = None
    
    conn.commit()
    conn.close()
    
    # Confirmation message based on status
    if status == "yes":
        confirmation = f"✅ እናመሰግናለን! ምላሽዎ {action}. እንደሚገኙ ተመዝግቧል። 🎉"
    elif status == "no":
        confirmation = f"✅ እናመሰግናለን! ምላሽዎ {action}. እንደማይገኙ ተመዝግቧል።"
    else:
        confirmation = f"✅ እናመሰግናለን! ምላሽዎ {action}. እርግጠኛ እንዳልሆኑ ተመዝግቧል።"
    
    # If status changed, show old vs new
    if action == "ተቀይሯል" and old_status and old_status != status:
        old_status_text = {
            "yes": "እገኛለሁ",
            "no": "አልገኝም",
            "maybe": "እርግጠኛ አይደለሁም"
        }.get(old_status, "አልተመዘገበም")
        
        new_status_text = {
            "yes": "እገኛለሁ",
            "no": "አልገኝም",
            "maybe": "እርግጠኛ አይደለሁም"
        }.get(status, "አልተመዘገበም")
        
        confirmation += f"\n\n📝 ከቀድሞ ሁኔታዎ ({old_status_text}) ወደ ({new_status_text}) ቀይረዋል።"
    
    bot.edit_message_text(confirmation, call.message.chat.id, call.message.message_id)
    bot.send_message(call.message.chat.id, "ቀጣይ አገልግሎት ይምረጡ 👇", reply_markup=user_menu())

# ==================== T-SHIRT ORDER WITH PAYMENT ====================
@bot.message_handler(func=lambda message: message.text == "👕 ቲሸርት ይዘዙ")
def tshirt_order(message):
    markup = InlineKeyboardMarkup(row_width=3)
    sizes = [
        InlineKeyboardButton("ትንሽ (S) - 350 ብር", callback_data="tshirt_S"),
        InlineKeyboardButton("መካከለኛ (M) - 350 ብር", callback_data="tshirt_M"),
        InlineKeyboardButton("ትልቅ (L) - 350 ብር", callback_data="tshirt_L")
    ]
    markup.add(*sizes)
    bot.send_message(message.chat.id, "👕 እባክዎ የቲሸርት መጠን ይምረጡ:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("tshirt_"))
def handle_tshirt_size(call):
    size = call.data.split("_")[1]
    size_name = {"S": "ትንሽ", "M": "መካከለኛ", "L": "ትልቅ"}
    msg = bot.send_message(call.message.chat.id, 
                          f"የተመረጠ መጠን: {size_name[size]} (350 ብር)\n\nስንት ቲሸርት ማዘዝ ይፈልጋሉ?")
    bot.register_next_step_handler(msg, process_tshirt_quantity, size, call.message.chat.id, call.message.message_id)

def process_tshirt_quantity(message, size, chat_id, original_msg_id):
    try:
        quantity = int(message.text)
        if quantity < 1 or quantity > 100:
            raise ValueError
        
        total_price = quantity * 350
        
        user_pending_tshirt[message.from_user.id] = {
            'size': size, 'quantity': quantity, 'total_price': total_price, 'step': 'waiting_for_payment'
        }
        
        try:
            bot.delete_message(chat_id, original_msg_id)
        except:
            pass
        
        payment_info = f"""
✅ **{quantity} ቲሸርት - {total_price} ብር** ተመርጧል

📱 **የክፍያ መረጃ:**
🏦 ባንክ: ንግድ ባንክ
👤 ስም: ጉቢ ጉባኤ
🔢 አካውንት: 100000000000
📱 ቴሌብር: 090000000

📸 **ከከፈሉ በኋላ የክፍያ ማረጋገጫዎን ስክሪን ሾት ይላኩ!**
        """
        bot.send_message(message.chat.id, payment_info, parse_mode="Markdown")
        bot.send_message(message.chat.id, "📸 **እባክዎ የክፍያ ማረጋገጫዎን ስክሪን ሾት ይላኩ**\n\nበቀጥታ ፎቶውን ይላኩልኝ።\n\n✅ ስክሪን ሾት ከላኩ በኋላ ማረጋገጫ ይደርስዎታል።", parse_mode="Markdown")
                        
    except ValueError:
        msg = bot.send_message(message.chat.id, "❌ እባክዎ ትክክለኛ ቁጥር ያስገቡ (1-100):")
        bot.register_next_step_handler(msg, process_tshirt_quantity, size, chat_id, original_msg_id)

# ==================== LOTTERY WITH PAYMENT ====================
@bot.message_handler(func=lambda message: message.text == "🎫 ሎተሪ ይግዙ")
def lottery_prompt(message):
    markup = InlineKeyboardMarkup(row_width=3)
    for i in range(1, 6):
        markup.add(InlineKeyboardButton(f"{i} ቲኬት - {i*100} ብር", callback_data=f"lottery_{i}"))
    bot.send_message(message.chat.id, "🎫 **ሎተሪ ቲኬት ይግዙ!** 🎫\n\n💰 **ዋጋ:** 100 ብር በአንድ ቲኬት\n\n🏆 **ሽልማቶች:**\n• 1ኛ እጣ: በገና\n• 2ኛ እጣ: መጽሐፍ ቅዱስ\n• 3ኛ እጣ: መንፈሳዊ መጽሐፍ\n\nእባክዎ የሚፈልጉትን ብዛት ይምረጡ።", parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("lottery_"))
def handle_lottery_quantity(call):
    try:
        qty = int(call.data.split("_")[1])
        amount = qty * 100
        
        user_pending_lottery[call.from_user.id] = {'quantity': qty, 'amount': amount, 'step': 'waiting_for_payment'}
        
        payment_info = f"""
✅ **{qty} ቲኬት - {amount} ብር** ተመርጧል

📱 **የክፍያ መረጃ:**
🏦 ባንክ: ንግድ ባንክ
👤 ስም: ጉቢ ጉባኤ
🔢 አካውንት: 1000*******
📱 ቴሌብር: 09*******

📸 **ከከፈሉ በኋላ የክፍያ ማረጋገጫዎን ስክሪን ሾት ይላኩ!**
        """
        bot.edit_message_text(payment_info, call.message.chat.id, call.message.message_id, parse_mode="Markdown")
        bot.send_message(call.message.chat.id, "📸 **እባክዎ የክፍያ ማረጋገጫዎን ስክሪን ሾት ይላኩ**\n\nበቀጥታ ፎቶውን ይላኩልኝ።\n\n✅ ስክሪን ሾት ከላኩ በኋላ ማረጋገጫ ይደርስዎታል።", parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Lottery error: {e}")

# ==================== PHOTO HANDLER ====================
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    print(f"📸 Photo received from user {message.from_user.id}")
    bot.send_message(message.chat.id, "⏳ ስክሪን ሾትዎ እየተሰራ ነው...", reply_markup=user_menu())
    
    if message.from_user.id in user_pending_tshirt:
        pending = user_pending_tshirt[message.from_user.id]
        size = pending['size']
        quantity = pending['quantity']
        total_price = pending['total_price']
        photo_file_id = message.photo[-1].file_id
        size_name = {"S": "ትንሽ", "M": "መካከለኛ", "L": "ትልቅ"}
        
        try:
            conn = sqlite3.connect('gubi_event.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO tshirt_orders (user_id, username, size, quantity, total_price, screenshot_file_id, status, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (message.from_user.id, message.from_user.username, size, quantity, total_price, photo_file_id, 'pending', datetime.now()))
            conn.commit()
            conn.close()
            
            confirmation = f"""
✅ **የቲሸርት ትዕዛዝዎ ተመዝግቧል!**

━━━━━━━━━━━━━━━━━━━━━
📋 **ዝርዝር:**
👕 መጠን: {size_name[size]}
🔢 ብዛት: {quantity}
💰 ክፍያ: {total_price} ብር
⏳ ሁኔታ: **በመጠባበቅ ላይ** (Pending)
📅 ቀን: {datetime.now().strftime('%Y-%m-%d %H:%M')}
━━━━━━━━━━━━━━━━━━━━━

📌 **ምን ቀጥሎ?**
✓ ክፍያዎ በአድሚንዎች እየተረጋገጠ ነው።
✓ ከተረጋገጠ በኋላ ማሳወቂያ ይደርስዎታል።
            """
            bot.send_message(message.chat.id, confirmation, parse_mode="Markdown", reply_markup=user_menu())
            del user_pending_tshirt[message.from_user.id]
            
            for admin_id in ADMIN_IDS:
                try:
                    bot.send_message(admin_id, f"🔔 **አዲስ የቲሸርት ትዕዛዝ!**\n\n👤 {message.from_user.first_name}\n🆔 `{message.from_user.id}`\n👕 {size_name[size]} x {quantity} = {total_price} ብር\n⏳ ሁኔታ: በመጠባበቅ ላይ\n\n📸 `/viewscreenshot {message.from_user.id}`\n✅ `/confirm_tshirt {message.from_user.id}`\n❌ `/reject_tshirt {message.from_user.id}`", parse_mode="Markdown")
                except:
                    pass
        except Exception as e:
            print(f"Database error: {e}")
    
    elif message.from_user.id in user_pending_lottery:
        pending = user_pending_lottery[message.from_user.id]
        quantity = pending['quantity']
        amount = pending['amount']
        photo_file_id = message.photo[-1].file_id
        
        try:
            conn = sqlite3.connect('gubi_event.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO lottery_purchases (user_id, username, quantity, total_price, screenshot_file_id, status, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (message.from_user.id, message.from_user.username, quantity, amount, photo_file_id, 'pending', datetime.now()))
            conn.commit()
            conn.close()
            
            confirmation = f"""
✅ **ስክሪን ሾት ተቀብሏል!**

━━━━━━━━━━━━━━━━━━━━━
📋 **የግዢ ዝርዝር:**
🎫 ቲኬቶች: {quantity}
💰 ክፍያ: {amount} ብር
⏳ ሁኔታ: **በመጠባበቅ ላይ** (Pending)
📅 ቀን: {datetime.now().strftime('%Y-%m-%d %H:%M')}
━━━━━━━━━━━━━━━━━━━━━

📌 **ምን ቀጥሎ?**
✓ ክፍያዎ በአድሚንዎች እየተረጋገጠ ነው።
🍀 **መልካም እድል!**
            """
            bot.send_message(message.chat.id, confirmation, parse_mode="Markdown", reply_markup=user_menu())
            del user_pending_lottery[message.from_user.id]
            
            for admin_id in ADMIN_IDS:
                try:
                    bot.send_message(admin_id, f"🔔 **አዲስ የሎተሪ ግዢ!**\n\n👤 {message.from_user.first_name}\n🆔 `{message.from_user.id}`\n🎫 {quantity} ቲኬቶች - {amount} ብር\n⏳ ሁኔታ: በመጠባበቅ ላይ\n\n📸 `/viewscreenshot {message.from_user.id}`\n✅ `/confirm_lottery {message.from_user.id}`\n❌ `/reject_lottery {message.from_user.id}`", parse_mode="Markdown")
                except:
                    pass
        except Exception as e:
            print(f"Database error: {e}")
    else:
        bot.send_message(message.chat.id, "❌ **ስህተት!**\n\nይቅርታ፣ በመጀመሪያ የሚፈልጉትን አገልግሎት ይምረጡ።\n\n1. '👕 ቲሸርት ይዘዙ' ወይም '🎫 ሎተሪ ይግዙ' ይምረጡ\n2. መጠን/ብዛት ይምረጡ\n3. ክፍያ ይፈጽሙ\n4. ስክሪን ሾት ይስቀሉ", parse_mode="Markdown", reply_markup=user_menu())

# ==================== VIEW SCREENSHOT COMMAND ====================
@bot.message_handler(commands=['viewscreenshot'])
def view_screenshot(message):
    if not is_admin(message.from_user.id):
        bot.send_message(message.chat.id, "⛔ Admin only")
        return
    
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.send_message(message.chat.id, "❌ እባክዎ ትክክለኛ ትዕዛዝ ይጠቀሙ።\n\n/viewscreenshot [user_id]")
            return
        
        user_id = int(parts[1])
        conn = sqlite3.connect('gubi_event.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT screenshot_file_id, 'tshirt', size, quantity, total_price, status, timestamp
            FROM tshirt_orders WHERE user_id = ? AND status = 'pending'
            ORDER BY timestamp DESC LIMIT 1
        ''', (user_id,))
        result = cursor.fetchone()
        order_type = "tshirt"
        
        if not result:
            cursor.execute('''
                SELECT screenshot_file_id, 'lottery', quantity, quantity, total_price, status, timestamp
                FROM lottery_purchases WHERE user_id = ? AND status = 'pending'
                ORDER BY timestamp DESC LIMIT 1
            ''', (user_id,))
            result = cursor.fetchone()
            order_type = "lottery"
        
        conn.close()
        
        if result and result[0]:
            file_id = result[0]
            size_names = {"S": "ትንሽ", "M": "መካከለኛ", "L": "ትልቅ"}
            
            if order_type == 'tshirt':
                size = result[2]
                quantity = result[3]
                total = result[4]
                status = result[5]
                timestamp = result[6]
                caption = f"""
👕 **ቲሸርት ትዕዛዝ - ስክሪን ሾት**
━━━━━━━━━━━━━━━━━━━━━
🆔 ተጠቃሚ: `{user_id}`
📏 መጠን: {size_names.get(size, size)}
🔢 ብዛት: {quantity}
💰 ክፍያ: {total} ብር
⏳ ሁኔታ: {status}
📅 ቀን: {timestamp[:16]}
━━━━━━━━━━━━━━━━━━━━━

✅ `/confirm_tshirt {user_id}` - ለማረጋገጥ
❌ `/reject_tshirt {user_id}` - ለመሰረዝ
                """
            else:
                quantity = result[2]
                total = result[4]
                status = result[5]
                timestamp = result[6]
                caption = f"""
🎫 **ሎተሪ ግዢ - ስክሪን ሾት**
━━━━━━━━━━━━━━━━━━━━━
🆔 ተጠቃሚ: `{user_id}`
🎫 ቲኬቶች: {quantity}
💰 ክፍያ: {total} ብር
⏳ ሁኔታ: {status}
📅 ቀን: {timestamp[:16]}
━━━━━━━━━━━━━━━━━━━━━

✅ `/confirm_lottery {user_id}` - ለማረጋገጥ
❌ `/reject_lottery {user_id}` - ለመሰረዝ
                """
            bot.send_photo(message.chat.id, file_id, caption=caption, parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, f"❌ ለተጠቃሚ {user_id} ምንም የተጠባባቂ ትዕዛዝ ወይም ስክሪን ሾት አልተገኘም።")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ ስህተት: {e}")

# ==================== CONFIRM & REJECT COMMANDS ====================

# ==================== CONFIRM & REJECT COMMANDS WITH DEBUG ====================

@bot.message_handler(commands=['confirm_tshirt'])
def confirm_tshirt(message):
    """Admin: Confirm t-shirt payment"""
    if not is_admin(message.from_user.id):
        bot.send_message(message.chat.id, "⛔ ይቅርታ፣ ይህን ማድረግ አይችሉም።")
        return
    
    try:
        # Get user ID from command: /confirm_tshirt 6840176075
        parts = message.text.split()
        if len(parts) < 2:
            bot.send_message(message.chat.id, "❌ ትክክለኛ ትዕዛዝ አይደለም።\n\nእንደ: /confirm_tshirt 123456789")
            return
        
        user_id = int(parts[1])
        
        # Debug: Send a message showing we're processing
        bot.send_message(message.chat.id, f"🔍 እባክዎ ይጠብቁ... ለተጠቃሚ {user_id} ትዕዛዝ እየተረጋገጠ ነው...")
        
        conn = sqlite3.connect('gubi_event.db')
        cursor = conn.cursor()
        
        # First, check if user has ANY t-shirt orders
        cursor.execute("SELECT COUNT(*) FROM tshirt_orders WHERE user_id = ?", (user_id,))
        total_orders = cursor.fetchone()[0]
        
        # Check if there's a pending order
        cursor.execute("""
            SELECT quantity, size, username, status, id 
            FROM tshirt_orders 
            WHERE user_id = ? AND status = 'pending' 
            ORDER BY timestamp DESC LIMIT 1
        """, (user_id,))
        
        order = cursor.fetchone()
        
        # Debug info
        debug_msg = f"📊 ውሂብ ምርመራ:\n"
        debug_msg += f"• ጠቅላላ ትዕዛዞች: {total_orders}\n"
        debug_msg += f"• የተጠባባቂ ትዕዛዞች: {'አለ' if order else 'የለም'}\n"
        
        if order:
            qty, size, username, status, order_id = order
            debug_msg += f"• ትዕዛዝ ID: {order_id}\n"
            debug_msg += f"• መጠን: {size}, ብዛት: {qty}\n"
            debug_msg += f"• ሁኔታ: {status}\n"
            
            bot.send_message(message.chat.id, debug_msg, parse_mode="Markdown")
            
            # Update status to confirmed
            cursor.execute("""
                UPDATE tshirt_orders 
                SET status = 'confirmed' 
                WHERE id = ? AND status = 'pending'
            """, (order_id,))
            conn.commit()
            
            size_names = {"S": "ትንሽ", "M": "መካከለኛ", "L": "ትልቅ"}
            size_display = size_names.get(size, size)
            
            # Notify user
            try:
                bot.send_message(user_id, 
                                f"✅ **የቲሸርት ትዕዛዝዎ ተረጋገጠ!** 🎉\n\n"
                                f"👕 {size_display} x {qty} = {qty*350} ብር\n\n"
                                f"ቲሸርቶችዎ በጉባኤው ላይ ዝግጁ ይሆናሉ።\n\n"
                                f"እናመሰግናለን!",
                                parse_mode="Markdown")
                bot.send_message(message.chat.id, f"✅ ለተጠቃሚ {user_id} ትዕዛዝ ተረጋግጧል! ማሳወቂያ ተልኳል።")
            except Exception as e:
                bot.send_message(message.chat.id, f"✅ ለተጠቃሚ {user_id} ትዕዛዝ ተረጋግጧል! (ነገር ግን ማሳወቂያ መላክ አልተቻለም: {e})")
        else:
            # Check if user has any t-shirt orders at all
            if total_orders > 0:
                # Get all orders for this user to see their status
                cursor.execute("""
                    SELECT id, status, size, quantity, timestamp 
                    FROM tshirt_orders 
                    WHERE user_id = ? 
                    ORDER BY timestamp DESC
                """, (user_id,))
                all_orders = cursor.fetchall()
                
                debug_msg += f"\n📋 ሁሉም ትዕዛዞች:\n"
                for order_row in all_orders:
                    order_id, status, size, qty, ts = order_row
                    debug_msg += f"  • ID: {order_id}, ሁኔታ: {status}, መጠን: {size}, ብዛት: {qty}, ቀን: {ts[:16]}\n"
                
                bot.send_message(message.chat.id, debug_msg, parse_mode="Markdown")
                bot.send_message(message.chat.id, f"❌ ለተጠቃሚ {user_id} ምንም የተጠባባቂ ትዕዛዝ አልተገኘም። ነገር ግን ሌሎች ትዕዛዞች አሉ።")
            else:
                bot.send_message(message.chat.id, f"❌ ለተጠቃሚ {user_id} ምንም አይነት ትዕዛዝ አልተገኘም።")
        
        conn.close()
        
    except ValueError:
        bot.send_message(message.chat.id, f"❌ የተሳሳተ የተጠቃሚ መታወቂያ። እንደ: /confirm_tshirt 123456789")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ ስህተት: {e}")
        print(f"Error details: {e}")

@bot.message_handler(commands=['confirm_lottery'])
def confirm_lottery(message):
    """Admin: Confirm lottery payment"""
    if not is_admin(message.from_user.id):
        bot.send_message(message.chat.id, "⛔ ይቅርታ፣ ይህን ማድረግ አይችሉም።")
        return
    
    try:
        # Get user ID from command
        parts = message.text.split()
        if len(parts) < 2:
            bot.send_message(message.chat.id, "❌ ትክክለኛ ትዕዛዝ አይደለም።\n\nእንደ: /confirm_lottery 123456789")
            return
        
        user_id = int(parts[1])
        
        bot.send_message(message.chat.id, f"🔍 እባክዎ ይጠብቁ... ለተጠቃሚ {user_id} ሎተሪ ግዢ እየተረጋገጠ ነው...")
        
        conn = sqlite3.connect('gubi_event.db')
        cursor = conn.cursor()
        
        # Check total lottery purchases
        cursor.execute("SELECT COUNT(*) FROM lottery_purchases WHERE user_id = ?", (user_id,))
        total_purchases = cursor.fetchone()[0]
        
        # Check pending lottery purchase
        cursor.execute("""
            SELECT quantity, username, status, id 
            FROM lottery_purchases 
            WHERE user_id = ? AND status = 'pending' 
            ORDER BY timestamp DESC LIMIT 1
        """, (user_id,))
        
        order = cursor.fetchone()
        
        debug_msg = f"📊 ውሂብ ምርመራ:\n"
        debug_msg += f"• ጠቅላላ ግዢዎች: {total_purchases}\n"
        debug_msg += f"• የተጠባባቂ ግዢዎች: {'አለ' if order else 'የለም'}\n"
        
        if order:
            qty, username, status, order_id = order
            debug_msg += f"• ግዢ ID: {order_id}\n"
            debug_msg += f"• ብዛት: {qty}\n"
            debug_msg += f"• ሁኔታ: {status}\n"
            
            bot.send_message(message.chat.id, debug_msg, parse_mode="Markdown")
            
            cursor.execute("""
                UPDATE lottery_purchases 
                SET status = 'confirmed' 
                WHERE id = ? AND status = 'pending'
            """, (order_id,))
            conn.commit()
            
            try:
                bot.send_message(user_id, 
                                f"✅ **የሎተሪ ግዢዎ ተረጋገጠ!** 🎉\n\n"
                                f"🎫 {qty} ቲኬቶች\n\n"
                                f"🍀 መልካም እድል!\n\n"
                                f"ሽልማቶች በጉባኤው ቀን ይወጣሉ።",
                                parse_mode="Markdown")
                bot.send_message(message.chat.id, f"✅ ለተጠቃሚ {user_id} ግዢ ተረጋግጧል! ማሳወቂያ ተልኳል።")
            except Exception as e:
                bot.send_message(message.chat.id, f"✅ ለተጠቃሚ {user_id} ግዢ ተረጋግጧል! (ነገር ግን ማሳወቂያ መላክ አልተቻለም: {e})")
        else:
            if total_purchases > 0:
                cursor.execute("""
                    SELECT id, status, quantity, timestamp 
                    FROM lottery_purchases 
                    WHERE user_id = ? 
                    ORDER BY timestamp DESC
                """, (user_id,))
                all_purchases = cursor.fetchall()
                
                debug_msg += f"\n📋 ሁሉም ግዢዎች:\n"
                for purchase in all_purchases:
                    order_id, status, qty, ts = purchase
                    debug_msg += f"  • ID: {order_id}, ሁኔታ: {status}, ብዛት: {qty}, ቀን: {ts[:16]}\n"
                
                bot.send_message(message.chat.id, debug_msg, parse_mode="Markdown")
                bot.send_message(message.chat.id, f"❌ ለተጠቃሚ {user_id} ምንም የተጠባባቂ ግዢ አልተገኘም። ነገር ግን ሌሎች ግዢዎች አሉ።")
            else:
                bot.send_message(message.chat.id, f"❌ ለተጠቃሚ {user_id} ምንም አይነት የሎተሪ ግዢ አልተገኘም።")
        
        conn.close()
        
    except ValueError:
        bot.send_message(message.chat.id, f"❌ የተሳሳተ የተጠቃሚ መታወቂያ። እንደ: /confirm_lottery 123456789")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ ስህተት: {e}")
        print(f"Error details: {e}")
# ==================== COMMENTS ====================
@bot.message_handler(func=lambda message: message.text == "💬 አስተያየት ይስጡ")
def comment_prompt(message):
    msg = bot.send_message(message.chat.id, "📝 **አስተያየትዎን ያጋሩን** 📝\n\nስለ ጉባኤው አስተያየትዎን ይጻፉ:", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_comment)

def process_comment(message):
    conn = sqlite3.connect('gubi_event.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO comments (user_id, username, comment, timestamp) VALUES (?, ?, ?, ?)',
                   (message.from_user.id, message.from_user.username, message.text, datetime.now()))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "✅ **እናመሰግናለን!** አስተያየትዎ ተመዝግቧል።", parse_mode="Markdown", reply_markup=user_menu())

# ==================== USER STATUS ====================
@bot.message_handler(func=lambda message: message.text == "📊 ሁኔታዎን ይመልከቱ")
def show_status(message):
    """የተጠቃሚ ሁኔታ - Shows RSVP with option to change"""
    user_id = message.from_user.id
    conn = sqlite3.connect('gubi_event.db')
    cursor = conn.cursor()
    
    # Get RSVP status
    cursor.execute("SELECT status, timestamp FROM rsvp WHERE user_id = ? ORDER BY timestamp DESC LIMIT 1", (user_id,))
    rsvp = cursor.fetchone()
    
    # Get t-shirt orders
    cursor.execute("SELECT size, quantity, status FROM tshirt_orders WHERE user_id = ?", (user_id,))
    shirts = cursor.fetchall()
    
    # Get lottery purchases
    cursor.execute("SELECT quantity, status FROM lottery_purchases WHERE user_id = ?", (user_id,))
    lottery = cursor.fetchall()
    
    conn.close()
    
    status_text = "📊 **የእርስዎ ሁኔታ** 📊\n\n"
    
    # RSVP Status with option to change
    if rsvp:
        rsvp_status, rsvp_date = rsvp
        if rsvp_status == "yes":
            status_text += "**✅ ለጉባኤው:** እገኛለሁ 🎉\n"
        elif rsvp_status == "no":
            status_text += "**❌ ለጉባኤው:** አልገኝም\n"
        else:
            status_text += "**🤔 ለጉባኤው:** እርግጠኛ አይደለሁም\n"
        status_text += f"   📅 ቀን: {rsvp_date[:16]}\n"
    else:
        status_text += "**⚠️ ለጉባኤው:** ገና አልተመዘገቡም\n"
    
    # T-Shirt Orders
    if shirts:
        status_text += "\n**👕 ቲሸርት ትዕዛዞች:**\n"
        size_names = {"S": "ትንሽ", "M": "መካከለኛ", "L": "ትልቅ"}
        for size, qty, status in shirts:
            emoji = "✅" if status == "confirmed" else "⏳" if status == "pending" else "❌"
            status_text += f"  • {size_names[size]}: {qty} - {emoji} {status}\n"
    else:
        status_text += "\n**👕 ቲሸርት:** የለም\n"
    
    # Lottery
    if lottery:
        status_text += "\n**🎫 ሎተሪ ግዢዎች:**\n"
        for qty, status in lottery:
            emoji = "✅" if status == "confirmed" else "⏳" if status == "pending" else "❌"
            status_text += f"  • {qty} ቲኬቶች - {emoji} {status}\n"
    else:
        status_text += "\n**🎫 ሎተሪ:** የለም\n"
    
    # Add inline button to change RSVP
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📝 ምላሽ መለወጥ", callback_data="change_rsvp"))
    
    bot.send_message(message.chat.id, status_text, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "change_rsvp")
def change_rsvp(call):
    """Handle change RSVP button click"""
    # Show RSVP options again
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("✅ አዎ እገኛለሁ", callback_data="rsvp_yes"),
        InlineKeyboardButton("❌ አይ፣ መገኘት አልችልም", callback_data="rsvp_no")
    )
    markup.row(
        InlineKeyboardButton("🤔 እርግጠኛ አይደለሁም", callback_data="rsvp_maybe")
    )
    
    bot.edit_message_text("ምላሽዎን መለወጥ ይፈልጋሉ? አዲስ ምላሽ ይምረጡ:", 
                         call.message.chat.id, 
                         call.message.message_id,
                         reply_markup=markup)
# ==================== ADMIN COMMANDS ====================
@bot.message_handler(commands=['admin'])
def admin_start(message):
    if not is_admin(message.from_user.id):
        bot.send_message(message.chat.id, "⛔ ይቅርታ፣ ይህን ማድረግ አይችሉም።")
        return
    bot.send_message(message.chat.id, "🔐 እንኳን ወደ አድሚን ፓነል በደህና መጡ!", reply_markup=admin_menu())

@bot.message_handler(func=lambda message: message.text == "🔙 ወደ ተጠቃሚ ማውጫ" and is_admin(message.from_user.id))
def back_to_user(message):
    bot.send_message(message.chat.id, "ወደ ተጠቃሚ ማውጫ ተመልሰዋል", reply_markup=user_menu())

@bot.message_handler(func=lambda message: message.text == "📊 አጠቃላይ ስታቲስቲክስ" and is_admin(message.from_user.id))
def admin_stats(message):
    conn = sqlite3.connect('gubi_event.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users"); users = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM rsvp WHERE status='yes'"); attending = cursor.fetchone()[0]
    cursor.execute("SELECT SUM(quantity) FROM tshirt_orders"); shirts = cursor.fetchone()[0] or 0
    cursor.execute("SELECT SUM(quantity) FROM lottery_purchases"); lottery = cursor.fetchone()[0] or 0
    cursor.execute("SELECT COUNT(*) FROM tshirt_orders WHERE status='pending'"); pending_tshirts = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM lottery_purchases WHERE status='pending'"); pending_lottery = cursor.fetchone()[0]
    conn.close()
    
    stats = f"""
📊 **አጠቃላይ ስታቲስቲክስ** 📊
👥 ተጠቃሚዎች: {users}
✅ የሚገኙ: {attending}
👕 ቲሸርቶች: {shirts}
🎫 ሎተሪ: {lottery}
⏳ የተጠባባቂ ቲሸርት: {pending_tshirts}
⏳ የተጠባባቂ ሎተሪ: {pending_lottery}
💰 **ገቢ:** {shirts * 350 + lottery * 100} ብር
"""
    bot.send_message(message.chat.id, stats, parse_mode="Markdown", reply_markup=admin_menu())

@bot.message_handler(func=lambda message: message.text == "📋 የተመዘገቡ ሰዎች" and is_admin(message.from_user.id))
def admin_rsvp(message):
    """የተመዘገቡ ሰዎች ዝርዝር - Shows latest status only"""
    conn = sqlite3.connect('gubi_event.db')
    cursor = conn.cursor()
    
    # Get the latest RSVP for each user
    cursor.execute('''
        SELECT u.first_name, u.last_name, u.username, r.status, MAX(r.timestamp)
        FROM rsvp r 
        LEFT JOIN users u ON r.user_id = u.user_id
        GROUP BY r.user_id
        ORDER BY MAX(r.timestamp) DESC
        LIMIT 20
    ''')
    data = cursor.fetchall()
    conn.close()
    
    if not data:
        bot.send_message(message.chat.id, "ምንም የተመዘገበ ሰው የለም", reply_markup=admin_menu())
        return
    
    text = "📋 **የተመዘገቡ ሰዎች (የቅርብ ምላሽ)** 📋\n\n"
    for first, last, username, status, ts in data:
        name = f"{first or ''} {last or ''}".strip() or username or "ያልታወቀ"
        emoji = "✅" if status == "yes" else "❌" if status == "no" else "🤔"
        status_text = "እገኛለሁ" if status == "yes" else "አልገኝም" if status == "no" else "እርግጠኛ አይደለሁም"
        text += f"{emoji} **{name}** - {status_text}\n   📅 {ts[:16]}\n\n"
    
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=admin_menu())
@bot.message_handler(func=lambda message: message.text == "👕 የቲሸርት ትዕዛዞች" and is_admin(message.from_user.id))
def admin_tshirts(message):
    conn = sqlite3.connect('gubi_event.db')
    cursor = conn.cursor()
    cursor.execute('''SELECT u.first_name, u.last_name, u.username, t.size, t.quantity, t.status, t.timestamp
                     FROM tshirt_orders t JOIN users u ON t.user_id = u.user_id ORDER BY t.timestamp DESC LIMIT 20''')
    data = cursor.fetchall()
    conn.close()
    if not data:
        bot.send_message(message.chat.id, "ምንም የቲሸርት ትዕዛዝ የለም", reply_markup=admin_menu())
        return
    size_names = {"S": "ትንሽ", "M": "መካከለኛ", "L": "ትልቅ"}
    text = "👕 **የቲሸርት ትዕዛዞች** 👕\n\n"
    for first, last, username, size, qty, status, ts in data:
        name = f"{first or ''} {last or ''}".strip() or username or "ያልታወቀ"
        emoji = "✅" if status == "confirmed" else "⏳" if status == "pending" else "❌"
        text += f"**{name}**: {size_names[size]} x {qty} = {qty*350} ብር {emoji}\n   📅 {ts[:10]}\n\n"
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=admin_menu())

@bot.message_handler(func=lambda message: message.text == "🎫 የሎተሪ ግዢዎች" and is_admin(message.from_user.id))
def admin_lottery(message):
    conn = sqlite3.connect('gubi_event.db')
    cursor = conn.cursor()
    cursor.execute('''SELECT u.first_name, u.last_name, u.username, l.quantity, l.status, l.timestamp
                     FROM lottery_purchases l JOIN users u ON l.user_id = u.user_id ORDER BY l.timestamp DESC LIMIT 20''')
    data = cursor.fetchall()
    conn.close()
    if not data:
        bot.send_message(message.chat.id, "ምንም የሎተሪ ግዢ የለም", reply_markup=admin_menu())
        return
    text = "🎫 **የሎተሪ ግዢዎች** 🎫\n\n"
    for first, last, username, qty, status, ts in data:
        name = f"{first or ''} {last or ''}".strip() or username or "ያልታወቀ"
        emoji = "✅" if status == "confirmed" else "⏳" if status == "pending" else "❌"
        text += f"**{name}**: {qty} ቲኬቶች - {qty*100} ብር {emoji}\n   📅 {ts[:10]}\n\n"
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=admin_menu())

@bot.message_handler(func=lambda message: message.text == "⏳ የተጠባባቂ ትዕዛዞች" and is_admin(message.from_user.id))
def admin_pending(message):
    """የተጠባባቂ ትዕዛዞች"""
    conn = sqlite3.connect('gubi_event.db')
    cursor = conn.cursor()
    
    # Get pending t-shirt orders
    cursor.execute('''
        SELECT user_id, username, size, quantity, total_price, timestamp
        FROM tshirt_orders 
        WHERE status = 'pending'
        ORDER BY timestamp DESC
    ''')
    tshirt_pending = cursor.fetchall()
    
    # Get pending lottery orders
    cursor.execute('''
        SELECT user_id, username, quantity, total_price, timestamp
        FROM lottery_purchases 
        WHERE status = 'pending'
        ORDER BY timestamp DESC
    ''')
    lottery_pending = cursor.fetchall()
    
    conn.close()
    
    if not tshirt_pending and not lottery_pending:
        bot.send_message(message.chat.id, "📭 ምንም የተጠባባቂ ትዕዛዝ የለም።", reply_markup=admin_menu())
        return
    
    size_names = {"S": "ትንሽ", "M": "መካከለኛ", "L": "ትልቅ"}
    text = "⏳ የተጠባባቂ ትዕዛዞች ⏳\n\n"
    
    for item in tshirt_pending:
        user_id, username, size, qty, price, ts = item
        text += "━━━━━━━━━━━━━━━━━━━━━\n"
        text += f"👕 ቲሸርት\n"
        text += f"👤 {username or user_id}\n"
        text += f"📏 {size_names.get(size, size)} x {qty} = {price} ብር\n"
        text += f"📅 {ts[:16]}\n"
        text += "━━━━━━━━━━━━━━━━━━━━━\n"
        text += f"📸 /viewscreenshot {message.from_user.id}\n"
        text += f"✅ /confirm_tshirt {user_id}\n"
        text += f"❌ /reject_tshirt {user_id}\n\n"
    
    for item in lottery_pending:
        user_id, username, qty, price, ts = item
        text += "━━━━━━━━━━━━━━━━━━━━━\n"
        text += f"🎫 ሎተሪ\n"
        text += f"👤 {username or user_id}\n"
        text += f"🎫 {qty} ቲኬቶች = {price} ብር\n"
        text += f"📅 {ts[:16]}\n"
        text += "━━━━━━━━━━━━━━━━━━━━━\n"
        text += f"📸 /viewscreenshot {message.from_user.id}\n"
        text += f"✅ /confirm_lottery {user_id}\n"
        text += f"❌ /reject_lottery {user_id}\n\n"
    
    # Send without parse_mode to avoid Markdown errors
    bot.send_message(message.chat.id, text, reply_markup=admin_menu())

@bot.message_handler(func=lambda message: message.text == "💬 የአስተያየቶች" and is_admin(message.from_user.id))
def admin_comments(message):
    conn = sqlite3.connect('gubi_event.db')
    cursor = conn.cursor()
    cursor.execute('''SELECT u.first_name, u.last_name, u.username, c.comment, c.timestamp
                     FROM comments c JOIN users u ON c.user_id = u.user_id ORDER BY c.timestamp DESC LIMIT 15''')
    data = cursor.fetchall()
    conn.close()
    if not data:
        bot.send_message(message.chat.id, "ምንም አስተያየት የለም", reply_markup=admin_menu())
        return
    text = "💬 **የአስተያየቶች** 💬\n\n"
    for first, last, username, comment, ts in data:
        name = f"{first or ''} {last or ''}".strip() or username or "ያልታወቀ"
        text += f"**{name}** ({ts[:10]}):\n{comment[:150]}\n\n"
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=admin_menu())

@bot.message_handler(func=lambda message: message.text == "📤 ውሂብ አስወጣ" and is_admin(message.from_user.id))
def export_data(message):
    import csv
    conn = sqlite3.connect('gubi_event.db')
    cursor = conn.cursor()
    tables = ['users', 'rsvp', 'tshirt_orders', 'lottery_purchases', 'comments']
    for table in tables:
        cursor.execute(f"SELECT * FROM {table}")
        data = cursor.fetchall()
        if data:
            filename = f"{table}_export.csv"
            with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow([desc[0] for desc in cursor.description])
                writer.writerows(data)
            with open(filename, 'rb') as f:
                bot.send_document(message.chat.id, f)
            os.remove(filename)
    conn.close()
    bot.send_message(message.chat.id, "✅ ሁሉም ውሂቦች ተልከዋል!", reply_markup=admin_menu())

# ==================== UNKNOWN MESSAGES ====================
@bot.message_handler(func=lambda message: True)
def handle_unknown(message):
    bot.send_message(message.chat.id, "❌ ይቅርታ፣ ይህን አልገባኝም።\n\nእባክዎ ከታች ያሉትን ቁልፎች ይጠቀሙ 👇", reply_markup=user_menu())

# ==================== START BOT ====================
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🤖 የጉቢ ጉባኤ አስተዳደር ቦት")
    print("="*60)
    print("✅ የውሂብ ጎታ: gubi_event.db")
    print("✅ የአድሚን መታወቂያዎች:", ADMIN_IDS)
    print("✅ ቦቱ እየሰራ ነው...")
    print("="*60)
    print("ለማቆም Ctrl+C ይጫኑ")
    print("="*60 + "\n")
    
    try:
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except KeyboardInterrupt:
        print("\n❌ ቦቱ ተቋርጧል")
    except Exception as e:
        print(f"\n❌ ስህተት: {e}")
        logger.error(f"Bot error: {e}")