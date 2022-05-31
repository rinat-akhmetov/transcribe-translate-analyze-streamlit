import pickle
from typing import List


class Alternative:
    confidence: float
    content: str

    def __init__(self, confidence: str, content: str):
        self.confidence = float(confidence)
        self.content = content


class Item:
    start_time: str
    end_time: str
    speaker_label: str
    _content: str

    def __init__(self, speaker_label: str, start_time: str = None, end_time: str = None):
        self.start_time = None
        if start_time is not None:
            self.start_time = float(start_time)
        self.end_time = None
        if end_time is not None:
            self.end_time = float(end_time)
        self.speaker_label = speaker_label

    def __str__(self):
        return f'{self.start_time} - {self.end_time} {self.content()}'

    def __repr__(self):
        return self.__str__()

    def content(self):
        return self._content

    def save(self, file_path):
        with open(file_path, 'wb') as handle:
            pickle.dump(self, handle, protocol=pickle.HIGHEST_PROTOCOL)


class AWSItem(Item):
    _type: str
    alternatives: List[Alternative]

    def content(self) -> str:
        return ' '.join([alternative.content for alternative in self.alternatives])

    def __init__(self, type: str, alternatives: List[Alternative], start_time: str = None, end_time: str = None,
                 speaker_label: str = None):
        self._type = type
        self.alternatives = []
        super().__init__(speaker_label, start_time, end_time)
        for alternative in alternatives:
            self.alternatives.append(Alternative(**alternative))

    @property
    def type(self):
        return self._type


class SpeakerItem:
    start_time: float
    end_time: float
    speaker_label: str

    def __init__(self, start_time: str, end_time: str, speaker_label: str):
        self.start_time = float(start_time)
        self.end_time = float(end_time)
        self.speaker_label = speaker_label


class SpeakerLabel:
    start_time: float
    end_time: float
    speaker_label: str
    items: List[SpeakerItem]

    def __init__(self, start_time: str, end_time: str, speaker_label: str, items: List[SpeakerItem]):
        self.start_time = float(start_time)
        self.end_time = float(end_time)
        self.speaker_label = speaker_label
        self.items = []
        for item in items:
            self.items.append(SpeakerItem(**item))
