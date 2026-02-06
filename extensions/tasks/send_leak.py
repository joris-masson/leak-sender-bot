from interactions import Task, IntervalTrigger, Extension, Embed, EmbedFooter, listen

from utils import open_db_connection


class Leak(Extension):
    @listen()
    async def on_startup(self):
        self.send_new_leaks.start()

        self.GAMES = [
            "GI",
            "HSR",
            "ZZZ"
        ]

    @Task.create(IntervalTrigger(minutes=15))
    async def send_new_leaks(self):
        new_leaks = self.get_new_leaks()
        channels = self.get_channels()

        db = open_db_connection()
        cursor = db.cursor()

        print("Nouveaux leaks: ", new_leaks)
        print("Salons: ", channels)

        for game in self.GAMES:
            for leak in new_leaks[game]:
                footer = EmbedFooter(f"/u/{leak["author"]}")

                embed = Embed(
                    title=leak["title"],
                    url=leak["link"],
                    footer=footer
                )

                embed.set_image(url=leak["media_link"])

                for channel in channels[game]:
                    print(f"[{game}] - leak {leak['id']} envoyé dans {channel.id}.")
                    await channel.send(embeds=embed)
                    query = f"UPDATE Kazooha.Leak SET sent=1 WHERE id='{leak['id']}'"
                    cursor.execute(query)
        db.commit()
        cursor.close()
        db.close()

    def get_new_leaks(self) -> dict:
        db = open_db_connection()
        cursor = db.cursor()

        res = {}

        for game in self.GAMES:
            query = f"SELECT DISTINCT * FROM Kazooha.Leak WHERE sent=0 AND game='{game}'"
            cursor.execute(query)

            leaks = []
            for leak in cursor.fetchall():
                leaks.append(
                    {
                        "id": leak[0],
                        "title": leak[3],
                        "link": leak[4],
                        "author": leak[5],
                        "media_link": leak[6]
                    }
                )
            res[game] = leaks

        cursor.close()
        db.close()

        return res

    def get_channels(self) -> dict:
        db = open_db_connection()
        cursor = db.cursor()

        bot_guilds = {str(guild.id) for guild in self.bot.guilds}

        res = {}

        for game in self.GAMES:
            query = f"SELECT DISTINCT * FROM Kazooha.LeakChannel WHERE game='{game}'"
            cursor.execute(query)

            channels = []
            for channel in cursor.fetchall():
                channel_id = channel[2]
                channel_guild_id = channel[1]
                if channel_guild_id in bot_guilds:
                    channels.append(self.bot.get_channel(channel_id))
            res[game] = channels
        return res
