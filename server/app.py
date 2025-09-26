from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
import requests
import logging
from pathvalidate import sanitize_filename
from canvasapi import Canvas
from canvasapi.exceptions import Unauthorized, ResourceDoesNotExist, CanvasException
import threading
import time
from datetime import datetime
import json
import uuid

# Configuration
from dotenv import load_dotenv
load_dotenv()

# Environment detection
FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
IS_PRODUCTION = FLASK_ENV == 'production'

API_PORT = int(os.environ.get('API_PORT', 8000))
API_HOST = os.environ.get('API_HOST', '0.0.0.0')

# CORS configuration based on environment
if IS_PRODUCTION:
    # Production: Use environment variable for allowed origins
    allowed_origins = os.environ.get('ALLOWED_ORIGINS', '')
    FRONTEND_URLS = [origin.strip() for origin in allowed_origins.split(',') if origin.strip()]
    if not FRONTEND_URLS:
        raise ValueError("ALLOWED_ORIGINS environment variable must be set in production")
else:
    # Development: Allow localhost on port 3000
    FRONTEND_URLS = [
        f"http://localhost:3000",
        f"http://127.0.0.1:3000"
    ]

app = Flask(__name__)

# Secret key configuration
SECRET_KEY = os.environ.get('SECRET_KEY')
if IS_PRODUCTION and (not SECRET_KEY or SECRET_KEY == 'your-secret-key-change-in-production'):
    raise ValueError("SECRET_KEY environment variable must be set to a secure value in production")
app.config['SECRET_KEY'] = SECRET_KEY or 'dev-key-not-secure'

# HTTPS enforcement in production
if IS_PRODUCTION:
    @app.before_request
    def force_https():
        if not request.is_secure and os.environ.get('FORCE_HTTPS', 'true').lower() == 'true':
            return redirect(request.url.replace('http://', 'https://'), code=301)

