# Canvas File Downloader

A React + Flask application for automatically downloading course files and assignment submissions from Canvas LMS.

## What It Does

- **Downloads all course files** organized by folders, maintaining Canvas structure  
- **Downloads assignment submissions** including your submitted attachments
- **Organizes files** in structure: `Term/Course-Code/folder-name/files`
- **Real-time progress tracking** with detailed logging
- **Handles large files** (>100MB) with streaming downloads
- **Skips existing files** to avoid re-downloading

### File Organization
```
downloads/
├── Fall-2024/
│   ├── CS101/
│   │   ├── assignments/
│   │   ├── lecture-notes/
│   │   └── resources/
│   └── CS201/
│       ├── assignments/
│       └── materials/
```

## Quick Start

### Prerequisites
- Python 3.8+
- Node.js 14+
- Canvas API token from your institution

### Installation

1. **Setup Backend**:
```bash
git clone <repo-url>
cd canvas-downloader

# Install Poetry if not already installed
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies and activate virtual environment
poetry install
poetry shell

# Start Flask server
python server/app.py
```

2. **Setup Frontend**:
```bash
# In a new terminal
npx create-react-app frontend
cd frontend
npm install lucide-react socket.io-client

# Copy the React component to src/App.js
# Start React server
npm start
```

3. **Access the app** at `http://localhost:3000`

## Usage

1. **Get Canvas API Token**:
   - Go to Canvas → Account Settings → Approved Integrations
   - Create New Access Token
   - Copy the token (save it securely)

2. **Configure the app**:
   - Click "Configuration" 
   - Enter Canvas URL: `https://your-school.instructure.com`
   - Enter your API token
   - Set download directory (default: `./downloads`)

3. **Download files**:
   - Select courses from the list
   - Click "Start Download"
   - Monitor progress in real-time

## API Endpoints

- `POST /api/courses` - Fetch user's courses
- `POST /api/download/start` - Start download process  
- `POST /api/download/<id>/stop` - Stop download
- `GET /api/download/<id>/status` - Check status
- **WebSocket** - Real-time progress updates

## Development

### Backend Development
```bash
poetry install --with dev
poetry shell

# Run with auto-reload
export FLASK_ENV=development
python app.py

# Run tests
pytest

# Format code
black app.py
flake8 app.py
```

### Frontend Development  
```bash
cd frontend
npm install
npm start

# Run tests
npm test

# Build for production
npm run build
```

## Troubleshooting

**Connection Issues**:
- Verify backend runs on `http://localhost:5000`
- Check Canvas API URL format (no trailing slash)
- Test API token validity

**Download Problems**:
- Check Canvas file permissions
- Monitor Flask logs: `tail -f canvas_downloader.log`
- Verify disk space and directory permissions

**Performance**:
- Download during off-peak hours
- Start with smaller courses for testing
- Use SSD storage for faster writes

## Deployment

### Local Network
```bash
# Backend
python app.py --host=0.0.0.0

# Frontend  
npm run build
```

### Docker
```dockerfile
# Backend
FROM python:3.9-slim
RUN pip install poetry
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-dev
COPY app.py ./
CMD ["poetry", "run", "python", "app.py"]
```

## License

Educational use only. Ensure compliance with your institution's Canvas usage policies.

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Make changes and add tests
4. Run tests: `poetry run pytest`
5. Submit pull request

Areas for contribution:
- Database integration for download history
- File type filtering and search
- Cloud storage integration (Google Drive, etc.)
- Mobile app version
- Scheduled/automated downloads