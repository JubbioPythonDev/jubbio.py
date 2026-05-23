import jubbio

APP_ID = "APPLICATION_ID_BURAYA"
BOT_TOKEN = "BOT_TOKEN_BURAYA"

client = jubbio.Client(application_id=APP_ID)

@client.event
async def on_ready():
    print(f"✅ {client.user} hazır!")

    await client.register_command(
        jubbio.SlashCommand(
            name="profil",
            description="Botun profil kartını gösterir"
        )
    )

    await client.register_command(
        jubbio.SlashCommand(
            name="anket",
            description="Hızlı bir anket oluşturur",
            options=[
                jubbio.SlashCommandOption(
                    name="soru",
                    description="Anket sorusu",
                    type=jubbio.CommandOptionType.STRING,
                    required=True,
                )
            ],
        )
    )

    await client.register_command(
        jubbio.SlashCommand(
            name="yardim",
            description="Tüm komutları listeler"
        )
    )

    print("📝 Komutlar kaydedildi!")

@client.command(name="profil")
async def on_profil(interaction: jubbio.Interaction):
    embed = jubbio.Embed(
        title="🤖 Bot Profili",
        description="Bu bot jubbio.py kütüphanesi ile geliştirilmiştir.",
        color=0x2ECC71
    )
    embed.add_field(name="Sürüm", value="v1.2.7", inline=True)
    embed.add_field(name="Kütüphane", value="jubbio.py", inline=True)
    embed.add_field(name="Lisans", value="MIT", inline=True)
    embed.set_footer(text="jubbio.py Topluluğu")

    row = jubbio.ActionRow()
    row.add_button(
        style=jubbio.ButtonStyle.PRIMARY,
        label="⭐ Beğen",
        custom_id="btn_like"
    )
    row.add_button(
        style=jubbio.ButtonStyle.SECONDARY,
        label="📊 İstatistikler",
        custom_id="btn_stats"
    )
    row.add_button(
        style=jubbio.ButtonStyle.LINK,
        label="📚 Dökümanlar",
        url="https://jubbio.com/dev/docs"
    )

    await interaction.respond(embed=embed, components=[row])

@client.command(name="anket")
async def on_anket(interaction: jubbio.Interaction):
    soru = interaction.get_option("soru")

    embed = jubbio.Embed(
        title="📊 Anket",
        description=soru,
        color=0xF39C12
    )
    embed.add_field(name="Oluşturan", value=interaction.user.display_name, inline=True)
    embed.set_footer(text="Oylamak için aşağıdaki butonları kullan!")

    row = jubbio.ActionRow()
    row.add_button(
        style=jubbio.ButtonStyle.SUCCESS,
        label="👍 Evet",
        custom_id="anket_evet"
    )
    row.add_button(
        style=jubbio.ButtonStyle.DANGER,
        label="👎 Hayır",
        custom_id="anket_hayir"
    )

    await interaction.respond(embed=embed, components=[row])

@client.command(name="yardim")
async def on_yardim(interaction: jubbio.Interaction):
    embed = jubbio.Embed(
        title="📖 Komut Listesi",
        description="Kullanabileceğin tüm komutlar aşağıda listelenmiştir.",
        color=0x9B59B6
    )
    embed.add_field(name="/profil", value="Botun profil kartını gösterir", inline=False)
    embed.add_field(name="/anket", value="Hızlı bir anket oluşturur", inline=False)
    embed.add_field(name="/yardim", value="Bu mesajı gösterir", inline=False)
    embed.set_footer(text="jubbio.py ile geliştirildi")

    await interaction.respond(embed=embed, ephemeral=True)

@client.component(custom_id="btn_like")
async def on_like(interaction: jubbio.Interaction):
    embed = jubbio.Embed(
        title="⭐ Teşekkürler!",
        description=f"{interaction.user.display_name} botu beğendi!",
        color=0xF1C40F
    )
    await interaction.respond(embed=embed, ephemeral=True)

@client.component(custom_id="btn_stats")
async def on_stats(interaction: jubbio.Interaction):
    embed = jubbio.Embed(
        title="📊 Bot İstatistikleri",
        description="Anlık bot verileri",
        color=0x3498DB
    )
    embed.add_field(name="Sunucu Sayısı", value=str(len(interaction._http and client.guilds or [])), inline=True)
    embed.add_field(name="Uptime", value="Aktif", inline=True)
    await interaction.respond(embed=embed, ephemeral=True)

@client.component(custom_id="anket_evet")
async def on_anket_evet(interaction: jubbio.Interaction):
    embed = jubbio.Embed(
        title="👍 Oyun Kaydedildi!",
        description=f"{interaction.user.display_name} **Evet** dedi!",
        color=0x2ECC71
    )
    await interaction.respond(embed=embed, ephemeral=True)

@client.component(custom_id="anket_hayir")
async def on_anket_hayir(interaction: jubbio.Interaction):
    embed = jubbio.Embed(
        title="👎 Oyun Kaydedildi!",
        description=f"{interaction.user.display_name} **Hayır** dedi!",
        color=0xE74C3C
    )
    await interaction.respond(embed=embed, ephemeral=True)

client.run(BOT_TOKEN)
