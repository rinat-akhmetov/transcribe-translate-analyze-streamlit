import json
from pprint import pprint

import boto3
from botocore.exceptions import ClientError

from dto import Item
from utils import cache


@cache
def translate_item(item: Item, source_language, target_language) -> Item:
    if len(bytes(item.content(), "utf-8")) > 5000:
        assert False, "Text is too long"
    translate_client = boto3.client('translate')
    translated_item = Item(
        start_time=item.start_time,
        end_time=item.end_time,
        speaker_label=item.speaker_label
    )
    try:
        response = translate_client.translate_text(
            Text=item.content(),
            SourceLanguageCode=source_language,
            TargetLanguageCode=target_language,
        )
        translated_item._content = response['TranslatedText']
    except ClientError:
        translated_item._content = 'error during translation'
    return translated_item


def translate(text, current_language, target_language):
    if len(bytes(text, "utf-8")) > 5000:
        assert False, "Text is too long"
    translate_client = boto3.client('translate')
    response = translate_client.translate_text(
        Text=text,
        SourceLanguageCode=current_language,
        TargetLanguageCode=target_language,
    )
    return response['TranslatedText']


def translate_subtitle(subtitle_path):
    with open(subtitle_path, 'r') as f:
        subtitles = json.load(f)
        for result in subtitles['results']['transcripts']:
            pprint(result['transcript'])


if __name__ == '__main__':
    text = 'Buenas tardes. Para. Para. Yesa est\u00e1 demandando a Ernesto de escribeme tu relaci\u00f3n'
    res = translate(text, 'es-ES', 'en-US')
    print('resul')
    # Fire(translate_subtitle)
