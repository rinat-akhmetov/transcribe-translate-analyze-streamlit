import logging
import subprocess
from pathlib import Path
from typing import List

import boto3
from fire import Fire
from tqdm import tqdm

from dto import AWSItem, SpeakerLabel
from transcribe.amazon import transcribe


def group_items_by_speaker(items: [AWSItem]) -> [AWSItem]:
    speakers: List[AWSItem] = []
    current = items[0]
    result = [items[0]]
    for item in items[1:]:
        if item.start_time is None:
            result[-1].alternatives.extend(item.alternatives)
            # item.speaker_label = current.speaker_label
            continue
        if result[-1].speaker_label == item.speaker_label and item.start_time - result[-1].start_time < 5:
            result[-1].alternatives.extend(item.alternatives)
            result[-1].end_time = item.end_time
            continue
        result.append(item)

        # if current.speaker_label != item.speaker_label:
        #     speakers.append(current)
        #     current = item
        # else:
        #     current.end_time = item.end_time
        #     current.alternatives.extend(item.alternatives)
    return result


def write_srt_to_file(video_path: str, subtitles_path: str, output_path: str):
    command = ['ffmpeg', '-y', '-i', video_path, '-max_muxing_queue_size', '9999', '-vf', f'subtitles={subtitles_path}',
               output_path]
    logging.info(f"process {' '.join(command)}")
    result = subprocess.run(command, stdout=subprocess.PIPE)
    logging.debug(result.stdout)


def format_time_for_subtitles(time: float) -> str:
    '00:00:01,840'
    'hh:mm:ss,ms'
    hours = int(time / 3600)
    minutes = int((time - hours * 3600) / 60)
    seconds = int(time - hours * 3600 - minutes * 60)
    milliseconds = int((time - hours * 3600 - minutes * 60 - seconds) * 1000)
    return f'{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}'


def create_subtitles_file(file_path: str, grouped_items: [AWSItem]):
    print(f'Creating subtitles file {file_path}')
    with open(file_path, 'w') as f:
        for index, item in enumerate(tqdm(grouped_items)):
            f.write(f'{index}\n')
            f.write(f'{format_time_for_subtitles(item.start_time)} --> {format_time_for_subtitles(item.end_time)}\n')
            f.write(f'{item.speaker_label}: {item.content()}\n\n')


def create_subtitle(response) -> List[AWSItem]:
    """
    Create a subtitle file from the response of the Transcribe API
    :param response:
    :return:
    """
    items_dict = {}
    items = []
    for item in tqdm(response['results']['items']):
        try:
            i = AWSItem(**item)
            items_dict[i.start_time] = i
            items.append(i)
        except Exception as e:
            print(e, item)
            assert e

    speaker_labels = []
    for speaker_label in tqdm(response['results']['speaker_labels']['segments']):
        try:
            speaker_labels.append(SpeakerLabel(**speaker_label))
        except Exception as e:
            print(e, speaker_label)
            assert e

    for speaker_label in speaker_labels:
        for item in speaker_label.items:
            items_dict[item.start_time].speaker_label = speaker_label.speaker_label
    grouped_items = group_items_by_speaker(items)
    return grouped_items


def upload_file_to_s3(file_path: str, bucket_name: str, s3_key: str):
    s3 = boto3.client('s3')
    s3.upload_file(file_path, bucket_name, s3_key)
    return f's3://{bucket_name}/{s3_key}'


def main(file_path: str):
    response = transcribe(file_path)
    subtitles_file_path = Path(file_path).with_suffix('.srt')

    create_subtitle(response, subtitles_file_path)


if __name__ == '__main__':
    Fire(main)
