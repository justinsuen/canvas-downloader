# Rate Limiting - Implementation Plan

**Date**: 2025-09-25
**Task**: Add rate limiting with course and file limits

## Rate Limits Required

### Course Fetching
- 100 courses per hour (rate limit on course processing)

### File Downloads
- 500 files per hour
- 2000 files per day

## Implementation Strategy

### Backend Changes
- Install flask-limiter
- Track course processing count in `/api/courses`
- Track file download count in download process
- Return 429 errors when limits exceeded

### Rate Limiting Setup
```python
from flask_limiter import Limiter
limiter = Limiter(app, key_func=get_remote_address)

# Course processing limit
course_count_tracker = {}

# File download limits
@limiter.limit("500 per hour; 2000 per day")
def download_file_with_limit():
    # file download logic
```

## Files to Modify
- `server/app.py` - rate limiting logic
- Add dependency for flask-limiter

## Success Criteria
- [x] 100 courses/hour limit on course fetching
- [x] 500 files/hour + 2000 files/day on downloads
- [x] Clear error messages when limits hit

## Implementation Details

### Rate Limits Applied
- **Course Processing**: 100 courses per hour (tracked per IP)
- **File Downloads**: 500 files per hour + 2000 files per day (tracked per IP)
- **Download Initiation**: 3 download starts per minute (flask-limiter)
- **Course API Calls**: 10 requests per minute (flask-limiter)

### Backend Changes
- Added flask-limiter with IP-based rate limiting
- Custom rate limit tracking for courses and files
- Rate limit checks in course processing and file download
- Returns 429 errors with descriptive messages

### Error Handling
Users get clear messages like:
- "Course processing limit exceeded. You can process 45 more courses this hour."
- "Hourly file download limit exceeded. You can download 123 more files this hour."

**Status**: ✅ COMPLETED