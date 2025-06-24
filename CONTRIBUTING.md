# Contributing to BizFindr

Thank you for your interest in contributing to BizFindr! We welcome contributions from the community.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
3. Create a new branch for your changes
4. Make your changes
5. Run tests
6. Commit and push your changes
7. Create a pull request

## Development Setup

### Prerequisites

- Python 3.9+
- MongoDB 6.0+
- Docker and Docker Compose (recommended)
- Node.js and npm (for frontend development)

### Local Development

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r backend/requirements-dev.txt
   ```

3. Set up environment variables:
   ```bash
   cp backend/.env.example backend/.env
   # Edit .env with your configuration
   ```

4. Run the development server:
   ```bash
   cd backend
   flask run
   ```

## Code Style

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) for Python code
- Use [Google Style Python Docstrings](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)
- Keep lines under 88 characters (Black's default)
- Use type hints for all function signatures

## Testing

Run tests with:
```bash
pytest
```

## Pull Request Process

1. Ensure any install or build dependencies are removed before the end of the layer when doing a build.
2. Update the README.md with details of changes to the interface.
3. Increase the version numbers in any examples files and the README.md to the new version.
4. You may merge the Pull Request once you have the sign-off of two other developers, or if you do not have permission to do that, you may request the second reviewer to merge it for you.
