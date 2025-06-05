from celery import shared_task
from celery_worker import app
from BaseAgent import BaseTask
from opentelemetry import trace
from opentelemetry.trace import SpanKind
# from .summ import summarize
import logging
import json

logger = logging.getLogger(__name__)


class colors:
    OKGREEN = "\033[92m"
    OKBLUE = "\033[94m"
    ENDC = "\033[0m"


# WORK IN PROGRESS - PLACEHOLDER
@app.task(base=BaseTask.BaseTask, bind=True)
def process_transcript(self, topic, message):
    with trace.get_tracer(__name__).start_as_current_span(
        "process_transcript", kind=SpanKind.PRODUCER
    ) as span:
        result = topic + "---" + message
        # adjusted_sleep_time = result * 2 / 1000  # Convert total to seconds and double it
        # # Simulate a blocking wait
        # time.sleep(adjusted_sleep_time)

        print(
            f"SummaryAgent {colors.OKGREEN}{topic}{colors.ENDC} + {colors.OKBLUE}{message}{colors.ENDC}"
        )
        # emit(event, data=None, room=None, skip_sid=None, namespace=None)
        print(self.sio)
        try:
            # self.sio.emit('celeryMessage', {'payloadString': message, 'destinationName': topic}, namespace='/celery') #
            client_id = self.extract_client_id(topic)
            print(f"client_id: {client_id}")
            message_data = json.loads(message)
            with trace.get_tracer(__name__).start_as_current_span(
                "redis_op"):
                if client_id: #must have client_id, otherwise it is a session_start or end
                    turns_counter = self.redis_client.llen(client_id) or 0
                    print(f"Turns counter: {turns_counter}")
                    if (turns_counter != 0) and (turns_counter % 2 == 0):
                        transcripts_obj = self.redis_client.lrange(client_id, 0, -1) # returns a list
                        # {"source":"internal","text":"example"}
                        transcripts_dicts = [json.loads(item) for item in transcripts_obj]
                        transcription_text = "\n".join(
                            f"{'Agent' if item['source'] == 'internal' else 'Customer'}: {item['text']}"
                            for item in transcripts_dicts
                        )
                        with trace.get_tracer(__name__).start_as_current_span(
                            "summarize"):
                            # new_summary = summarize(transcription_text)
                            new_summary = ""

                            if new_summary:
                                summary_topic = f"agent-assist/{client_id}/summarization"
                                summary_message = json.dumps(
                                    {
                                        "type": "summary",
                                        "parameters": {"text": new_summary, "final": False},
                                    }
                                )
                                try:
                                    self.sio.emit(
                                        "celeryMessage",
                                        {
                                            "payloadString": summary_message,
                                            "destinationName": summary_topic,
                                            'agent_id': message_data['agent_id']
                                        },
                                        namespace="/celery",
                                        
                                    )
                                except Exception as e:
                                    print(f"Error publishing extracted entities: {e}")
        except Exception as e:
            print(e)
    # the return result is stored in the celery backend
    return result
