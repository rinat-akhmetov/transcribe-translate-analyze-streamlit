from operator import itemgetter
from typing import NamedTuple

import cv2
import numpy as np
from fire import Fire
from insightface.app import FaceAnalysis
from tqdm import tqdm

app = FaceAnalysis(providers=['CUDAExecutionProvider', 'CPUExecutionProvider'])
app.prepare(ctx_id=0, det_size=(640, 640))
THRESHOLD = 0.6


class Face(NamedTuple):
    bbox: np.ndarray
    kps: np.ndarray
    det_score: float
    landmark_3d_68: np.ndarray
    landmark_2d_106: np.ndarray
    pose: np.ndarray
    gender: int
    age: int
    embedding: np.ndarray


class Person:
    face: Face
    img: np.ndarray
    diag: float

    def resized_img(self, size=100):
        return cv2.resize(self.img, (size, size))

    def __init__(self, img, diag, face):
        self.face: Face = face
        self.diag: float = diag
        self.img: np.ndarray = img
        self.name: str = ''
        self.counter: int = 1


def cosine_similarity(x, y):
    return np.dot(x, y) / (np.sqrt(np.dot(x, x)) * np.sqrt(np.dot(y, y)))


first_item = itemgetter(0)


def diag_bbox(face):
    return np.linalg.norm(face.bbox[:2] - face.bbox[2:])


def sort_faces(faces) -> list:
    img, faces = faces
    persons = []
    for face in faces:
        x1, y1, x2, y2 = [int(x) for x in face.bbox]
        face_img = img[y1:y2, x1:x2]
        persons.append(Person(diag=diag_bbox(face), face=face, img=face_img))
    fd_sorted = sorted(persons, key=lambda x: x.diag, reverse=True)
    return fd_sorted


def process_images(images):
    persons = {}
    for image in images:
        img = cv2.imread(image)
        new_persons = process_media(img)
        for i, person in enumerate(new_persons):
            for name, current_person in persons.items():
                similarity = cosine_similarity(current_person.face.embedding, person.face.embedding)
                if similarity >= THRESHOLD:
                    break
            else:
                persons[f'person #{len(persons)}'] = person

    for name, person in persons.items():
        cv2.imwrite(f"{name}.jpg", person.img)


def process_media(image) -> list:
    faces = (image, [Face(**face) for face in app.get(image)])
    fs = sort_faces(faces)[:2]
    return fs


def generate_frames(file_path):
    # read video by opencv
    cap = cv2.VideoCapture(file_path)
    frame_width = int(cap.get(3))
    frame_height = int(cap.get(4))
    out = cv2.VideoWriter('outpy.avi', cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'), 30, (frame_width, frame_height))
    fps = cap.get(cv2.CAP_PROP_FPS)
    persons = {}
    for name, person in persons.items():
        cv2.imwrite(f"{name}.jpg", person.img)

    pbar = tqdm(total=int(cap.get(cv2.CAP_PROP_FRAME_COUNT)))
    while True:
        pbar.update(1)
        ret, frame = cap.read()
        size = 144
        addition = np.zeros((frame.shape[0], size, 3), dtype=np.uint8)
        if ret:
            new_persons = process_media(frame)
            for i, person in enumerate(new_persons):
                for name, current_person in persons.items():
                    similarity = cosine_similarity(current_person.face.embedding, person.face.embedding)
                    if similarity >= THRESHOLD:
                        current_person.counter += 1
                        break
                else:
                    person.name = f'person #{len(persons)}'
                    persons[person.name] = person

            sorted_persons = sorted(persons.items(), key=lambda x: x[1].counter, reverse=True)
            faces = [person.resized_img(size) for name, person in sorted_persons[:5]]
            if len(faces) > 0:
                addition[:len(faces) * size, :, :] = np.concatenate(faces, axis=0)
            show_frame = np.concatenate((frame, addition), axis=1)
            # cv2.imshow('frame', show_frame)
            out.write(show_frame)
            # if cv2.waitKey(1) & 0xFF == ord('q'):
            #     break
        else:
            break
    cap.release()
    out.release()


if __name__ == '__main__':
    Fire({
        'main': generate_frames,
    })
