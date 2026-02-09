from interactions import EmbedFooter, Embed


class Leak:
    def __init__(self, leak_id: str, timestamp: str, game: str, title: str, link: str, author_name: str, media_link: str):
        self.leak_id = leak_id
        self.timestamp = timestamp
        self.game = game
        self.title = title
        self.link = link
        self.author_name = author_name
        self.media_link = media_link

    def get_embed(self) -> Embed:
        footer = EmbedFooter(f"/u/{self.author_name}")

        embed = Embed(
            title=self.title,
            url=self.link,
            footer=footer
        )

        embed.set_image(url=self.media_link)

        return embed

    def __str__(self):
        return f"{self.title}({self.leak_id})"
