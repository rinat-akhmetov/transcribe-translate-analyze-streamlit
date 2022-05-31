import os
from pathlib import Path

import streamlit as st
from joblib import Parallel, delayed

from dto import AWSItem, Item
from subtitles.subtitles import create_subtitle, create_subtitles_file, write_srt_to_file
from transcribe.amazon import transcribe
from translate.translate import translate_item

os.environ['AWS_ACCESS_KEY_ID'] = st.secrets['AWS_ACCESS_KEY_ID']
os.environ['AWS_SECRET_ACCESS_KEY'] = st.secrets['AWS_SECRET_ACCESS_KEY']
os.environ['AWS_REGION'] = 'us-east-1'
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'


def process(parent_component, video_path: str, source_language='es-ES', target_language: str = 'en-US'):
    progress_bar = st.progress(0)
    step = 100 // 6
    transcription = transcribe_video_step(parent_component, source_language, video_path)
    progress_bar.progress(1 * step)
    grouped_items = create_subtitles_step(parent_component, transcription, video_path)
    progress_bar.progress(2 * step)
    create_subtitles_file_step(parent_component, video_path, grouped_items)
    progress_bar.progress(3 * step)
    translated_items = translate_items_step(parent_component, grouped_items, source_language, target_language)
    progress_bar.progress(4 * step)
    subtitles_file_path = create_subtitles_file_step(parent_component, video_path, translated_items)
    progress_bar.progress(5 * step)
    output_path = burn_subtitles_to_video_step(parent_component, video_path, subtitles_file_path)
    progress_bar.progress(6 * step)
    progress_bar.empty()
    return output_path, grouped_items, translated_items


def transcribe_video_step(parent_component, source_language, video_path):
    message = parent_component.info('Transcribing the video...')
    transcription = transcribe(video_path, language=source_language)
    message.empty()
    return transcription


def create_subtitles_step(parent_component, transcription, video_path):
    message = parent_component.info('creating subtitles...')
    grouped_items: list[AWSItem] = create_subtitle(transcription)
    subtitles_file_path = Path(video_path).with_suffix('.srt')
    create_subtitles_file(str(subtitles_file_path), grouped_items)
    message.empty()
    return grouped_items


def burn_subtitles_to_video_step(parent_component, video_path, subtitles_file_path):
    message = parent_component.info('Writing subtitles to video...')
    output_path = str(Path(video_path).with_suffix('.en.mp4'))
    write_srt_to_file(video_path, str(subtitles_file_path), output_path)
    message.empty()
    return output_path


def translate_items_step(parent_component, grouped_items, source_language, target_language):
    message = parent_component.info('Translating subtitles...')
    translated_items: list[Item] = Parallel(n_jobs=15)(
        delayed(translate_item)(item, source_language, target_language) for item in grouped_items)
    message.empty()
    return translated_items


def create_subtitles_file_step(parent_component, video_path: str, translated_items: list[Item], suffix='.en.srt'):
    message = parent_component.info('Creating subtitles file...')
    subtitles_file_path = Path(video_path).with_suffix(suffix)
    create_subtitles_file(str(subtitles_file_path), translated_items)
    message.empty()
    return subtitles_file_path


def main_app():
    st.title('Transcribe, Translate and Analyze')

    source_language = language_component()

    is_valid, video_path = file_uploader_component(st.sidebar)

    source_texts = []
    source_items: list[AWSItem] = []
    translated_items: list[Item] = []
    translated_texts = []
    if is_valid:
        with st.spinner(text='Preparing Video'):
            video_path, source_items, translated_items = process(st, video_path, source_language)
            print('show video', video_path)
            st.video(video_path)
            source_column, translated_column = st.columns(2)
            for item in source_items:
                source_texts.append(
                    source_column.text_area(label=f'{item.speaker_label}', value=item.content())
                )
            for item in translated_items:
                translated_texts.append(
                    translated_column.text_area(label=f'{item.speaker_label}', value=item.content()))
            # st.balloons()
        # if st.button('ReProcess'):
        #     reprocess(st, video_path, source_items, translated_items, source_language)


def reprocess(parent_component, video_path: str, grouped_items: list[Item],
              translated_items: list[Item], source_language='es-ES',
              target_language: str = 'en-US'):
    progress_bar = st.progress(0)
    step = 100 // 5
    translated_items = translate_items_step(parent_component, grouped_items, source_language, target_language)

    subtitles_file_path = create_subtitles_file_step(parent_component, video_path, translated_items)
    output_path = burn_subtitles_to_video_step(parent_component, video_path, subtitles_file_path)

    progress_bar.empty()
    return output_path, grouped_items, translated_items


def language_component():
    source = ('es-ES', 'de-DE', 'es-US', 'fr-FR', 'fr-CA')
    source_language_index = st.sidebar.selectbox("Select Language", range(len(source)), format_func=lambda x: source[x])
    source_language = source[source_language_index]
    return source_language


def file_uploader_component(parent_component):
    uploaded_file = parent_component.file_uploader("Video", type=['mp4'])
    video_path = None
    if uploaded_file is not None:
        is_valid = True
        with st.spinner(text='Uploading...'):
            # st.sidebar.video(uploaded_file)
            Path(os.path.join("data", "videos")).mkdir(parents=True, exist_ok=True)

            with open(os.path.join("data", "videos", uploaded_file.name), "wb") as f:
                f.write(uploaded_file.getbuffer())
            video_path = f'data/videos/{uploaded_file.name}'
    else:
        is_valid = False
    return is_valid, video_path


if __name__ == '__main__':
    main_app()
