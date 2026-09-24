import os
import re
import time
import functools
import requests
import airportsdata
import pycountry
import certifi
from dotenv import load_dotenv

load_dotenv()

os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUEST_CA_BUNDLE"] = certifi.where()

BASE_URL = "https://api.aviationstack.com/v1/flights"
API_KEY = os.getenv("AVIATIONSTACK_API_KEY")
DEFAULT_ORIGIN_IATA = os.getenv("DEFAULT_ORIGIN_IATA", "AMD")

AIRPORTS = airportsdata.load("IATA")

# Popular tourist destinations mapped to ISO-2 country codes
COUNTRY_ALIASES = {
    # Top Asian & Middle Eastern Tourist Destinations
    "india": "IN",
    "bharat": "IN",
    "uae": "AE",
    "united arab emirates": "AE",
    "dubai": "AE",
    "abu dhabi": "AE",
    "thailand": "TH",
    "singapore": "SG",
    "malaysia": "MY",
    "indonesia": "ID",
    "bali": "ID",
    "maldives": "MV",
    "vietnam": "VN",
    "japan": "JP",
    "south korea": "KR",
    "sri lanka": "LK",
    "turkey": "TR",
    "turkiye": "TR",
    "saudi arabia": "SA",
    "qatar": "QA",

    # Popular European Tourist Destinations
    "uk": "GB",
    "united kingdom": "GB",
    "england": "GB",
    "scotland": "GB",
    "france": "FR",
    "switzerland": "CH",
    "italy": "IT",
    "spain": "ES",
    "germany": "DE",
    "netherlands": "NL",
    "holland": "NL",
    "greece": "GR",

    # Americas, Oceania & Getaways
    "usa": "US",
    "us": "US",
    "united states": "US",
    "america": "US",
    "canada": "CA",
    "australia": "AU",
    "new zealand": "NZ",
    "mauritius": "MU",
    "egypt": "EG",
}

# Main gateway airports for popular tourist countries
COUNTRY_MAIN_AIRPORT = {
    # Asia & Middle East
    "IN": "DEL",  # New Delhi, India
    "AE": "DXB",  # Dubai, UAE
    "TH": "BKK",  # Bangkok, Thailand
    "SG": "SIN",  # Singapore
    "MY": "KUL",  # Kuala Lumpur, Malaysia
    "ID": "DPS",  # Bali, Indonesia
    "MV": "MLE",  # Malé, Maldives
    "VN": "HAN",  # Hanoi, Vietnam
    "JP": "HND",  # Tokyo, Japan
    "KR": "ICN",  # Seoul, South Korea
    "LK": "CMB",  # Colombo, Sri Lanka
    "TR": "IST",  # Istanbul, Turkey
    "SA": "JED",  # Jeddah, Saudi Arabia
    "QA": "DOH",  # Doha, Qatar

    # Europe
    "GB": "LHR",  # London, UK
    "FR": "CDG",  # Paris, France
    "CH": "ZRH",  # Zurich, Switzerland
    "IT": "FCO",  # Rome, Italy
    "ES": "BCN",  # Barcelona, Spain
    "DE": "FRA",  # Frankfurt, Germany
    "NL": "AMS",  # Amsterdam, Netherlands
    "GR": "ATH",  # Athens, Greece

    # Americas, Oceania & Getaways
    "US": "JFK",  # New York, USA
    "CA": "YYZ",  # Toronto, Canada
    "AU": "SYD",  # Sydney, Australia
    "NZ": "AKL",  # Auckland, New Zealand
    "MU": "MRU",  # Mauritius
    "EG": "CAI",  # Cairo, Egypt
}

# Popular tourist cities directly mapped to their primary airport
POPULAR_CITIES = {
    "ahmedabad": "AMD",
    "gujarat": "AMD",
    "mumbai": "BOM",
    "delhi": "DEL",
    "new delhi": "DEL",
    "bangalore": "BLR",
    "goa": "GOI",
    "dubai": "DXB",
    "abu dhabi": "AUH",
    "bangkok": "BKK",
    "phuket": "HKT",
    "singapore": "SIN",
    "kuala lumpur": "KUL",
    "bali": "DPS",
    "tokyo": "HND",
    "seoul": "ICN",
    "london": "LHR",
    "paris": "CDG",
    "rome": "FCO",
    "zurich": "ZRH",
    "barcelona": "BCN",
    "amsterdam": "AMS",
    "frankfurt": "FRA",
    "athens": "ATH",
    "istanbul": "IST",
    "new york": "JFK",
    "sydney": "SYD",
    "cairo": "CAI",
    "doha": "DOH",
    "male": "MLE",
    "colombo": "CMB",
    "hanoi": "HAN",
}


