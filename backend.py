import os
import operator
import logging
import certifi
from dotenv import load_dotenv
from typing import TypedDict, Annotated
from langchain_core.messages import AnyMessage

load_dotenv()

# Suppress internal SDK warnings about AFC in Models.generate_content
logging.getLogger("google_genai.models").setLevel(logging.ERROR)

os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()


def get_database_url() -> str:
    """Retrieve and format PostgreSQL database URL with SSL requirements."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL is missing. Please add your PostgreSQL database URL to .env")

    if "sslmode=" not in database_url:
        separator = "&" if "?" in database_url else "?"
        database_url = f"{database_url}{separator}sslmode=require"

    return database_url


def extract_text_content(content) -> str:
    """Helper to safely extract pure text from LLM response whether it's str or list."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            p.get("text", "") if isinstance(p, dict) else getattr(p, "text", str(p))
            for p in content
        )
    return str(content)


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
GROQ_MAX_TOKENS = int(os.getenv("GROQ_MAX_TOKENS", "4096"))

# Initialize LLM with fallback
candidate_models = []

if GEMINI_API_KEY:
    from langchain_google_genai import ChatGoogleGenerativeAI
    candidate_models.append(
        ChatGoogleGenerativeAI(
            model=GEMINI_MODEL,
            google_api_key=GEMINI_API_KEY,
            max_output_tokens=4096,
            thinking_budget=0,
            max_retries=1,
        )
    )
    # High-availability backup Gemini model if primary encounters 503 or 429
    backup_gemini = "gemini-3.5-flash-lite" if GEMINI_MODEL != "gemini-3.5-flash-lite" else "gemini-3.5-flash"
    candidate_models.append(
        ChatGoogleGenerativeAI(
            model=backup_gemini,
            google_api_key=GEMINI_API_KEY,
            max_output_tokens=4096,
            thinking_budget=0,
            max_retries=1,
        )
    )

if GROQ_API_KEY:
    from langchain_groq import ChatGroq
    candidate_models.append(
        ChatGroq(
            model=GROQ_MODEL,
            api_key=GROQ_API_KEY,
            max_tokens=GROQ_MAX_TOKENS,
        )
    )
    # Fallback to active Groq model if configured model encounters 404
    if GROQ_MODEL != "openai/gpt-oss-20b":
        candidate_models.append(
            ChatGroq(
                model="openai/gpt-oss-20b",
                api_key=GROQ_API_KEY,
                max_tokens=GROQ_MAX_TOKENS,
            )
        )

if not candidate_models:
    raise ValueError("Neither GEMINI_API_KEY nor GROQ_API_KEY was found in environment.")

llm = candidate_models[0] if len(candidate_models) == 1 else candidate_models[0].with_fallbacks(candidate_models[1:])


class TravelState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    user_query: str
    flight_results: str
    hotel_results: str
    itinerary: str
    llm_calls: Annotated[int, operator.add]


def run_travel_agent(user_input: str, thread_id: str | None = None):
    from db.postgres_model import run_travel_agent as _run
    return _run(user_input, thread_id)


def stream_travel_agent(user_input: str, thread_id: str | None = None):
    from db.postgres_model import stream_travel_agent as _stream
    return _stream(user_input, thread_id)
