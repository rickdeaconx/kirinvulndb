import json
import logging
from typing import Dict, Any, Optional
from aiokafka import AIOKafkaProducer
import asyncio

from app.core.config import settings

logger = logging.getLogger(__name__)


class KafkaProducerManager:
    """Kafka producer for streaming vulnerability updates"""
    
    def __init__(self):
        self.producer: Optional[AIOKafkaProducer] = None
        self.is_connected = False
        self.bootstrap_servers = settings.KAFKA_BOOTSTRAP_SERVERS
        
    async def start(self):
        """Start the Kafka producer"""
        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                compression_type='gzip',
                acks='all',  # Wait for all replicas
                retries=3,
                max_in_flight_requests_per_connection=1,  # Ensure ordering
                enable_idempotence=True  # Prevent duplicates
            )
            
            await self.producer.start()
            self.is_connected = True
            logger.info(f"Kafka producer started, connected to {self.bootstrap_servers}")
            
        except Exception as e:
            logger.error(f"Failed to start Kafka producer: {e}")
            self.is_connected = False
            raise
    
    async def stop(self):
        """Stop the Kafka producer"""
        if self.producer:
            await self.producer.stop()
            self.is_connected = False
            logger.info("Kafka producer stopped")
    
    async def send_vulnerability_update(self, vulnerability_data: Dict[str, Any]):
        """Send vulnerability update to Kafka"""
        if not self.is_connected or not self.producer:
            logger.warning("Kafka producer not connected, skipping message")
            return
        
        try:
            topic = settings.KAFKA_TOPIC_VULNERABILITIES
            key = vulnerability_data.get('vulnerability_id', '')
            
            # Add metadata
            message = {
                "type": "vulnerability_update",
                "timestamp": vulnerability_data.get("updated_at") or vulnerability_data.get("created_at"),
                "data": vulnerability_data
            }
            
            # Send to Kafka
            await self.producer.send(topic, value=message, key=key)
            logger.debug(f"Sent vulnerability update to Kafka: {key}")
            
        except Exception as e:
            logger.error(f"Failed to send vulnerability update to Kafka: {e}")
    
    async def send_alert_notification(self, alert_data: Dict[str, Any]):
        """Send alert notification to Kafka"""
        if not self.is_connected or not self.producer:
            logger.warning("Kafka producer not connected, skipping alert")
            return
        
        try:
            topic = settings.KAFKA_TOPIC_ALERTS
            key = alert_data.get('id', '')
            
            message = {
                "type": "alert_notification",
                "timestamp": alert_data.get("created_at"),
                "data": alert_data
            }
            
            await self.producer.send(topic, value=message, key=key)
            logger.debug(f"Sent alert notification to Kafka: {key}")
            
        except Exception as e:
            logger.error(f"Failed to send alert to Kafka: {e}")
    
    async def send_custom_event(self, topic: str, event_data: Dict[str, Any], key: Optional[str] = None):
        """Send custom event to specified topic"""
        if not self.is_connected or not self.producer:
            logger.warning("Kafka producer not connected, skipping custom event")
            return
        
        try:
            await self.producer.send(topic, value=event_data, key=key)
            logger.debug(f"Sent custom event to topic {topic}")
            
        except Exception as e:
            logger.error(f"Failed to send custom event to {topic}: {e}")
    
    async def flush(self):
        """Flush pending messages"""
        if self.producer:
            await self.producer.flush()
    
    def health_check(self) -> Dict[str, Any]:
        """Check producer health"""
        return {
            "connected": self.is_connected,
            "bootstrap_servers": self.bootstrap_servers
        }


# Global Kafka producer instance
kafka_producer = KafkaProducerManager()