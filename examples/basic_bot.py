import jubbio

APP_ID = "APPLICATION_ID_BURAYA"
BOT_TOKEN = "BOT_TOKEN_BURAYA"

client = jubbio.Client(application_id=APP_ID)

@client.event
async def on_ready():
    print(f"✅ {client.user} olarak giriş yapıldı!")
    print(f"📡 {len(client.guilds)} sunucuda aktif")

@client.event
async def on_message(message):
    if message.content == "!ping":
        embed = jubbio.Embed(
            title="🏓 Pong!",
            description="Bot aktif ve çalışıyor.",
            color=0x2ECC71
        )
        embed.add_field(name="Durum", value="Çevrimiçi", inline=True)
        embed.add_field(name="Kütüphane", value="jubbio.py", inline=True)
        embed.set_footer(text="jubbio.py ile geliştirildi")
        await message.channel.send(embed=embed)

    elif message.content == "!merhaba":
        embed = jubbio.Embed(
            title="👋 Hoş Geldin!",
            description=f"Merhaba {message.author.mention}! Seninle tanıştığıma memnunum.",
            color=0xE91E63
        )
        embed.add_field(name="Kullanıcı", value=message.author.display_name, inline=True)
        embed.add_field(name="Sunucu", value="Bu sunucu", inline=True)
        embed.set_footer(text="jubbio.py ile yapıldı ❤️")
        await message.channel.send(embed=embed)

    elif message.content == "!sunucu":
        guild = await client.get_guild(message.guild_id)
        embed = jubbio.Embed(
            title=f"📊 {guild.name}",
            description="Sunucu istatistikleri aşağıda listelendi.",
            color=0x3498DB
        )
        embed.add_field(name="ID", value=guild.id, inline=True)
        embed.add_field(name="Üye Sayısı", value=str(guild.member_count), inline=True)
        embed.add_field(name="Sahip ID", value=guild.owner_id, inline=True)
        embed.set_footer(text="jubbio.py")
        await message.channel.send(embed=embed)

    elif message.content == "!buton":
        row = jubbio.ActionRow(
            jubbio.Button(
                style=jubbio.ButtonStyle.SUCCESS,
                label="Tıkla!",
                custom_id="test_btn",
                emoji="🎉",
            ),
            jubbio.Button(
                style=jubbio.ButtonStyle.LINK,
                label="Jubbio",
                url="https://jubbio.com",
            ),
        )
        embed = jubbio.Embed(
            title="🎮 Etkileşimli Butonlar",
            description="Aşağıdaki butonları kullanarak etkileşime geçebilirsin!",
            color=0x9B59B6
        )
        await message.channel.send(embed=embed, components=[row])

@client.component(custom_id="test_btn")
async def test_button(interaction):
    embed = jubbio.Embed(
        title="🎉 Butona Tıklandı!",
        description=f"{interaction.user.display_name} butona başarıyla tıkladı!",
        color=0xF39C12
    )
    await interaction.respond(embed=embed, ephemeral=True)

@client.event
async def on_member_join(member):
    print(f"➕ {member.user.username} sunucuya katıldı!")

@client.event
async def on_member_ban(member):
    print(f"🔨 {member.user.username} yasaklandı!")

client.run(BOT_TOKEN)
