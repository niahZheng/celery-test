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
        print(f"CacheAgent {colors.OKGREEN}{topic}{colors.ENDC} + {colors.OKBLUE}{message}{colors.ENDC}")
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

        try:
            with trace.get_tracer(__name__).start_as_current_span("save_redis") as child_span:
                #self.await_sio_emit('celeryMessage', {'payloadString': message, 'destinationName': topic}, namespace='/celery')
                #self.sio.emit('celeryMessage', {'payloadString': message, 'destinationName': topic}, namespace='/celery')
                #{"type":"transcription","parameters":{"source":"internal","text":"excellent okay what color did you want the new yorker in ","seq":7,"timestamp":24.04}} on topic: agent-assist/87ba0766-efc7-42c8-b2ec-af829f6b73ce/transcription
                #{"type":"session_ended"} on topic: agent-assist/87ba0766-efc7-42c8-b2ec-af829f6b73ce
                client_id = self.extract_client_id(topic)
                logger.debug(f"client_id: {client_id}")

                try:
                    message_data = json.loads(message)
                    if message_data.get("type", "") == "transcription":
                        transcript_obj = message_data.get("parameters", {})#.get("text", None)
                        print(f"Saving rpush {transcript_obj}")
                        self.redis_client.rpush(client_id, json.dumps(transcript_obj))
                except (json.JSONDecodeError, AttributeError):
                    return None
        except Exception as e:
            print(e)
    # the return result is stored in the celery backend
    return result