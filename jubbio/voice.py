import asyncio
import logging
import shlex
from typing import Optional, Dict, Any

try:
    import yt_dlp
    has_ytdlp = True
except ImportError:
    has_ytdlp = False

try:
    from livekit import rtc
    has_livekit = True
except ImportError:
    has_livekit = False

log = logging.getLogger(__name__)

class VoiceConnectionStatus:
    CONNECTING = "Connecting"
    SIGNALLING = "Signalling"
    READY = "Ready"
    DISCONNECTED = "Disconnected"
    DESTROYED = "Destroyed"

class AudioPlayerStatus:
    IDLE = "Idle"
    BUFFERING = "Buffering"
    PLAYING = "Playing"
    PAUSED = "Paused"

class VoiceConnection:

    def __init__(self, client, guild_id: str, channel_id: str):
        if not has_livekit:
            raise RuntimeError("Ses desteği (voice) için 'livekit' paketi yüklenmelidir. Lütfen `pip install livekit` komutunu çalıştırın.")

        self.client = client
        self.guild_id = guild_id
        self.channel_id = channel_id
        self.room: Optional[rtc.Room] = None
        self.status = VoiceConnectionStatus.CONNECTING
        self.player = AudioPlayer(self)
        self.connected_event = asyncio.Event()

    async def _connect_livekit(self, endpoint: str, token: str):
        self.status = VoiceConnectionStatus.SIGNALLING

        url = endpoint if endpoint.startswith("ws") else f"wss://{endpoint}"

        self.room = rtc.Room()

        @self.room.on("disconnected")
        def on_disconnected():
            log.info(f"Ses bağlantısı kesildi: {self.guild_id}")
            self.status = VoiceConnectionStatus.DISCONNECTED

        try:
            log.info(f"LiveKit'e bağlanılıyor: {url}")
            await self.room.connect(url, token)
            self.status = VoiceConnectionStatus.READY
            log.info(f"Ses kanalına başarıyla bağlanıldı: {self.guild_id}")
            await self.player._start_livekit_track()
            self.connected_event.set()
        except Exception as e:
            log.error(f"LiveKit bağlantı hatası: {e}")
            self.status = VoiceConnectionStatus.DISCONNECTED
            self.connected_event.set()

    async def disconnect(self):
        if self.room:
            await self.room.disconnect()
        self.status = VoiceConnectionStatus.DISCONNECTED

    async def destroy(self):
        await self.disconnect()
        self.status = VoiceConnectionStatus.DESTROYED
        if self.guild_id in self.client.voice_clients:
            del self.client.voice_clients[self.guild_id]


