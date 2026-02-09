from interactions import Task, IntervalTrigger, Extension, listen, GuildText

from leak import Leak
from utils import open_db_connection


class SendLeak(Extension):
    @listen()
    async def on_startup(self):
        self.send_new_leaks.start()

        self.GAMES = [
            "GI",
            "HSR",
            "ZZZ"
        ]

        self.BOT_GUILDS = {str(guild.id) for guild in self.bot.guilds}

    @Task.create(IntervalTrigger(minutes=15))
    async def send_new_leaks(self):
        new_leaks = self.get_new_leaks()

        for channel_id in new_leaks:
            channel = self.bot.get_channel(channel_id)
            for guild_id, leak in new_leaks[channel_id]:
                if guild_id in self.BOT_GUILDS:
                    await self.send_leak(leak, channel)


    def get_new_leaks(self) -> dict[tuple[str, set[Leak]]]:
        db = open_db_connection()
        cursor = db.cursor()

        res = {}

        query = f"""SELECT
                        leak.*,
                        leak_channel.guild_id,
                        leak_channel.channel_id
                    FROM Kazooha.Leak leak
                    JOIN Kazooha.LeakChannel leak_channel
                        ON leak.game = leak_channel.game
                    LEFT JOIN Kazooha.LeakMessage leak_message
                        ON leak.id = leak_message.leak_id
                        AND leak_channel.guild_id = leak_message.guild_id
                        AND leak_channel.channel_id = leak_message.channel_id
                    WHERE leak_message.message_id IS NULL
                """

        cursor.execute(query)

        for data in cursor.fetchall():
            guild_id = data[7]
            channel_id = data[8]
            if channel_id not in res.keys():
                res[channel_id] = set()

            leak = Leak(
                data[0],
                data[1],
                data[2],
                data[3],
                data[4],
                data[5],
                data[6]
            )

            res[channel_id].add((guild_id, leak))

        cursor.close()
        db.close()

        return res

    async def send_leak(self, leak: Leak, channel: GuildText):
        leak_embed = leak.get_embed()

        db = open_db_connection()
        cursor = db.cursor()

        query = "INSERT INTO Kazooha.LeakMessage (leak_id, guild_id, channel_id, message_id) VALUES (%s, %s, %s, %s)"
        message = await channel.send(embeds=leak_embed)
        cursor.execute(query, (
            leak.leak_id,
            str(channel.guild.id),
            str(channel.id),
            str(message.id)
        ))
        db.commit()

        cursor.close()
        db.close()
