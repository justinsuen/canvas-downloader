
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


class submissionView():
    id = 0

    attachments = []
    grade = ""
    raw_score = ""
    submission_comments = ""
    total_possible_points = ""
    attempt = 0
    user_id = "no-id"

    preview_url = ""
    ext_url = ""

    def __init__(self):
        self.attachments = []


class attachmentView():
    id = 0

    filename = ""
    url = ""


class assignmentView():
    id = 0

    title = ""
    description = ""
    assigned_date = ""
    due_date = ""
    submissions = []

    html_url = ""
    ext_url = ""
    updated_url = ""

    def __init__(self):
        self.submissions = []


def _getUser():
    return canvas.get_current_user()


def _getCourses(user):
    return user.get_courses(include="term")


def _getCurrentCourses(user):
    return user.get_courses(enrollment_status='active')


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

    # Get all assignments
    assignments = course.get_assignments()

    try:
        for assignment in assignments:
            # Create a new assignment view
            assignment_view = assignmentView()

            # ID
            assignment_view.id = assignment.id if \
                hasattr(assignment, "id") else ""

            # Title
            assignment_view.title = sanitize_filename(str(assignment.name)) if \
                hasattr(assignment, "name") else ""
            # Description
            assignment_view.description = str(assignment.description) if \
                hasattr(assignment, "description") else ""

            # Assigned date
            assignment_view.assigned_date = assignment.created_at_date if \
                hasattr(assignment, "created_at_date") else ""
            # Due date
            assignment_view.due_date = assignment.due_at_date if \
                hasattr(assignment, "due_at_date") else ""

            # HTML Url
            assignment_view.html_url = assignment.html_url if \
                hasattr(assignment, "html_url") else ""
            # External URL
            assignment_view.ext_url = str(assignment.url) if \
                hasattr(assignment, "url") else ""
            # Other URL (more up-to-date)
            assignment_view.updated_url = str(assignment.submissions_download_url).split("submissions?")[0] if \
                hasattr(assignment, "submissions_download_url") else ""

            try:
                try:  # Download all submissions for entire class
                    submissions = assignment.get_submissions()
                    submissions[0]  # Trigger Unauthorized if not allowed
                except Unauthorized:
                    print(
                        "Not authorized to download entire class submissions for this assignment")
                    # Download submission for this user only
                    submissions = [assignment.get_submission(user_id)]
                # throw error if no submissions found at all but without error
                submissions[0]
            except (ResourceDoesNotExist, NameError, IndexError):
                print('Got no submissions from either class or user: {}'.format(user_id))
            except Exception as e:
                print("Failed to retrieve submissions for this assignment")
                print(e.__class__.__name__)
            else:
                try:
                    for submission in submissions:

                        sub_view = submissionView()

                        # Submission ID
                        sub_view.id = submission.id if \
                            hasattr(submission, "id") else 0

                        # My grade
                        sub_view.grade = str(submission.grade) if \
                            hasattr(submission, "grade") else ""
                        # My raw score
                        sub_view.raw_score = str(submission.score) if \
                            hasattr(submission, "score") else ""
                        # Total possible score
                        sub_view.total_possible_points = str(assignment.points_possible) if \
                            hasattr(assignment, "points_possible") else ""
                        # Submission comments
                        sub_view.submission_comments = str(submission.submission_comments) if \
                            hasattr(submission, "submission_comments") else ""
                        # Attempt
                        sub_view.attempt = submission.attempt if \
                            hasattr(submission, "attempt") and submission.attempt is not None else 0
                        # User ID
                        sub_view.user_id = str(submission.user_id) if \
                            hasattr(submission, "user_id") else ""

                        # Submission URL
                        sub_view.preview_url = str(submission.preview_url) if \
                            hasattr(submission, "preview_url") else ""
                        #   External URL
                        sub_view.ext_url = str(submission.url) if \
                            hasattr(submission, "url") else ""

                        try:
                            submission.attachments
                        except AttributeError:
                            print('No attachments')
                        else:
                            for attachment in submission.attachments:
                                attach_view = attachmentView()
                                attach_view.url = attachment["url"]
                                attach_view.id = attachment["id"]
                                attach_view.filename = attachment["filename"]
                                sub_view.attachments.append(attach_view)
                        assignment_view.submissions.append(sub_view)
                except Exception as e:
                    print("Skipping submission that gave the following error:")
                    print(e)

            assignment_views.append(assignment_view)
    except Exception as e:
        print("Skipping course assignments that gave the following error:")
        print(e)

    for assignment in assignment_views:
        for submission in assignment.submissions:
            assignment_title = sanitize_filename(str(assignment.title))
            attachment_dir = os.path.join(
                course_dir, "assignments", assignment_title)
            if (len(assignment.submissions) != 1):
                attachment_dir = os.path.join(
                    attachment_dir, str(submission.user_id))
            if (not os.path.exists(attachment_dir)) and (submission.attachments):
                os.makedirs(attachment_dir)
            for attachment in submission.attachments:
                filepath = os.path.join(attachment_dir, sanitize_filename(str(attachment.id) +
                                        "_" + attachment.filename))
                if not os.path.exists(filepath):
                    print('Downloading attachment: {}'.format(filepath))
                    r = requests.get(attachment.url, allow_redirects=True)
                    with open(filepath, 'wb') as f:
                        f.write(r.content)
                else:
                    print('File already exists: {}'.format(filepath))