class AudioPlayer:

    def __init__(self, vc: VoiceConnection):
        self.vc = vc
        self.status = AudioPlayerStatus.IDLE
        self._ffmpeg_process = None
        self._play_task = None
        self.audio_source = rtc.AudioSource(48000, 2)
        self.audio_track = rtc.LocalAudioTrack.create_audio_track("bot_audio", self.audio_source)
        self._track_published = False
        self.queue = []
        self.current_song = None
        try:
            import static_ffmpeg
            static_ffmpeg.add_paths()
        except ImportError:
            pass
        self.ytdl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': True,
        }

    async def _start_livekit_track(self):
        if not self._track_published and self.vc.room:
            options = rtc.TrackPublishOptions()
            options.source = rtc.TrackSource.SOURCE_MICROPHONE
            await self.vc.room.local_participant.publish_track(self.audio_track, options)
            self._track_published = True

    async def play(self, query_or_url: str):
        if not has_ytdlp:
            raise RuntimeError("yt-dlp paketi eksik. pip install yt-dlp komutunu çalıştırın.")

        self.queue.append(query_or_url)

        if self.status == AudioPlayerStatus.IDLE:
            await self._play_next()

    async def _play_next(self):
        if not self.queue:
            self.status = AudioPlayerStatus.IDLE
            self.current_song = None
            return

        self.status = AudioPlayerStatus.BUFFERING
        query_or_url = self.queue.pop(0)
        self.current_song = query_or_url

        loop = asyncio.get_event_loop()
        def extract():
            with yt_dlp.YoutubeDL(self.ytdl_opts) as ydl:
                return ydl.extract_info(f"ytsearch:{query_or_url}" if not query_or_url.startswith("http") else query_or_url, download=False)

        try:
            data = await loop.run_in_executor(None, extract)
            if 'entries' in data:
                data = data['entries'][0]
            url = data['url']
        except Exception as e:
            log.error(f"yt-dlp hatası: {e}")
            asyncio.create_task(self._play_next())
            return

        await self._start_livekit_track()

        ffmpeg_cmd = [
            'ffmpeg', '-hide_banner', '-loglevel', 'error',
            '-i', url,
            '-f', 's16le', '-ar', '48000', '-ac', '2',
            '-'
        ]

        try:
            self._ffmpeg_process = await asyncio.create_subprocess_exec(
                *ffmpeg_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
        except FileNotFoundError:
            raise RuntimeError("FFmpeg bulunamadı. Lütfen sisteminize FFmpeg kurun ve PATH'e ekleyin.")

        self.status = AudioPlayerStatus.PLAYING
        self._play_task = asyncio.create_task(self._stream_audio())

        async def _log_stderr():
            while self._ffmpeg_process:
                line = await self._ffmpeg_process.stderr.readline()
                if not line:
                    break
                log.debug(f"FFmpeg: {line.decode().strip()}")
        asyncio.create_task(_log_stderr())

    async def _stream_audio(self):
        frame_size = 3840
        delay = 0.02
        try:
            start_time = asyncio.get_event_loop().time()
            loops = 0

            while self.status == AudioPlayerStatus.PLAYING and self._ffmpeg_process:
                data = await self._ffmpeg_process.stdout.readexactly(frame_size)

                frame = rtc.AudioFrame(
                    data=data,
                    sample_rate=48000,
                    num_channels=2,
                    samples_per_channel=960
                )
                await self.audio_source.capture_frame(frame)

                loops += 1
                next_expected_time = start_time + (loops * delay)
                current_time = asyncio.get_event_loop().time()
                sleep_amount = next_expected_time - current_time

                if sleep_amount > 0:
                    await asyncio.sleep(sleep_amount)

        except asyncio.IncompleteReadError:
            pass
        except Exception as e:
            log.error(f"Stream hatası: {e}")
        finally:
            if self._ffmpeg_process:
                try: self._ffmpeg_process.kill()
                except: pass
                self._ffmpeg_process = None

            if self.status != AudioPlayerStatus.IDLE:
                asyncio.create_task(self._play_next())

    async def stop(self):
        self.status = AudioPlayerStatus.IDLE
        self.queue.clear()
        self.current_song = None
        if self._ffmpeg_process:
            try:
                self._ffmpeg_process.kill()
            except:
                pass
            self._ffmpeg_process = None
        if self._play_task and not self._play_task.done():
            self._play_task.cancel()

    async def skip(self):
        if self._ffmpeg_process:
            try:
                self._ffmpeg_process.kill()
            except:
                pass
            self._ffmpeg_process = None

async def join_voice_channel(client, guild_id: str, channel_id: str, self_mute: bool = False, self_deaf: bool = False, timeout: float = 10.0) -> VoiceConnection:
    if guild_id in client.voice_clients:
        existing = client.voice_clients[guild_id]
        await existing.destroy()

    vc = VoiceConnection(client, guild_id, channel_id)
    client.voice_clients[guild_id] = vc

    await client._gateway.update_voice_state(guild_id, channel_id, self_mute, self_deaf)

    try:
        await asyncio.wait_for(vc.connected_event.wait(), timeout=timeout)
        if vc.status != VoiceConnectionStatus.READY:
            raise RuntimeError("LiveKit sunucusuna bağlanılamadı.")
    except asyncio.TimeoutError:
        await vc.destroy()
        raise TimeoutError("Ses kanalına bağlanırken zaman aşımı (Gateway yanıt vermedi) veya yetkiniz yok.")

    return vc
