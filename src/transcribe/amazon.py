# SPDX-License-Identifier: Apache-2.0

"""
Purpose

Shows how to use AWS SDK for Python (Boto3) to call Amazon Transcribe to make a
transcription of an audio file.

This script is intended to be used with the instructions for getting started in the
Amazon Transcribe Developer Guide here:
    https://docs.aws.amazon.com/transcribe/latest/dg/getting-started.html.
"""
import json
import logging
import time
from pathlib import Path
from typing import Optional

import boto3
import requests
from fire import Fire
from tqdm import tqdm

from utils import upload_file_to_s3


def transcribe_file(job_name, file_uri, language='es-ES', output_folder='subtitles/'):
    transcribe_client = boto3.client('transcribe')
    job = check_the_job(job_name)
    if job is None:
        job = transcribe_client.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={'MediaFileUri': file_uri},
            MediaFormat='mp4',
            LanguageCode=language,
            Settings={
                'ShowSpeakerLabels': True,
                'MaxSpeakerLabels': 10,
                'ShowAlternatives': False,
                # 'MaxAlternatives': 123,
            },
        )
    max_tries = 180
    pbar = tqdm(total=max_tries)
    while max_tries > 0:
        max_tries -= 1
        job = transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
        job_status = job['TranscriptionJob']['TranscriptionJobStatus']
        pbar.set_description(f'{job_name} status: {job_status}')
        pbar.update(1)
        if job_status in ['COMPLETED', 'FAILED']:
            logging.info(f"Job {job_name} is {job_status}.")
            if job_status == 'COMPLETED':
                logging.debug(
                    f"Download the transcript from\n"
                    f"\t{job['TranscriptionJob']['Transcript']['TranscriptFileUri']}.")
                response = requests.get(job['TranscriptionJob']['Transcript']['TranscriptFileUri'])
                with open(f'{output_folder}/{job_name}.json', 'w') as f:
                    result = response.json()
                    json.dump(result, f)
                return result
            return None
        # else:
        # print(f"Waiting for {job_name}. Current status is {job_status}.")
        time.sleep(10)


def check_the_job(job_name: str) -> Optional[dict]:
    transcribe_client = boto3.client('transcribe')
    try:
        job = transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
        job = job['TranscriptionJob']
        if job['TranscriptionJobStatus'] == 'FAILED':
            logging.error(f"Job {job_name} failed.")
            logging.error(f"Error message: {job['FailureReason']}")
        elif job['TranscriptionJobStatus'] == 'COMPLETED':
            logging.info(f"Job {job_name} completed.")
            return job
    except Exception as e:
        logging.error(f"Job {job_name} does not exist.")
    return None


def transcribe(file_uri: str, language='es-ES', subtitles_folder='./artifacts/subtitles/') -> Optional[dict]:
    project_name = Path(file_uri).name
    Path(subtitles_folder).mkdir(exist_ok=True)
    if not file_uri.startswith('s3://'):
        s3_uri = upload_file_to_s3(file_uri)
    else:
        s3_uri = file_uri
    return transcribe_file(project_name, s3_uri, language, subtitles_folder)


def transcribe_cli(file_uri: str):
    result = transcribe(file_uri)
    result = None
    if result is not None:
        print(json.dumps(result, indent=4))


if __name__ == '__main__':
    Fire(transcribe_cli)
