import json
import logging
import asyncio
from typing import Dict, Any, Callable, Optional
from aiokafka import AIOKafkaConsumer
from concurrent.futures import ThreadPoolExecutor

from app.core.config import settings
from app.services.websocket_manager import websocket_manager

logger = logging.getLogger(__name__)


class KafkaConsumerManager:
    """Kafka consumer for processing vulnerability updates and alerts"""
    
    def __init__(self):
        self.consumers: Dict[str, AIOKafkaConsumer] = {}
        self.is_running = False
        self.bootstrap_servers = settings.KAFKA_BOOTSTRAP_SERVERS
        self.group_id = settings.KAFKA_GROUP_ID
        self.handlers: Dict[str, Callable] = {}
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Register default handlers
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default message handlers"""
        self.handlers["vulnerability_update"] = self._handle_vulnerability_update
        self.handlers["alert_notification"] = self._handle_alert_notification
    
    async def start(self):
        """Start Kafka consumers"""
        try:
            # Start vulnerability consumer
            await self._start_consumer(
                topic=settings.KAFKA_TOPIC_VULNERABILITIES,
                consumer_name="vulnerabilities"
            )
            
            # Start alerts consumer
            await self._start_consumer(
                topic=settings.KAFKA_TOPIC_ALERTS,
                consumer_name="alerts"
            )
            
            self.is_running = True
            logger.info("Kafka consumers started")
            
            # Start consumption tasks
            asyncio.create_task(self._consume_messages())
            
        except Exception as e:
            logger.error(f"Failed to start Kafka consumers: {e}")
            raise
    
    async def stop(self):
        """Stop all Kafka consumers"""
        self.is_running = False
        
        for consumer_name, consumer in self.consumers.items():
            try:
                await consumer.stop()
                logger.info(f"Stopped Kafka consumer: {consumer_name}")
            except Exception as e:
                logger.error(f"Error stopping consumer {consumer_name}: {e}")
        
        self.consumers.clear()
        
        # Shutdown executor
        self.executor.shutdown(wait=True)
        logger.info("Kafka consumers stopped")
    
    async def _start_consumer(self, topic: str, consumer_name: str):
        """Start a single Kafka consumer"""
        consumer = AIOKafkaConsumer(
            topic,
            bootstrap_servers=self.bootstrap_servers,
            group_id=self.group_id,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            key_deserializer=lambda k: k.decode('utf-8') if k else None,
            auto_offset_reset='latest',  # Start from latest messages
            enable_auto_commit=True,
            auto_commit_interval_ms=1000,
            session_timeout_ms=30000,
            heartbeat_interval_ms=10000
        )
        
        await consumer.start()
        self.consumers[consumer_name] = consumer
        logger.info(f"Started Kafka consumer for topic {topic}")
    
    async def _consume_messages(self):
        """Consume messages from all topics"""
        while self.is_running:
            try:
                # Create tasks for each consumer
                tasks = []
                for consumer_name, consumer in self.consumers.items():
                    task = asyncio.create_task(
                        self._consume_from_consumer(consumer_name, consumer)
                    )
                    tasks.append(task)
                
                if tasks:
                    # Wait for any task to complete, then continue
                    done, pending = await asyncio.wait(
                        tasks, 
                        timeout=1.0, 
                        return_when=asyncio.FIRST_COMPLETED
                    )
                    
                    # Cancel pending tasks
                    for task in pending:
                        task.cancel()
                
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error in message consumption loop: {e}")
                await asyncio.sleep(1)
    
    async def _consume_from_consumer(self, consumer_name: str, consumer: AIOKafkaConsumer):
        """Consume messages from a specific consumer"""
        try:
            async for message in consumer:
                if not self.is_running:
                    break
                
                try:
                    await self._process_message(message)
                except Exception as e:
                    logger.error(f"Error processing message from {consumer_name}: {e}")
                
        except Exception as e:
            logger.error(f"Error consuming from {consumer_name}: {e}")
    
    async def _process_message(self, message):
        """Process a Kafka message"""
        try:
            data = message.value
            message_type = data.get("type", "unknown")
            
            # Get handler for message type
            handler = self.handlers.get(message_type)
            if handler:
                # Run handler in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(self.executor, handler, data)
            else:
                logger.warning(f"No handler for message type: {message_type}")
                
        except Exception as e:
            logger.error(f"Error processing Kafka message: {e}")
    
    def _handle_vulnerability_update(self, message_data: Dict[str, Any]):
        """Handle vulnerability update messages"""
        try:
            vulnerability_data = message_data.get("data", {})
            
            # Broadcast to WebSocket clients
            asyncio.create_task(
                websocket_manager.broadcast_vulnerability_update(vulnerability_data)
            )
            
            # Additional processing can be added here
            logger.debug(f"Processed vulnerability update: {vulnerability_data.get('vulnerability_id')}")
            
        except Exception as e:
            logger.error(f"Error handling vulnerability update: {e}")
    
    def _handle_alert_notification(self, message_data: Dict[str, Any]):
        """Handle alert notification messages"""
        try:
            alert_data = message_data.get("data", {})
            
            # Broadcast to WebSocket clients
            asyncio.create_task(
                websocket_manager.broadcast_alert_notification(alert_data)
            )
            
            # Could add email/Slack notifications here
            logger.debug(f"Processed alert notification: {alert_data.get('id')}")
            
        except Exception as e:
            logger.error(f"Error handling alert notification: {e}")
    
    def register_handler(self, message_type: str, handler: Callable):
        """Register a custom message handler"""
        self.handlers[message_type] = handler
        logger.info(f"Registered handler for message type: {message_type}")
    
    def health_check(self) -> Dict[str, Any]:
        """Check consumer health"""
        return {
            "running": self.is_running,
            "consumers": list(self.consumers.keys()),
            "bootstrap_servers": self.bootstrap_servers,
            "group_id": self.group_id
        }


# Global Kafka consumer instance
kafka_consumer = KafkaConsumerManager()