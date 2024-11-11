from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (ApplicationBuilder, CommandHandler,
                          CallbackQueryHandler, ConversationHandler,
                          ContextTypes, MessageHandler, filters)
from datetime import datetime, timedelta
from flask import Flask
from threading import Thread

# Your Telegram bot token
TOKEN = '7615852859:AAHCSQBrE5doTj3jVFlavHpcT4fJG8ma2R8'

# Define stages of the conversation
SELECT_BATTLEFRONT, SELECT_BOSS, SELECT_AREA, SET_TIMER = range(4)

# Data for battlefronts, bosses, and areas
battlefronts = ["BattleFront 1", "World BF"]
bosses_battlefront1 = [
    "Forgotten Anggolt", "Forgotten Kiaron", "Forgotten Grish",
    "Forgotten Inferno"
]
bosses_worldbf = [
    "Forgotten Liantte", "Forgotten Seyron", "Forgotten Gottmol",
    "Forgotten Gehenna"
]
areas = {
    "Forgotten Anggolt": [
        "Rally Point of Belligerence", "Rally Point of Unity",
        "Rally Point of Victory", "Training Grounds of Belligerence",
        "Training Grounds of Unity", "Training Grounds of Victory",
        "Conquest of Belligerence", "Conquest of Unity", "Conquest of Victory"
    ],
    "Forgotten Kiaron": [
        "Marching Point of Belligerence", "Marching Point of Unity",
        "Marching Point of Victory", "Assault Point of Belligerence",
        "Assault Point of Unity", "Assault Point of Victory"
    ],
    "Forgotten Grish": [
        "Conflict Point of Belligerence", "Conflict Point of Unity",
        "Conflict Point of Victory", "Confrontation Point of Belligerence",
        "Confrontation Point of Unity", "Confrontation Point of Victory"
    ],
    "Forgotten Inferno": [
        "Source of Heavy Combat", "Rocky Mountain Cliff",
        "Cloud Path Watchtower", "Stonegrave Summit", "Newbreeze Order",
        "High Grounds Summit", "Horizon Peaks"
    ],
    "Forgotten Liantte": ["Shaded Gateway"],
    "Forgotten Seyron":
    ["Diminished Wilderness", "Ruined Wilderness", "Abandoned Wilderness"],
    "Forgotten Gottmol": ["Forlon Field", "Weathered Field", "Faded Field"],
    "Forgotten Gehenna": [
        "Forlon Rocky Mountain", "Weathered Rocky Mountain",
        "Faded Rocky Mountain"
    ]
}


# Store user data
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [[InlineKeyboardButton(bf, callback_data=str(idx))]
                for idx, bf in enumerate(battlefronts)]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Select a battlefront:",
                                    reply_markup=reply_markup)
    return SELECT_BATTLEFRONT


async def select_battlefront(update: Update,
                             context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    choice = int(query.data)
    context.user_data['battlefront'] = battlefronts[choice]

    # Using a simplified approach to build keyboard
    bosses = bosses_battlefront1 if context.user_data[
        'battlefront'] == "BattleFront 1" else bosses_worldbf
    keyboard = [[InlineKeyboardButton(boss, callback_data=str(idx))]
                for idx, boss in enumerate(bosses)]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text="Select a boss:",
                                  reply_markup=reply_markup)
    return SELECT_BOSS


async def select_boss(update: Update,
                      context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    choice = int(query.data)
    if context.user_data['battlefront'] == "BattleFront 1":
        context.user_data['boss'] = bosses_battlefront1[choice]
    else:
        context.user_data['boss'] = bosses_worldbf[choice]

    keyboard = [[InlineKeyboardButton(area, callback_data=str(idx))]
                for idx, area in enumerate(areas[context.user_data['boss']])]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text="Select an area:",
                                  reply_markup=reply_markup)
    return SELECT_AREA


async def select_area(update: Update,
                      context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    choice = int(query.data)
    context.user_data['area'] = areas[context.user_data['boss']][choice]

    await query.edit_message_text(
        text=
        "Please send the time of death in the format HH:MM AM/PM (e.g., 4:30 PM):"
    )
    return SET_TIMER


async def set_timer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    time_of_death_str = update.message.text
    try:
        time_of_death = datetime.strptime(time_of_death_str, '%I:%M %p')
        spawn_hours = {
            "Forgotten Anggolt": 5,
            "Forgotten Kiaron": 6,
            "Forgotten Grish": 6,
            "Forgotten Inferno": 8,
            "Forgotten Liantte": 5,
            "Forgotten Seyron": 6,
            "Forgotten Gottmol": 6,
            "Forgotten Gehenna": 8,
        }.get(context.user_data['boss'], 0)

        spawning_time = time_of_death + timedelta(hours=spawn_hours)
        delay_time = spawning_time + timedelta(hours=2)

        # Assign color emojis based on battlefront and boss
        battlefront_color = "🔵" if context.user_data[
            "battlefront"] == "BattleFront 1" else "🟡"
        boss_color = "🔵" if context.user_data[
            "battlefront"] == "BattleFront 1" else "🟡"
        time_of_spawn_color = "🔴"

        await update.message.reply_text(
            f'{battlefront_color} {context.user_data["battlefront"]}\n'
            f'Boss: {boss_color} {context.user_data["boss"]}\n'
            f'Area: {context.user_data["area"]}\n'
            f'Time of Death: {time_of_death.strftime("%I:%M %p")}\n'
            f'{time_of_spawn_color} Time of Spawn: {spawning_time.strftime("%I:%M %p")}\n'
            f'Delay Time: {delay_time.strftime("%I:%M %p")}')
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text(
            'Invalid time format. Please use HH:MM AM/PM (e.g., 4:30 PM):')
        return SET_TIMER


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text('Operation canceled.')
    return ConversationHandler.END


# Create the Flask app
app = Flask(__name__)


# Define a simple route to keep Replit's server alive
@app.route('/')
def index():
    return "Your bot is running!"


# Function to run Flask app in a separate thread
def run_flask():
    app.run(host="0.0.0.0", port=8080)


# Start the Flask server in a separate thread
def keep_alive():
    thread = Thread(target=run_flask)
    thread.start()


def main() -> None:
    application = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SELECT_BATTLEFRONT: [CallbackQueryHandler(select_battlefront)],
            SELECT_BOSS: [CallbackQueryHandler(select_boss)],
            SELECT_AREA: [CallbackQueryHandler(select_area)],
            SET_TIMER:
            [MessageHandler(filters.TEXT & ~filters.COMMAND, set_timer)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        per_message=False)

    application.add_handler(conv_handler)

    keep_alive()  # Call the keep_alive function to start the Flask server
    application.run_polling()


if __name__ == '__main__':
    main()
