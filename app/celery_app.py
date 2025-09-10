from celery import Celery
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Create Celery app
celery_app = Celery(
    "kirinvulndb",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.collection_tasks",
        "app.tasks.notification_tasks",
        "app.tasks.analysis_tasks"
    ]
)

# Configure Celery
celery_app.conf.update(
    # Task routing
    task_routes={
        'app.tasks.collection_tasks.*': {'queue': 'collection'},
        'app.tasks.notification_tasks.*': {'queue': 'notifications'},
        'app.tasks.analysis_tasks.*': {'queue': 'analysis'},
    },
    
    # Task execution
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Task retry configuration
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Rate limiting
    task_annotations={
        'app.tasks.collection_tasks.collect_nvd_vulnerabilities': {
            'rate_limit': '10/m'  # 10 per minute
        },
        'app.tasks.collection_tasks.collect_vendor_advisories': {
            'rate_limit': '30/m'  # 30 per minute
        },
        'app.tasks.notification_tasks.send_email_alert': {
            'rate_limit': '100/m'  # 100 per minute
        }
    },
    
    # Beat schedule (periodic tasks)
    beat_schedule={
        'collect-cve-vulnerabilities': {
            'task': 'app.tasks.collection_tasks.collect_nvd_vulnerabilities',
            'schedule': settings.CVE_COLLECTION_INTERVAL,  # seconds
        },
        'collect-vendor-advisories': {
            'task': 'app.tasks.collection_tasks.collect_vendor_advisories',
            'schedule': settings.VENDOR_COLLECTION_INTERVAL,
        },
        'collect-community-sources': {
            'task': 'app.tasks.collection_tasks.collect_community_sources',
            'schedule': settings.COMMUNITY_COLLECTION_INTERVAL,
        },
        'cleanup-old-data': {
            'task': 'app.tasks.maintenance_tasks.cleanup_old_data',
            'schedule': 86400,  # Daily
        },
        'generate-statistics': {
            'task': 'app.tasks.analysis_tasks.generate_daily_statistics',
            'schedule': 3600,  # Hourly
        }
    },
)

logger.info("Celery app configured successfully")