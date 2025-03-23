import telegram
from telegram.ext import Updater, MessageHandler, Filters
import re
import json
import openai

# Thay bằng API token của bot bạn
TOKEN = '7961502574:AAFXpziT1AOgjEOc3S1rfK_ou0r5tnUu2qs'

# Thay bằng API key của OpenAI
openai.api_key = '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'

# Danh sách người gửi đã biết
known_senders = {}

# Hàm lưu giao dịch vào file JSON
def save_transaction(sender, amount, time):
    with open('transactions.json', 'a', encoding='utf-8') as f:
        json.dump({'sender': sender, 'amount': amount, 'time': time}, f)
        f.write('\n')

# Hàm xử lý tin nhắn từ IFTTT
def handle_message(update, context):
    message = update.message.text
    # Trích xuất thông tin từ thông báo
    # Định dạng: NotificationMessage: TK 03xxx366]GD: -40,000VND 23/03/25 23:05 ]SD: 2,306,602VND]ND: HOANG KIM TRI THANH chuyen tien
    match = re.search(r'NotificationMessage:.*GD: ([+-]?\d+,\d+VND) (\d{2}/\d{2}/\d{2} \d{2}:\d{2}).*ND: (.+?) (?:chuyen tien|nhan tien)', message)
    if match:
        amount = match.group(1)  # Số tiền (ví dụ: -40,000VND hoặc +40,000VND)
        time = match.group(2)    # Thời gian (ví dụ: 23/03/25 23:05)
        sender = match.group(3)  # Người gửi (ví dụ: HOANG KIM TRI THANH)

        # Chỉ xử lý giao dịch nhận tiền (số tiền dương)
        if '+' in amount:
            amount = amount.replace('+', '')  # Bỏ dấu + để lưu số tiền
            if sender in known_senders:
                # Ghi nhận nếu là thành viên đã biết
                save_transaction(sender, amount, time)
                context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=f"Đã ghi nhận {amount} từ {sender} vào {time}.")
            else:
                # Hỏi xác nhận nếu người gửi mới
                context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=f"Giao dịch mới: {amount} từ {sender}. Đây có phải thành viên đội bóng không? Trả lời 'có' hoặc 'không'.")
                context.user_data['pending'] = {'sender': sender, 'amount': amount, 'time': time}

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

# Hàm gửi câu hỏi đến LLM
def ask_llm(question):
    transactions = []
    try:
        with open('transactions.json', 'r', encoding='utf-8') as f:
            for line in f:
                transactions.append(json.loads(line.strip()))
    except FileNotFoundError:
        transactions = []

    prompt = f"Dựa trên dữ liệu giao dịch sau: {transactions}\nTrả lời câu hỏi: {question}"
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=150
    )
    return response.choices[0].text.strip()

# Hàm xử lý câu hỏi từ bạn
def handle_question(update, context):
    question = update.message.text
    answer = ask_llm(question)
    context.bot.send_message(chat_id=update.effective_chat.id, text=answer)

# Khởi động bot
updater = Updater(TOKEN, use_context=True)
dp = updater.dispatcher

# Xử lý tin nhắn từ IFTTT (nhóm MB Bank Notifications)
dp.add_handler(MessageHandler(Filters.text & Filters.chat(chat_id=-4687082642), handle_message))

# Xử lý phản hồi từ bạn
dp.add_handler(MessageHandler(Filters.text & Filters.user(username='@HoangThanh'), handle_response))

# Xử lý câu hỏi từ bạn
dp.add_handler(MessageHandler(Filters.text & Filters.user(username='@HoangThanh'), handle_question))

updater.start_polling()
updater.idle()