import os
import config
import logging

import requests
import tqdm

from pathvalidate import sanitize_filename
from canvasapi import Canvas
from canvasapi.exceptions import Unauthorized, ResourceDoesNotExist

logging.basicConfig(filename='download.log',  level=logging.DEBUG)

canvas = Canvas(config.API_URL, config.API_KEY)

headers = {'Authorization': f'Bearer {config.API_KEY}'}
# _path = '/home/voldemort/Documents/Course-Notes'
_path = './output-df'

def _mkDir(path):
    return os.makedirs(os.path.dirname(path), exist_ok=True)


def _shouldWrite(path):
    # Ensure folder exists before writing
    if os.path.exists(path):
        return False
    else:
        _mkDir(path)
        return True


def _getUser():
    return canvas.get_current_user()


def _getCurrentCourses(user):
    print('Getting Current Courses...')
    return user.get_courses(include="term", enrollment_status='active')


def _getCourses(user):
    print('Retrieving Courses...')
    return user.get_courses(include="term")


def _downloadFile(file, folder_path):
    try:
        f_name = file.title
    except AttributeError:
        try:
            f_name = file.display_name
        except:
            import pdb
            pdb.set_trace()
    f_path = os.path.join(folder_path + f_name)

    if _shouldWrite(f_path):
        try:
            file.download(f_path)
        except (Unauthorized, ResourceDoesNotExist) as e:
            logging.error('%s file %s not accessible', e, f_name)


def downloadAssignmentSubmissions(course, course_dir):
    # Download Assignments:
    try:
        assignments = list(course.get_assignments())
        assignment_dir = course_dir + '/assignments/'

        if not os.path.exists(assignment_dir):
            _mkDir(assignment_dir)

        for assignment in assignments:
            # Get Submissions
            submissions = assignment.get_submission(user)

            # Download Submission Attachment
            for attachment in submissions.attachments:

                file_path = os.path.join(assignment_dir, sanitize_filename(str(attachment.filename)))

                if not os.path.exists(file_path):
                    r = requests.get(attachment.url, allow_redirects=True)
                    with open(file_path, 'wb') as f:
                        f.write(r.content)

    except:
        logging.error('Unable to get submission file...')


def downloadCourseFiles(course, course_dir, course_code):
    # Download Files
    try:
        folders = course.get_folders()

        for folder in tqdm.tqdm(folders, desc=f'{course_code} Folders', total=len(list(folders)), leave=False):
            try:
                files = folder.get_files()

                for file in files:

                    folder_path = course_dir + '/' + str(folder) + '/'

                    _downloadFile(file, folder_path)

            except:
                logging.error('Course %s folder %s not accessible', course_code, str(folder))
    except:
        logging.error('%s not accessible', course_code)


user = _getUser()
courses = _getCourses(user)

def download_files():
    # Course Iterator
    for course in tqdm.tqdm(courses, desc='Downloading', total=len(list(courses)), leave=False):

        course_code = ''

        # Ensure Course has Name and Term Attributes
        if not hasattr(course, "name") or not hasattr(course, "term"):
            pass
        else:
            # Course Code
            course_code = sanitize_filename(course.course_code)

            # Course Term
            course_term = course.term["name"].replace(' ', '-')

            # Course Directory
            course_dir = os.path.join(_path, course_term, course_code)

        # Download Course Files
        downloadCourseFiles(course, course_dir, course_code)

        # Download Assignment Submissions
        downloadAssignmentSubmissions(course, course_dir)


if __name__ == "__main__":
    download_files()
