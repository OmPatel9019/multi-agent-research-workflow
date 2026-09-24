import asyncio
from backend import TravelState
from tools.flight_tool import search_flights


async def flight_agent(state: TravelState):
    query = state.get("user_query", "")
    flight_data = await asyncio.to_thread(search_flights, query)

    return {
        "flight_results": flight_data
    }