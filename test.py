from tools.tavily_tool import tavily_search
from tools.flight_tool import search_flights
from backend import run_travel_agent

# tavily_search is already a function that connects to Tavily and formats the output
# res = tavily_search("What is the famous tourist places in India")

# print(res)

# res = search_flights("Plan a 7 days Japan trip from India")
# print(res)

user_input = input("Enter travel request: ")

response = run_travel_agent(
    user_input=user_input,
    thread_id="test_user"
)

print("\nFINAL RESPONSE:\n")
print(response["answer"])