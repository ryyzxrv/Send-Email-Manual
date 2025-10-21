import telebot
import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ===== KONFIGURASI =====
TELEGRAM_TOKEN = "TOKEN_LU"
EMAIL_SENDER = "EMAIL_LU"
EMAIL_PASSWORD = "APP_PW_EMAIL_LU"  # App Password Gmail

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Simpan email pending (tujuan: subject)
pending_emails = {}

# ======= KIRIM EMAIL =======
@bot.message_handler(commands=['email'])
def send_email(message):
    try:
        parts = message.text.replace("/email ", "", 1).split(" | ", maxsplit=2)
        if len(parts) < 3:
            bot.reply_to(message, "鈿狅笍 Format salah!\n/email tujuan@domain.com | Subjek | Isi pesan")
            return

        to_addr, subject, body = parts[0].strip(), parts[1].strip(), parts[2].strip()

        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = to_addr
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)

        # simpan ke pending list
        pending_emails[to_addr] = subject

        bot.reply_to(message, f"鉁� Email berhasil dikirim ke {to_addr}\nGunakan /status untuk cek balasan.")

    except Exception as e:
        bot.reply_to(message, f"鉂� Gagal kirim email:\n{e}")


# ======= CEK BALASAN =======
@bot.message_handler(commands=['status'])
def check_status(message):
    try:
        if not pending_emails:
            bot.reply_to(message, "馃摥 Tidak ada email yang menunggu balasan.")
            return

        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(EMAIL_SENDER, EMAIL_PASSWORD)
        mail.select("inbox")

        result, data = mail.search(None, "ALL")
        mail_ids = data[0].split()

        found_reply = False

        for to_addr, subject in list(pending_emails.items()):
            for i in reversed(mail_ids[-20:]):  # cek 20 email terakhir
                res, msg_data = mail.fetch(i, "(RFC822)")
                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)

                from_addr = msg["From"]
                subject_reply = msg["Subject"] or ""

                # cek kalau subjek sama / ada "Re:" + tujuan sama
                if subject in subject_reply:
                    # ambil body
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                body = part.get_payload(decode=True).decode(errors="ignore")
                                break
                    else:
                        body = msg.get_payload(decode=True).decode(errors="ignore")

                    bot.reply_to(
                        message,
                        f"馃摡 Balasan diterima!\n\nDari: {from_addr}\nSubjek: {subject_reply}\n\n{body[:500]}..."
                    )
                    found_reply = True
                    del pending_emails[to_addr]
                    break

            if not found_reply:
                bot.reply_to(message, f"鈴� Email ke {to_addr} dengan subjek '{subject}' belum dibalas.")

        mail.logout()

    except Exception as e:
        bot.reply_to(message, f"鉂� Gagal cek balasan:\n{e}")


@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message,
        "馃憢 Halo! Gunakan:\n"
        "/email tujuan@domain.com | Subjek | Isi pesan\n"
        "/status 鈫� cek apakah email sudah dibalas"
    )

print("馃殌 Bot berjalan...")
bot.polling(none_stop=True)
