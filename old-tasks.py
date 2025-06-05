
import time
from celery import Celery
import socketio

from celery import Task

class SocketioTask(Task):
    _sio = None

    @property
    def sio(self):
        if self._sio is None:
            self._sio = socketio.Client(logger=True, engineio_logger=True)
            self._sio.connect('http://localhost:8000', namespaces=['/celery']) 
            print("Starting Socketio")
        return self._sio


app = Celery('tasks', broker='amqp://admin:adminpass@localhost:5672', backend="redis://localhost:6379/1")
      #- CELERY_BROKER_LINK=${CELERY_BROKER_LINK-amqp://admin:adminpass@rabbitmq}

class colors:
    OKGREEN = '\033[92m'
    OKBLUE = '\033[94m'
    ENDC = '\033[0m'


# @sio.event
# def connect():
#     print('Connected to API Socketio')

# @sio.event
# def disconnect():
#     print('Disconnected from API Socketio')

# # Start Socket.IO client
# def start_socket_client():
#     sio.connect('http://localhost:8000')  # Adjust URL as per your setup
#     #  sio.connect('http://localhost:8000', namespaces=['/celery'])  # Adjust URL as per your setup
#     #sio.wait()


# print("Starting Socketio")
# start_socket_client()

# Define the task
@app.task
def add(x, y):
    result = x + y
    adjusted_sleep_time = result * 2 / 1000  # Convert total to seconds and double it
    # Simulate a blocking wait
    time.sleep(adjusted_sleep_time)

    print(f"The result of {x} + {y} is {colors.OKGREEN}{result}{colors.ENDC} at {colors.OKBLUE}{adjusted_sleep_time:.3f} seconds{colors.ENDC}")

    # the return result is stored in the celery backend
    return result

# Define the task
@app.task(base=SocketioTask, bind=True)
def echo(self,topic, message):
    result = topic + '---' + message
    # adjusted_sleep_time = result * 2 / 1000  # Convert total to seconds and double it
    # # Simulate a blocking wait
    # time.sleep(adjusted_sleep_time)

    print(f"Received {colors.OKGREEN}{topic}{colors.ENDC} + {colors.OKBLUE}{message}{colors.ENDC}")
    # emit(event, data=None, room=None, skip_sid=None, namespace=None)
    print(self.sio)
    try:
        self.sio.emit('celeryMessage', {'payloadString': message, 'destinationName': topic}, namespace='/celery') #
    except Exception as e:
        print(e)
    # the return result is stored in the celery backend
    return result


# @sio.on('connect')
# def on_connect():
#     print("I'm connected to the default namespace!")
#     sio.emit('celeryMessage', {'payloadString': 'test', 'destinationName': 'atopic'})



# Start the Celery worker
if __name__ == '__main__':
    app.worker_main()
    # print("Starting Socketio")
    # start_socket_client()