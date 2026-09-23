from langchain_core.messages import AIMessage
from backend import TravelState
from tools.tavily_tool import tavily_search


def hotel_agent(state: TravelState):
    query = f"Best hotels for {state.get('user_query', '')}"
    hotel_results = tavily_search(query)

    return {
        "hotel_results": hotel_results,
        "messages": [
            AIMessage(content="Hotel information fetched.")
        ],
        "llm_calls": state.get("llm_calls", 0) + 1
    }