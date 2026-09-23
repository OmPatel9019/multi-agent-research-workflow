from langgraph.graph import StateGraph, START, END
from backend import TravelState
from agents.flight_agent import flight_agent
from agents.hotel_agent import hotel_agent
from agents.Itinerary_agent import itinerary_agent
from agents.final_response_agent import final_agent

graph = StateGraph(TravelState)

graph.add_node("flight_agent", flight_agent)
graph.add_node("hotel_agent", hotel_agent)
graph.add_node("itinerary_agent", itinerary_agent)
graph.add_node("final_agent", final_agent)

graph.add_edge(START, "flight_agent")
graph.add_edge("flight_agent", "hotel_agent")
graph.add_edge("hotel_agent", "itinerary_agent")
graph.add_edge("itinerary_agent", "final_agent")
graph.add_edge("final_agent", END)