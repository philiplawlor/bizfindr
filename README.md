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
- Background task processing with Celery
- Scheduled tasks with Celery Beat
- Real-time task monitoring with Flower
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
   - `CELERY_BROKER_URL`: Celery broker URL (default: `redis://redis:6379/1`)
   - `FLOWER_BASIC_AUTH`: Credentials for Flower dashboard (default: `admin:admin`)

4. Start the application with Docker Compose:
   ```bash
   docker-compose up -d
   ```

   This will start the following services:
   - Flask application (port 5000)
   - MongoDB (port 27017)
   - Redis (port 6379)
   - Celery worker
   - Celery beat (for scheduled tasks)
   - Flower (task monitoring dashboard, port 5555)

5. Access the application:
   - Web interface: http://localhost:5000
   - API documentation: http://localhost:5000/api/docs
   - Flower dashboard: http://localhost:5555 (username/password from FLOWER_BASIC_AUTH)

## Background Tasks

BizFindr uses Celery for background task processing. The following task queues are available:

- `default`: General purpose tasks
- `metrics`: Business metrics calculation and reporting
- `notifications`: Email and user notifications
- `maintenance`: System cleanup and maintenance tasks
- `import`: Data import tasks
- `export`: Data export tasks
- `reports`: Report generation tasks

### Scheduled Tasks

The following periodic tasks are configured by default:

| Task | Schedule | Description |
|------|----------|-------------|
| `update_business_metrics` | Hourly | Updates business metrics and analytics |
| `cleanup_old_data` | Daily at 2 AM | Cleans up old data and temporary files |
| `send_daily_digest` | Daily at 8 AM | Sends daily digest emails to users |

### Monitoring Tasks

Celery tasks can be monitored using the Flower dashboard:

1. Access the Flower dashboard at http://localhost:5555
2. Use the credentials from `FLOWER_BASIC_AUTH` (default: admin/admin)
3. View task status, workers, and task history

### Running Tasks Manually

You can run tasks manually using the Celery CLI:

```bash
# Start a Celery worker
celery -A app.core.celery_app.celery_app worker --loglevel=info

# Start Celery beat for scheduled tasks
celery -A app.core.celery_app.celery_app beat --loglevel=info

# Call a specific task from Python
from app.tasks.metrics import update_business_metrics
update_business_metrics.delay(business_id="your_business_id")
```

## Development

### Adding New Tasks

1. Create a new module in `app/tasks/` for your task category (e.g., `app/tasks/notifications.py`)
2. Define your task functions using the `@task` decorator:
   ```python
   from app.core.celery_app import task
   
   @task(bind=True, max_retries=3, default_retry_delay=60, time_limit=300)
   def my_task(self, arg1, arg2):
       try:
           # Task implementation
           return {"status": "success"}
       except Exception as exc:
           self.retry(exc=exc)
   ```

3. Register the task in `app/tasks/__init__.py`
4. If it's a periodic task, add it to `CeleryConfig.beat_schedule` in `app/core/celery_config.py`

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

- **Flower Dashboard**: Real-time monitoring of Celery tasks at http://localhost:5555
- **Prometheus Metrics**: Task metrics are exposed at `/metrics` endpoint
- **Logging**: All task executions are logged with structured JSON format

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

1. **Tasks not executing**
   - Check Celery worker logs: `docker-compose logs celery-worker`
   - Verify Redis connection
   - Check task routing and queue configuration

2. **Task failures**
   - Check task logs in Flower
   - Look for exceptions in application logs
   - Verify task dependencies and environment

3. **Performance issues**
   - Monitor worker resource usage
   - Adjust concurrency settings
   - Optimize task granularity

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
| `CELERY_BROKER_URL` | `redis://redis:6379/1` | Celery broker URL |
| `CELERY_RESULT_BACKEND` | `redis://redis:6379/1` | Celery result backend |
| `FLOWER_BASIC_AUTH` | `admin:admin` | Flower dashboard credentials |
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
