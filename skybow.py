from mutagen.mp3 import MP3


def get_audio_length(path: str):
    audio = MP3(path)
    return audio.info.length
