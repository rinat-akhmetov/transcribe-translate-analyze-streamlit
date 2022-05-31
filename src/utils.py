import hashlib
import logging
import pickle
from glob import glob
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

from dto import AWSItem


def check_s3_file(bucket_name, project_name):
    s3_client = boto3.client('s3')
    try:
        return s3_client.head_object(Bucket=bucket_name, Key=project_name)
    except ClientError:
        # Not found
        pass
    return False


def upload_file_to_s3(audio_path: str, bucket_name: str = 'lokoai-lambdas-demo'):
    s3_client = boto3.client('s3')
    project_name = Path(audio_path).name
    if not check_s3_file(bucket_name, project_name):
        print('uploading {} to s3'.format(project_name))
        s3_client.upload_file(audio_path, bucket_name, project_name)
    return f's3://{bucket_name}/{project_name}'


def create_markdown(items: list[AWSItem]):
    """
    create markdown from items
    :param items:
    :return:
    """
    result = ''
    for item in items:
        result += f'{item.speaker_label}: {item.content()}\n\n'
    return result


def cache(function):
    def wrapper(*args):
        arguments = '-'.join([str(x) for x in args])
        hash_object = hashlib.sha256(bytes(arguments, "utf-8"))
        h = hash_object.hexdigest()
        Path('cache').mkdir(exist_ok=True)
        if not glob(f'cache/{function.__name__}_{h}.pickle'):
            logging.debug('Cache miss. Making new request.')
            response = function(*args)
            logging.debug('Caching...')
            logging.debug(f'to cache/{function.__name__}_{h}.pickle')
            with open(f'cache/{function.__name__}_{h}.pickle', 'wb') as f:
                pickle.dump(response, f)
        else:
            logging.debug('Cache hit.')
            logging.debug(f'from cache/{function.__name__}_{h}.pickle')
            with open(f'cache/{function.__name__}_{h}.pickle', 'rb') as f:
                response = pickle.load(f)
        return response

    return wrapper
