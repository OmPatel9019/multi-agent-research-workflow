import uuid
import json
import asyncio
import psycopg
from psycopg.rows import dict_row
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage

from backend import get_database_url, extract_text_content
from workflows.Stategraph import graph

_checkpointer = None
_conn = None


def get_checkpointer():
    """Returns singleton checkpointer supporting both async and sync graph execution."""
    global _checkpointer
    if _checkpointer is None:
        _checkpointer = MemorySaver()
    return _checkpointer


# Compile the multi-agent graph with singleton checkpointer
checkpointer = get_checkpointer()
travel_graph = graph.compile(checkpointer=checkpointer)


def run_travel_agent(user_input: str, thread_id: str | None = None) -> dict:
    """Executes the multi-agent travel workflow synchronously (e.g. for CLI/scripts)."""
    if not thread_id:
        thread_id = f"user_{uuid.uuid4().hex}"

    config = {"configurable": {"thread_id": thread_id}}

    init_state = {
        "messages": [HumanMessage(content=user_input)],
        "user_query": user_input,
        "flight_results": "",
        "hotel_results": "",
        "itinerary": "",
        "llm_calls": 0,
    }

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            result = pool.submit(asyncio.run, travel_graph.ainvoke(init_state, config=config)).result()
    else:
        result = asyncio.run(travel_graph.ainvoke(init_state, config=config))

    raw_answer = result["messages"][-1].content if result.get("messages") else "No response generated."
    final_answer = extract_text_content(raw_answer)

    return {
        "thread_id": thread_id,
        "answer": final_answer,
        "flight_results": result.get("flight_results", ""),
        "hotel_results": result.get("hotel_results", ""),
        "itinerary": result.get("itinerary", final_answer),
        "llm_calls": result.get("llm_calls", 1),
    }


async def stream_travel_agent(user_input: str, thread_id: str | None = None):
    """Streams graph lifecycle events and live LLM tokens to provide real-time UI feedback."""
    if not thread_id:
        thread_id = f"user_{uuid.uuid4().hex}"

    config = {"configurable": {"thread_id": thread_id}}

    init_state = {
        "messages": [HumanMessage(content=user_input)],
        "user_query": user_input,
        "flight_results": "",
        "hotel_results": "",
        "itinerary": "",
        "llm_calls": 0,
    }

    full_answer_tokens = []
    flight_results_collected = ""
    hotel_results_collected = ""

    # Stream graph lifecycle and token events
    async for event in travel_graph.astream_events(init_state, config=config, version="v2"):
        kind = event.get("event")
        name = event.get("name")

        # 1. Pipeline Stage Indicators (Feedback Loops)
        if kind == "on_chain_start" and name in ["flight_agent", "hotel_agent", "planner_agent"]:
            stage_messages = {
                "flight_agent": ("flight", "Searching live flight schedules & availability..."),
                "hotel_agent": ("hotel", "Researching top hotels & accommodations..."),
                "planner_agent": ("planner", "Crafting comprehensive itinerary, budget & recommendations..."),
            }
            stage_key, stage_desc = stage_messages.get(name, (name, f"Executing {name}..."))
            yield f"event: status\ndata: {json.dumps({'stage': stage_key, 'message': stage_desc})}\n\n"

        # 2. Capture completed tool payloads when research completes
        elif kind == "on_chain_end" and name in ["flight_agent", "hotel_agent"]:
            output_data = event.get("data", {}).get("output", {})
            if "flight_results" in output_data:
                flight_results_collected = output_data["flight_results"]
                yield f"event: research\ndata: {json.dumps({'type': 'flights', 'content': flight_results_collected})}\n\n"
            if "hotel_results" in output_data:
                hotel_results_collected = output_data["hotel_results"]
                yield f"event: research\ndata: {json.dumps({'type': 'hotels', 'content': hotel_results_collected})}\n\n"

        # 3. Live Token Streaming from Planner LLM
        elif kind == "on_chat_model_stream":
            chunk = event.get("data", {}).get("chunk")
            if chunk:
                text = extract_text_content(getattr(chunk, "content", ""))
                if text:
                    full_answer_tokens.append(text)
                    yield f"event: token\ndata: {json.dumps({'token': text})}\n\n"

    # Final summary event
    complete_text = "".join(full_answer_tokens).strip()

    yield f"event: done\ndata: {json.dumps({'thread_id': thread_id, 'answer': complete_text, 'flight_results': flight_results_collected, 'hotel_results': hotel_results_collected})}\n\n"