# Configure CORS to allow WebSocket connections
CORS(app, resources={
    r"/*": {
        "origins": FRONTEND_URLS,
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Initialize SocketIO with proper CORS settings
socketio = SocketIO(app, cors_allowed_origins=FRONTEND_URLS, logger=True, engineio_logger=True)

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["1000 per day", "100 per hour"]
)

# Global variables for tracking downloads
active_downloads = {}
download_locks = {}

# Rate limiting tracking
course_processing_counts = {}  # {ip: {'count': N, 'reset_time': timestamp}}
file_download_counts = {}      # {ip: {'hourly': N, 'daily': N, 'hour_reset': timestamp, 'day_reset': timestamp}}

def check_course_processing_limit(client_ip, course_count):
    """Check if client can process this many courses (100/hour limit)"""
    now = time.time()

    if client_ip not in course_processing_counts:
        course_processing_counts[client_ip] = {'count': 0, 'reset_time': now + 3600}

    # Reset if hour has passed
    if now > course_processing_counts[client_ip]['reset_time']:
        course_processing_counts[client_ip] = {'count': 0, 'reset_time': now + 3600}

    # Check if adding these courses would exceed limit
    current_count = course_processing_counts[client_ip]['count']
    if current_count + course_count > 100:
        return False, f"Course processing limit exceeded. You can process {100 - current_count} more courses this hour."

    # Update count
    course_processing_counts[client_ip]['count'] += course_count
    return True, None

def check_file_download_limit(client_ip, file_count=1):
    """Check if client can download files (500/hour, 2000/day limits)"""
    now = time.time()

    if client_ip not in file_download_counts:
        file_download_counts[client_ip] = {
            'hourly': 0, 'daily': 0,
            'hour_reset': now + 3600, 'day_reset': now + 86400
        }

    counts = file_download_counts[client_ip]

    # Reset hourly if hour has passed
    if now > counts['hour_reset']:
        counts['hourly'] = 0
        counts['hour_reset'] = now + 3600

    # Reset daily if day has passed
    if now > counts['day_reset']:
        counts['daily'] = 0
        counts['day_reset'] = now + 86400

    # Check limits
    if counts['hourly'] + file_count > 500:
        return False, f"Hourly file download limit exceeded. You can download {500 - counts['hourly']} more files this hour."

    if counts['daily'] + file_count > 2000:
        return False, f"Daily file download limit exceeded. You can download {2000 - counts['daily']} more files today."

    # Update counts
    counts['hourly'] += file_count
    counts['daily'] += file_count
    return True, None

def sanitize_log_message(message):
    """Remove API keys and sensitive data from log messages"""
    import re
    if isinstance(message, str):
        # Remove API keys (40+ character hex strings)
        message = re.sub(r'[a-f0-9]{40,}', '[API_KEY_REDACTED]', message, flags=re.IGNORECASE)
        # Remove URLs with tokens
        message = re.sub(r'access_token=[^&\s]+', 'access_token=[REDACTED]', message, flags=re.IGNORECASE)
    return message

def emit_log_to_client(message, log_type='info', socket_id=None):
    """Helper function to emit logs to frontend via Socket.IO"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    sanitized_message = sanitize_log_message(message)

    log_entry = {
        'message': sanitized_message,
        'type': log_type,
        'timestamp': timestamp
    }

    if socket_id:
        socketio.emit('download_log', log_entry, room=socket_id)
        logger.info(f"[Socket {socket_id[:8]}] {sanitized_message}")
    else:
        logger.info(f"[No Socket] {sanitized_message}")

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('canvas_downloader.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DownloadManager:
    def __init__(self, download_id, api_url, api_key, output_path, selected_courses, socket_id, client_ip):
        self.download_id = download_id
        self.api_url = api_url
        self.api_key = api_key
        self.output_path = output_path
        self.selected_courses = selected_courses
        self.socket_id = socket_id
        self.client_ip = client_ip
        self.canvas = None
        self.user = None
        self.status = 'initializing'
        self.progress = {'current': 0, 'total': 0, 'current_file': ''}
        self.logs = []
        self.should_stop = False
        
    def emit_progress(self, data):
        """Emit progress update to the specific client"""
        socketio.emit('download_progress', data, room=self.socket_id)
        
    def emit_log(self, message, log_type='info'):
        """Emit log message to the specific client"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = {
            'message': message,
            'type': log_type,
            'timestamp': timestamp
        }
        self.logs.append(log_entry)
        emit_log_to_client(message, log_type, self.socket_id)
        
    def initialize_canvas(self):
        """Initialize Canvas API connection"""
        try:
            self.canvas = Canvas(self.api_url, self.api_key)
            self.user = self.canvas.get_current_user()
            self.emit_log(f'Connected to Canvas as {self.user.name}', 'success')
            return True
        except Exception as e:
            self.emit_log(f'Failed to connect to Canvas: {str(e)}', 'error')
            return False
            
    def ensure_directory(self, path):
        """Create directory if it doesn't exist"""
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            return True
        except Exception as e:
            self.emit_log(f'Failed to create directory {path}: {str(e)}', 'error')
            return False
            
    def should_download_file(self, file_path):
        """Check if file should be downloaded (doesn't exist)"""
        return not os.path.exists(file_path)
        
    def download_file(self, file, file_path, course_code):
        """Download a single file"""
        if self.should_stop:
            return False

        # Check file download rate limit
        can_download, limit_message = check_file_download_limit(self.client_ip)
        if not can_download:
            self.emit_log(limit_message, 'error')
            return False  # Stop downloading due to rate limit

        try:
            # Get file name safely
            try:
                file_name = file.display_name
            except AttributeError:
                file_name = getattr(file, 'filename', f'file_{file.id}')
                
            file_name = sanitize_filename(file_name)
            full_path = os.path.join(file_path, file_name)
            
            if not self.should_download_file(full_path):
                self.emit_log(f'Skipping existing file: {file_name}', 'info')
                return True
                
            if not self.ensure_directory(full_path):
                return False
                
            # Update progress
            self.progress['current_file'] = f"{course_code}/{file_name}"
            self.emit_progress(self.progress)
            
            # Download file
            file_size = getattr(file, 'size', 0)
            if file_size and file_size > 100000000:  # 100MB
                self._download_large_file(file, full_path)
            else:
                file.download(full_path)
                
            self.emit_log(f'Downloaded: {file_name}', 'success')
            return True
            
        except (Unauthorized, ResourceDoesNotExist) as e:
            self.emit_log(f'Access denied for file {file_name}: {str(e)}', 'warning')
            return True  # Continue with other files
        except Exception as e:
            self.emit_log(f'Failed to download {file_name}: {str(e)}', 'error')
            return True  # Continue with other files
            
    def _download_large_file(self, file, file_path):
        """Download large files with streaming"""
        try:
            response = requests.get(file.url, stream=True, timeout=30)
            response.raise_for_status()
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if self.should_stop:
                        break
                    f.write(chunk)
                    
        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)  # Remove partial download
            raise e
            
    def download_course_files(self, course, course_dir, course_code):
        """Download all files for a course"""
        try:
            folders = list(course.get_folders())
            self.emit_log(f'Found {len(folders)} folders in {course_code}', 'info')
            
            for folder in folders:
                if self.should_stop:
                    break
                    
                try:
                    folder_name = sanitize_filename(str(folder.name))
                    folder_path = os.path.join(course_dir, folder_name)
                    
                    files = list(folder.get_files())
                    self.emit_log(f'Processing folder "{folder_name}" with {len(files)} files', 'info')
                    
                    for file in files:
                        if self.should_stop:
                            break
                            
                        self.download_file(file, folder_path, course_code)
                        self.progress['current'] += 1
                        self.emit_progress(self.progress)
                        
                except Exception as e:
                    self.emit_log(f'Error processing folder {folder.name}: {str(e)}', 'warning')
                    continue
                    
        except Exception as e:
            self.emit_log(f'Failed to access course files for {course_code}: {str(e)}', 'error')
            
    def download_assignment_submissions(self, course, course_dir, course_code):
        """Download assignment submissions for a course"""
        try:
            assignments = list(course.get_assignments())
            assignment_dir = os.path.join(course_dir, 'assignments')
            
            if not assignments:
                return
                
            self.emit_log(f'Found {len(assignments)} assignments in {course_code}', 'info')
            
            for assignment in assignments:
                if self.should_stop:
                    break
                    
                try:
                    submission = assignment.get_submission(self.user.id)
                    
                    if hasattr(submission, 'attachments') and submission.attachments:
                        for attachment in submission.attachments:
                            if self.should_stop:
                                break
                                
                            try:
                                attachment_name = sanitize_filename(attachment.filename)
                                file_path = os.path.join(assignment_dir, attachment_name)
                                
                                if not self.should_download_file(file_path):
                                    continue
                                    
                                if not self.ensure_directory(file_path):
                                    continue
                                    
                                # Update progress
                                self.progress['current_file'] = f"{course_code}/assignments/{attachment_name}"
                                self.emit_progress(self.progress)
                                
                                # Download attachment
                                response = requests.get(attachment.url, allow_redirects=True, timeout=30)
                                response.raise_for_status()
                                
                                with open(file_path, 'wb') as f:
                                    f.write(response.content)
                                    
                                self.emit_log(f'Downloaded assignment: {attachment_name}', 'success')
                                self.progress['current'] += 1
                                self.emit_progress(self.progress)
                                
                            except Exception as e:
                                self.emit_log(f'Failed to download attachment {attachment.filename}: {str(e)}', 'warning')
                                
                except Exception as e:
                    self.emit_log(f'Error processing assignment {assignment.name}: {str(e)}', 'warning')
                    continue
                    
        except Exception as e:
            self.emit_log(f'Failed to access assignments for {course_code}: {str(e)}', 'error')
            
    def calculate_total_files(self, courses):
        """Calculate total number of files to download"""
        total = 0
        self.emit_log('Calculating total files...', 'info')
        
        for course in courses:
            if self.should_stop:
                break
                
            try:
                # Count course files
                folders = list(course.get_folders())
                for folder in folders:
                    try:
                        files = list(folder.get_files())
                        total += len(files)
                    except:
                        continue
                        
                # Count assignment attachments
                try:
                    assignments = list(course.get_assignments())
                    for assignment in assignments:
                        try:
                            submission = assignment.get_submission(self.user.id)
                            if hasattr(submission, 'attachments') and submission.attachments:
                                total += len(submission.attachments)
                        except:
                            continue
                except:
                    continue
                    
            except Exception as e:
                self.emit_log(f'Error counting files for {course.course_code}: {str(e)}', 'warning')
                continue
                
        return total
        
    def run_download(self):
        """Main download process"""
        try:
            self.status = 'connecting'
            self.emit_log('Starting download process...', 'info')
            
            # Initialize Canvas connection
            if not self.initialize_canvas():
                self.status = 'error'
                return
                
            # Get selected courses
            self.status = 'fetching_courses'
            self.emit_log('Fetching course information...', 'info')
            
            all_courses = list(self.user.get_courses(include="term"))
            selected_course_objects = [c for c in all_courses if c.id in self.selected_courses]
            
            if not selected_course_objects:
                self.emit_log('No valid courses found for download', 'error')
                self.status = 'error'
                return
                
            # Calculate total files
            self.status = 'calculating'
            total_files = self.calculate_total_files(selected_course_objects)
            self.progress['total'] = total_files
            self.emit_log(f'Found {total_files} files across {len(selected_course_objects)} courses', 'info')
            
            # Start downloading
            self.status = 'downloading'
            self.emit_log('Starting file downloads...', 'info')
            
            for course in selected_course_objects:
                if self.should_stop:
                    break
                    
                try:
                    course_code = sanitize_filename(course.course_code)
                    course_term = course.term["name"].replace(' ', '-') if hasattr(course, 'term') and course.term else 'Unknown-Term'
                    course_dir = os.path.join(self.output_path, course_term, course_code)
                    
                    self.emit_log(f'Processing course: {course.name} ({course_code})', 'info')
                    
                    # Download course files
                    self.download_course_files(course, course_dir, course_code)
                    
                    # Download assignment submissions
                    self.download_assignment_submissions(course, course_dir, course_code)
                    
                    self.emit_log(f'Completed course: {course_code}', 'success')
                    
                except Exception as e:
                    self.emit_log(f'Error processing course {course.name}: {str(e)}', 'error')
                    continue
                    
            # Finish
            if self.should_stop:
                self.status = 'stopped'
                self.emit_log('Download stopped by user', 'warning')
            else:
                self.status = 'completed'
                self.emit_log(f'Download completed! Downloaded {self.progress["current"]} files', 'success')
                
        except Exception as e:
            self.status = 'error'
            self.emit_log(f'Download failed: {str(e)}', 'error')
            
        finally:
            # Cleanup
            if self.download_id in active_downloads:
                del active_downloads[self.download_id]

