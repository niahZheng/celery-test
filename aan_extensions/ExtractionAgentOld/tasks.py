from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from celery_worker import app
from BaseAgent import BaseTask
# from .entity import process_message
import json
import logging

from opentelemetry import trace
from opentelemetry.trace import SpanKind

logger = logging.getLogger(__name__)

class colors:
    OKGREEN = '\033[92m'
    OKBLUE = '\033[94m'
    ENDC = '\033[0m'

@app.task(base=BaseTask.BaseTask, bind=True, soft_time_limit=5)
def process_transcript(self,topic, message):
    with trace.get_tracer(__name__).start_as_current_span("process_transcript", kind=SpanKind.PRODUCER) as span:
        try:
            result = topic + '---' + message
            print(f"ExtractionAgent {colors.OKGREEN}{topic}{colors.ENDC} + {colors.OKBLUE}{message}{colors.ENDC}")
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
                with trace.get_tracer(__name__).start_as_current_span("extract_entities") as child_span:
                    #self.await_sio_emit('celeryMessage', {'payloadString': message, 'destinationName': topic}, namespace='/celery')
                    #self.sio.emit('celeryMessage', {'payloadString': message, 'destinationName': topic}, namespace='/celery')
                    # self.redis_client.append_to_list_json()

                    # extract client_id from topic
                    # extract transcript from message
                    #{"type":"transcription","parameters":{"source":"internal","text":"excellent okay what color did you want the new yorker in ","seq":7,"timestamp":24.04}} on topic: agent-assist/87ba0766-efc7-42c8-b2ec-af829f6b73ce/transcription
                    #{"type":"session_ended"} on topic: agent-assist/87ba0766-efc7-42c8-b2ec-af829f6b73ce
                    client_id = self.extract_client_id(topic)
                    logger.debug(f"client_id: {client_id}")

                    try:
                        message_data = json.loads(message)
                        transcript = message_data.get("parameters", {}).get("text", None)
                    except (json.JSONDecodeError, AttributeError):
                        return None
                    if transcript:
                        # extracted_entities = process_message(transcript) 
                        extracted_entities = {}
                        for title, value in extracted_entities.items():
                            if value:
                                entities_topic = f"agent-assist/{client_id}/extraction"
                                entities_message = json.dumps({
                                    "type": "extraction",
                                    "parameters": {
                                        "title": title,
                                        "value": value }
                                })
                                try:
                                    self.sio.emit('celeryMessage', {'payloadString': entities_message, 'destinationName': entities_topic, 'agent_id': message_data['agent_id']}, namespace='/celery')
                                    # result = client.publish(entities_topic, entities_message)
                                    # if result.rc == mqtt.MQTT_ERR_SUCCESS:
                                    #     print(f"Published extracted entity for {client_id}: {title}: {value}")
                                    # else:
                                    #     print(f"Failed to publish extracted entity for {client_id}, Error: {result.rc}")
                                except Exception as e:
                                    print(f"Error publishing extracted entities: {e}")

            except Exception as e:
                print(e)
        except SoftTimeLimitExceeded as e:
            #cleanup - in the future we could cancel a request object here
            logger.debug("Time Exceeded for task")
        return result
    # the return result is stored in the celery backend
