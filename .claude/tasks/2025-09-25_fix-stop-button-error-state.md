# Fix Stop Download Button During Error States

**Date**: 2025-09-25
**Issue**: When there is an error during download, the stop download button doesn't work/disappears

## Problem Analysis

### Root Cause
When a download encounters an error, the stop button becomes unavailable because:

1. **CourseSelector.jsx line 84**: UI only shows stop button when `downloadStatus === 'downloading'`
2. **CanvasDownloader.jsx line 251**: When error occurs, `setDownloadStatus('error')` is called
3. **Result**: Status changes from `'downloading'` to `'error'`, so stop button UI disappears
4. **Missing UI state**: No UI handling exists for `'error'` status - falls back to start button

### Current Logic Flow
```javascript
// When error occurs:
setDownloadStatus('error')  // Changes from 'downloading' to 'error'

// UI only shows stop button for:
downloadStatus === 'downloading'  // Now false, so shows start button instead
```

### Additional Issues
1. **No error state UI**: The `'error'` status isn't handled in CourseSelector UI
2. **downloadId persistence**: When error occurs, `downloadId` might still exist, creating confusion
3. **Inconsistent state**: User sees "Start Download" button even though download might still be running in background

## Solution Plan

### 1. Add Error State UI Handling
- Modify CourseSelector to show stop button for both `'downloading'` AND `'error'` states
- Add visual indication that there's an error but download may still be running
- Keep stop functionality available during error states

### 2. Improve Status Management
- Ensure proper cleanup when stopping downloads in error state
- Clear downloadId and reset progress when stopping from error state
- Add better error messaging for user clarity

### 3. Enhanced Stop Button Logic
- Make stop button work regardless of current status
- Add fallback stop behavior for error states
- Ensure proper state reset after stopping

## Implementation Tasks

### CourseSelector.jsx Changes
- **Current condition**: `downloadStatus === 'downloading'`
- **New condition**: `downloadStatus === 'downloading' || downloadStatus === 'error'`
- Add error styling/messaging when status is 'error'
- Show "Stop Download" button for both downloading and error states
- Add visual indicator for error state (red styling, error icon, etc.)

### CanvasDownloader.jsx Changes
- Improve `handleStopDownload` to handle error states
- Ensure proper cleanup regardless of current status
- Add better error state management
- Reset progress and downloadId when stopping from error state

## Expected Outcome

- **Stop button availability**: Remains available even when errors occur
- **User control**: Users can always stop downloads regardless of error state
- **Clear feedback**: Visual indication of error conditions while keeping stop functionality
- **Proper cleanup**: State properly reset when stopping from any state
- **Better UX**: No confusion about download state or available actions

## Technical Details

### Files to Modify
1. `frontend/src/components/CourseSelector.jsx` - UI condition and error state display
2. `frontend/src/components/CanvasDownloader.jsx` - Stop button logic and state management

### Status States to Handle
- `'idle'` - Show start button
- `'downloading'` - Show stop button with progress
- `'error'` - Show stop button with error indication
- `'completed'` - Show start button (ready for new download)

### Error State UI Requirements
- Keep stop button visible and functional
- Add visual error indicator (red styling, error icon)
- Maintain progress display if available
- Clear error messaging about what went wrong