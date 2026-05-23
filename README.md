<h1 align="center">jubbio.py</h1>

<p align="center">
  <strong>Jubbio botları geliştirmek için modern, asenkron ve nesne yönelimli <ins>bağımsız (unofficial)</ins> Python kütüphanesi.</strong>
</p>

<p align="center">
  <b>⚠️ DİKKAT:</b> Bu proje topluluk tarafından geliştirilmiştir ve <b>Jubbio</b> geliştiricileri/sahipleri ile <u>hiçbir resmi bağlantısı yoktur</u>. Jubbio API'sini kullanmak için gayri-resmi bir köprü görevi görür.
</p>

<p align="center">
  <a href="https://pypi.org/project/jubbio.py/">
    <img src="https://img.shields.io/pypi/v/jubbio.py?style=for-the-badge&logo=pypi&color=0073b7" alt="PyPI Version">
  </a>
  <img src="https://img.shields.io/badge/Python-3.9+-yellow?style=for-the-badge&logo=python&logoColor=white" alt="Python Versions">
  <img src="https://img.shields.io/badge/asyncio-supported-success?style=for-the-badge" alt="Asyncio">
  <img src="https://img.shields.io/badge/License-MIT-blueviolet?style=for-the-badge" alt="License">
</p>

<p align="center">
  <a href="#-kurulum"><b>Kurulum</b></a> •
  <a href="#-temel-özellikler"><b>Özellikler</b></a> •
  <a href="#-hızlı-başlangıç"><b>Örnekler</b></a> •
  <a href="#-api-referansı"><b>Dokümantasyon</b></a>
</p>

<hr>

## Temel Özellikler

* **Tamamen Asenkron:** `aiohttp` ve `asyncio` altyapısı ile "non-blocking" performans.
* **Tanıdık ve Sezgisel:** `discord.py` benzeri, öğrenmesi kolay dekoratör (`@client.event`) tabanlı tasarım.
* **Tam Donanımlı:** Slash komutları, embedler (zengin kartlar), butonlar (ActionRow) ve fazlası.
* **Dayanıklı Gateway:** WebSockets üzerinden kopmalara karşı otomatik yeniden bağlanma ve rate-limit yönetimi.

<br>

## Kurulum

Paketi kurmanın en kolay yolu PyPI üzerinden `pip` kullanmaktır:

```bash
pip install -U jubbio.py
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
    # Kendi mesajlarımızı yoksayalım
    if message.author.bot:
        return

    if message.content == '!ping':
        await message.channel.send('Pong!')

client.run('BOT_TOKEN_BURAYA')
```

### Slash Komutları (Uygulama Komutları)

Kullanıcıların `/bilgi` yazarak çağırabileceği modern komutlar oluşturabilirsiniz:

```python
@client.event
async def on_ready():
    # Komutu oluşturup sunucuya kaydedelim
    cmd = jubbio.SlashCommand(
        name='profil',
        description='Kullanıcı profilini görüntüler',
    )
    await client.register_command(cmd, guild_id='SUNUCU_ID')

@client.command(name='profil')
async def profil_komutu(interaction):
    embed = jubbio.Embed(
        title=f"{interaction.user.display_name}",
        color=jubbio.Color.purple()
    )
    embed.add_field(name='ID', value=interaction.user.id)
    await interaction.respond(embed=embed)
```

### Butonlar ve Etkileşimler (Components)

Kullanıcıların tıklayabileceği interaktif butonlar gönderebilirsiniz:

```python
@client.event
async def on_message(message):
    if message.content == '!onay':
        embed = jubbio.Embed(description="Şartları kabul ediyor musunuz?", color=jubbio.Color.blue())
        
        row = jubbio.ActionRow(
            jubbio.Button(style=jubbio.ButtonStyle.SUCCESS, label='Evet', custom_id='btn_yes'),
            jubbio.Button(style=jubbio.ButtonStyle.DANGER, label='Hayır', custom_id='btn_no')
        )
        await message.channel.send(embed=embed, components=[row])

@client.component(custom_id='btn_yes')
async def onaylandi(interaction):
    await interaction.respond('Teşekkürler, onaylandı!', ephemeral=True)
```

<br>

## API Referansı

### Client Ana Metotları
| Metot | Ne İşe Yarar? |
|-------|----------|
| `client.run(token)` | Botu gateway'e bağlar ve çalıştırır. |
| `client.register_command(cmd)` | Sunucuya veya globale slash komut kaydeder. |
| `client.send_dm(user_id, msg)` | Belirtilen kullanıcıya özel mesaj atar. |

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
  <i>Bu kütüphane bağımsız geliştiriciler tarafından oluşturulmuştur ve Jubbio Inc. ile doğrudan bağlantısı yoktur.</i>
</p>
