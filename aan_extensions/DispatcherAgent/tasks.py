# import ExtractionAgent.tasks
# import TranscriptionAgent.tasks
from celery import chain, group
from celery_worker import app
from BaseAgent import BaseTask
from aan_extensions import TranscriptionAgent, CacheAgent, SummaryAgent, NextBestActionAgent

import logging

from opentelemetry import trace
from opentelemetry.trace import SpanKind

logger = logging.getLogger(__name__)

class colors:
    OKGREEN = '\033[92m'
    OKBLUE = '\033[94m'
    ENDC = '\033[0m'

@app.task(base=BaseTask.BaseTask, bind=True)
def process_transcript(self,topic, message):
    result = {}
    with trace.get_tracer(__name__).start_as_current_span("process_transcript", kind=SpanKind.PRODUCER) as span:
        try:
            with trace.get_tracer(__name__).start_as_current_span("dispatch_tasks") as child_span:
                TranscriptionAgent.tasks.process_transcript.s(topic, message).apply_async()
                
                # Moving extraction to after CacheAgent since it needs full transcripts
                # ExtractionAgent.tasks.process_transcript.s(topic,message).apply_async()
                NextBestActionAgent.tasks.process_transcript.s(topic,message).apply_async()
                chained_tasks = chain(
                    CacheAgent.tasks.process_transcript.s(topic,message),
                   # NextBestActionAgent.tasks.process_transcript.si(topic,message),
                    # SummaryAgent.tasks.process_transcript.si(topic,message)
                    group(
                         SummaryAgent.tasks.process_transcript.si(topic,message)
                    )
                )
                chained_tasks.apply_async()
                #self.await_sio_emit('celeryMessage', {'payloadString': message, 'destinationName': topic}, namespace='/celery')
                # self.sio.emit('celeryMessage', {'payloadString': message, 'destinationName': topic}, namespace='/celery')
                # self.redis_client.append_to_list_json()
        except Exception as e:
            print(e)
    # the return result is stored in the celery backend
    return result