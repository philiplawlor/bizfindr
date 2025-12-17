# BizFindr (v0.2.0)

A web application that fetches and displays business registration data from the Connecticut Open Data API.

**Version:** 0.2.0  
**Last Updated:** June 24, 2025

## Features

- Automated data fetching from CT.gov API
- MongoDB storage for business registrations
- Searchable web interface
- RESTful API endpoints
- Docker containerization
- Background task processing (refactored - simple Redis-based tasks)
- Redis-based caching and rate limiting
- Comprehensive logging and monitoring

## Prerequisites

- Docker and Docker Compose
- Python 3.9+
- MongoDB 6.0+
- Redis 7.0+

## Getting Started

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/bizfindr.git
   cd bizfindr
   ```

2. Copy the example environment file:
   ```bash
   cp backend/.env.example backend/.env
   ```

3. Update the environment variables in `.env` as needed, especially:
   - `CT_API_KEY`: Your CT.gov API key
   - `SECRET_KEY`: A secure secret key for the application
   - `MONGO_URI`: MongoDB connection string (default: `mongodb://mongo:27017/bizfindr`)
   - `REDIS_URL`: Redis connection URL (default: `redis://redis:6379/0`)
   - `REDIS_URL`: Redis connection URL (default: `redis://redis:6379/0`)

4. Start the application with Docker Compose:
   ```bash
   docker-compose up -d
   ```

   This will start the following services:
   - Flask application (port 5656)
   - MongoDB (port 27017)
   - Redis (port 6379)
   - MongoDB Express (port 8081)

5. Access the application:
   - Web interface: http://localhost:5656
   - API documentation: http://localhost:5656/api/docs
   - MongoDB Express: http://localhost:8081

## Background Tasks

Background task processing has been simplified to use Redis-based task queues without Celery. The current implementation provides:

- Simple task queuing using Redis lists
- Basic task status tracking
- Retry mechanisms for failed tasks
- Task logging and monitoring

For complex background processing, the system can be extended with a more robust task queue in the future.

## Development

### Adding New Tasks

Simple background tasks can be added using the Redis-based task system:

1. Create task functions in `app/services/task_service.py`
2. Use the `queue_task` utility to enqueue tasks
3. Process tasks using the `process_tasks` endpoint

Example:
```python
from app.services.task_service import queue_task

# Queue a background task
queue_task("task_name", {"param1": "value1"})
```

### Task Best Practices

- Use meaningful task names and docstrings
- Set appropriate time limits and retry policies
- Handle task failures gracefully
- Use task routing to appropriate queues
- Monitor task performance and resource usage
- Include comprehensive logging
- Test tasks in isolation

## Monitoring and Logging

### Task Monitoring

- **Application Logs**: Task executions are logged with structured JSON format
- **Redis Monitoring**: Monitor task queues using Redis CLI or monitoring tools
- **API Endpoints**: Task status available through `/api/v1/tasks` endpoints

### Log Files

Application and task logs are written to:
- `/var/log/bizfindr/app.log` (inside container)
- Standard output (captured by Docker)

### Alerting

Configure alerts for:
- Failed tasks
- Long-running tasks
- Queue backlogs
- Worker failures

## Troubleshooting

### Common Issues

1. **Background tasks not executing**
   - Check Redis connection and queue status
   - Verify task processing endpoint is accessible
   - Check application logs for any errors

2. **Task failures**
   - Check task logs in application logs
   - Look for exceptions in application logs
   - Verify task dependencies and environment
   - Monitor Redis queue length

3. **Performance issues**
   - Monitor application resource usage
   - Check Redis memory usage
   - Optimize task granularity and database queries

For additional help, check the [Troubleshooting Guide](docs/TROUBLESHOOTING.md).

## Project Structure

```
.
├── backend/                  # Backend application
│   ├── app/                  # Application package
│   │   ├── api/              # API endpoints
│   │   ├── core/             # Core functionality
│   │   │   ├── cache.py      # Redis caching
│   │   │   ├── celery_app.py # Celery application
│   │   │   └── config.py     # Configuration
│   │   ├── models/           # Database models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/         # Business logic
│   │   ├── tasks/            # Celery tasks
│   │   │   ├── cleanup.py    # Maintenance tasks
│   │   │   ├── metrics.py    # Metrics tasks
│   │   │   └── notifications.py # Notification tasks
│   │   └── utils/            # Utility functions
│   ├── scripts/              # Utility scripts
│   ├── tests/                # Test suite
│   ├── .env                  # Environment variables
│   ├── pyproject.toml        # Poetry dependencies
│   └── docker-entrypoint.sh  # Docker entrypoint
├── frontend/                 # Web interface
├── docs/                     # Documentation
├── scripts/                  # Deployment scripts
└── docker-compose.yml        # Docker Compose configuration
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_APP` | `app` | Flask application module |
| `FLASK_ENV` | `production` | Application environment |
| `SECRET_KEY` | - | Secret key for session management |
| `MONGO_URI` | `mongodb://mongo:27017/bizfindr` | MongoDB connection string |
| `REDIS_URL` | `redis://redis:6379/0` | Redis connection URL |
| `CT_API_KEY` | - | CT.gov API key |
| `LOG_LEVEL` | `INFO` | Logging level |
| `LOG_FILE` | `/var/log/bizfindr/app.log` | Log file path |

## Deployment

### Production Deployment

1. Set up a production environment:
   ```bash
   cp .env.production .env
   # Update production settings
   ```

2. Build and start the stack:
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
   ```

3. Monitor the deployment:
   ```bash
   docker-compose logs -f
   ```

### Scaling Workers

To scale Celery workers:

```bash
docker-compose up -d --scale celery-worker=4
```

### Database Backups

Configure regular MongoDB backups:

```bash
# Create backup
mongodump --uri=$MONGO_URI --out=/backups/bizfindr-$(date +%Y%m%d)

# Restore from backup
mongorestore --uri=$MONGO_URI /path/to/backup
```

## License

[Your License Here]

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Support

For support, please open an issue or contact [Your Support Email].

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
