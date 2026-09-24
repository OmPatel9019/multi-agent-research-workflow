import asyncio
from backend import TravelState
from tools.tavily_tool import tavily_search


async def hotel_agent(state: TravelState):
    query = f"Best hotels for {state.get('user_query', '')}"
    hotel_results = await asyncio.to_thread(tavily_search, query)

    return {
        "hotel_results": hotel_results
    }