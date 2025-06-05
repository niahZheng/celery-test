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

    async def initialize_sio(self):
        if self._sio is None:
            self._sio = socketio.AsyncClient(logger=True, engineio_logger=True)
            await self._sio.connect(
                os.getenv("ANN_SOCKETIO_SERVER", "http://localhost:8000"),
                namespaces=["/celery"],
            )
            print("Socketio client initialized")
            self._sio_status = True
        else:
            print("Using existing socketio client")

    async def sio(self):
        if self._sio is None:
            await self.initialize_sio()
        print(self._sio)
        return self._sio

    async def await_sio_emit(self, event, data, namespace):
        sio = await self.sio()
        return await sio.emit(event, data, namespace)

    async def async_sio_emit(self, event, data, namespace):
        sio = await self.sio()
        print(sio)
        sio.emit(event, data, namespace)
    
    def get_sio_status(self):
        return self._sio_status

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
