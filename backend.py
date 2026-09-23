import os
import operator
import certifi
from dotenv import load_dotenv
from typing import TypedDict, Annotated

from langchain_core.messages import AnyMessage, HumanMessage, AIMessage, SystemMessage
from langchain_groq import ChatGroq

load_dotenv()

os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()


def get_database_url() -> str:
    """Retrieve and format PostgreSQL database URL with SSL requirements."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError(
            "DATABASE_URL is missing. Please add your PostgreSQL database URL to .env"
        )

    if "sslmode=" not in database_url:
        separator = "&" if "?" in database_url else "?"
        database_url = f"{database_url}{separator}sslmode=require"

    return database_url


GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is missing. Please add it to your .env file.")

GROQ_MODEL = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")
GROQ_MAX_TOKENS = int(os.getenv("GROQ_MAX_TOKENS", "800"))

# Shared LLM instance
llm = ChatGroq(
    model=GROQ_MODEL,
    api_key=GROQ_API_KEY,
    max_tokens=GROQ_MAX_TOKENS
)


# State definition for the multi-agent graph
class TravelState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    user_query: str
    flight_results: str
    hotel_results: str
    itinerary: str
    llm_calls: int


# Re-export runner function
def run_travel_agent(user_input: str, thread_id: str | None = None):
    from db.postgres_model import run_travel_agent as _run
    return _run(user_input, thread_id)