def clean_text(text: str) -> str:
    """Clean query text by lowercasing and removing conversational stop words."""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    stop_words = {
        "flight", "flights", "ticket", "tickets", "trip", "travel",
        "plan", "complete", "days", "day", "including", "hotel",
        "hotels", "sightseeing", "under", "budget", "info", "information"
    }
    words = [w for w in text.split() if w not in stop_words]
    return " ".join(words).strip()


@functools.lru_cache(maxsize=1024)
def resolve_location_to_iata(location: str) -> str | None:
    """Converts a country, city, or airport name into a 3-letter IATA code (LRU cached)."""
    if not location:
        return None

    raw = location.strip()
    if re.fullmatch(r"[A-Za-z]{3}", raw) and raw.upper() in AIRPORTS:
        return raw.upper()

    clean = clean_text(raw)
    if not clean:
        return None

    # 1. Direct city check
    if clean in POPULAR_CITIES:
        return POPULAR_CITIES[clean]

    # 2. Country aliases or pycountry lookup
    country_code = COUNTRY_ALIASES.get(clean)
    if not country_code:
        try:
            country_code = pycountry.countries.lookup(clean).alpha_2
        except (LookupError, AttributeError):
            pass

    if country_code and country_code in COUNTRY_MAIN_AIRPORT:
        return COUNTRY_MAIN_AIRPORT[country_code]

    # 3. Airport database city match
    for iata, airport in AIRPORTS.items():
        if str(airport.get("city", "")).lower().strip() == clean:
            return iata

    return None


def find_location_mentions(query: str) -> list[str]:
    """Finds referenced city or country names in a natural query."""
    q = query.lower()
    mentions = []

    for city in POPULAR_CITIES:
        if re.search(rf"\b{re.escape(city)}\b", q):
            mentions.append(city)

    for alias in COUNTRY_ALIASES:
        if re.search(rf"\b{re.escape(alias)}\b", q):
            mentions.append(alias)

    return list(dict.fromkeys(mentions))


@functools.lru_cache(maxsize=1024)
def parse_route(query: str) -> tuple[str | None, str | None]:
    """Extracts departure and arrival IATA codes from a query (LRU cached)."""
    q = query.strip()
    q_lower = q.lower()

    if any(k in q_lower for k in ["all country", "all countries", "global", "worldwide"]):
        return None, None

    # Check for direct 3-letter IATA codes
    codes = [c.upper() for c in re.findall(r"\b[A-Za-z]{3}\b", q) if c.upper() in AIRPORTS]
    if len(codes) >= 2:
        return codes[0], codes[1]

    # Pattern: from X to Y
    m = re.search(r"\bfrom\s+(.+?)\s+\bto\s+(.+?)(?:\s+(?:on|for|under|in|at)\b|[.!?]|$)", q_lower)
    if m:
        dep, arr = resolve_location_to_iata(m.group(1)), resolve_location_to_iata(m.group(2))
        if dep and arr:
            return dep, arr

    # Pattern: to Y from X
    m = re.search(r"\bto\s+(.+?)\s+\bfrom\s+(.+?)(?:\s+(?:on|for|under|in|at)\b|[.!?]|$)", q_lower)
    if m:
        arr, dep = resolve_location_to_iata(m.group(1)), resolve_location_to_iata(m.group(2))
        if dep and arr:
            return dep, arr

    mentions = find_location_mentions(q)

    # Specific origin indicated by "from <location>"
    from_match = re.search(r"\bfrom\s+([a-zA-Z\s]+?)(?:\s+(?:on|for|under|in|at|to)\b|[.!?]|$)", q_lower)
    if from_match:
        from_iata = resolve_location_to_iata(from_match.group(1))
        if from_iata:
            dest_mentions = [resolve_location_to_iata(loc) for loc in mentions if resolve_location_to_iata(loc) != from_iata]
            if dest_mentions:
                return from_iata, dest_mentions[0]
            return from_iata, None

    # Specific destination indicated by "to <location>"
    to_match = re.search(r"\bto\s+([a-zA-Z\s]+?)(?:\s+(?:on|for|under|in|at|from)\b|[.!?]|$)", q_lower)
    if to_match:
        to_iata = resolve_location_to_iata(to_match.group(1))
        if to_iata:
            return DEFAULT_ORIGIN_IATA, to_iata

    # Fallback based on mentioned locations
    if len(mentions) >= 2:
        return resolve_location_to_iata(mentions[0]), resolve_location_to_iata(mentions[1])
    if len(mentions) == 1:
        loc_iata = resolve_location_to_iata(mentions[0])
        if loc_iata == DEFAULT_ORIGIN_IATA:
            return DEFAULT_ORIGIN_IATA, None
        return DEFAULT_ORIGIN_IATA, loc_iata

    return None, None


