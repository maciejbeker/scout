import requests
import re
import os
import time
import logging

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import google.generativeai as genai
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import googlemaps

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Suppress third-party loggers
logging.getLogger('google.auth').setLevel(logging.ERROR)
logging.getLogger('google.auth.transport').setLevel(logging.ERROR)
logging.getLogger('google.auth.transport.requests').setLevel(logging.ERROR)
logging.getLogger('urllib3.connectionpool').setLevel(logging.ERROR)

# Load environment variables from .env file
load_dotenv()

app = FastAPI()


class APIClients:

    def __init__(self):
        self.genai_client = None
        self.gmaps_client = None
        self.initialized = False

    def initialize(self):
        """Initialize API clients if not already initialized"""
        if self.initialized:
            return

        try:
            # Initialize Gemini AI
            genai_api_key = os.getenv("GENAI_API_KEY", "").strip()
            if not genai_api_key:
                raise ValueError("GENAI_API_KEY not found")

            genai.configure(api_key=genai_api_key, transport='rest')
            self.genai_client = genai.GenerativeModel(
                'gemini-1.5-flash',
                generation_config=genai.GenerationConfig(
                    temperature=0.7, max_output_tokens=500))
            logger.info("Initialized Gemini AI client")

            # Initialize Google Maps
            maps_api_key = os.getenv("MAPS_API_KEY", "").strip()
            if not maps_api_key:
                raise ValueError("MAPS_API_KEY not found")
            self.gmaps_client = googlemaps.Client(key=maps_api_key)
            logger.info("Initialized Google Maps client")

            self.initialized = True
            logger.info("All API clients successfully initialized")

        except Exception as e:
            logger.error(f"Error initializing APIs: {str(e)}")
            self.reset()
            raise

    def reset(self):
        """Reset all clients to None"""
        self.genai_client = None
        self.gmaps_client = None
        self.initialized = False


# Create a single instance of APIClients
api_clients = APIClients()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class URLRequest(BaseModel):
    url: str


class Coordinate(BaseModel):
    name: str
    latitude: float
    longitude: float
    address: str


class CoordinateResponse(BaseModel):
    coordinates: list[Coordinate]
    no_coordinates: list[str]


@app.on_event("startup")
async def startup():
    """Initialize APIs when FastAPI starts"""
    try:
        api_clients.initialize()
    except Exception as e:
        logger.warning(f"Failed to initialize APIs during startup: {str(e)}")


@app.get("/health")
def health_check():
    logger.info("Health check endpoint called")
    return {"status": "healthy"}


@app.post("/api/generate_coordinates", response_model=CoordinateResponse)
def generate_coordinates(request: URLRequest):
    start_time = time.time()
    url = request.url.strip()
    logger.info(f"Starting processing URL: {url}")

    if not url:
        logger.error("URL is empty")
        raise HTTPException(status_code=400, detail="URL is required.")

    try:
        # Ensure APIs are initialized
        api_clients.initialize()

        logger.info("Fetching URL content...")
        url_response = requests.get(url,
                                    headers={'User-Agent': 'Mozilla/5.0'},
                                    timeout=10)
        url_response.raise_for_status()
        logger.info(
            f"URL fetch completed in {time.time() - start_time:.2f} seconds")

        logger.info("Calling Gemini AI...")
        prompt = (
            "The article discusses various topics such as tourist attractions, restaurants, nature spots, "
            "or other points of interest in terms of 'the best of ...'.\n"
            "Your task is to identify mentioned objects and provide a clear numbered list. "
            "I don't want from you to analyze the article and its strengths etc. Just identify and provide the objects.\n"
            "Additional guidelines:\n"
            "- Each item should include the full location context (city, country)\n"
            "- Format: Name, City, Country\n"
            "- Do not include any additional information or commentary.\n"
            "Example:\n"
            "Article: 'Top 10 Restaurants in Warsaw'\n"
            "Output:\n"
            "1. Restaurant A, Warsaw, Poland\n"
            "2. Restaurant B, Warsaw, Poland\n"
            "...\n\n"
            f"Article to use:\n{url_response.text}")

        response = api_clients.genai_client.generate_content(prompt)
        logger.info(
            f"AI response received in {time.time() - start_time:.2f} seconds")

        locations = re.findall(r'\d+\.\s+(.+)', response.text)
        logger.info(f"Found {len(locations)} locations")

        coordinates = []
        no_coordinates = []

        logger.info("Starting geocoding process...")
        for loc in locations:
            try:
                geocode_result = api_clients.gmaps_client.geocode(loc)
                if geocode_result:
                    location = geocode_result[0]['geometry']['location']
                    formatted_address = geocode_result[0]['formatted_address']
                    coordinates.append(
                        Coordinate(name=loc.split(',')[0],
                                   latitude=location['lat'],
                                   longitude=location['lng'],
                                   address=formatted_address))
                    logger.info(f"Successfully geocoded: {loc}")
                else:
                    logger.warning(f"No geocoding results for: {loc}")
                    no_coordinates.append(loc)
            except Exception as e:
                logger.error(f"Geocoding error for {loc}: {str(e)}")
                no_coordinates.append(loc)

        logger.info(
            f"Total processing completed in {time.time() - start_time:.2f} seconds"
        )
        return CoordinateResponse(coordinates=coordinates,
                                  no_coordinates=no_coordinates)

    except requests.RequestException as e:
        logger.error(
            f"URL fetch error after {time.time() - start_time:.2f} seconds: {str(e)}"
        )
        raise HTTPException(status_code=500,
                            detail=f"Error fetching URL: {str(e)}")
    except Exception as e:
        logger.error(
            f"Processing error after {time.time() - start_time:.2f} seconds: {str(e)}",
            exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
