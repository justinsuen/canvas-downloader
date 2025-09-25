from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
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

API_PORT = int(os.environ.get('API_PORT', 8000))
API_HOST = os.environ.get('API_HOST', '0.0.0.0')

FRONTEND_URLS = [
    f"http://localhost:3000",
    f"http://127.0.0.1:3000",
    # Add more frontend URLs if needed
]

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')

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

# Global variables for tracking downloads
active_downloads = {}
download_locks = {}

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
    def __init__(self, download_id, api_url, api_key, output_path, selected_courses, socket_id):
        self.download_id = download_id
        self.api_url = api_url
        self.api_key = api_key
        self.output_path = output_path
        self.selected_courses = selected_courses
        self.socket_id = socket_id
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
        socketio.emit('download_log', log_entry, room=self.socket_id)
        logger.info(f"[{self.download_id}] {message}")
        
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
def get_courses():
    try:
        data = request.json
        api_url = data.get('apiUrl')
        api_key = data.get('apiKey')
        
        if not api_url or not api_key:
            return jsonify({'error': 'API URL and API key are required'}), 400
            
        # Initialize Canvas
        canvas = Canvas(api_url, api_key)
        user = canvas.get_current_user()
        
        # Get courses with additional includes
        courses = list(user.get_courses(
            include=["term", "course_progress", "storage_quota_used_mb", "total_students"],
            enrollment_status='active'
        ))
        
        # Format courses for frontend
        course_list = []
        for course in courses:
            try:
                # Safely get course attributes with defaults
                course_name = getattr(course, 'name', 'Unnamed Course')
                course_code = getattr(course, 'course_code', 'No Code')
                
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
        
        return jsonify({
            'courses': course_list,
            'user': {
                'name': getattr(user, 'name', 'Unknown User'),
                'id': getattr(user, 'id', 0)
            }
        })
        
    except Unauthorized:
        logger.error("Canvas API authentication failed")
        return jsonify({'error': 'Invalid Canvas API credentials'}), 401
    except CanvasException as e:
        logger.error(f"Canvas API error: {str(e)}")
        return jsonify({'error': f'Canvas API error: {str(e)}'}), 500
    except Exception as e:
        logger.error(f"Error fetching courses: {str(e)}")
        return jsonify({'error': f'Failed to fetch courses: {str(e)}'}), 500

@app.route('/api/download/start', methods=['POST'])
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
        download_manager = DownloadManager(
            download_id, api_url, api_key, output_path, selected_courses, socket_id
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