import pickle
from pathlib import Path
from typing import NamedTuple

import cv2
import numpy as np
import pandas as pd

from dto import Item


class Face(NamedTuple):
    bbox: np.ndarray
    kps: np.ndarray
    det_score: float
    embedding: np.ndarray


class Person:
    face: Face
    faces: list[Face]
    img: np.ndarray
    diag: float
    showed_frames = list[int]

    def save(self, file_path):
        with open(file_path, 'wb') as handle:
            pickle.dump(self, handle, protocol=pickle.HIGHEST_PROTOCOL)

    def mean_face(self):
        return np.mean(list(map(lambda x: x.embedding, self.faces)), axis=0)

    def resized_img(self, size=100):
        return cv2.resize(self.img, (size, size))

    def __str__(self) -> str:
        return f'Person[{self.name} counter:{self.counter} diag:{self.diag} showed_frame len:{len(self.showed_frames)}]'

    def __repr__(self) -> str:
        return self.__str__()

    def __init__(self, img, diag, face):
        self.face: Face = face
        self.diag: float = diag
        self.img: np.ndarray = img
        self.name: str = ''
        self.counter: int = 1
        self.faces = [face]
        self.showed_frames = []
        self._showed_times = []
        self.fps = 30

    def showed_times(self):
        seqs = []
        prev = self.showed_frames[0]
        last_seq = [prev]
        for x in self.showed_frames[1:]:
            if abs(x - prev) <= 2:
                last_seq.append(x)
            else:
                seqs.append(last_seq)
                last_seq = [x]
            prev = x
        seqs.append(last_seq)
        start_times = []
        end_times = []
        for seq in seqs:
            start_times.append(seq[0] / self.fps)
            end_times.append(seq[-1] / self.fps)
        d = {
            'name': [self.name] * len(start_times),
            'start_time': start_times,
            'end_time': end_times
        }
        return pd.DataFrame(d)


def sort_people(people: dict[str, Person]) -> list[Person]:
    """
    Sort people by counter and diag
    :param people:
    :return:
    """
    counters = list(map(lambda x: x.counter, people.values()))
    diags = list(map(lambda x: x.diag, people.values()))
    normalized_counter = lambda person: person.counter - np.mean(counters) / np.max(counters)
    normalized_diag = lambda person: person.diag - np.mean(diags) / np.max(diags)
    sorted_people = sorted(people.values(), key=lambda x: normalized_counter(x) + normalized_diag(x),
                           reverse=True)
    return sorted_people


def save_people_faces(save_directory, persons: dict[str, Person], top_k=5):
    sorted_persons = sort_people(persons)

    Path(save_directory).mkdir(parents=True, exist_ok=True)
    for name, person in sorted_persons[:top_k]:
        person.save(Path(save_directory) / f'{name}.pickle')


def save_translated_items(save_directory, translated_items: list[Item]):
    Path(save_directory).mkdir(parents=True, exist_ok=True)
    for translated_item in translated_items:
        translated_item.save(Path(save_directory) / f'translated_item-{id(translated_items)}.pickle')
