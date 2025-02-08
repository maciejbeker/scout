interface Coordinate {
  name: string;
  latitude: number;
  longitude: number;
  address: string;
}

interface CoordinateResponse {
  coordinates: Coordinate[];
  no_coordinates: string[];
}

let map: google.maps.Map;

function initMap(coordinates: Coordinate[]) {
  const firstLoc = coordinates[0];
  const mapElement = document.getElementById("map") as HTMLElement;
  let currentInfoWindow: google.maps.InfoWindow | null = null;

  map = new google.maps.Map(mapElement, {
    zoom: 13,
    center: { lat: firstLoc.latitude, lng: firstLoc.longitude }
  });

  coordinates.forEach((coord: Coordinate) => {
    const infoWindow = new google.maps.InfoWindow({
      content: `
        <div class="marker-info">
          <h3>${coord.name}</h3>
          <p>${coord.address}</p>
          <a href="https://www.google.com/maps/search/?api=1&query=${coord.latitude},${coord.longitude}" 
             target="_blank" 
             class="view-on-maps">
            View on Google Maps
          </a>
        </div>
      `
    });

    const marker = new google.maps.Marker({
      map,
      position: { lat: coord.latitude, lng: coord.longitude },
      title: coord.name,
      label: {
        text: coord.name,
        className: 'marker-label'
      }
    });

    marker.addListener('click', () => {
      if (currentInfoWindow) {
        currentInfoWindow.close();
      }
      infoWindow.open(map, marker);
      currentInfoWindow = infoWindow;
    });
  });
}

function buildMarkerContent(title: string): HTMLElement {
  const container = document.createElement('div');
  container.className = 'marker-container';
  
  const label = document.createElement('div');
  label.className = 'marker-label';
  label.textContent = title;
  
  const pin = document.createElement('div');
  pin.className = 'marker-pin';
  
  container.appendChild(label);
  container.appendChild(pin);
  
  return container;
}

async function handleGenerate(event: Event) {
  event.preventDefault();
  
  const form = document.getElementById('generateForm') as HTMLFormElement;
  const urlInput = document.getElementById('urlInput') as HTMLInputElement;
  const loadingSpinner = document.getElementById('loadingSpinner') as HTMLDivElement;
  const mapContainer = document.getElementById('map') as HTMLDivElement;
  const errorMessage = document.getElementById('errorMessage') as HTMLDivElement;
  
  const url = urlInput.value.trim();
  
  if (!url) {
      errorMessage.textContent = 'Please enter a URL';
      errorMessage.style.display = 'block';
      return;
  }

  try {
      form.classList.add('loading');
      loadingSpinner.style.display = 'block';
      errorMessage.style.display = 'none';
      mapContainer.style.display = 'none';
      
      const response = await fetch('https://scout-api-560247360518.europe-central2.run.app/api/generate_coordinates', {
          method: 'POST',
          headers: {
              'Content-Type': 'application/json'
          },
          body: JSON.stringify({ url })
      });
      
      const data: CoordinateResponse = await response.json();
      
      if (data.coordinates && data.coordinates.length > 0) {
          mapContainer.style.display = 'block';
          initMap(data.coordinates);
      } else {
          throw new Error('No locations found');
      }
  } catch (error) {
      errorMessage.textContent = error instanceof Error ? error.message : 'An error occurred';
      errorMessage.style.display = 'block';
      mapContainer.style.display = 'none';
  } finally {
      form.classList.remove('loading');
      loadingSpinner.style.display = 'none';
  }
}

window.addEventListener('load', () => {
  const form = document.getElementById('generateForm');
  if (form) {
      form.addEventListener('submit', handleGenerate);
  }
});