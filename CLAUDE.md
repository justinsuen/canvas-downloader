# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Canvas File Downloader is a React + Flask application for automatically downloading course files and assignment submissions from Canvas LMS. The application organizes files by term/course structure and provides real-time progress tracking.

## CLAUDE Instructions

### Core Workflow: Research → Plan → Implement → Validate
Start every feature with: "Let me research the codebase and create a plan before implementing."

- **Research**: Understand existing patterns and architecture.
- **Plan**: Propose approach and verify with you. The plan should be a detailed implementation plan and the reasoning behind each decision. Each task should be broken down into smaller tasks and each task should have a clear objective. Don't over plan it. Always think MVP first.
- **Implement**: Build with tests and error handling.
- **Validate**: ALWAYS run formatters, linters, and tests after implementation.

### Imperatives
- Always start in plan mode to make a plan. Don't be verbose. Be concise.
- Write the plan to .claude/tasks/{YYYY-MM-DD}_{TASK_NAME}.md.
- If the task requires external knowledge or a certain package, research to get the latest knowledge and add it to the plan. Use Task tool to research.

## Architecture

### Backend (Python Flask)
- **Main file**: `server/app.py` - Flask server with Socket.IO for real-time communication
- **Key components**:
  - `DownloadManager` class handles download orchestration and progress tracking
  - Socket.IO provides real-time updates to frontend
  - Canvas API integration using `canvasapi` library
  - File streaming for large downloads (>100MB)

### Frontend (React)
- **Location**: `frontend/` directory
- **Framework**: React with Create React App
- **UI**: Tailwind CSS for styling, Lucide React for icons
- **Real-time**: Socket.IO client for progress updates
- **Structure**: Components in `frontend/src/components/`

### Dependencies Management
- **Backend**: Poetry (`pyproject.toml`) for Python dependency management
- **Frontend**: npm (`package.json`) for JavaScript dependencies

## Development Commands

### Backend Development
```bash
# Install dependencies and activate virtual environment
poetry install
poetry shell

# Start Flask development server
python server/app.py

# Development mode with auto-reload
export FLASK_ENV=development
python server/app.py

# Run tests
pytest

# Code formatting and linting
black server/app.py
flake8 server/app.py
```

### Frontend Development
```bash
cd frontend

# Install dependencies
npm install

# Start development server (runs on port 3000)
npm start

# Run tests
npm test

# Build for production
npm run build
```

### Full Stack Development
- Backend runs on `http://localhost:8000` (configurable via API_PORT env var)
- Frontend runs on `http://localhost:3000`
- Socket.IO WebSocket connection for real-time updates
- CORS configured to allow frontend-backend communication

## Key Features & Workflows

### File Organization
Downloads are organized as: `downloads/Term/Course-Code/folder-name/files`
- Assignment submissions go to `downloads/Term/Course-Code/assignments/`
- Course files maintain Canvas folder structure

### Download Process
1. User provides Canvas API URL and token
2. Backend fetches course list via Canvas API
3. User selects courses to download
4. DownloadManager calculates total files and starts background download
5. Real-time progress updates sent via Socket.IO
6. Files are deduplicated (skips existing files)
7. Large files (>100MB) use streaming download

### API Endpoints
- `POST /api/courses` - Fetch user's Canvas courses
- `POST /api/download/start` - Start download process
- `POST /api/download/<id>/stop` - Stop active download
- `GET /api/download/<id>/status` - Get download status
- `GET /api/health` - Health check endpoint

## File Structure
- `server/app.py` - Main Flask application with Socket.IO
- `frontend/` - React application
- `downloads/` - Default download directory (created automatically)
- `canvas_downloader.log` - Application logs