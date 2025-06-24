# BizFindr Setup Guide

This guide will help you set up the BizFindr application on your local machine for development and testing purposes.

## Prerequisites

- Docker and Docker Compose
- Git
- (Optional) Python 3.9+ and Node.js (for development without Docker)

## Docker Setup (Recommended)

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/bizfindr.git
   cd bizfindr
   ```

2. Copy the example environment file:
   ```bash
   cp backend/.env.example backend/.env
   ```

3. Update the environment variables in `backend/.env` as needed.

4. Start the application:
   ```bash
   # Linux/macOS
   ./scripts/start.sh

   # Windows
   .\scripts\start.bat
   ```

5. The application will be available at `http://localhost:5000`

## Manual Setup (Development)

### Backend Setup

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

2. Install Python dependencies:
   ```bash
   cd backend
   pip install -r requirements-dev.txt
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. Run the development server:
   ```bash
   flask run
   ```

### Frontend Setup

1. Install Node.js dependencies:
   ```bash
   cd frontend
   npm install
   ```

2. Start the development server:
   ```bash
   npm run dev
   ```

## Database Setup

### MongoDB

1. Install MongoDB (or use Docker)
2. Create a database named `bizfindr`
3. Create necessary collections:
   - `registrations`
   - `fetch_history`

### Environment Variables

Create a `.env` file in the backend directory with the following variables:

```
FLASK_APP=app
FLASK_ENV=development
MONGO_URI=mongodb://mongo:27017/bizfindr
API_BASE_URL=https://data.ct.gov/resource/n7gp-d28j.json
```

## Running Tests

```bash
# Run all tests
pytest

# Run tests with coverage report
pytest --cov=app --cov-report=term-missing
```

## Deployment

For production deployment, configure the following:

1. Set `FLASK_ENV=production`
2. Configure a production-ready WSGI server (Gunicorn, uWSGI)
3. Set up a reverse proxy (Nginx, Apache)
4. Configure HTTPS with Let's Encrypt
