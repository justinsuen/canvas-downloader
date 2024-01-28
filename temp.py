
import os
import re
import requests

from canvasapi import Canvas
import config
from pathvalidate import sanitize_filename
from canvasapi.exceptions import Unauthorized, ResourceDoesNotExist

canvas = Canvas(config.API_URL, config.API_KEY)

headers = {'Authorization': f'Bearer {config.API_KEY}'}
# _path = '/home/voldemort/Documents/Course-Notes'
_path = './output/'


def _getUser():
    return canvas.get_current_user()


def _getCourses(user):
    return user.get_courses(include="term")


def _getCurrentCourses(user):
    return user.get_courses(include="term", enrollment_status='active')


def _mkDir(path):
    return os.makedirs(os.path.dirname(path), exist_ok=True)


def _shouldWrite(path):
    # Ensure folder exists before writing
    if os.path.exists(path):
        return False
    else:
        _mkDir(path)
        return True


def _downloadFile(path):
    if _shouldWrite(path):
        try:
            file.download(file_path)
        except (Unauthorized, ResourceDoesNotExist) as e:
            print(f"file not accesible")
            print(str(e))


user = _getUser()
courses = _getCourses(user)
user_id = user.id

for course in courses:
    if not hasattr(course, "name") or not hasattr(course, "term"):
        continue
    else:
        # Course Code
        course_code = sanitize_filename(course.course_code)

        # Course Term
        course_term = course.term["name"].replace(' ', '-')

        # Course Directory
        course_dir = os.path.join(_path, course_term, course_code)

        # Create Directory
        if not os.path.exists(course_dir):
            os.makedirs(course_dir)

        sub_dirs = ['/powerpoints', '/files', '/assignments', '/syllabus']
        # Create Sub-Directories
        for sub_dir in sub_dirs:
            dir = course_dir + sub_dir
            if not os.path.exists(dir):
                os.makedirs(dir)

        # Get Files
        files = course.get_files()

        # Sort Files
        for file in files:
            try:
                filename = file.title
            except AttributeError:
                try:
                    filename = file.display_name
                except:
                    import pdb
                    pdb.set_trace()

            # Download Powerpoints
            if '.ppt' in filename:
                file_path = os.path.join(
                    course_dir, 'powerpoints', filename)
                _downloadFile(file_path)

            # Download Syllabus
            elif 'syllabus' in filename.lower():
                file_path = os.path.join(
                    course_dir, 'syllabus', filename)
                _downloadFile(file_path)

            # Download Extra Files
            else:
                file_path = os.path.join(
                    course_dir, 'files', filename)
                _downloadFile(file_path)

            # Get Assignments
                assignment_views = []

    # TODO: Get all assignments
    # TODO: Get all media files
