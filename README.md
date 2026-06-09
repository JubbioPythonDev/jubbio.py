<h1 align="center">jubbio.py</h1>

<p align="center">
  <strong>Jubbio botları geliştirmek için modern, asenkron ve nesne yönelimli <ins>bağımsız (unofficial)</ins> Python kütüphanesi.</strong>
</p>

<p align="center">
  <b>DİKKAT:</b> Bu proje topluluk tarafından geliştirilmiştir ve <b>Jubbio</b> geliştiricileri/sahipleri ile <u>hiçbir resmi bağlantısı yoktur</u>. Jubbio API'sini kullanmak için gayri-resmi bir köprü görevi görür.
</p>

<p align="center">
  <a href="https://pypi.org/project/jubbio.py/">
    <img src="https://img.shields.io/badge/PyPI-v1.2.7-0073b7?style=for-the-badge&logo=pypi" alt="PyPI Version">
  </a>
  <img src="https://img.shields.io/badge/Python-3.9+-yellow?style=for-the-badge&logo=python&logoColor=white" alt="Python Versions">
  <img src="https://img.shields.io/badge/asyncio-supported-success?style=for-the-badge" alt="Asyncio">
  <img src="https://img.shields.io/badge/License-MIT-blueviolet?style=for-the-badge" alt="License">
  <img src="https://img.shields.io/badge/Voice-LiveKit-ff6600?style=for-the-badge" alt="Voice Support">
</p>

<p align="center">
  <a href="#kurulum"><b>Kurulum</b></a> •
  <a href="#temel-özellikler"><b>Özellikler</b></a> •
  <a href="#hızlı-başlangıç"><b>Örnekler</b></a> •
  <a href="#api-referansı"><b>Dokümantasyon</b></a>
</p>

<hr>

## Temel Özellikler

* **Tamamen Asenkron:** `aiohttp` ve `asyncio` altyapısı ile "non-blocking" performans.
* **Tanıdık ve Sezgisel:** `discord.py` benzeri, öğrenmesi kolay dekoratör (`@client.event`) tabanlı tasarım.
* **Tam Donanımlı:** Slash komutları, embedler (zengin kartlar), butonlar (ActionRow) ve fazlası.
* **Ses & Müzik:** LiveKit tabanlı ses kanalı desteği, YouTube'dan müzik çalma (`yt-dlp` + `FFmpeg`), kuyruk sistemi, atlama ve durdurma.
* **Dayanıklı Gateway:** WebSockets üzerinden kopmalara karşı otomatik yeniden bağlanma ve rate-limit yönetimi.

<br>

## Kurulum

Paketi kurmanın en kolay yolu PyPI üzerinden `pip` kullanmaktır:

```bash
pip install -U jubbio.py
```

Ses desteği (Voice) için ek bağımlılıklar:

```bash
pip install -U "jubbio.py[voice]"
```

<br>

## Hızlı Başlangıç

Basit bir ping-pong botu yazmak sadece birkaç satır sürer:

```python
import jubbio

client = jubbio.Client()

@client.event
async def on_ready():
    print(f'Sisteme giriş yapıldı: {client.user}')

@client.event
async def on_message(message):
    if message.author.bot:
        return

    if message.content == '!ping':
        embed = jubbio.Embed(
            title="Pong!",
            description="Bot aktif ve çalışıyor.",
            color=0x2ECC71
        )
        await message.channel.send(embed=embed)

client.run('BOT_TOKEN_BURAYA')
```

### Slash Komutları (Uygulama Komutları)

```python
@client.event
async def on_ready():
    cmd = jubbio.SlashCommand(
        name='profil',
        description='Kullanıcı profilini görüntüler',
    )
    await client.register_command(cmd)

@client.command(name='profil')
async def profil_komutu(interaction):
    embed = jubbio.Embed(
        title=f"{interaction.user.display_name}",
        color=0x9B59B6
    )
    embed.add_field(name='ID', value=interaction.user.id, inline=True)
    embed.add_field(name='Kullanıcı Adı', value=interaction.user.username, inline=True)
    embed.set_footer(text="jubbio.py")
    await interaction.respond(embed=embed)
```

