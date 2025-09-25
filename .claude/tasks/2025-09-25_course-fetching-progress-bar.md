# Course Fetching Progress Bar - Implementation Plan

**Date**: 2025-09-25
**Task**: Add progress bar during course fetching process, similar to file download progress

## Problem Statement
Currently during course fetching, users only see a loading spinner with no indication of progress. The backend processes each course individually to count files/folders, but the frontend doesn't show this incremental progress. Users don't know how many courses are being processed or how much time remains.

## Current Behavior Analysis
- Loading spinner appears during entire course fetch process
- Backend processes courses sequentially in `/api/courses` endpoint
- Backend logs show individual course processing but no progress updates
- Frontend has no progress indication beyond spinner

## Desired Behavior
- Show progress bar: "Processing courses... (3/15)"
- Progress updates as each course is processed
- Similar UI to existing file download progress bar
- Maintain loading state until all courses are processed

## Implementation Plan

### 1. Backend: Add Course Processing Progress
- **File**: `server/app.py` - `/api/courses` endpoint
- **Changes**:
  - Count total courses before processing loop
  - Emit progress updates via Socket.IO as each course is processed
  - Use similar pattern to `download_progress` events
  - Format: `{'current': 3, 'total': 15, 'course_name': 'CS 101'}`

### 2. Frontend: Add Course Progress State
- **File**: `frontend/src/components/CanvasDownloader.jsx`
- **Changes**:
  - Add new state for course fetching progress
  - Listen for new Socket.IO event (e.g., `course_progress`)
  - Pass progress to CourseSelector component

### 3. Frontend: Display Course Progress UI
- **File**: `frontend/src/components/CourseSelector.jsx`
- **Changes**:
  - Add progress bar component when `downloadStatus === 'loading'`
  - Show "Processing courses... (X/Y)" text
  - Display current course being processed
  - Reuse existing progress bar styling from download progress

### 4. Progress Event Naming
- Use `course_fetch_progress` to distinguish from `download_progress`
- Reset progress state when course fetching completes

## Technical Details

### Socket.IO Events
```javascript
// Backend emits:
socketio.emit('course_fetch_progress', {
  current: currentCourse,
  total: totalCourses,
  course_name: course.name
}, room=socket_id)

// Frontend listens:
socket.on('course_fetch_progress', (data) => {
  setCourseProgress(data);
});
```

### UI Design
```jsx
{downloadStatus === 'loading' && courseProgress.total > 0 && (
  <div className="space-y-3">
    <div className="flex items-center justify-between text-sm text-gray-600">
      <span>Processing courses: {courseProgress.current}/{courseProgress.total}</span>
      <span>{Math.round((courseProgress.current / courseProgress.total) * 100)}%</span>
    </div>
    <div className="w-full bg-gray-200 rounded-full h-2">
      <div
        className="h-2 bg-blue-600 rounded-full transition-all duration-300"
        style={{ width: `${(courseProgress.current / courseProgress.total) * 100}%` }}
      />
    </div>
    {courseProgress.course_name && (
      <p className="text-xs text-gray-500">
        Processing: {courseProgress.course_name}
      </p>
    )}
  </div>
)}
```

## Success Criteria
- [x] Progress bar appears during course fetching (after authentication)
- [x] Shows "Processing courses... (X/Y)" with accurate counts
- [x] Progress bar fills incrementally as courses are processed
- [x] Displays name of current course being processed
- [x] Progress bar disappears when courses load completely
- [x] Loading spinner is replaced by progress bar during course processing

## Implementation Details

### Backend Changes (`server/app.py`)
- Added course counting and progress tracking in `/api/courses` endpoint
- Emits `course_fetch_progress` events with current/total/course_name data
- Progress updates sent for each course as it's being processed

### Frontend Changes (`frontend/src/components/CanvasDownloader.jsx`)
- Added `courseProgress` state to track course processing progress
- Added Socket.IO event listener for `course_fetch_progress` events
- Reset progress state when starting new course fetch
- Pass courseProgress to CourseSelector component

### UI Changes (`frontend/src/components/CourseSelector.jsx`)
- Enhanced loading state to show different messages based on progress
- Added progress bar component during course processing phase
- Shows "Processing: X/Y" with percentage and current course name
- Maintains loading spinner with enhanced progress information

## New User Experience
1. User saves Canvas configuration
2. "Fetching courses from Canvas..." appears with spinner
3. User authentication completes → "Connected" status
4. **NEW**: Message changes to "Processing courses..."
5. **NEW**: Progress bar appears showing "Processing: 3/15 (20%)"
6. **NEW**: Current course name displayed: "Current: Computer Science 101"
7. Progress bar fills incrementally as each course is processed
8. Loading completes and course list populates

## Technical Implementation
- Backend emits progress after processing each course's folder/file counts
- Frontend shows smooth progress bar animation
- Progress resets on each new course fetch attempt
- Handles edge cases like processing errors gracefully

**Status**: ✅ COMPLETED