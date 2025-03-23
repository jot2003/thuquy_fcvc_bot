import telegram
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler
import re
import json

# Thay bằng API token của bot bạn
TOKEN = '7961502574:AAFXpziT1AOgjEOc3S1rfK_ou0r5tnUu2qs'

# Danh sách người gửi đã biết
known_senders = {}

# Hàm lưu giao dịch vào file JSON
def save_transaction(sender, amount, time):
    print(f"Saving transaction: {sender}, {amount}, {time}")
    with open('transactions.json', 'a', encoding='utf-8') as f:
        json.dump({'sender': sender, 'amount': amount, 'time': time}, f)
        f.write('\n')

# Hàm xử lý tin nhắn từ IFTTT
def handle_message(update, context):
    print("Received a message!")
    message = update.message.text
    print(f"Message content: {message}")
    match = re.search(r'NotificationMessage:.*GD: ([+-]?\d+,\d+VND) (\d{2}/\d{2}/\d{2} \d{2}:\d{2}).*ND: (.+?) (?:chuyen tien|nhan tien)', message)
    if match:
        print("Message matched the pattern!")
        amount = match.group(1)
        time = match.group(2)
        sender = match.group(3)
        print(f"Extracted: amount={amount}, time={time}, sender={sender}")

        if '+' in amount:
            amount = amount.replace('+', '')
            if sender in known_senders:
                save_transaction(sender, amount, time)
                context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=f"Đã ghi nhận {amount} từ {sender} vào {time}.")
            else:
                context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=f"Giao dịch mới: {amount} từ {sender}. Đây có phải thành viên đội bóng không? Trả lời 'có' hoặc 'không'.")
                context.user_data['pending'] = {'sender': sender, 'amount': amount, 'time': time}
    else:
        print("Message did not match the pattern.")

# Hàm xử lý phản hồi từ bạn
def handle_response(update, context):
    response = update.message.text.lower()
    if 'pending' in context.user_data:
        pending = context.user_data['pending']
        if response == 'có':
            known_senders[pending['sender']] = True
            save_transaction(pending['sender'], pending['amount'], pending['time'])
            context.bot.send_message(chat_id=update.effective_chat.id,
                                   text=f"Đã ghi nhận {pending['sender']} là thành viên đội bóng.")
        elif response == 'không':
            known_senders[pending['sender']] = False
            context.bot.send_message(chat_id=update.effective_chat.id,
                                   text=f"Đã ghi nhận {pending['sender']} không phải thành viên đội bóng.")
        del context.user_data['pending']

# Hàm gửi nội dung file transactions.json
def get_transactions(update, context):
    try:
        with open('transactions.json', 'r', encoding='utf-8') as f:
            transactions = f.readlines()
        if transactions:
            context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="Danh sách giao dịch:\n" + "\n".join(transactions))
        else:
            context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="Chưa có giao dịch nào.")
    except FileNotFoundError:
        context.bot.send_message(chat_id=update.effective_chat.id,
                               text="Chưa có giao dịch nào.")

# Khởi động bot
print("Starting bot...")
updater = Updater(TOKEN, use_context=True)
dp = updater.dispatcher

# Xử lý tin nhắn từ IFTTT (nhóm MB Bank Notifications)
dp.add_handler(MessageHandler(Filters.text & Filters.chat(chat_id=-4687082642), handle_message))

# Xử lý phản hồi từ bạn
dp.add_handler(MessageHandler(Filters.text & Filters.user(username='@HoangThanh'), handle_response))

# Lệnh để xem giao dịch
dp.add_handler(CommandHandler("get_transactions", get_transactions))

updater.start_polling()
updater.idle()