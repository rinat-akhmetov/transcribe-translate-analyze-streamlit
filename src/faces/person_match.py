import pickle
from glob import glob

from faces.utils import Person


def load_people(people_folder: str) -> list[Person]:
    people_files = glob(f'{people_folder}/*.pickle')
    people = []
    for person_file_path in sorted(people_files):
        print('Loading', person_file_path)
        with open(person_file_path, 'rb') as handle:
            person = pickle.load(handle)
        people.append(person)
    return people
