"""
Message Queue Service for Real-time Data Processing
Supports both Kafka and RabbitMQ
"""
import json
import logging
from typing import Dict, Optional, Callable, Any
from abc import ABC, abstractmethod
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)


class MessageQueueInterface(ABC):
    """Abstract interface for message queue implementations"""

    @abstractmethod
    def publish(self, topic: str, message: Dict) -> bool:
        """Publish a message to a topic/queue"""
        pass

    @abstractmethod
    def subscribe(
        self, topic: str, callback: Callable[[Dict], None], consumer_group: Optional[str] = None
    ):
        """Subscribe to a topic/queue with a callback"""
        pass

    @abstractmethod
    def close(self):
        """Close connections"""
        pass


class RabbitMQQueue(MessageQueueInterface):
    """RabbitMQ implementation"""

    def __init__(self):
        try:
            import pika

            self.pika = pika
            self.connection = None
            self.channel = None
            self._connect()
        except ImportError:
            logger.warning(
                "pika not installed. Install with: pip install pika"
            )
            self.pika = None

    def _connect(self):
        """Establish connection to RabbitMQ"""
        if self.pika is None:
            return

        try:
            credentials = self.pika.PlainCredentials(
                settings.RABBITMQ_USER, settings.RABBITMQ_PASSWORD
            )
            parameters = self.pika.ConnectionParameters(
                host=settings.RABBITMQ_HOST,
                port=settings.RABBITMQ_PORT,
                virtual_host=settings.RABBITMQ_VHOST,
                credentials=credentials,
            )
            self.connection = self.pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()

            # Declare queues
            self.channel.queue_declare(queue=settings.RABBITMQ_QUEUE_PATIENT_DATA, durable=True)
            self.channel.queue_declare(queue=settings.RABBITMQ_QUEUE_IMAGING_DATA, durable=True)
            self.channel.queue_declare(queue=settings.RABBITMQ_QUEUE_ALERTS, durable=True)

            logger.info("Connected to RabbitMQ")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
            self.connection = None
            self.channel = None

    def publish(self, topic: str, message: Dict) -> bool:
        """Publish a message to a queue"""
        if self.channel is None:
            logger.warning("RabbitMQ not connected")
            return False

        try:
            # Map topic to queue name
            queue_mapping = {
                "patient_data": settings.RABBITMQ_QUEUE_PATIENT_DATA,
                "imaging_data": settings.RABBITMQ_QUEUE_IMAGING_DATA,
                "alerts": settings.RABBITMQ_QUEUE_ALERTS,
            }
            queue_name = queue_mapping.get(topic, topic)

            message_body = json.dumps({
                **message,
                "timestamp": datetime.now().isoformat(),
            })

            self.channel.basic_publish(
                exchange="",
                routing_key=queue_name,
                body=message_body,
                properties=self.pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                ),
            )
            logger.debug(f"Published message to {queue_name}")
            return True
        except Exception as e:
            logger.error(f"Error publishing message: {str(e)}")
            return False

    def subscribe(
        self, topic: str, callback: Callable[[Dict], None], consumer_group: Optional[str] = None
    ):
        """Subscribe to a queue with a callback"""
        if self.channel is None:
            logger.warning("RabbitMQ not connected")
            return

        try:
            queue_mapping = {
                "patient_data": settings.RABBITMQ_QUEUE_PATIENT_DATA,
                "imaging_data": settings.RABBITMQ_QUEUE_IMAGING_DATA,
                "alerts": settings.RABBITMQ_QUEUE_ALERTS,
            }
            queue_name = queue_mapping.get(topic, topic)

            def on_message(ch, method, properties, body):
                try:
                    message = json.loads(body.decode("utf-8"))
                    callback(message)
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                except Exception as e:
                    logger.error(f"Error processing message: {str(e)}")
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

            self.channel.basic_consume(
                queue=queue_name, on_message_callback=on_message, auto_ack=False
            )
            logger.info(f"Subscribed to {queue_name}")

        except Exception as e:
            logger.error(f"Error subscribing to queue: {str(e)}")

    def close(self):
        """Close RabbitMQ connection"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            logger.info("RabbitMQ connection closed")


class KafkaQueue(MessageQueueInterface):
    """Kafka implementation"""

    def __init__(self):
        try:
            from kafka import KafkaProducer, KafkaConsumer
            from kafka.errors import KafkaError

            self.KafkaProducer = KafkaProducer
            self.KafkaConsumer = KafkaConsumer
            self.KafkaError = KafkaError
            self.producer = None
            self.consumers = {}
            self._connect_producer()
        except ImportError:
            logger.warning(
                "kafka-python not installed. Install with: pip install kafka-python"
            )
            self.KafkaProducer = None
            self.KafkaConsumer = None

    def _connect_producer(self):
        """Establish Kafka producer connection"""
        if self.KafkaProducer is None:
            return

        try:
            self.producer = self.KafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                acks="all",  # Wait for all replicas
                retries=3,
            )
            logger.info("Connected to Kafka producer")
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {str(e)}")
            self.producer = None

    def publish(self, topic: str, message: Dict) -> bool:
        """Publish a message to a Kafka topic"""
        if self.producer is None:
            logger.warning("Kafka producer not connected")
            return False

        try:
            # Map topic to Kafka topic name
            topic_mapping = {
                "patient_data": settings.KAFKA_TOPIC_PATIENT_DATA,
                "imaging_data": settings.KAFKA_TOPIC_IMAGING_DATA,
                "alerts": settings.KAFKA_TOPIC_ALERTS,
            }
            kafka_topic = topic_mapping.get(topic, topic)

            message_with_timestamp = {
                **message,
                "timestamp": datetime.now().isoformat(),
            }

            future = self.producer.send(kafka_topic, message_with_timestamp)
            future.get(timeout=10)  # Wait for message to be sent
            logger.debug(f"Published message to {kafka_topic}")
            return True
        except Exception as e:
            logger.error(f"Error publishing message: {str(e)}")
            return False

    def subscribe(
        self, topic: str, callback: Callable[[Dict], None], consumer_group: Optional[str] = None
    ):
        """Subscribe to a Kafka topic with a callback"""
        if self.KafkaConsumer is None:
            logger.warning("Kafka consumer not available")
            return

        try:
            topic_mapping = {
                "patient_data": settings.KAFKA_TOPIC_PATIENT_DATA,
                "imaging_data": settings.KAFKA_TOPIC_IMAGING_DATA,
                "alerts": settings.KAFKA_TOPIC_ALERTS,
            }
            kafka_topic = topic_mapping.get(topic, topic)

            consumer_group_id = consumer_group or f"{kafka_topic}_consumer"

            consumer = self.KafkaConsumer(
                kafka_topic,
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                group_id=consumer_group_id,
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                auto_offset_reset="latest",
                enable_auto_commit=True,
            )

            self.consumers[topic] = consumer

            # Start consuming in a separate thread
            import threading

            def consume_messages():
                for message in consumer:
                    try:
                        callback(message.value)
                    except Exception as e:
                        logger.error(f"Error processing message: {str(e)}")

            thread = threading.Thread(target=consume_messages, daemon=True)
            thread.start()

            logger.info(f"Subscribed to {kafka_topic}")

        except Exception as e:
            logger.error(f"Error subscribing to topic: {str(e)}")

    def close(self):
        """Close Kafka connections"""
        if self.producer:
            self.producer.close()
        for consumer in self.consumers.values():
            consumer.close()
        logger.info("Kafka connections closed")


class MessageQueueFactory:
    """Factory for creating message queue instances"""

    @staticmethod
    def create() -> MessageQueueInterface:
        """Create appropriate message queue based on configuration"""
        queue_type = settings.MESSAGE_QUEUE_TYPE.lower()

        if queue_type == "kafka":
            return KafkaQueue()
        elif queue_type == "rabbitmq":
            return RabbitMQQueue()
        else:
            logger.warning(
                f"Unknown queue type: {queue_type}. Defaulting to RabbitMQ"
            )
            return RabbitMQQueue()


# Global message queue instance
_message_queue: Optional[MessageQueueInterface] = None


def get_message_queue() -> MessageQueueInterface:
    """Get or create global message queue instance"""
    global _message_queue
    if _message_queue is None:
        _message_queue = MessageQueueFactory.create()
    return _message_queue

