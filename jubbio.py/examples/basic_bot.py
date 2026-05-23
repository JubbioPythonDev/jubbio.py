"""
Basit Jubbio Bot Örneği
~~~~~~~~~~~~~~~~~~~~~~~
Temel komutlar ve olay dinleme.
"""
import jubbio

client = jubbio.Client()


@client.event
async def on_ready():
    """Bot hazır olduğunda çalışır."""
    print(f"✅ {client.user} olarak giriş yapıldı!")
    print(f"📡 {len(client.guilds)} sunucuda aktif")


@client.event
async def on_message(message):
    """Yeni mesaj geldiğinde çalışır."""

    if message.content == "!ping":
        await message.channel.send("🏓 Pong!")

    elif message.content == "!merhaba":
        embed = jubbio.Embed(
            title="👋 Merhaba!",
            description=f"Hoş geldin {message.author.mention}!",
            color=jubbio.Color.purple(),
        )
        embed.set_footer(text="jubbio.py ile yapıldı ❤️")
        await message.channel.send(embed=embed)

    elif message.content == "!sunucu":
        guild = await client.get_guild(message.guild_id)
        embed = jubbio.Embed(
            title=f"📊 {guild.name}",
            color=jubbio.Color.blue(),
        )
        embed.add_field(name="ID", value=guild.id, inline=True)
        embed.add_field(name="Üye Sayısı", value=str(guild.member_count), inline=True)
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
        await message.channel.send("Butona bas! 👇", components=[row])


@client.component(custom_id="test_btn")
async def test_button(interaction):
    """Butona tıklandığında çalışır."""
    await interaction.respond(
        f"🎉 {interaction.user.display_name} butona tıkladı!",
        ephemeral=True,
    )


@client.event
async def on_member_join(member):
    """Yeni üye katıldığında çalışır."""
    print(f"➕ {member.user.username} sunucuya katıldı!")


@client.event
async def on_member_ban(member):
    """Üye yasaklandığında çalışır."""
    print(f"🔨 {member.user.username} yasaklandı!")


# Botu başlat
client.run("BOT_TOKEN_BURAYA")
