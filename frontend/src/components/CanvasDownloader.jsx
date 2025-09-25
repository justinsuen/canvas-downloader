import React, { useState, useEffect } from 'react';
import { Download } from 'lucide-react';
import ConfigurationPanel from './ConfigurationPanel';
import CourseSelector from './CourseSelector';
import LogPanel from './LogPanel';
import Header from './Header';
import io from 'socket.io-client';

const CanvasDownloader = () => {
  const [config, setConfig] = useState({
    apiUrl: '',
    apiKey: '',
    outputPath: './downloads'
  });
  const [courses, setCourses] = useState([]);
  const [selectedCourses, setSelectedCourses] = useState(new Set());
  const [downloadStatus, setDownloadStatus] = useState('idle');
  const [progress, setProgress] = useState({ current: 0, total: 0, currentFile: '' });
  const [logs, setLogs] = useState([]);
  const [showConfig, setShowConfig] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [downloadId, setDownloadId] = useState(null);
  const [socket, setSocket] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [backendConnected, setBackendConnected] = useState(false);
  const [courseProgress, setCourseProgress] = useState({ current: 0, total: 0, course_name: '' });


  const API_PORT = process.env.REACT_APP_API_PORT || 8000;
  const API_HOST = process.env.REACT_APP_API_HOST || 'localhost';

  const API_BASE = `http://${API_HOST}:${API_PORT}`;
  const API_URL = `${API_BASE}/api`;

  // Mock data for demonstration (fallback when backend is not available)
  const mockCourses = [
    {
      id: 1,
      name: 'Computer Science 101',
      course_code: 'CS101',
      term: { name: 'Fall 2024' },
      file_count: 45,
      folder_count: 8
    },
    {
      id: 2,
      name: 'Data Structures and Algorithms',
      course_code: 'CS201',
      term: { name: 'Fall 2024' },
      file_count: 32,
      folder_count: 6
    },
    {
      id: 3,
      name: 'Database Systems',
      course_code: 'CS301',
      term: { name: 'Fall 2024' },
      file_count: 28,
      folder_count: 5
    }
  ];

  // Initialize socket connection
  useEffect(() => {
    console.log('Initializing Socket.IO connection...');

    const newSocket = io(API_BASE, {
      transports: ['websocket', 'polling'],
      timeout: 5000,
      forceNew: true
    });

    setSocket(newSocket);

    newSocket.on('connect', () => {
      console.log('Socket.IO connected with ID:', newSocket.id);
      setIsConnected(true);
      setBackendConnected(true);
      addLog('Connected to Canvas Downloader server', 'success');

      // Test the connection
      newSocket.emit('test_connection', { message: 'Hello from React!' });
    });

    newSocket.on('disconnect', (reason) => {
      console.log('Socket.IO disconnected:', reason);
      setIsConnected(false);
      setBackendConnected(false);
      addLog(`Disconnected from server: ${reason}`, 'warning');
    });

    newSocket.on('connect_error', (error) => {
      console.error('Socket.IO connection error:', error);
      setIsConnected(false);
      setBackendConnected(false);
      addLog(`Connection failed: ${error.message}`, 'error');
    });

    newSocket.on('connected', (data) => {
      console.log('Server welcome message:', data);
      addLog(data.status, 'info');
    });

    newSocket.on('test_response', (data) => {
      console.log('Test response from server:', data);
      addLog('Socket.IO connection test successful!', 'success');
    });

    newSocket.on('download_progress', (data) => {
      console.log('Progress update:', data);
      setProgress(data);
    });

    newSocket.on('download_log', (logEntry) => {
      console.log('Log from server:', logEntry);
      // Ensure server logs also use 24-hour format
      const newDate = new Date();
      if (logEntry.timestamp) {
        const [hours, minutes, seconds] = logEntry.timestamp.split(':');
        newDate.setHours(hours, minutes, seconds);
      }

      console.log(newDate);

      const normalizedLogEntry = {
        ...logEntry,
        timestamp: newDate.toLocaleTimeString('en-GB', { hour12: false })
      };
      setLogs(prev => [...prev, normalizedLogEntry]);
    });

    newSocket.on('user_authenticated', (data) => {
      console.log('User authenticated:', data);
      setCurrentUser(data.user);
      addLog(`Authenticated as ${data.user.name}`, 'success');
    });

    newSocket.on('course_fetch_progress', (data) => {
      console.log('Course fetch progress:', data);
      setCourseProgress(data);
    });

    newSocket.on('error', (error) => {
      console.error('Socket.IO error:', error);
      addLog(`Socket error: ${error.message}`, 'error');
    });

    return () => {
      console.log('Cleaning up Socket.IO connection');
      newSocket.close();
    };
  }, []);

  const addLog = (message, type = 'info') => {
    const timestamp = new Date().toLocaleTimeString('en-GB', { hour12: false });
    setLogs(prev => [...prev, { message, type, timestamp }]);
  };

  // Test backend connection
  const testBackendConnection = async () => {
    try {
      const response = await fetch(`${API_URL}/health`, {
        method: 'GET',
        timeout: 5000
      });

      if (response.ok) {
        setBackendConnected(true);
        addLog('Backend server is running', 'success');
        return true;
      } else {
        throw new Error('Backend not responding');
      }
    } catch (error) {
      setBackendConnected(false);
      addLog('Backend server not available - using demo mode', 'warning');
      return false;
    }
  };

  const fetchCourses = async () => {
    if (!config.apiUrl || !config.apiKey) return;

    setDownloadStatus('loading');
    setCourseProgress({ current: 0, total: 0, course_name: '' }); // Reset progress
    addLog('Fetching courses from Canvas...', 'info');

    // Test backend connection first
    const backendAvailable = await testBackendConnection();

    if (!backendAvailable) {
      setCourses(mockCourses);
      setDownloadStatus('idle');
      addLog('Using demo data - start Flask backend for real functionality', 'warning');
      return;
    }

    try {
      const response = await fetch(`${API_URL}/courses`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          apiUrl: config.apiUrl,
          apiKey: config.apiKey,
          socketId: socket?.id
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to fetch courses');
      }

      const data = await response.json();
      setCourses(data.courses);
      setCurrentUser(data.user);
      addLog(`Found ${data.courses.length} courses for ${data.user.name}`, 'success');
      setDownloadStatus('idle');

    } catch (error) {
      addLog(`Failed to fetch courses: ${error.message}`, 'error');
      setDownloadStatus('error');
      setCourses(mockCourses);
      addLog('Using demo data - check your Canvas API credentials', 'warning');
    }
  };

  const startRealDownload = async () => {
    if (selectedCourses.size === 0) {
      addLog('No courses selected for download', 'error');
      return;
    }

    if (!socket || !isConnected || !backendConnected) {
      addLog('Not connected to server - starting demo mode', 'warning');
      simulateDownload();
      return;
    }

    setDownloadStatus('downloading');
    addLog(`Starting download of ${selectedCourses.size} courses`, 'info');

    try {
      const response = await fetch(`${API_URL}/download/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          apiUrl: config.apiUrl,
          apiKey: config.apiKey,
          outputPath: config.outputPath,
          selectedCourses: Array.from(selectedCourses),
          socketId: socket.id
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to start download');
      }

      const data = await response.json();
      setDownloadId(data.download_id);
      addLog('Real download started successfully!', 'success');

    } catch (error) {
      addLog(`Failed to start download: ${error.message}`, 'error');
      setDownloadStatus('error');
    }
  };

  const stopRealDownload = async () => {
    if (!downloadId) {
      setDownloadStatus('idle');
      setProgress({ current: 0, total: 0, currentFile: '' });
      addLog('Download stopped', 'warning');
      return;
    }

    try {
      const response = await fetch(`${API_URL}/download/${downloadId}/stop`, {
        method: 'POST'
      });

      if (response.ok) {
        addLog('Download stop requested', 'info');
      } else {
        addLog('Failed to stop download, but resetting status', 'warning');
      }
    } catch (error) {
      addLog(`Failed to stop download: ${error.message}`, 'error');
    } finally {
      // Always reset state regardless of API response
      setDownloadStatus('idle');
      setDownloadId(null);
      setProgress({ current: 0, total: 0, currentFile: '' });
    }
  };

  // Fallback simulation for demo mode
  const simulateDownload = async () => {
    const selectedCoursesArray = courses.filter(c => selectedCourses.has(c.id));
    const totalFiles = selectedCoursesArray.reduce((sum, course) => sum + course.file_count, 0);

    setProgress({ current: 0, total: totalFiles, currentFile: '' });
    addLog(`Starting demo download of ${selectedCoursesArray.length} courses (${totalFiles} files)`, 'info');

    let currentFileCount = 0;

    for (const course of selectedCoursesArray) {
      addLog(`Processing course: ${course.name}`, 'info');

      for (let i = 0; i < course.file_count; i++) {
        await new Promise(resolve => setTimeout(resolve, 50)); // Faster for demo
        currentFileCount++;
        const fileName = `file_${i + 1}.pdf`;
        setProgress({
          current: currentFileCount,
          total: totalFiles,
          currentFile: `${course.course_code}/${fileName}`
        });

        if (Math.random() > 0.95) { // Simulate occasional warnings
          addLog(`Warning: Simulated issue with ${fileName}`, 'warning');
        }
      }

      addLog(`Completed downloading ${course.name}`, 'success');
    }

    setDownloadStatus('completed');
    addLog('Demo download completed! Start Flask backend for real downloads.', 'success');
  };

  const handleStartDownload = () => {
    if (backendConnected && socket && isConnected) {
      startRealDownload();
    } else {
      simulateDownload();
    }
  };

  const handleStopDownload = () => {
    if (backendConnected && downloadId) {
      stopRealDownload();
    } else {
      // Handle demo mode or error states
      setDownloadStatus('idle');
      setProgress({ current: 0, total: 0, currentFile: '' });
      setDownloadId(null);
      addLog('Download stopped', 'warning');
    }
  };

  return (
    <div className="h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-6 flex flex-col">
      <div className="w-full max-w-none lg:w-[85%] mx-auto flex flex-col h-full">
        <Header
          showConfig={showConfig}
          setShowConfig={setShowConfig}
          backendConnected={backendConnected}
          isConnected={isConnected}
          currentUser={currentUser}
        />

        <div className="flex flex-col lg:flex-row gap-6 flex-1 min-h-0">
          <CourseSelector
            courses={courses}
            selectedCourses={selectedCourses}
            setSelectedCourses={setSelectedCourses}
            downloadStatus={downloadStatus}
            progress={progress}
            courseProgress={courseProgress}
            startDownload={handleStartDownload}
            stopDownload={handleStopDownload}
            backendConnected={backendConnected}
          />

          <LogPanel
            logs={logs}
            setLogs={setLogs}
            backendConnected={backendConnected}
            isConnected={isConnected}
          />
        </div>
      </div>

      {/* Configuration Panel Overlay */}
      {showConfig && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
          onClick={() => setShowConfig(false)}
        >
          <div
            className="max-w-lg w-full mx-4"
            onClick={(e) => e.stopPropagation()}
          >
            <ConfigurationPanel
              config={config}
              setConfig={setConfig}
              setShowConfig={setShowConfig}
              addLog={addLog}
              onSave={() => {
                // Fetch courses only when user saves configuration
                if (config.apiUrl && config.apiKey) {
                  fetchCourses();
                }
              }}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default CanvasDownloader;