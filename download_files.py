import requests
from canvasapi import Canvas
import config
from pathvalidate import sanitize_filename
from canvasapi.exceptions import Unauthorized, ResourceDoesNotExist
import os
import time
import json

from canvasapi.canvas_object import CanvasObject
from canvasapi.file import File
from canvasapi.paginated_list import PaginatedList
from canvasapi.util import combine_kwargs

canvas = Canvas(config.API_URL, config.API_KEY)

headers = {'Authorization': f'Bearer {config.API_KEY}'}
_path = 'C://Users/jdundas/Documents/Course-Files'
_names = []

class MediaObject(CanvasObject):
    pass


def get_media_objects(self, *args, **kwargs):
    return PaginatedList(
        MediaObject,
        self._requester,
        "GET",
        "courses/{}/media_objects".format(self.id),
        {"course_id": self.id},
        _kwargs=combine_kwargs(**kwargs),
    )

def make_path():
    return os.path.join(
        _path, *[sanitize_filename(n) for n in _names])


def _mkdir(path):
    return os.makedirs(path, exist_ok=True)

def handle_media_video(self, item):
    media_name = item.title
    media_path = os.path.join(self.path, media_name)
    sources = item.media_sources
    sources.sort(key=lambda s: int(s['size']), reverse=True)
    media_url = sources[0]['url']
    self._dl(media_url, media_path)

#TODO: Check if folder/file exist, if true - skip
def _should_write(path):
    # Ensure folder exists before writing
    if os.path.exists(path):
        return False
    else:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        return True

def _get_user():
    return canvas.get_current_user()

def _get_current_courses(user):
    print('Getting Courses...')
    return user.get_courses()

def _download_file(file):
    pass

def download_files(courses):
    pass

user = _get_user()
courses = _get_current_courses(user)

def download_files():
    path = make_path()
    for course in courses:
        try:
            print('Getting folders for ' + str(course))
            folders = course.get_folders()
            for folder in folders:
                try:
                    files = folder.get_files()
                    for file in files:
                        try:
                            f_name = file.title
                        except AttributeError:
                            try:
                                f_name = file.display_name
                            except:
                                import pdb
                                pdb.set_trace()
                        c_path = str(course).split('-')[0][:6]
                        fp = c_path + '/' + str(folder) + '/' + f_name
                        f_path = os.path.join(path, fp)

                        if _should_write(f_path):
                            try:
                                file.download(f_path)
                            except (Unauthorized, ResourceDoesNotExist) as e:
                                print(f"file not accesible")
                                print(str(e))
                except (Unauthorized, ResourceDoesNotExist) as e:
                    print("Folder not accesile...")
        except:
            print('Course not available...')

def download_media():
    pass

download_files()