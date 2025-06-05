from celery import shared_task
from celery_worker import app
from BaseAgent import BaseTask
import logging
import json

from opentelemetry import trace
from opentelemetry.trace import SpanKind

logger = logging.getLogger(__name__)

class colors:
    OKGREEN = '\033[92m'
    OKBLUE = '\033[94m'
    ENDC = '\033[0m'

@app.task(base=BaseTask.BaseTask, bind=True)
def process_transcript(self,topic, message):
    with trace.get_tracer(__name__).start_as_current_span("process_transcript", kind=SpanKind.PRODUCER) as span:
        result = topic + '---' + message
        print(f"TranscriptAgent {colors.OKGREEN}{topic}{colors.ENDC} + {colors.OKBLUE}{message}{colors.ENDC}")
        # print(self.sio)
        message_headers = process_transcript.request.headers
        
        # Extract baggage items from message headers
        # Seems like the node app isn't sending any baggage properly from the auto instrumentation
        baggage = {}
        print(message_headers)
        if message_headers is not None and not message_headers:
            for key, value in message_headers.items():
                logger.debug(f"headers: {key}={value}")
                print(f"headers: {key}={value}")
                if key.startswith('baggage-'):
                    baggage[key[len('baggage-'):]] = value
            
            # Process baggage items as needed
            for key, value in baggage.items():
                logger.debug(f"Baggage: {key}={value}")
        message_data = json.loads(message)
        try:
            with trace.get_tracer(__name__).start_as_current_span("emit_socketio") as child_span:
                #self.await_sio_emit('celeryMessage', {'payloadString': message, 'destinationName': topic}, namespace='/celery')

                self.sio.emit('celeryMessage', {'payloadString': message, 'destinationName': topic, 'agent_id': message_data['agent_id']}, namespace='/celery')
                # self.redis_client.append_to_list_json()
        except Exception as e:
            print(e)
    # the return result is stored in the celery backend
    return result