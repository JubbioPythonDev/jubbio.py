import jubbio
from jubbio.voice import join_voice_channel

APP_ID = "APPLICATION_ID_BURAYA"
BOT_TOKEN = "BOT_TOKEN_BURAYA"

client = jubbio.Client(
    application_id=APP_ID,
    intents=jubbio.Intents(jubbio.Intents.GUILDS | jubbio.Intents.GUILD_VOICE_STATES | jubbio.Intents.GUILD_MESSAGES)
)

@client.event
async def on_ready():
    print(f"✅ {client.user} hazır!")

    await client.register_command(
        jubbio.SlashCommand(
            name="oynat",
            description="YouTube'dan müzik çalar veya kuyruğa ekler",
            options=[
                jubbio.SlashCommandOption(
                    name="sarki",
                    description="Şarkı adı veya YouTube linki",
                    type=3,
                    required=True
                )
            ]
        )
    )

    await client.register_command(
        jubbio.SlashCommand(
            name="atla",
            description="Sıradaki şarkıya geçer"
        )
    )

    await client.register_command(
        jubbio.SlashCommand(
            name="durdur",
            description="Çalan müziği durdurur ve kuyruğu temizler"
        )
    )

    await client.register_command(
        jubbio.SlashCommand(
            name="kuyruk",
            description="Şarkı kuyruğunu gösterir"
        )
    )

    await client.register_command(
        jubbio.SlashCommand(
            name="ayril",
            description="Botu sesli kanaldan çıkarır"
        )
    )

    print("📝 Komutlar kaydedildi!")

@client.command(name="oynat")
async def on_oynat(interaction: jubbio.Interaction):
    sarki = interaction.get_option("sarki")

    if not interaction.member or not interaction.member.voice or not interaction.member.voice.channel_id:
        embed = jubbio.Embed(
            title="❌ Hata",
            description="Şarkı açmak için önce bir ses kanalına katılmalısın!",
            color=0xE74C3C
        )
        return await interaction.respond(embed=embed, ephemeral=True)

    await interaction.defer()

    guild_id = interaction.guild_id
    channel_id = interaction.member.voice.channel_id

    try:
        if guild_id not in client.voice_clients:
            vc = await join_voice_channel(client, guild_id, channel_id)
        else:
            vc = client.voice_clients[guild_id]

        await vc.player.play(sarki)

        embed = jubbio.Embed(
            title="🎵 Kuyruğa Eklendi",
            description=f"**{sarki}**",
            color=0x2ECC71
        )
        embed.add_field(name="İsteyen", value=interaction.user.display_name, inline=True)
        embed.add_field(name="Sıra", value=str(len(vc.player.queue) + 1), inline=True)
        embed.set_footer(text="jubbio.py Müzik")
        await interaction.edit_original_message(embed=embed)

    except Exception as e:
        embed = jubbio.Embed(
            title="❌ Hata",
            description=str(e),
            color=0xE74C3C
        )
        await interaction.edit_original_message(embed=embed)

@client.command(name="atla")
async def on_atla(interaction: jubbio.Interaction):
    vc = client.voice_clients.get(interaction.guild_id)
    if not vc or not vc.player:
        embed = jubbio.Embed(
            title="❌ Hata",
            description="Şu an bir şey çalmıyor.",
            color=0xE74C3C
        )
        return await interaction.respond(embed=embed, ephemeral=True)

    await vc.player.skip()

    embed = jubbio.Embed(
        title="⏭️ Atlandı",
        description="Sıradaki şarkıya geçiliyor...",
        color=0xF39C12
    )
    embed.set_footer(text="jubbio.py Müzik")
    await interaction.respond(embed=embed)

@client.command(name="durdur")
async def on_durdur(interaction: jubbio.Interaction):
    vc = client.voice_clients.get(interaction.guild_id)
    if not vc or not vc.player:
        embed = jubbio.Embed(
            title="❌ Hata",
            description="Şu an bir şey çalmıyor.",
            color=0xE74C3C
        )
        return await interaction.respond(embed=embed, ephemeral=True)

    await vc.player.stop()

    embed = jubbio.Embed(
        title="🛑 Durduruldu",
        description="Müzik durduruldu ve kuyruk temizlendi.",
        color=0xE74C3C
    )
    embed.set_footer(text="jubbio.py Müzik")
    await interaction.respond(embed=embed)

@client.command(name="kuyruk")
async def on_kuyruk(interaction: jubbio.Interaction):
    vc = client.voice_clients.get(interaction.guild_id)
    if not vc or not vc.player:
        embed = jubbio.Embed(
            title="🎵 Kuyruk",
            description="Şu an bir şey çalmıyor.",
            color=0x95A5A6
        )
        return await interaction.respond(embed=embed, ephemeral=True)

    embed = jubbio.Embed(
        title="🎵 Şarkı Kuyruğu",
        color=0x3498DB
    )

    if vc.player.current_song:
        embed.add_field(name="🔊 Şu An Çalıyor", value=f"**{vc.player.current_song}**", inline=False)

    if vc.player.queue:
        queue_text = ""
        for i, song in enumerate(vc.player.queue[:10], 1):
            queue_text += f"`{i}.` {song}\n"
        if len(vc.player.queue) > 10:
            queue_text += f"\n_...ve {len(vc.player.queue) - 10} şarkı daha_"
        embed.add_field(name="📋 Sıradakiler", value=queue_text, inline=False)
    else:
        embed.add_field(name="📋 Sıradakiler", value="Kuyruk boş.", inline=False)

    embed.set_footer(text=f"Toplam: {len(vc.player.queue)} şarkı")
    await interaction.respond(embed=embed, ephemeral=True)

@client.command(name="ayril")
async def on_ayril(interaction: jubbio.Interaction):
    vc = client.voice_clients.get(interaction.guild_id)
    if vc:
        await vc.player.stop()
        await vc.destroy()
        embed = jubbio.Embed(
            title="👋 Ayrıldım",
            description="Sesli kanaldan ayrıldım.",
            color=0x95A5A6
        )
        await interaction.respond(embed=embed)
    else:
        embed = jubbio.Embed(
            title="❌ Hata",
            description="Zaten bir ses kanalında değilim.",
            color=0xE74C3C
        )
        await interaction.respond(embed=embed, ephemeral=True)

client.run(BOT_TOKEN)