# API Routes
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/api/courses', methods=['POST'])
@limiter.limit("3 per minute")
def get_courses():
    try:
        data = request.json
        api_url = data.get('apiUrl')
        api_key = data.get('apiKey')
        socket_id = data.get('socketId')

        emit_log_to_client("Received request to fetch courses from Canvas API", 'info', socket_id)

        if not api_url or not api_key:
            emit_log_to_client("Missing API URL or API key in request", 'error', socket_id)
            return jsonify({'error': 'API URL and API key are required'}), 400

        emit_log_to_client(f"Initializing Canvas API connection to {api_url}", 'info', socket_id)
        # Initialize Canvas
        canvas = Canvas(api_url, api_key)

        emit_log_to_client("Fetching current user information from Canvas", 'info', socket_id)
        user = canvas.get_current_user()
        emit_log_to_client(f"Successfully authenticated as user: {user.name}", 'success', socket_id)

        # Emit user info immediately to update connection status
        if socket_id:
            user_info = {
                'name': getattr(user, 'name', 'Unknown User'),
                'id': getattr(user, 'id', 0)
            }
            socketio.emit('user_authenticated', {'user': user_info}, room=socket_id)

        emit_log_to_client("Fetching user's courses from Canvas API...", 'info', socket_id)
        # Get courses with additional includes
        courses = list(user.get_courses(
            include=["term", "course_progress", "storage_quota_used_mb", "total_students"],
            enrollment_status='active'
        ))
        emit_log_to_client(f"Retrieved {len(courses)} active courses from Canvas", 'success', socket_id)

        # Check course processing rate limit
        client_ip = get_remote_address()
        can_process, limit_message = check_course_processing_limit(client_ip, len(courses))
        if not can_process:
            emit_log_to_client(limit_message, 'error', socket_id)
            return jsonify({'error': limit_message}), 429

        # Format courses for frontend
        course_list = []
        total_courses = len(courses)

        for course_index, course in enumerate(courses, 1):
            try:
                # Safely get course attributes with defaults
                course_name = getattr(course, 'name', 'Unnamed Course')
                course_code = getattr(course, 'course_code', 'No Code')

                # Emit progress update
                if socket_id:
                    progress_data = {
                        'current': course_index,
                        'total': total_courses,
                        'course_name': course_name
                    }
                    socketio.emit('course_fetch_progress', progress_data, room=socket_id)
                
                # Handle term safely
                term_info = {'name': 'Unknown Term'}
                if hasattr(course, 'term') and course.term:
                    if isinstance(course.term, dict):
                        term_info = course.term
                    else:
                        term_info = {'name': getattr(course.term, 'name', 'Unknown Term')}
                
                # Get folder and file counts (simplified for performance)
                folder_count = 0
                file_count = 0
                
                try:
                    # Try to get a rough count of folders and files
                    folders = list(course.get_folders())
                    folder_count = len(folders)
                    
                    # Sample first few folders for file count estimate
                    sample_folders = folders[:3] if len(folders) > 3 else folders
                    sample_file_count = 0
                    
                    for folder in sample_folders:
                        try:
                            files = list(folder.get_files())
                            sample_file_count += len(files)
                        except Exception as e:
                            logger.warning(f"Could not count files in folder {folder}: {str(e)}")
                            continue
                    
                    # Estimate total files based on sample
                    if len(folders) > 0 and len(sample_folders) > 0:
                        file_count = int(sample_file_count * (len(folders) / len(sample_folders)))
                    else:
                        file_count = sample_file_count
                        
                    # Ensure minimum count for UI
                    file_count = max(file_count, 1)
                    
                except Exception as e:
                    logger.warning(f"Could not count folders/files for course {course_name}: {str(e)}")
                    # Use default estimates
                    folder_count = 5
                    file_count = 20
                
                course_data = {
                    'id': getattr(course, 'id', 0),
                    'name': course_name,
                    'course_code': course_code,
                    'term': term_info,
                    'folder_count': folder_count,
                    'file_count': file_count
                }
                course_list.append(course_data)
                
                logger.info(f"Processed course: {course_name} ({course_code})")
                
            except Exception as e:
                logger.warning(f"Error processing course {getattr(course, 'id', 'unknown')}: {str(e)}")
                continue
                
        logger.info(f"Successfully processed {len(course_list)} courses")
        
        emit_log_to_client(f"Successfully processed {len(course_list)} courses", 'success', socket_id)

        return jsonify({
            'courses': course_list,
            'user': {
                'name': getattr(user, 'name', 'Unknown User'),
                'id': getattr(user, 'id', 0)
            }
        })

    except Unauthorized:
        emit_log_to_client("Canvas API authentication failed - invalid credentials", 'error', socket_id)
        return jsonify({'error': 'Invalid Canvas API credentials'}), 401
    except CanvasException as e:
        emit_log_to_client(f"Canvas API error: {str(e)}", 'error', socket_id)
        return jsonify({'error': f'Canvas API error: {str(e)}'}), 500
    except Exception as e:
        emit_log_to_client(f"Error fetching courses: {str(e)}", 'error', socket_id)
        return jsonify({'error': f'Failed to fetch courses: {str(e)}'}), 500

