import os
import interactions

from dotenv import load_dotenv


load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = interactions.Client()

bot.load_extension("extensions.tasks.send_leak")

@interactions.listen()
async def on_startup():
    print("Bot is ready!")


bot.start(BOT_TOKEN)
