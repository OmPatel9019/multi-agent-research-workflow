from langchain_core.messages import HumanMessage, SystemMessage
from backend import TravelState, llm


def final_agent(state: TravelState):
    final_prompt = f"""
Generate the final travel response for the user.

User Request:
{state.get('user_query', '')}

Flights:
{state.get('flight_results', 'No specific flights found.')}

Hotels:
{state.get('hotel_results', 'No specific hotels found.')}

Itinerary:
{state.get('itinerary', '')}

Format the final answer beautifully using these sections:

1. Trip Summary
2. Flight Information
3. Hotel Suggestions
4. Day-by-Day Itinerary
5. Estimated Budget
6. Final Recommendations

Important:
- Be clear, practical, and well-structured.
- Mention that live flight API provides live status and may not provide ticket prices if pricing is unavailable.
- Keep the response useful for real travel planning.
"""

    response = llm.invoke([
        SystemMessage(content="You are a professional AI travel booking assistant."),
        HumanMessage(content=final_prompt)
    ])

    return {
        "messages": [response],
        "llm_calls": state.get("llm_calls", 0) + 1
    }
