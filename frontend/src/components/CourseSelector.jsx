import React from 'react';
import { Folder, File, CheckCircle, Play, Pause, AlertCircle } from 'lucide-react';

const CourseSelector = ({
  courses,
  selectedCourses,
  setSelectedCourses,
  downloadStatus,
  progress,
  startDownload,
  stopDownload
}) => {
  const toggleCourseSelection = (courseId) => {
    const newSelected = new Set(selectedCourses);
    if (newSelected.has(courseId)) {
      newSelected.delete(courseId);
    } else {
      newSelected.add(courseId);
    }
    setSelectedCourses(newSelected);
  };

  const selectAllCourses = () => {
    if (selectedCourses.size === courses.length) {
      setSelectedCourses(new Set());
    } else {
      setSelectedCourses(new Set(courses.map(c => c.id)));
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 flex-1 flex flex-col min-h-0">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold">Available Courses</h2>
        <button
          onClick={selectAllCourses}
          className="text-sm text-blue-600 hover:text-blue-700"
        >
          {selectedCourses.size === courses.length ? 'Deselect All' : 'Select All'}
        </button>
      </div>

      {courses.length === 0 ? (
        <div className="text-center py-8 text-gray-500 flex-1 flex flex-col items-center justify-center">
          <Folder className="mx-auto mb-2" size={48} />
          <p>No courses found. Please configure your API settings.</p>
        </div>
      ) : (
        <div className="space-y-3 overflow-y-auto flex-1 min-h-0 pr-2">
          {courses.map(course => (
            <div
              key={course.id}
              className={`border rounded-lg p-4 cursor-pointer transition-colors ${selectedCourses.has(course.id)
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300'
                }`}
              onClick={() => toggleCourseSelection(course.id)}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h3 className="font-medium text-gray-900">{course.name}</h3>
                  <p className="text-sm text-gray-600">{course.course_code} • {course.term.name}</p>
                  <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                    <span className="flex items-center gap-1">
                      <Folder size={12} />
                      {course.folder_count} folders
                    </span>
                    <span className="flex items-center gap-1">
                      <File size={12} />
                      {course.file_count} files
                    </span>
                  </div>
                </div>
                {selectedCourses.has(course.id) && (
                  <CheckCircle className="text-blue-600 flex-shrink-0" size={20} />
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="mt-6 pt-6 border-t border-gray-200 flex-shrink-0">
        {(downloadStatus === 'downloading' || downloadStatus === 'error') ? (
          <div className="space-y-3">
            {downloadStatus === 'error' && (
              <div className="flex items-center gap-2 text-sm text-red-700 bg-red-50 px-3 py-2 rounded-lg border border-red-200">
                <AlertCircle size={14} />
                <span>Error occurred - you can still stop the download</span>
              </div>
            )}
            <div className={`flex items-center justify-between text-sm ${downloadStatus === 'error' ? 'text-red-600' : 'text-gray-600'}`}>
              <span>Progress: {progress.current}/{progress.total}</span>
              <span>{Math.round((progress.current / progress.total) * 100)}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-all duration-300 ${downloadStatus === 'error' ? 'bg-red-500' : 'bg-blue-600'}`}
                style={{ width: `${(progress.current / progress.total) * 100}%` }}
              ></div>
            </div>
            {progress.currentFile && (
              <p className={`text-xs ${downloadStatus === 'error' ? 'text-red-500' : 'text-gray-500'}`}>
                {downloadStatus === 'error' ? 'Last file: ' : 'Downloading: '}
                {progress.currentFile}
              </p>
            )}
            <button
              onClick={stopDownload}
              className={`w-full flex items-center justify-center gap-2 px-4 py-2 text-white rounded-lg transition-colors ${
                downloadStatus === 'error'
                  ? 'bg-red-700 hover:bg-red-800'
                  : 'bg-red-600 hover:bg-red-700'
              }`}
            >
              <Pause size={16} />
              Stop Download
            </button>
          </div>
        ) : (
          <button
            onClick={startDownload}
            disabled={selectedCourses.size === 0}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
          >
            <Play size={16} />
            Start Download ({selectedCourses.size} courses)
          </button>
        )}
      </div>
    </div>
  );
};

export default CourseSelector;