### Butonlar ve Etkileşimler (Components)

```python
@client.event
async def on_message(message):
    if message.content == '!onay':
        embed = jubbio.Embed(
            title="Onay Gerekli",
            description="Şartları kabul ediyor musunuz?",
            color=0x3498DB
        )

        row = jubbio.ActionRow(
            jubbio.Button(style=jubbio.ButtonStyle.SUCCESS, label='Evet', custom_id='btn_yes'),
            jubbio.Button(style=jubbio.ButtonStyle.DANGER, label='Hayır', custom_id='btn_no')
        )
        await message.channel.send(embed=embed, components=[row])

@client.component(custom_id='btn_yes')
async def onaylandi(interaction):
    embed = jubbio.Embed(
        title="Onaylandı",
        description="Teşekkürler, işleminiz onaylandı!",
        color=0x2ECC71
    )
    await interaction.respond(embed=embed, ephemeral=True)
```

### Müzik Botu

```python
import jubbio
from jubbio.voice import join_voice_channel

client = jubbio.Client(
    application_id="APP_ID",
    intents=jubbio.Intents(jubbio.Intents.GUILDS | jubbio.Intents.GUILD_VOICE_STATES)
)

@client.command(name='oynat')
async def oynat(interaction):
    sarki = interaction.get_option("sarki")
    channel_id = interaction.member.voice.channel_id

    if interaction.guild_id not in client.voice_clients:
        vc = await join_voice_channel(client, interaction.guild_id, channel_id)
    else:
        vc = client.voice_clients[interaction.guild_id]

    await vc.player.play(sarki)

    embed = jubbio.Embed(
        title="Kuyruga Eklendi",
        description=f"**{sarki}**",
        color=0x2ECC71
    )
    await interaction.respond(embed=embed)
```

<br>

## API Referansı

### Client Ana Metotları
| Metot | Ne İşe Yarar? |
|-------|----------|
| `client.run(token)` | Botu gateway'e bağlar ve çalıştırır. |
| `client.register_command(cmd)` | Sunucuya veya globale slash komut kaydeder. |
| `client.send_dm(user_id, msg)` | Belirtilen kullanıcıya özel mesaj atar. |
| `client.get_user(user_id)` | Kullanıcı bilgilerini getirir. |
| `client.get_guild(guild_id)` | Sunucu bilgilerini getirir. |

### Ses (Voice) Metotları
| Metot | Ne İşe Yarar? |
|-------|----------|
| `join_voice_channel(client, guild_id, channel_id)` | Ses kanalına bağlanır. |
| `vc.player.play(query)` | Şarkı çalar veya kuyruğa ekler. |
| `vc.player.skip()` | Şu anki şarkıyı atlar. |
| `vc.player.stop()` | Müziği durdurur ve kuyruğu temizler. |
| `vc.destroy()` | Ses bağlantısını kapatır. |

### Olaylar (Events)
| Olay | Açıklama |
|------|----------|
| `on_ready` | Bot hazır olduğunda |
| `on_message(message)` | Yeni mesaj geldiğinde |
| `on_interaction(interaction)` | Etkileşim olduğunda (Buton, Komut vb.) |
| `on_guild_join(guild)` | Yeni sunucuya katılınca |
| `on_guild_remove(guild)` | Sunucudan ayrılınca |
| `on_member_ban(member)` | Üye yasaklanınca |
| `on_member_unban(member)` | Yasak kaldırılınca |
| `on_member_join(member)` | Üye katılınca |
| `on_member_remove(member)` | Üye ayrılınca |
| `on_invite_create(invite)` | Davet oluşturulunca |
| `on_presence_update(data)` | Durum güncellenince |

<br>

---

<p align="center">
  <i>Bu kütüphane bağımsız geliştiriciler tarafından oluşturulmuştur ve Jubbio ile doğrudan bağlantısı yoktur.</i>
</p>
