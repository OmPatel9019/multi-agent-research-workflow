from langchain_core.messages import HumanMessage, SystemMessage
from backend import TravelState, llm, extract_text_content


async def planner_agent(state: TravelState):
    """Synthesizes flights, hotels, and travel preferences into a complete itinerary in a single LLM call."""
    user_query = state.get("user_query", "")
    flight_results = state.get("flight_results", "No specific live flights found.")
    hotel_results = state.get("hotel_results", "No specific hotels found.")

    prompt = f"""You are an elite AI Travel Concierge. Generate a comprehensive, realistic, and complete travel plan for:
"{user_query}"

### Live Flight Research:
{flight_results}

### Hotel & Lodging Research:
{hotel_results}

Format your final response cleanly with the following markdown sections:

# Trip Overview & Highlights
[Brief trip summary, vibe, best time to visit, and key highlights]

# Flight Options & Arrival
[Summary of available flight options, departure/arrival airports, and flight tips]

# Recommended Accommodations
[Top hotel recommendations with pricing expectations and why they match the traveler's budget]

# Day-by-Day Detailed Itinerary
IMPORTANT: Write out EVERY SINGLE DAY from Day 1 to the final day requested without cutting off or skipping.
For EACH day use this format:
### Day 1: [Catchy Title / Location Focus]
- **Morning**: [Specific activities & breakfast tip]
- **Afternoon**: [Sightseeing, cultural spots & lunch recommendation]
- **Evening**: [Sunset view, dinner venue & nightlife/relaxation]

### Day 2: [Title]
...
(Continue for ALL requested days completely)

# Estimated Budget Breakdown
[Realistic breakdown: Flights, Hotels, Food, Activities, Local Transport, and Total Estimate]

# Practical Travel Tips
[Local customs, transport cards, packing essentials, and safety recommendations]
"""

    response = await llm.ainvoke([
        SystemMessage(content="You are a professional AI travel booking assistant and itinerary architect. You always provide complete itineraries from Day 1 to the final day without cutting off."),
        HumanMessage(content=prompt)
    ])

    final_text = extract_text_content(response.content)

    return {
        "itinerary": final_text,
        "messages": [response],
        "llm_calls": state.get("llm_calls", 0) + 1
    }
