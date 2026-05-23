import jubbio

APP_ID = "APPLICATION_ID_BURAYA"
BOT_TOKEN = "BOT_TOKEN_BURAYA"

client = jubbio.Client(application_id=APP_ID)

@client.event
async def on_ready():
    print(f"✅ {client.user} hazır!")

    await client.register_command(
        jubbio.SlashCommand(
            name="ping",
            description="Bot gecikmesini gösterir",
        )
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
        )
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
        )
    )

    await client.register_command(
        jubbio.SlashCommand(
            name="kullanici-bilgi",
            description="Kullanıcı hakkında detaylı bilgi verir",
            options=[
                jubbio.SlashCommandOption(
                    name="kullanici",
                    description="Bilgisi gösterilecek kullanıcı",
                    type=jubbio.CommandOptionType.USER,
                    required=True,
                )
            ],
        )
    )

    print("📝 Komutlar kaydedildi!")

@client.command(name="ping")
async def ping(interaction):
    embed = jubbio.Embed(
        title="🏓 Pong!",
        description="Bot başarıyla yanıt verdi.",
        color=0x2ECC71
    )
    embed.add_field(name="Durum", value="✅ Çevrimiçi", inline=True)
    embed.add_field(name="Protokol", value="WebSocket", inline=True)
    embed.set_footer(text="jubbio.py")
    await interaction.respond(embed=embed)

@client.command(name="avatar")
async def avatar(interaction):
    user_id = interaction.get_option("kullanici")
    if user_id:
        user = await client.get_user(user_id)
    else:
        user = interaction.user

    embed = jubbio.Embed(
        title=f"🖼️ {user.display_name}",
        description="Kullanıcının profil fotoğrafı",
        color=0x9B59B6
    )
    if user.avatar_url:
        embed.set_image(url=user.avatar_url)
    else:
        embed.description = "Bu kullanıcının avatarı bulunmuyor."
    embed.set_footer(text="jubbio.py")
    await interaction.respond(embed=embed)

@client.command(name="duyuru")
async def duyuru(interaction):
    baslik = interaction.get_option("baslik")
    mesaj = interaction.get_option("mesaj")

    embed = jubbio.Embed(
        title=f"📢 {baslik}",
        description=mesaj,
        color=0xE74C3C
    )
    embed.add_field(name="Duyuran", value=interaction.user.display_name, inline=True)
    embed.set_footer(text="Duyuru Sistemi")
    await interaction.respond(embed=embed)

@client.command(name="kullanici-bilgi")
async def kullanici_bilgi(interaction):
    user_id = interaction.get_option("kullanici")
    user = await client.get_user(user_id)

    embed = jubbio.Embed(
        title=f"👤 {user.display_name}",
        description="Kullanıcı detayları aşağıda listelenmiştir.",
        color=0x3498DB
    )
    embed.add_field(name="ID", value=str(user.id), inline=True)
    embed.add_field(name="Kullanıcı Adı", value=user.username, inline=True)
    if user.avatar_url:
        embed.set_image(url=user.avatar_url)
    embed.set_footer(text="jubbio.py")
    await interaction.respond(embed=embed)

client.run(BOT_TOKEN)
