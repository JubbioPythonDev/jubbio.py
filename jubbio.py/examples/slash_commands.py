"""
Slash Komut Botu Örneği
~~~~~~~~~~~~~~~~~~~~~~~
Slash komut kayıt ve kullanım örneği.
"""
import jubbio

client = jubbio.Client()


@client.event
async def on_ready():
    print(f"✅ {client.user} hazır!")

    # Slash komutları kaydet (guild_id ile anlık aktif olur)
    GUILD_ID = "SUNUCU_ID_BURAYA"

    await client.register_command(
        jubbio.SlashCommand(
            name="ping",
            description="Bot gecikmesini gösterir",
        ),
        guild_id=GUILD_ID,
    )

    await client.register_command(
        jubbio.SlashCommand(
            name="avatar",
            description="Kullanıcının avatarını gösterir",
            options=[
                jubbio.SlashCommandOption(
                    name="kullanici",
                    description="Avatarı gösterilecek kullanıcı",
                    type=jubbio.CommandOptionType.USER,
                    required=False,
                )
            ],
        ),
        guild_id=GUILD_ID,
    )

    await client.register_command(
        jubbio.SlashCommand(
            name="duyuru",
            description="Kanala duyuru gönderir",
            options=[
                jubbio.SlashCommandOption(
                    name="baslik",
                    description="Duyuru başlığı",
                    type=jubbio.CommandOptionType.STRING,
                    required=True,
                ),
                jubbio.SlashCommandOption(
                    name="mesaj",
                    description="Duyuru içeriği",
                    type=jubbio.CommandOptionType.STRING,
                    required=True,
                ),
            ],
        ),
        guild_id=GUILD_ID,
    )

    print("📝 Komutlar kaydedildi!")


@client.command(name="ping")
async def ping(interaction):
    await interaction.respond("🏓 Pong!")


@client.command(name="avatar")
async def avatar(interaction):
    user_id = interaction.get_option("kullanici")
    if user_id:
        user = await client.get_user(user_id)
    else:
        user = interaction.user

    embed = jubbio.Embed(
        title=f"🖼️ {user.display_name} - Avatar",
        color=jubbio.Color.purple(),
    )
    if user.avatar_url:
        embed.set_image(url=user.avatar_url)
    else:
        embed.description = "Bu kullanıcının avatarı yok."

    await interaction.respond(embed=embed)


@client.command(name="duyuru")
async def duyuru(interaction):
    baslik = interaction.get_option("baslik")
    mesaj = interaction.get_option("mesaj")

    embed = jubbio.Embed(
        title=f"📢 {baslik}",
        description=mesaj,
        color=jubbio.Color.gold(),
    )
    embed.set_footer(text=f"Duyuran: {interaction.user.display_name}")

    # Kanala gönder (herkese görünür)
    channel = interaction.member and interaction.channel_id
    await interaction.respond(embed=embed)


client.run("BOT_TOKEN_BURAYA")
