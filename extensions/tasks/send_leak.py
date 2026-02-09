from interactions import Task, IntervalTrigger, Extension, listen, GuildText, Button, ButtonStyle, GuildPublicThread
from interactions.api.events import Component

from leak import Leak
from utils import open_db_connection


class SendLeak(Extension):
    @listen()
    async def on_startup(self):
        self.send_new_leaks.start()

        self.BOT_GUILDS = {str(guild.id) for guild in self.bot.guilds}

        await self.send_new_leaks()

    @listen(Component)
    async def on_component(self, event: Component):
        ctx = event.ctx

        leak_id = ctx.custom_id.replace("button_spoil_", '')
        leak = self.get_leak(leak_id)
        message_id = self.get_leak_message_id(leak_id, str(ctx.guild.id), str(ctx.channel.id))

        original_leak_message = self.bot.get_channel(ctx.channel.id).get_message(message_id)

        threads = await ctx.channel.fetch_all_threads()
        for thread in threads.threads:
            if thread.name == "Spoil":
                await original_leak_message.delete()
                await self.send_leak(leak, thread, False)
                return
        thread = await ctx.channel.create_public_thread("Spoil")
        await original_leak_message.delete()
        await self.send_leak(leak, thread, False)

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

    def get_leak(self, leak_id: str) -> Leak:
        db = open_db_connection()
        cursor = db.cursor()

        query = f"SELECT id, timestamp, game, title, link, author_name, media_link FROM Kazooha.Leak WHERE id='{leak_id}'"
        cursor.execute(query)

        leak = cursor.fetchone()

        cursor.close()
        db.close()

        return Leak(
            leak[0],
            leak[1],
            leak[2],
            leak[3],
            leak[4],
            leak[5],
            leak[6]
        )

    def get_leak_message_id(self, leak_id: str, guild_id: str, channel_id: str) -> str:
        db = open_db_connection()
        cursor = db.cursor()

        query = f"SELECT message_id FROM Kazooha.LeakMessage WHERE leak_id=%s AND guild_id=%s AND channel_id=%s"
        cursor.execute(query, (
            leak_id,
            guild_id,
            channel_id
        ))

        message_id = cursor.fetchone()

        cursor.close()
        db.close()

        return message_id[0]

    async def send_leak(self, leak: Leak, channel: GuildText | GuildPublicThread, show_spoil_button: bool = True):
        leak_embed = leak.get_embed()

        db = open_db_connection()
        cursor = db.cursor()

        query = "INSERT INTO Kazooha.LeakMessage (leak_id, guild_id, channel_id, message_id) VALUES (%s, %s, %s, %s)"

        if show_spoil_button:
            spoil_button = Button(
                custom_id=f"button_spoil_{leak.leak_id}",
                style=ButtonStyle.GRAY,
                label="Spoil !",
            )

            message = await channel.send(embeds=leak_embed, components=spoil_button)
        else:
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
