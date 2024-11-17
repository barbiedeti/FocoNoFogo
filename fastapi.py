from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
from typing import Optional, List
import os
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
import requests
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse


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
    return FileResponse("appfogo/appfogo/favicon.ico")
                        
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
    "MS": "cbm@ms.gov.br", #e-mails ficticios
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


# Função de email
def send_email(subject: str, content: str, to_email: str):
    api_key = os.environ.get('your_api_key')
    domain = os.environ.get('your_domain')
    if not api_key or not domain:
        raise HTTPException(status_code=500, detail="Configurações Inválidas")
    return requests.post(
        f"https://api.mailgun.net/v3/{domain}mailgun.org/messages",
        auth=("api", api_key),
        data={"from": "<your_domain_mail>",
                "to": [to_email],
                "subject": subject,
                "text": content}
                )

# Endpoint to report a fire
#@app.post("/report_fire") 
#async def report_fire(report: FireReport):
    # Send the location to the firefighters
 #   content = f"Incêndio relatado em {report.location.latitude}, {report.location.longitude}\nDescription: {report.description}"
  #  send_call(content)
   # return {"message": "Fogo relatado com sucesso."}

@app.post("/twilio_redirect") #endpoint para redirecionar chamadas
async def twilio_redirect():
    account_sid = os.environ.get('your_sid')
    auth_token = os.environ.get('your_auth')
    client = Client(account_sid, auth_token)

    call = client.calls.create(
        url = "https://your_remote_servidor.ngrok/twilio_redirect",
       #twiml=f'<Response><Say>Por favor tome medidas para se proteger enquanto nossa unidade chega.</Say></Response>',
        from_='phone_number_from_twilio',
        to='+55193'  # Número de emergência
    )
    print(f"Call SID: {call.sid}")
    #Encaminhamento
    response = VoiceResponse()
    response.say("Ligação encaminhada para o corpo de bombeiros")
    response.dial("+55193")  # Número de emergência
    return Response (content=str(response), media_type="application/xml")

# Endpoint to make an anonymous report
@app.post("/anonymous_report")
async def anonymous_report(report: AnonymousReport):
   #verifica se o estado é valido
   if report.state not in email_bombeiros:
       raise HTTPException(status_code=400, detail="Estado Inválido")
   
   #envia email para o corpo de bombeiros
   subject = "Relatório Anônimo de Incêndio"
   to_email = email_bombeiros[report.state]
   content = f"Descrição: {report.description}"
   response = send_email(subject,content,to_email)
   if response.status_code != 200:
       raise HTTPException(status_code=500, detail="Erro ao enviar email")
   return {"message": "Denúncia enviada com sucesso."}

#endpoint para pontos de incêndio
@app.get("/fire_points", response_model=List[FirePoint])
async def get_fire_point():
    url = "https://firms.modaps.eosdis.nasa.gov/api/area/csv/bd0075c061f10c45f6abdf12854dfbbe/VIIRS_SNPP_NRT/-85,-57,-32,14/1/2024-11-17"
    response = requests.get(url)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Erro ao obter dados")
    
    fire_points = []
    lines = response.text.splitlines()
    for line in lines[1:]: #ignora cabeçalho
        parts = line.split(',')
        if len(parts) >=2:
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
   return JSONResponse(
       status_code=exc.status_code,
       content={"message": exc.detail}
   )


