from canvasapi import Canvas
import config
from pathvalidate import sanitize_filename
from canvasapi.exceptions import Unauthorized, ResourceDoesNotExist
import os


canvas = Canvas(config.API_URL, config.API_KEY)

headers = {'Authorization': f'Bearer {config.API_KEY}'}
# _path = '/home/voldemort/Documents/Course-Notes'
_path = './output-old'
_names = []


def makePath():
    return os.path.join(
        _path, *[sanitize_filename(n) for n in _names])


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
    return user.get_courses(enrollment_status='active')


def _getCourses(user):
    print('Getting Courses...')
    return user.get_courses()


def _downloadFile(file, folder_path):
    try:
        f_name = file.title
    except AttributeError:
        try:
            f_name = file.display_name
        except:
            import pdb
            pdb.set_trace()
    fp = folder_path + f_name
    f_path = os.path.join(_path, fp)

    if _shouldWrite(f_path):
        try:
            file.download(f_path)
        except (Unauthorized, ResourceDoesNotExist) as e:
            print(f"file not accesible")
            print(str(e))


def downloadCourseFiles(course, path):
    try:
        print('Getting folders for ' + str(course))
        folders = course.get_folders()
        for folder in folders:
            try:
                files = folder.get_files()
                for file in files:
                    folder_path = str(course).split(
                        '-')[0][:6] + '/' + str(folder) + '/'
                    _downloadFile(file, folder_path)
            except (Unauthorized, ResourceDoesNotExist) as e:
                print("Folder not accesile...")
    except:
        print('Course not available...')


user = _getUser()
courses = _getCourses(user)


def download_files():
    path = makePath()
    for course in courses:
        downloadCourseFiles(course, path)


if __name__ == "__main__":
    download_files()
