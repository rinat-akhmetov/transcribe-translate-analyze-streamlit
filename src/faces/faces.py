import cv2
import numpy as np
from fire import Fire
from insightface.app import FaceAnalysis
from tqdm import tqdm

from faces.utils import Person, Face, save_people_faces, sort_people

app = FaceAnalysis(
    allowed_modules=['recognition', 'detection'],
    providers=['CUDAExecutionProvider', 'CPUExecutionProvider']
)
app.prepare(ctx_id=0, det_size=(640, 640))


def cosine_similarity(x, y) -> float:
    """"
    Calculate cosine similarity between two vectors
    """
    return np.dot(x, y) / (np.sqrt(np.dot(x, x)) * np.sqrt(np.dot(y, y)))


def diag_bbox(face: Face) -> float:
    """
    Calculate diagonal of bounding box
    :param face:
    :return:
    """
    return np.linalg.norm(face.bbox[:2] - face.bbox[2:])


def create_people(img: np.array, faces: list[Face]) -> list[Person]:
    """
    Create Person objects from list of Face objects
    :param img:
    :param faces:
    :return:
    """
    persons = []
    for face in faces:
        x1, y1, x2, y2 = [int(x) for x in face.bbox]
        face_img = img[y1:y2, x1:x2]
        persons.append(Person(diag=diag_bbox(face), face=face, img=face_img))
    fd_sorted = list(sorted(persons, key=lambda x: x.diag, reverse=True))
    return fd_sorted


def process_media(image: np.array) -> list[Person]:
    """
    Process media and return list of Person objects
    :param image:
    :return:
    """
    faces = [Face(**face) for face in app.get(image)]
    people = create_people(image, faces)
    return people


def generate_frames(file_path) -> np.array:
    """
    Generator for frames from video
    :param file_path:
    :return:
    """
    # read video by opencv
    cap = cv2.VideoCapture(file_path)

    pbar = tqdm(total=int(cap.get(cv2.CAP_PROP_FRAME_COUNT)))
    while True:
        pbar.update(1)
        ret, frame = cap.read()
        if ret:
            yield frame
        else:
            break
    cap.release()


def process(file_path, threshold=0.6):
    """"
    Process video and return list of Person objects
    :param threshold:
    :param file_path:
    """
    # read video by opencv
    frame_number = 0
    persons: dict[str, Person] = {}

    for frame in generate_frames(file_path):
        frame_number += 1
        new_persons = process_media(frame)
        size = 144
        right_faces_panel = np.zeros((frame.shape[0], size, 3), dtype=np.uint8)
        for i, person in enumerate(new_persons):
            for name, current_person in persons.items():
                similarity = cosine_similarity(current_person.mean_face(), person.face.embedding)
                if similarity >= threshold:
                    current_person.faces.append(person.face)
                    current_person.showed_frames.append(frame_number)
                    current_person.counter += 1
                    if person.diag > current_person.diag:
                        current_person.img = person.img
                        current_person.diag = person.diag
                    break
            else:
                person.name = f'person #{len(persons)}'
                person.showed_frames.append(frame_number)
                persons[person.name] = person

        sorted_persons = sort_people(persons)

        faces = [person.resized_img(size) for person in sorted_persons[:5]]
        print(sorted_persons[:5])
        if len(faces) > 0:
            right_faces_panel[:len(faces) * size, :, :] = np.concatenate(faces, axis=0)
        show_frame = np.concatenate((frame, right_faces_panel), axis=1)
        cv2.imshow('frame', show_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    save_people_faces('people', persons, top_k=5)
    print('frame_number', frame_number)
    with open('frame_number.txt', 'w') as f:
        f.write(str(frame_number))


if __name__ == '__main__':
    Fire(process)
