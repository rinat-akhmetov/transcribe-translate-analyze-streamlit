import os
from pathlib import Path

from fire import Fire
from joblib import Parallel, delayed

from dto import Item, TranslatedItem
from subtitles.subtitles import create_subtitle, create_subtitles_file, write_srt_to_file
from transcribe.amazon import transcribe
from translate.translate import translate_item
from utils import create_markdown

os.environ['AWS_PROFILE'] = 'EDU'
os.environ['AWS_REGION'] = 'us-east-1'
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'


def process(video_path: str, source_language='es-ES', target_language: str = 'en-US') -> str:
    """
    Process a video.
    """
    transcription = transcribe(video_path, language=source_language)

    subtitles_file_path = Path(video_path).with_suffix('.srt')

    grouped_items: list[Item] = create_subtitle(transcription, subtitles_file_path)
    translated_items: list[TranslatedItem] = Parallel(n_jobs=15)(
        delayed(translate_item)(item, source_language, target_language) for item in grouped_items)
    subtitles_file_path = Path(video_path).with_suffix('.en.srt')
    create_subtitles_file(str(subtitles_file_path), translated_items)
    output_path = str(Path(video_path).with_suffix('.en.mp4'))
    write_srt_to_file(video_path, str(subtitles_file_path), output_path)
    markdown = create_markdown(translated_items)
    return output_path, markdown
    # group the items by 5000 bytes content


if __name__ == '__main__':
    Fire(process)
