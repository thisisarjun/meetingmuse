from common.logger import Logger
from meetingmuse.graph.graph import GraphBuilder
from meetingmuse.models.node import NodeName
from meetingmuse.models.state import MeetingMuseBotState
from scripts.chatbot import ChatBot
from scripts.common import initialize_nodes

logger = Logger()
nodes = initialize_nodes()
model = nodes["model"]
intent_classifier = nodes["intent_classifier"]
meeting_details_service = nodes["meeting_details_service"]
conversation_router = nodes["conversation_router"]

classify_intent_node = nodes[NodeName.CLASSIFY_INTENT]
greeting_node = nodes[NodeName.GREETING]
collecting_info_node = nodes[NodeName.COLLECTING_INFO]
clarify_request_node = nodes[NodeName.CLARIFY_REQUEST]
human_schedule_meeting_more_info_node = nodes[NodeName.HUMAN_SCHEDULE_MEETING_MORE_INFO]
prompt_missing_meeting_details_node = nodes[NodeName.PROMPT_MISSING_MEETING_DETAILS]
schedule_meeting_node = nodes[NodeName.SCHEDULE_MEETING]
human_interrupt_retry_node = nodes[NodeName.HUMAN_INTERRUPT_RETRY]
end_node = nodes[NodeName.END]


if __name__ == "__main__":
    graph_builder = GraphBuilder(
        state=MeetingMuseBotState,
        greeting_node=greeting_node,
        clarify_request_node=clarify_request_node,
        collecting_info_node=collecting_info_node,
        schedule_meeting_node=schedule_meeting_node,
        human_interrupt_retry_node=human_interrupt_retry_node,
        conversation_router=conversation_router,
        classify_intent_node=classify_intent_node,
        human_schedule_meeting_more_info_node=human_schedule_meeting_more_info_node,
        prompt_missing_meeting_details_node=prompt_missing_meeting_details_node,
        end_node=end_node,
    )
    graph = graph_builder.build()
    chatbot = ChatBot(graph)

    while True:
        try:
            user_input = input("User: ")
            if user_input.lower() in ["quit", "exit", "q"]:
                print("Goodbye!")
                break
            chatbot.process_input(user_input)
        except Exception as e:
            print(e)
            break
