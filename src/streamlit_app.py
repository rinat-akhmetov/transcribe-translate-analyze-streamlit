import os
from pathlib import Path

import streamlit as st
from joblib import Parallel, delayed

from dto import Item, TranslatedItem
from subtitles.subtitles import create_subtitle, create_subtitles_file, write_srt_to_file
from transcribe.amazon import transcribe
from translate.translate import translate_item
from utils import create_markdown

os.environ['AWS_ACCESS_KEY_ID'] = st.secrets['AWS_ACCESS_KEY_ID']
os.environ['AWS_SECRET_ACCESS_KEY'] = st.secrets['AWS_SECRET_ACCESS_KEY']
os.environ['AWS_REGION'] = 'us-east-1'
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'


def process(progress_bar, st, video_path: str, source_language='es-ES', target_language: str = 'en-US'):
    message = st.info('Transcribing the video...')
    transcription = transcribe(video_path, language=source_language)
    step = 100 // 6
    progress_bar.progress(1 * step)
    message.empty()
    message = st.info('creating subtitles...')

    subtitles_file_path = Path(video_path).with_suffix('.srt')

    grouped_items: list[Item] = create_subtitle(transcription, subtitles_file_path)
    message.empty()
    message = st.info('Translating subtitles...')
    progress_bar.progress(2 * step)
    translated_items: list[TranslatedItem] = Parallel(n_jobs=15)(
        delayed(translate_item)(item, source_language, target_language) for item in grouped_items)
    progress_bar.progress(3 * step)
    message.empty()
    message = st.info('Creating translated subtitles...')
    subtitles_file_path = Path(video_path).with_suffix('.en.srt')
    create_subtitles_file(str(subtitles_file_path), translated_items)

    message.empty()
    message = st.info('Writing subtitles to video...')
    progress_bar.progress(4 * step)
    output_path = str(Path(video_path).with_suffix('.en.mp4'))
    write_srt_to_file(video_path, str(subtitles_file_path), output_path)

    message.empty()
    message = st.info('Creating markdown...')
    progress_bar.progress(5 * step)
    markdown = create_markdown(translated_items)
    message.empty()
    message = st.info('the subtitles have been converted to markdown')
    progress_bar.progress(100)
    message.empty()
    return output_path, markdown


if __name__ == '__main__':

    st.title('Transcribe, Translate and Analyze')

    source = ('es-ES', 'de-DE', 'es-US', 'fr-FR', 'fr-CA')
    source_language_index = st.sidebar.selectbox("Select Language", range(len(source)), format_func=lambda x: source[x])
    source_language = source[source_language_index]

    uploaded_file = st.sidebar.file_uploader("Video", type=['mp4'])
    if uploaded_file is not None:
        is_valid = True
        with st.spinner(text='Uploading...'):
            # st.sidebar.video(uploaded_file)
            Path(os.path.join("data", "videos")).mkdir(parents=True, exist_ok=True)

            with open(os.path.join("data", "videos", uploaded_file.name), "wb") as f:
                f.write(uploaded_file.getbuffer())
            source = f'data/videos/{uploaded_file.name}'
    else:
        is_valid = False

    if is_valid:
        print('valid')
        if st.button('Process'):
            left, right = st.columns(2)
            my_bar = st.progress(0)
            with st.spinner(text='Preparing Video'):
                video_path, markdown = process(my_bar, st, source, source_language)
                left.video(video_path)
                right.markdown(markdown)
                my_bar.empty()
                st.balloons()
