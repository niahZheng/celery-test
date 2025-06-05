from celery import shared_task
from celery_worker import app
from BaseAgent import BaseTask
import logging
import json
import re

from opentelemetry import trace
from opentelemetry.trace import SpanKind

logger = logging.getLogger(__name__)

class colors:
    OKGREEN = '\033[92m'
    OKBLUE = '\033[94m'
    ENDC = '\033[0m'

def update_action_status(session_id, action_id, status):
    if session_id in actions:
        for action in actions[session_id]:
            if action['action_id'] == action_id:
                action['status'] = status
                break
def publish_action(client, session_id, action, action_id,options=[]):
    if action=="noresponse":
        return
    topic = f"agent-assist/{session_id}/nextbestaction"
    message = json.dumps({
        "type": "new_action",
        "parameters": {
            "text": action,
            "action_id": action_id,
            "options": options 
        }
    })

    logging.info(f"Publishing action to {topic}: {message}")
    result = client.publish(topic, message)
    logging.info(f"Publish result: {result.rc}")

# WORK IN PROGRESS - PLACEHOLDER
# this runs after cache agent, which means the transcriptions are there
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
            f"NextBestAction {colors.OKGREEN}{topic}{colors.ENDC} + {colors.OKBLUE}{message}{colors.ENDC}"
        )
        # emit(event, data=None, room=None, skip_sid=None, namespace=None)
        print(self.sio)
        try:
            # self.sio.emit('celeryMessage', {'payloadString': message, 'destinationName': topic}, namespace='/celery') #
            client_id = self.extract_client_id(topic)
            print(f"initial client_id: {client_id}")
            with trace.get_tracer(__name__).start_as_current_span(
                "redis_op"):
                message_data = json.loads(message)
                # check what kind of event it is
                event_type = self.extract_event(topic)
                session_id_pattern = re.compile(r"agent-assist/([^/]+)/.*") 
                match = session_id_pattern.match(topic)

                if topic == "agent-assist/session" and message_data['type'] == 'session_started':
                    # create wa session and store in redis
                    # create actions list and store in redis
                    # actually you can't have empty lists in redis
                    # self.redis_client.rpush(client_id + '_actions', json.dumps())
                    client_id = message_data['parameters']['session_id']
                    # wa_session_id = create_session()
                    wa_session_id = "123"

                    print(f"client_id: {client_id} - wa_session_id {wa_session_id}")
                    self.redis_client.set(client_id + '_nba_wa', wa_session_id)
                elif match and message_data['type'] == 'session_ended':
                    self.redis_client.delete(client_id + '_nba_wa')
                    self.redis_client.delete(client_id + '_nba_actions')
                elif event_type == 'transcription':
                    # external - GNBA
                    # internal - check completion
                    #last_transcript = json.loads(self.redis_client.lindex(client_id, -1))
                    message_data = json.loads(message)
                    last_transcript = message_data["parameters"]

                    wa_session = self.redis_client.get(client_id + '_nba_wa')
                    print(f"client_id: {client_id} - redis_wa_session_id {wa_session}")
                    print(f"last_transcript: {last_transcript}")
                    if last_transcript['source'] == 'external':
                        #check if there is an active action
                        nba_length = self.redis_client.llen(client_id + '_nba_actions')
                        print(f"nba_length {nba_length}")
                        if nba_length == 0:
                            # action, options = generate_next_best_action(client_id, last_transcript["text"],wa_session) 
                            action = "noresponse"
                            options = []
                            logging.info(f"Generated action for session {client_id}: {action}")
                            if action and action !="noresponse":
                                # since actions are distributed, maybe this action_id thing is inefficient?
                                # maybe the action IDs can be random
                                # or they should be defined on the WA skill itself
                                action_id = self.redis_client.llen(client_id + '_nba_actions') or 0
                                action_payload = {"action_id": action_id, "action": action, "status": "pending"}
                                self.redis_client.rpush(client_id + '_nba_actions', json.dumps(action_payload) )
                                # emit messages to UI
                                #publish_action(client, client_id, action, action_id,options)
                                celeryMessage = json.dumps({
                                    "type": "new_action",
                                    "parameters": {
                                        "text": action,
                                        "action_id": action_id,
                                        "options": options 
                                    }
                                })
                                celeryTopic = f"agent-assist/{client_id}/nextbestaction"
                                self.sio.emit(
                                        "celeryMessage",
                                        {
                                            "payloadString": celeryMessage,
                                            "destinationName": celeryTopic,
                                            'agent_id': message_data['agent_id']
                                        },
                                        namespace="/celery",
                                        
                                )
                    elif last_transcript['source'] == 'internal':
                        #actions = json.loads(self.redis_client.lindex(client_id + '_nba_actions', -1) or "[]")
                        actions = self.redis_client.lrange(client_id + '_nba_actions', 0, -1) or []
                        # actions is array of:
                        # {"action_id": action_id, "action": action, "status": "pending"}

                        # completed_action_ids_idxs, completed_actions_ids = check_action_completion(client_id, last_transcript["text"],actions)
                        completed_action_ids_idxs = []
                        completed_actions_ids = []

                        # completed_action_ids is a list of action_ids
                        # updates the actions list in redis with completed status

                        # first we emit all the action IDs that are completed for the frontend (fast!)
                        for action_id in completed_actions_ids:
                            celeryTopic = f"agent-assist/{client_id}/nextbestaction"
                            celeryMessage = json.dumps({
                                "type": "completed_action",
                                "parameters": {
                                    "action_id": action_id
                                }
                            })
                            self.sio.emit(
                                    "celeryMessage",
                                    {
                                        "payloadString": celeryMessage,
                                        "destinationName": celeryTopic,
                                        'agent_id': message_data['agent_id']
                                    },
                                    namespace="/celery",
                                    
                            )
                        # then we update those action indexs on redis
                        #self.redis_client.ltrim(client_id + '_nba_actions', 99 , 0) # we delete it

                        ## TODO we need to finish the action on assistant and then reset the action object

                        # for action_id_idx in completed_action_ids_idxs:
                        #     existing_action = action[action_id_idx]
                        #     existing_action['status'] =  "completed"
                        #     self.redis_client.lset(client_id + '_nba_actions', action_id_idx, json.dumps(existing_action))                          
                #  `agent-assist/${session_id}/nextbestaction-completion`
                elif match and message_data['type'] == 'manual_completion':
                    # agent clicked on UI
                    wa_session = self.redis_client.get(client_id + '_nba_wa')
                    # action, options = generate_next_best_action(client_id, message_data['parameters']['text'],wa_session,True) 
                    if action:
                            action_id = self.redis_client.llen(client_id + '_nba_actions') or 0
                            action_payload = {"action_id": action_id, "action": action, "status": "pending"}
                            self.redis_client.rpush(client_id + '_nba_actions', json.dumps(action_payload) )
                            # emit messages to UI
                            #publish_action(client, client_id, action, action_id,options)
                            celeryMessage = json.dumps({
                                "type": "new_action",
                                "parameters": {
                                    "text": action,
                                    "action_id": action_id,
                                    "options": options 
                                }
                            })
                            celeryTopic = f"agent-assist/{client_id}/nextbestaction"
                            self.sio.emit(
                                    "celeryMessage",
                                    {
                                        "payloadString": celeryMessage,
                                        "destinationName": celeryTopic,
                                        'agent_id': message_data['agent_id']
                                    },
                                    namespace="/celery",
                                    
                            )
        except Exception as e:
            print(e)
    # the return result is stored in the celery backend
    return result
