from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import os
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
import requests
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite requisições de qualquer origem. Ajuste conforme necessário.
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos os métodos (GET, POST, etc.).
    allow_headers=["*"],  # Permite todos os headers.
)
@app.get("/favicon.ico")
async def favicon():
    return FileResponse("static/favicon.ico")
                        
# Define the location model
class Location(BaseModel):
    latitude: float
    longitude: float

# Define the fire report model
class FireReport(BaseModel):
    location: Location
    description: Optional[str] = None

# Define the anonymous report model
class AnonymousReport(BaseModel):
    description: str
    state: str

# Define o modelo de focos de incêndio
class FirePoint(BaseModel):
    latitude: float
    longitude: float

#Dicionário de email do corpo de bombeiros de cada estado
email_bombeiros = {
    "AC": "cbm@ac.gov.br",
    "AL": "cbm@al.gov.br",
    "AM": "cbm@am.gov.br",
    "AP": "cbm@ap.gov.br",
    "BA": "cbm@ba.gov.br",
    "CE": "cbm@ce.gov.br",
    "DF": "cbm@df.gov.br",
    "ES": "cbm@es.gov.br",
    "GO": "cbm@go.gov.br",
    "MA": "cbm@ma.gov.br",
    "MG": "cbm@mg.gov.br",
    "MS": "cbm@ms.gov.br",
    "MT": "cbm@mt.gov.br",
    "PA": "cbm@pa.gov.br",
    "PB": "cbm@pb.gov.br",
    "PE": "cbm@pe.gov.br",
    "PI": "cbm@pi.gov.br",
    "PR": "cbm@pr.gov.br",
    "RJ": "cbm@rj.gov.br",
    "RN": "cbm@rn.gov.br",
    "RO": "cbm@ro.gov.br",
    "RR": "cbm@rr.gov.br",
    "RS": "cbm@rs.gov.br",
    "SC": "cbm@sc.gov.br",
    "SE": "cbm@se.gov.br",
    "SP": "cbm@sp.gov.br",
    "TO": "cbm@to.gov.br"
}
#Lista para pontos de incêndio
fire_points = []

# Função para receber ligação
def send_call(content: str):
    account_sid = os.environ.get('your_acc_sid')
    auth_token = os.environ.get('your_auth_token')
    client = Client(account_sid, auth_token)

    call = client.calls.create(
       twiml=f'<Response><Say>{content}</Say></Response>',
        from_='+14783313332',
        to='+55193'  # Número de emergência
    )

    print(call.sid)
# Função de email
def send_email(subject: str, text: str, to_email: str):
    api_key = os.environ.get('your_api_key')
    domain = os.environ.get('your_domain')
    return requests.post(
        f"https://api.mailgun.net/v3/{domain}/messages",
        auth=("api", api_key),
        data={"from": "email_exemplo@example.com",
                "to": [to_email],
                "subject": subject,
                "text": text}
                )

# Endpoint to report a fire
@app.post("/report_fire")
async def report_fire(report: FireReport):
    # Send the location to the firefighters
    content = f"Incêndio relatado em {report.location.latitude}, {report.location.longitude}\nDescription: {report.description}"
    send_call(content)
    return {"message": "Fogo relatado com sucesso."}

# Endpoint to make an anonymous report
@app.post("/anonymous_report")
async def anonymous_report(report: AnonymousReport):
   #verifica se o estado é valido
   if report.state not in email_bombeiros:
       raise HTTPException(status_code=400, detail="Estado Inválido")
   
   #envia email para o corpo de bombeiros
   subject = "Relatório Anônimo de Incêndio"
   to_email = email_bombeiros[report.state]
   text = text
   send_email(subject,text,to_email)
   return

#endpoint para pontos de incêndio
@app.get("/fire_points", response_model=List[FirePoint])
async def get_fire_point():
    url = "https://firms.modaps.eosdis.nasa.gov/map/#d:24hrs;@-48.5,-6.1,4.6z"
    response = requests.get(url)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Erro ao obter dados")
    
    fire_points = []
    lines = response.text.splitlines()
    for line in lines[1:]: #ignora cabeçalho
        parts = line.split(',')
    try:
        latitude = float(parts[0])
        longitude = float(parts[1])
        fire_points.append(FirePoint(latitude=latitude, longitude=longitude))
    except (ValueError, IndexError):
        pass

    return fire_points

# Error handling
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return {"error": exc.detail}
