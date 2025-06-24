# Changelog

All notable changes to the BizFindr project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Removed
- Removed Celery, Celery Beat, and Flower services
- Removed Celery-related dependencies and configuration
- Removed task queue functionality (to be replaced in a future release)

## [0.2.0] - 2025-06-24

### Added
- Celery worker, beat, and Flower services for background task processing
- Redis-based task queue and result backend
- Monitoring stack with Prometheus, Grafana, and Alertmanager
- Comprehensive documentation for all services
- Health checks and resource limits for all containers
- Python 3.12 support
- Poetry for dependency management
- GitHub Actions CI/CD pipeline
- Pre-commit hooks for code quality

### Changed
- Updated to Python 3.12
- Migrated from requirements.txt to Poetry
- Improved Docker configuration and build process
- Enhanced error handling and logging
- Updated all dependencies to latest stable versions

### Fixed
- Resolved Celery worker/beat import issues
- Fixed Docker Compose networking and volume configurations
- Addressed security vulnerabilities in dependencies
- Fixed health check configurations for all services

### Changed
- N/A

### Fixed
- N/A

### Deprecated
- N/A

### Removed
- N/A

### Security
- N/A

## [0.1.0] - 2025-06-23

### Added
- Initial project setup and structure
