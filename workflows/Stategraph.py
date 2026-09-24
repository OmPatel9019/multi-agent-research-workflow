from langgraph.graph import StateGraph, START, END
from backend import TravelState
from agents.flight_agent import flight_agent
from agents.hotel_agent import hotel_agent
from agents.planner_agent import planner_agent

graph = StateGraph(TravelState)

# Nodes
graph.add_node("flight_agent", flight_agent)
graph.add_node("hotel_agent", hotel_agent)
graph.add_node("planner_agent", planner_agent)

# Parallel Fan-Out: Execute flight research & hotel research concurrently
graph.add_edge(START, "flight_agent")
graph.add_edge(START, "hotel_agent")

# Fan-In: Once both research agents finish, run unified planner in a single LLM pass
graph.add_edge(["flight_agent", "hotel_agent"], "planner_agent")
graph.add_edge("planner_agent", END)