@app.route('/api/download/start', methods=['POST'])
@limiter.limit("3 per minute")  # Limit download initiation
def start_download():
    try:
        data = request.json
        api_url = data.get('apiUrl')
        api_key = data.get('apiKey')
        output_path = data.get('outputPath', './downloads')
        selected_courses = data.get('selectedCourses', [])
        socket_id = data.get('socketId')
        
        if not all([api_url, api_key, selected_courses, socket_id]):
            return jsonify({'error': 'Missing required parameters'}), 400
            
        # Generate download ID
        download_id = str(uuid.uuid4())
        
        # Create download manager
        client_ip = get_remote_address()
        download_manager = DownloadManager(
            download_id, api_url, api_key, output_path, selected_courses, socket_id, client_ip
        )
        
        # Store in active downloads
        active_downloads[download_id] = download_manager
        
        # Start download in background thread
        thread = threading.Thread(target=download_manager.run_download)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'download_id': download_id,
            'status': 'started'
        })
        
    except Exception as e:
        logger.error(f"Error starting download: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/download/<download_id>/stop', methods=['POST'])
def stop_download(download_id):
    try:
        if download_id in active_downloads:
            active_downloads[download_id].should_stop = True
            return jsonify({'status': 'stopping'})
        else:
            return jsonify({'error': 'Download not found'}), 404
            
    except Exception as e:
        logger.error(f"Error stopping download: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/download/<download_id>/status', methods=['GET'])
def get_download_status(download_id):
    try:
        if download_id in active_downloads:
            manager = active_downloads[download_id]
            return jsonify({
                'status': manager.status,
                'progress': manager.progress,
                'logs': manager.logs[-10:]  # Last 10 log entries
            })
        else:
            return jsonify({'error': 'Download not found'}), 404
            
    except Exception as e:
        logger.error(f"Error getting download status: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Socket.IO events
@socketio.on('connect')
def handle_connect():
    logger.info(f'Client connected: {request.sid}')
    emit('connected', {'status': 'Connected to Canvas Downloader server'})
    
@socketio.on('disconnect')
def handle_disconnect():
    logger.info(f'Client disconnected: {request.sid}')

@socketio.on('join_download')
def handle_join_download(data):
    download_id = data.get('download_id')
    logger.info(f'Client {request.sid} joining download {download_id}')
    if download_id and download_id in active_downloads:
        # Send current status
        manager = active_downloads[download_id]
        emit('download_progress', manager.progress)
        emit('download_status', {'status': manager.status})

@socketio.on('test_connection')
def handle_test_connection(data):
    logger.info(f'Test connection from {request.sid}: {data}')
    emit('test_response', {'status': 'success', 'message': 'Socket.IO working!'})

@socketio.on_error_default
def default_error_handler(e):
    logger.error(f'Socket.IO error: {str(e)}')
    emit('error', {'message': str(e)})

def main():
    """Main entry point for the application"""
    # Create output directory if it doesn't exist
    os.makedirs('./downloads', exist_ok=True)
    
    # Print startup info
    print("="*60)
    print("🚀 Canvas Downloader Backend Starting...")
    print(f"📡 Flask server: http://{API_HOST}:{API_PORT}")
    print(f"🔍 Health check: http://localhost:{API_PORT}/api/health") 
    print(f"🔌 Socket.IO: ws://localhost:{API_PORT}")
    print(f"🌐 Allowed origins: {', '.join(FRONTEND_URLS)}")
    print("="*60)
    
    # Run the application
    socketio.run(app, debug=True, host=API_HOST, port=API_PORT, allow_unsafe_werkzeug=True)

if __name__ == '__main__':
    main()