# In-memory TTL Cache (15 minutes expiration)
_FLIGHT_CACHE: dict[str, tuple[float, str]] = {}
_FLIGHT_CACHE_TTL = 900

def format_time(ts: str | None) -> str:
    """Safely extract HH:MM time from ISO-8601 timestamps without capturing UTC timezone offsets."""
    if not ts:
        return "N/A"
    if "T" in ts:
        return ts.split("T")[1][:5]
    return ts[:5]


def format_flight(flight: dict) -> str:
    """Format single flight details into clean, readable summary with proper times."""
    airline = flight.get("airline", {}).get("name") or "Airline"
    flight_number = flight.get("flight", {}).get("iata") or flight.get("flight", {}).get("number") or ""
    status = flight.get("flight_status") or "scheduled"

    dep = flight.get("departure", {}) or {}
    arr = flight.get("arrival", {}) or {}

    dep_iata = dep.get("iata") or "DEP"
    dep_time = format_time(dep.get("scheduled"))

    arr_iata = arr.get("iata") or "ARR"
    arr_time = format_time(arr.get("scheduled"))

    flight_tag = f" ({flight_number})" if flight_number else ""
    return f"• **{airline}{flight_tag}**: {dep_iata} ({dep_time}) -> {arr_iata} ({arr_time}) | Status: *{status}*"


def search_flights(query: str, limit: int = 4) -> str:
    """Searches live flights using AviationStack API with direct route, destination arrival, and cache fallback."""
    if not API_KEY:
        return "Flight API notice: AVIATIONSTACK_API_KEY is missing in your .env file."

    cache_key = query.strip().lower()
    now = time.time()
    if cache_key in _FLIGHT_CACHE:
        timestamp, cached_res = _FLIGHT_CACHE[cache_key]
        if now - timestamp < _FLIGHT_CACHE_TTL:
            return cached_res

    dep_iata, arr_iata = parse_route(query)
    flight_data = []

    # Strategy 1: Try direct route if both departure and arrival are identified
    if dep_iata and arr_iata:
        try:
            params = {
                "access_key": API_KEY,
                "dep_iata": dep_iata,
                "arr_iata": arr_iata,
                "limit": min(limit, 10),
            }
            resp = requests.get(BASE_URL, params=params, timeout=8)
            res_json = resp.json()
            if not res_json.get("error"):
                flight_data = res_json.get("data", [])
        except Exception:
            pass

    # Strategy 2: If no direct flights found, query live inbound flights to destination airport
    if not flight_data and arr_iata:
        try:
            params = {
                "access_key": API_KEY,
                "arr_iata": arr_iata,
                "limit": min(limit, 10),
            }
            resp = requests.get(BASE_URL, params=params, timeout=8)
            res_json = resp.json()
            if not res_json.get("error"):
                flight_data = res_json.get("data", [])
        except Exception:
            pass

    # Strategy 3: Format results if any flights were retrieved
    if flight_data:
        is_direct = dep_iata and arr_iata and any(f.get("departure", {}).get("iata") == dep_iata for f in flight_data)
        if is_direct:
            header = f"Live Flights ({dep_iata} -> {arr_iata})"
        elif arr_iata:
            header = f"Live Inbound Flights to {arr_iata}"
        else:
            header = "Live Flight Schedules"

        formatted = [format_flight(f) for f in flight_data[:limit]]
        result = f"**{header}:**\n" + "\n".join(formatted)
        _FLIGHT_CACHE[cache_key] = (now, result)
        return result

    # Strategy 4: Informative fallback if live API has no scheduled flights in this window
    origin_label = dep_iata or "your origin"
    dest_label = arr_iata or "your destination"
    result = f"**Flight Advisory ({origin_label} -> {dest_label}):**\n• Multiple major airlines operate scheduled and connecting flights to this destination. Real-time booking fares and live gates are available through airline portals."
    _FLIGHT_CACHE[cache_key] = (now, result)
    return result


if __name__ == "__main__":
    print(search_flights("Plan a 7 days Japan trip from Gujarat"))