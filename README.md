# Traverly AI — A Multi-Agent Travel Planner with LangGraph

An open-source AI travel planner that turns a natural-language trip request into a practical travel plan with flight suggestions, hotel ideas, and a day-by-day itinerary. The project uses a multi-agent workflow built with LangGraph, LangChain, and FastAPI.

## Why this project?

Planning a trip usually means jumping between multiple websites, tools, and spreadsheets. This project brings that flow into one experience by combining:

- a flight-search agent,
- a hotel-research agent,
- an itinerary-planning agent, and
- a final response agent,

all coordinated through a LangGraph workflow.

## Features

- ✈️ **Flight research** using AviationStack
- 🏨 **Hotel suggestions** using Tavily search
- 🧠 **Multi-agent orchestration** with LangGraph
- 📝 **Structured travel itinerary generation**
- 🌐 **FastAPI backend** with a clean web interface
- 💾 **Conversation state persistence** using PostgreSQL
- ⚡ **LLM-powered responses** with Groq & Google Gemini
- 🐳 **Docker ready** with Dockerfile and Docker Compose support

## Tech Stack

- Python 3.10+
- FastAPI
- Jinja2 + HTML/CSS/JavaScript frontend
- LangGraph
- LangChain
- Groq & Google Gemini LLMs
- PostgreSQL
- Tavily API
- AviationStack API
- Docker & Docker Compose

## Project Structure

```text
.
├── agents/               # Multi-agent definitions (flight, hotel, itinerary, final)
├── db/                   # Database connection and state checkpointing
├── static/               # Static frontend assets (CSS, JS, icons)
├── templates/            # HTML templates (Jinja2)
├── tools/                # Flight (AviationStack) and search (Tavily) integrations
├── workflows/            # LangGraph workflow definition & state schemas
├── app.py                # FastAPI app entry point & route definitions
├── backend.py            # LangGraph travel workflow runner
├── Dockerfile            # Container definition
├── docker-compose.yml    # Docker service orchestration
└── requirements.txt      # Python dependencies
```

## Prerequisites

Before running the project locally, make sure you have:

- Python 3.10 or newer installed
- PostgreSQL running and accessible (or a cloud PostgreSQL instance such as Render/Neon/Supabase)
- API keys for:
  - Groq (or Google Gemini)
  - Tavily
  - AviationStack

## Environment Variables

Create a `.env` file in the project root with the following variables:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/travel_db
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.1-8b-instant
GOOGLE_API_KEY=your_google_api_key
GEMINI_MODEL=gemini-2.5-flash
AVIATIONSTACK_API_KEY=your_aviationstack_api_key
TAVILY_API_KEY=your_tavily_api_key
DEFAULT_ORIGIN_IATA=DAC
```

## Installation & Setup

### 1. Local Environment

```bash
# Clone the repository
git clone https://github.com/your-username/trip-planner.git
cd trip-planner

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 2. Running with Docker (Alternative)

```bash
docker compose up --build
```

## Running the App

Start the FastAPI server:

```bash
python app.py
```

Then open your browser at:

```text
http://127.0.0.1:8000/
```

## API Endpoints

- `GET /health` — Health check
- `GET /` — Interactive web application UI
- `POST /api/travel` — Submit a travel request

### Example Request

```bash
curl -X POST http://127.0.0.1:8000/api/travel \
  -H "Content-Type: application/json" \
  -d '{"message":"Plan a 3-day trip to Tokyo with a budget of $1200"}'
```

## How the Workflow Works

```mermaid
flowchart TD
    User([User Request]) --> FlightAgent[Flight Search Agent]
    FlightAgent --> HotelAgent[Hotel Research Agent]
    HotelAgent --> ItineraryAgent[Itinerary Planning Agent]
    ItineraryAgent --> FinalAgent[Final Response Agent]
    FinalAgent --> Output([Structured Travel Plan])
```

1. **User Request**: The user submits their trip destination, duration, budget, and preferences.
2. **Flight Agent**: Gathers available flight routes, prices, and airport schedules using AviationStack.
3. **Hotel Agent**: Searches for accommodation options matching budget and location using Tavily Search.
4. **Itinerary Agent**: Constructs a detailed day-by-day sightseeing and activity schedule.
5. **Final Agent**: Synthesizes and formats the final plan into an interactive, beautifully structured travel plan.
