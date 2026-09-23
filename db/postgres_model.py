import uuid
import psycopg
from psycopg.rows import dict_row
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage

from backend import get_database_url
from workflows.Stategraph import graph

# Database checkpointer initialization with fallback
try:
    DATABASE_URL = get_database_url()
    _conn = psycopg.connect(
        DATABASE_URL,
        autocommit=True,
        row_factory=dict_row
    )
    checkpointer = PostgresSaver(_conn)
    checkpointer.setup()
except Exception as e:
    print(f"Warning: Could not connect to PostgreSQL checkpointer ({e}). Using in-memory checkpointer fallback.")
    checkpointer = MemorySaver()

travel_graph = graph.compile(checkpointer=checkpointer)


# Main runner function
def run_travel_agent(user_input: str, thread_id: str | None = None) -> dict:
    """Executes the multi-agent travel workflow for a given user query."""
    if not thread_id:
        thread_id = f"user_{uuid.uuid4().hex}"

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    result = travel_graph.invoke(
        {
            "messages": [
                HumanMessage(content=user_input)
            ],
            "user_query": user_input,
            "flight_results": "",
            "hotel_results": "",
            "itinerary": "",
            "llm_calls": 0
        },
        config=config
    )

    final_answer = result["messages"][-1].content if result.get("messages") else "No response generated."

    return {
        "thread_id": thread_id,
        "answer": final_answer,
        "flight_results": result.get("flight_results", ""),
        "hotel_results": result.get("hotel_results", ""),
        "itinerary": result.get("itinerary", ""),
        "llm_calls": result.get("llm_calls", 0),
    }