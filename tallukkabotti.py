from typing import Final

# pip install python-telegram-bot
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import random
from datetime import datetime, time

TOKEN: Final = "6847538676:AAHs6fqbhVv4rr0MKgke4IQPhdFT_hPMwUY"
username: Final = "@tallukkabot"

# Käytetään jos tietyllä aikavälillä /issleep komennossa
def in_between(now, start, end):
    if start <= end:
        return start <= now < end
    else:
        return start <= now or now < end

# komennot
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Moi mun nimi on Eetu!")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Vihtu kirjoita jotai nii voin vastata.")

papanviinat_responses = [
    "Juuh nyt ois sitä vitun PAPAN VIINAA tarjol !!! :D",
    "Papan viinaa? Sehän on aina hyvää!",
    "Papan viina, paras tapa rentoutua!",
    # saa lisätä vapasti :D
]
async def papanviinat_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response = random.choice(papanviinat_responses)
    await update.message.reply_text(response)

async def issleep_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response = random.choice(issleep_responses)
    await update.message.reply_text("Öööö E mä nuku nyh" if in_between(datetime.now().time(), time(21), time(6)) else response)

issleep_responses = [
    "Juuh käy sellane et tääl mun luon all in bileet",
    "Juh on hereil tääl näih",
    "Aa juuh oon jus menos sin Kilttiksel",
    ]

# VASTAUKSIA
# --------------------------------------------------------------------------------------------------------    

def handle_response(text: str) -> str:
    
    processed: str = text.lower()

    greetings = ["moi", "Moi", "hei", "Hei", "moro", "Moro"]
    if any(word in text for word in greetings):
        return "No moi!"

    kalja_responses =[
        "ääääääääääh no viihtu kai pitää sit ryypätä",
        'okei hyvä juon lisää kaljaa'
    ]

    if "kalja" in text:
        return random.choice(kalja_responses)
    
    nih_responses = [
    "ÖÖÖÖÖ no emmää tiä riippuu vähä kontekstist :D",
    f"Öööö kello tulee koht {datetime.now().strftime('%H:%M')} et oisko teijä aika lähtee koht? :D", 
    "Juuuuh :D"
    # Saa lisäillä lisää Eetun heittoja :D
    ]

    if "NIH" in text:
        return random.choice(nih_responses)
    
    homo_responses = [
        'isäs on :D',
        'no juuh :D',
        'suusex 8=======D',
        'Eih'
    ]

    if "homo" in text or 'Homo' in text:
        return random.choice(homo_responses)
    
    kayko_responses = [
    'Juuh sellane käy', 
    'öööööööö EI', 
    'öööööööööööööö juuuh tän voi tul', 
    'vittu sä oot autisti :D',
    'JUH käyks vaik et painut vittuu :D'
    ]

    if 'käykö' in text or 'Käykö' in text or 'Käyks' in text or 'käyks' in text:
        return random.choice(kayko_responses)
    
    tuplis_responses = [
        'Ketää tupliksel tänää?? Vetää AIIIVAN ylilaidallinen :DDD litra long iland ice teatä naamaan ja merilyniin tanssimaan :DDD flip cuppia autokannella :DDD iskelmäbaarii laulaa aikuista naista :DDDD PURKILLINE verovapaata denssii huuleen :DDD syömäkisa buffassa :DDD kolme pulloo vergiä boksereihi :DDD jouluristeilyl jatkoille :DDD huomenna päivällä klo 12 sammuu pallomereen :DD ketä imus????',
        'ööö no periaattees vois',
        'ööööööööö EI vitus 🤮🤮🤮'
    ]

    if 'tuplis' in text or 'Tuplis' in text or 'tupliksel' in text or 'Tupliksel' in text:
        return random.choice(tuplis_responses)
    
    kullin_pituus_responses = [
        f"{random.randint(1, 30)} cm",
        f"{random.randint(1, 12)} tuumaa",
    ]

    if "kullin pituus" in processed or "kullin koko" in processed:
        random_length = random.choice(kullin_pituus_responses)
        length_value = int(random_length.split()[0])

        if (length_value < 10 and 'tuumaa' not in random_length) or ('tuumaa' in random_length and length_value < 3):
            return f"se o {random_length}\nhäähääää vitun millimuna :D"
        else:
            return f"se o {random_length}"
    
    return "mee ny vittuu siit"

# -------------------------------------------------------------------------------------------------------

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type: str = update.message.chat.type
    text: str = update.message.text

    print(f'User ({update.message.chat.id}) in {message_type}: "{text}"')

    if message_type == 'group':
        if username in text:
            new_text: str = text.replace(username, '').strip()
            response: str = handle_response(new_text)
        else:
            return
    else:
        response: str = handle_response(text)
    
    print('Bot', response)
    await update.message.reply_text(response)

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error {context.error}')

if __name__ == '__main__':
    print('Starting bot...')
    app = Application.builder().token(TOKEN).build()

    # Commands
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('papanviinat', papanviinat_command))
    app.add_handler(CommandHandler('issleep', issleep_command))

    # Messages
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    # errors
    app.add_error_handler(error)

    # polls the bot
    print('Polling...')
    app.run_polling(poll_interval=1)