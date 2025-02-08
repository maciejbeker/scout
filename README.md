# Scout - Location Explorer

![screenshot](dist/scout.png)

Scout is a web application that helps users explore locations mentioned in online articles. It extracts location data from articles and visualizes them on an interactive map.

## Features

- Extract locations from any online article URL
- Interactive map visualization using Google Maps
- Clickable markers with location details
- Mobile-responsive design
- Error handling and loading states

## Architecture

The project consists of two main components:

- **Frontend**: A static website built with TypeScript and Google Maps API
- **Backend**: A FastAPI service using Gemini AI for location extraction and Google Maps for geocoding

## Prerequisites

- Node.js 16+
- Python 3.11+
- Google Cloud Platform account with:
  - Maps JavaScript API
  - Geocoding API
  - Gemini AI API

## Environment Variables
1. Create a `.env` file in the root directory:
```
MAPS_API_KEY=your_google_maps_api_key
GENAI_API_KEY=your_genai_api_key
```
2. Update `dist/index.html` with your Google Maps API key:
```
<script src="https://maps.googleapis.com/maps/api/js?key=<YOUR_MAPS_API_KEY>"></script>
```

## Running with Docker locally

### Backend Service

```bash
# Build and run the backend
cd api
docker build -t scout-api .
docker run -p 8080:8080 \
  -e MAPS_API_KEY=your_maps_api_key \
  -e GENAI_API_KEY=your_genai_api_key \
  scout-api
```

### Frontend Service

```bash
# Build and run the frontend
docker build -t scout-frontend .
docker run -p 80:8080 scout-frontend
```

### Using Docker Compose (Recommended)

```bash
docker-compose up --build
```

The application will be available at:
- Frontend: http://localhost
- Backend API: http://localhost:8080

## License

This project is licensed under the MIT License - see the LICENSE file for details.