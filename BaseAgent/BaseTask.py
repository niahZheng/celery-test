from celery import Celery
import socketio
import redis
import os
import json

from celery import Task


class BaseTask(Task):
    _sio = None
    _redis_client = None
    _sio_status = False

    @property
    def sio(self):
        if self._sio is None:
            self._sio = socketio.Client(logger=True, engineio_logger=True)
            self._sio.connect(
                os.getenv("ANN_SOCKETIO_SERVER", "http://localhost:8000"),
                namespaces=["/celery"],
            )
            print("Socketio client initialized")
        return self._sio

    @property
    def redis_client(self):
        if self._redis_client is None:
            self._redis_client = redis.StrictRedis(
                host=os.getenv("AAN_REDIS_HOST", "localhost"),
                port=os.getenv("AAN_REDIS_PORT", 6379),
                db=os.getenv("AAN_REDIS_DB_INDEX", 2),
            )
            print("Starting Redis client")
        return self._redis_client

    def create_json(self, key, value):
        json_value = json.dumps(value)
        self._redis_client.set(key, json_value)

    def read_json(self, key):
        json_value = self._redis_client.get(key)
        if json_value:
            return json.loads(json_value)
        return None

    def update_json(self, key, value):
        json_value = json.dumps(value)
        if self._redis_client.exists(key):
            self._redis_client.set(key, json_value)
        else:
            raise KeyError(f"Key '{key}' does not exist in Redis")

    def delete(self, key):
        if self._redis_client.exists(key):
            self._redis_client.delete(key)
        else:
            raise KeyError(f"Key '{key}' does not exist in Redis")

    def append_to_list_json(self, key, value):
        """
        Append a value to the list stored at the given key.
        If the key does not exist, a new list is created.
        """
        json_value = json.dumps(value)
        self._redis_client.rpush(key, json_value)

    def get_list_len(self, key):
        """
        Returns length using LLEN for a key. Returns 0 when the key doesn't exist
        """
        return self._redis_client.llen(key)

    def extract_client_id(self, topic):
        """
        Get the client_id from an agent assist topic
        """
        # Split the input string by '/'
        parts = topic.split('/')
        
        # Check if there are at least three parts (two slashes)
        if len(parts) >= 3:
            # Return the string between the first and second slashes
            return parts[1]
        else:
            # If no UUID is found, return None
            return None
    
    def extract_event(self, topic):
        """
        Get the client_id from an agent assist topic
        """
        # Split the input string by '/'
        parts = topic.split('/')
        
        # Check if there are at least three parts (two slashes)
        if len(parts) >= 3:
            # Return the string between the first and second slashes
            return parts[2]
        else:
            # If no event is found, return None
            return None

    def extract_agent_id(self, message):
        """
        Get the agent_id from an agent assist message
        """
        try:
            message_data = json.loads(message)
            agent_id = message_data.get("agent_id", "")
            return agent_id
        except (json.JSONDecodeError, AttributeError):
            return None