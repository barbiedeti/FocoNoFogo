document.getElementById('fire-report-form').addEventListener('submit', async function(event) {
    event.preventDefault();

    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(async function(position) {
            const latitude = position.coords.latitude;
            const longitude = position.coords.longitude;

            const response = await fetch('http://127.0.0.1:8000/report_fire', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    location: { latitude, longitude },
                    description
                })
            });

            const result = await response.json();
            alert(result.message);
        }, function(error) {
            alert('Erro ao obter localização: ' + error.message);
        });
    } else {
        alert('Geolocalização não é suportada pelo seu navegador.');
    }
});

document.getElementById('anonymous-report-form').addEventListener('submit', async function(event) {
    event.preventDefault();
    const description = document.getElementById('anon-description').value;
    const state = document.getElementById('state').value;

    const response = await fetch('http://127.0.0.1:8000/anonymous_report', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            description,
            state
        })
    });

    const result = await response.json();
    alert(result.message);
});

// Inicializar o map
var map = L.map('map').setView([-14.2350, -51.9253], 4);

L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 18,
}).addTo(map);

// Obter pontos de incêndio do servidor
async function getFirePoints() {
    const response = await fetch('http://127.0.0.1:8000/fire_points');
    const firePoints = await response.json();

    firePoints.forEach(point => {
        L.marker([point.latitude, point.longitude]).addTo(map)
            .bindPopup(`Incêndio relatado: ${point.latitude}, ${point.longitude}`);
    });
}

getFirePoints();