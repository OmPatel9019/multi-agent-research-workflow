from langchain_core.messages import HumanMessage, SystemMessage
from backend import TravelState, llm, extract_text_content


def itinerary_agent(state: TravelState):
    prompt = f"""
Create a complete travel itinerary.

User Query:
{state.get('user_query', '')}

Flight Results:
{state.get('flight_results', 'No specific flights found.')}

Hotel Results:
{state.get('hotel_results', 'No specific hotels found.')}

Make the itinerary practical, budget-aware, and easy to follow.
"""

    response = llm.invoke([
        SystemMessage(content="You are an expert travel planner."),
        HumanMessage(content=prompt)
    ])

    return {
        "itinerary": extract_text_content(response.content),
        "messages": [response],
        "llm_calls": state.get("llm_calls", 0) + 1
    }