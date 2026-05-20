'''
 ░▒▓███████▓▒░▒▓████████▓▒░▒▓███████▓▒░▒▓████████▓▒░▒▓█▓▒░▒▓███████▓▒░░▒▓████████▓▒░▒▓█▓▒░        
░▒▓█▓▒░      ░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░   ░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░        
░▒▓█▓▒░      ░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░   ░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░        
 ░▒▓██████▓▒░░▒▓██████▓▒░ ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░   ░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓██████▓▒░ ░▒▓█▓▒░        
       ░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░   ░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░        
       ░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░   ░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░        
░▒▓███████▓▒░░▒▓████████▓▒░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░   ░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓████████▓▒░▒▓████████▓▒░ 
                                                                                                  
SENTINEL HEAT EARLY WARNING SYSTEM
AUTOR: RICARDO ESPARZA
ESCRITO Y ANALIZADO POR UN HUMANO, NO POR IA GENERATIVA.
NO SE UTILIZÓ IA GENERATIVA EN NINGÚN PASO DE LA PROGRAMACIÓN.
'''

#∘₊ ☆─── SECCIÓN 1 ───☆₊∘#
# EJECUCIÓN INICIAL
import math
import firebase_admin
from firebase_admin import credentials, db
import requests
import json
from shapely.geometry import shape, Point
import schedule
import time

with open("RALTO.geojson") as rMuyAlto:
    jsRMuyAlto = json.load(rMuyAlto)
with open("RALTOMENOS.geojson") as rAlto:
    jsRAlto = json.load(rAlto)

OWM_API = "XXX"
PW_API = "XXX"
urlGOB = "http://servertorreon.dyndns-server.com:8085/monitoring/Torreon/airValue.html"

#FIREBASE
cred = credentials.Certificate("XXX.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "XXX"
})
refU = db.reference("Sentinel")
refA = db.reference("calidadAire")

#ONESIGNAL
ONESIGNAL_APP_ID = "XXX"
ONESIGNAL_REST_API_KEY = "XXX"
#∘₊ ☆─── FINAL DE SECCIÓN 1 ───☆₊∘#
def loopSentinel():
    #∘₊ ☆─── SECCIÓN 2 ───☆₊∘#
    # Valores dependientes de OpenWeatherMap, PirateWeather y la API municipal de monitoreo para calidad del aire
    # ÁREA PARA OPENWEATHERMAP
    urlTRC_OWM = "https://api.openweathermap.org/data/2.5/weather?lat=25.54&lon=-103.45&appid="+OWM_API #URL específica para datos de Torreón, para obtener datos para otras localidades cambiar lat y long
    tiempoOWM = requests.get(urlTRC_OWM)
    tiempoPythonOWM = tiempoOWM.json()                      #Convertir el JSON que sacamos de OWM para poder leerlo en python
    mainOWM = tiempoPythonOWM["main"]
    tempActualOWM = round(mainOWM["temp"] - 273.15,2)       #Extraer temperatura actual del JSON y convertirlo a Celsius
    humedadActualOWM = mainOWM["humidity"]
    windOWM = tiempoPythonOWM["wind"]
    vientoOWM = windOWM["speed"]
    # ÁREA PARA PIRATEWEATHER
    urlTRC_PW = "https://api.pirateweather.net/forecast/"+PW_API+"/25.54,-103.45?units=si"
    tiempoPW = requests.get(urlTRC_PW)
    tiempoPythonPW = tiempoPW.json()
    currentlyPW = tiempoPythonPW["currently"]
    tempActualPW = currentlyPW["temperature"]
    humedadActualPW = currentlyPW["humidity"]*100
    vientoPW = currentlyPW["windSpeed"]
    # ÁREA PARA ESTACIÓN DE MONITOREO DE CALIDAD DEL AIRE DEL MUNICIPIO DE TORREÓN
    headers = {"User-Agent": "Mozilla/5.0 (Linux; Android 16; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.7727.138 Mobile Safari/537.36"}
    calAire = requests.get(urlGOB,headers=headers)
    ICA = "NO DISPONIBLE"

    try:
        calAire = requests.get(urlGOB, timeout=10)
        if calAire.status_code == 200:
            renglones = calAire.text.strip().split("\n")
            
            if len(renglones) >= 3:
                columnas = [col.strip() for col in renglones[2].split("|")]
                
                if len(columnas) >= 3:
                    parametro = columnas[1]
                    try:
                        valor = int(columnas[2])
                        
                        if "PM10" in parametro:
                            if valor <= 50: ICA = "BUENA"
                            elif valor <= 75: ICA = "ACEPTABLE"
                            elif valor <= 155: ICA = "MALA"
                            elif valor <= 235: ICA = "MUY MALA"
                            else: ICA = "EXTREMADAMENTE MALA"
                            
                        elif "PM2.5" in parametro:
                            if valor <= 25: ICA = "BUENA"
                            elif valor <= 45: ICA = "ACEPTABLE"
                            elif valor <= 79: ICA = "MALA"
                            elif valor <= 147: ICA = "MUY MALA"
                            else: ICA = "EXTREMADAMENTE MALA"
                    except ValueError:
                        print("Inválido.")
    except Exception as e:
        print(f"{e}")
    #OBTENCIÓN DE PROMEDIO DE TEMPERATURA, HUMEDAD Y VELOCIDAD DEL VIENTO ENTRE OWM Y PW
    Tamb = (tempActualOWM+tempActualPW)/2
    velocidadAire = (vientoOWM+vientoPW)/2
    humRel = (humedadActualOWM+humedadActualPW)/2
    #∘₊ ☆─── FINAL DE SECCIÓN 2 ───☆₊∘#

    #∘₊ ☆─── SECCIÓN 3 ───☆₊∘#
    #ALGORITMO DE ALERTAMIENTO
    def sentinelgorithm(pesoPersona, alturaPersona, edad, pobRA, Tambuser):
        #CONSTANTES
        # EN ORDEN: Temperatura de piel asumiendo vasodilatación máxima; Factor de área de ropa; Resistencia térmica de ropa; Resistencia evaporativa de ropa; Calor latente de vaporización de sudor en J/g; Densidad del sudor; Factor de emisividad del cuerpo humano; Constante de Steffan-Boltzman
        Tsk, fcl, Rcl, Revapropa, lam, rho, epsilon, alpha = 35, 1.1767, 0.08835, 0.027, 2426, 1, 0.97, 5.67E-8 
        # ESTABLECIMIENTO DE TASA DE SUDORACIÓN MÁXIMA POR EDAD Y HUMEDAD MÁXIMA DE LA PIEL POR EDAD
        if 12 <= edad <= 17: Smax, wmax = 0.94, 0.85
        elif 18 <= edad <= 40: Smax, wmax = 0.75, 0.79
        elif 41 <= edad <= 64: Smax, wmax = 0.62, 0.71
        elif edad >= 65: Smax, wmax = 0.51, 0.65

        #CÁLCULO DE SUPERVIVIENCIA O HABITABILIDAD USANDO MODELO DE VANOS ET AL.
        Tr = Tambuser + 15
        hr = 4 * epsilon * alpha * 0.70 * ((((Tsk + Tr) / 2) + 273.2) ** 3)
        viscosidadCineAire = (1.33E-5) + ((9E-8) * Tambuser)
        Re = ((velocidadAire * alturaPersona) / viscosidadCineAire)
        Nu = 0.24 * ((Re) ** 0.6)
        kaire = (2.41E-2) + ((7.8E-5) * Tambuser)
        hc = ((Nu * kaire) / alturaPersona)
        hcomb = hr + hc 

        t0 = ((hr * Tr) + (hc * Tambuser)) / hcomb
        areaPersona = (0.202) * (pesoPersona ** 0.425) * (alturaPersona ** 0.725)
        METbase = 1.5
        M = METbase * 58.2 * areaPersona 
        MTasa = METbase * 58.2

        radPielConvPiel = ((Tsk - t0) / (Rcl + (1 / (hcomb * fcl)))) * areaPersona
        convRespiratoria = 0.0014 * (MTasa * (34 - Tambuser)) * areaPersona
        presVapH2O = (humRel / 100) * (math.exp(18.956 - (4030.18 / (Tambuser + 235))) / 10)
        evapRespiratoria = 0.0173 * (MTasa * (5.87 - presVapH2O)) * areaPersona

        evapRequerida = M - radPielConvPiel - convRespiratoria - evapRespiratoria
        presVapPielSat = math.exp(18.956 - (4030.18 / (Tsk + 235))) / 10
        he = hc * 16.5 
        evapMaxPermitidaAmbiente = ((presVapPielSat - presVapH2O) / (Revapropa + (1 / (he * fcl)))) * areaPersona
        wrequerida = evapRequerida / evapMaxPermitidaAmbiente

        r = 0.5 if wrequerida > 1 else 1 - ((wrequerida ** 2) / 2)

        #ASIGNAR UN SSURV DISTINTO (HIPERTERMIA A 39°C) SI USUARIO ES PARTE DE POBLACIONES DE RIESGO ALTO
        if pobRA == "true":
            Ssurv = 0.55 * pesoPersona #W/kg OBTENIDO DE BALANCE TÉRMICO REAL A TRES HORAS (Q = mCpDeltaT)
        else:
            Ssurv = 0.83 * pesoPersona 
        evapMaxHum = wmax * evapMaxPermitidaAmbiente
        evapMaxSudor = ((Smax * lam * rho) / 3.6) * r

        #CLASIFICACIÓN DE RIESGO
        if (evapRequerida - evapMaxHum) <= Ssurv:
            EvapMaxLim = min(evapMaxHum, evapMaxSudor)
            if evapRequerida <= EvapMaxLim:
                TasaMetMax = (EvapMaxLim - radPielConvPiel) / (1 - areaPersona * (0.0014 * (34 - Tamb) + 0.0173 * (5.87 - presVapH2O)))
                METmax = TasaMetMax / (58.2 * areaPersona)
                return "VERDE", METmax #SIN RIESGO, PUEDE HACER ACTIVIDAD DE X METs
            else:
                METmax = 0
                return "AMARILLA", METmax #RIESGO SI NO SE SUSPENDE ACTIVIDAD
        else:
            METmax = 0
            return "ROJA", METmax #RIESGO MORTAL AUNQUE SE SUSPENDA ACTIVIDAD
    #∘₊ ☆─── FINAL DE SECCIÓN 3 ───☆₊∘#

    #∘₊ ☆─── SECCIÓN 4 ───☆₊∘#
    # ALERTAMIENTO PUSH
    def sentinelAlerts(osID, titulo, mensaje, acID, alertIcon):
        if not osID: return
        
        headers = {
            "Authorization": f"Basic {ONESIGNAL_REST_API_KEY}",
            "Content-Type": "application/json; charset=utf-8"
        }
        
        payload = {
            "app_id": ONESIGNAL_APP_ID,
            "include_subscription_ids": osID, #ONESIGNAL IDS!!!!!!!!!!!!!!!!!!!!!
            "headings": {"en": titulo, "es": titulo},
            "contents": {"en": mensaje, "es": mensaje},
            "android_channel_id": acID,
            "small_icon": alertIcon,
            "large_icon": alertIcon

        }
        
        try:
            response = requests.post("https://onesignal.com/api/v1/notifications", json=payload, headers=headers)
        except Exception as e:
            print(f"Error al enviar alertas: {e}")

    def alertICA(tituloAire, mensajeAire, acID, alertIcon):
        headers = {
            "Authorization": f"Basic {ONESIGNAL_REST_API_KEY}",
            "Content-Type": "application/json; charset=utf-8"
        }
        
        payload = {
            "app_id": ONESIGNAL_APP_ID,
            "included_segments": ["All"],
            "headings": {"en": tituloAire, "es": tituloAire},
            "contents": {"en": mensajeAire, "es": mensajeAire},
            "android_channel_id": acID,
            "small_icon": alertIcon,
            "large_icon": alertIcon
        }
        
        print("Sent ICA")
        try:
            response = requests.post("https://onesignal.com/api/v1/notifications", json=payload, headers=headers)
        except Exception as eAire:
            print(f"Error al enviar alerta de calidad del aire: {eAire}")
    #∘₊ ☆─── FINAL DE SECCIÓN 4 ───☆₊∘#

    #∘₊ ☆─── SECCIÓN 5 ───☆₊∘#
    #SACAR DATOS DE FIREBASE Y ESTABLECER aUUIDs PARA ALERTA
    datosUsuarios = refU.get()

    redAlert_aUUIDs = []
    yellowAlert_aUUIDs = []
    allClear_aUUIDs = []
    actividadUpdate = {}
    batchUpdate = {}

    if datosUsuarios:
        
        for aUUID, data in datosUsuarios.items():
            peso = data.get("peso")
            altura = data.get("altura")
            edad = data.get("edad")
            aUUID = aUUID
            pobRA = data.get("pobRA")
            lat = data.get("lat")
            long = data.get("long")
            osID = data.get("osID")

            Tambuser = Tamb

            if lat is not None and long is not None:
                pusuario = Point(float(long), float(lat))
                for feature in jsRMuyAlto["features"]:
                    polygonRMAlto = shape(feature["geometry"])
                    if polygonRMAlto.contains(pusuario):
                        Tambuser += 3
                    else:
                        pass
                for feature in jsRAlto["features"]:
                    polygonRAlto = shape(feature["geometry"])
                    if polygonRAlto.contains(pusuario):
                        Tambuser += 1.5
                    else:
                        pass
            
            edoAlerta = data.get("edoAlerta","VERDE")
            
            if all(v is not None for v in [peso, altura, edad, aUUID, pobRA, osID]):
                
                peso = float(str(peso).replace('"',''))
                altura = float(str(altura).replace('"',''))
                edad = int(str(edad).replace('"',''))
                aUUID = str(aUUID).replace('"','')
                osID = str(osID).replace('"','')

                edoAlertaActual, METmax = sentinelgorithm(float(peso), float(altura), int(edad), str(pobRA), Tambuser)
                
                actividadSegura = "REPOSO"
                if edoAlertaActual == "VERDE":
                    if METmax > 6:
                        actividadSegura = "FUERTE"
                    elif 3 <= METmax <= 6:
                        actividadSegura = "MODERADA"
                    elif 1.5 <= METmax < 3:
                        actividadSegura = "LIGERA"
                    else:
                        actividadSegura = "REPOSO"
                actividadUpdate[aUUID] = actividadSegura

                if edoAlertaActual != edoAlerta:
                    if edoAlertaActual == "ROJA":
                        redAlert_aUUIDs.append(osID)
                        batchUpdate[aUUID] = edoAlertaActual
                    elif edoAlertaActual == "AMARILLA":
                        yellowAlert_aUUIDs.append(osID)
                        batchUpdate[aUUID] = edoAlertaActual
                    elif edoAlertaActual == "VERDE" and edoAlerta in ["ROJA", "AMARILLA"]:
                        allClear_aUUIDs.append(osID)
                        batchUpdate[aUUID] = edoAlertaActual

        if redAlert_aUUIDs:
            sentinelAlerts(
                redAlert_aUUIDs, 
                "🚨 PELIGRO MORTAL: EVACUAR HACIA INTERIOR FRESCO", 
                "Mantén la calma. Las condiciones en exteriores son peligrosas para la vida. Evacúa inmediatamente hacia un interior fresco y mantente hidratado. En caso de emergencia, llama al 911.",
                "XXX",
                "warning"
            )

        if yellowAlert_aUUIDs:
            sentinelAlerts(
                yellowAlert_aUUIDs, 
                "⚠️ PRECAUCIÓN: SUSPENDER ACTIVIDADES", 
                "Mantén la calma. Suspende cualquier actividad física y mantente hidratado. En caso de emergencia, llama al 911.",
                "XXX",
                "susp_act"
            )

        if allClear_aUUIDs:
            sentinelAlerts(
                allClear_aUUIDs, 
                "🟩 CONDICIONES SEGURAS", 
                "Gracias por tu cooperación. Las condiciones exteriores han vuelto a ser seguras. ¡La prenveción es nuestra fuerza!",
                "XXX",
                "allclear"
            )

        if batchUpdate or actividadUpdate:
            updates = {}
            for aUUID, edoNuevo in batchUpdate.items():
                updates[f"{aUUID}/edoAlerta"] = edoNuevo
            for aUUID, actNueva in actividadUpdate.items():
                updates[f"{aUUID}/actividadSegura"] = actNueva
            refU.update(updates)
    else:
        print("Sin datos 눈_눈")

    edoICA = refA.get() or {}

    lastEdoICA = edoICA.get("tagAire", "SEGURO")
    lastEdoAlert = edoICA.get("alertamiento", "DESACTIVADO")

    if ICA in ["NO DISPONIBLE"]:
        ICA = lastEdoICA
        newEdoAlert = lastEdoAlert
    else:
        if ICA in ["MALA", "MUY MALA", "EXTREMADAMENTE MALA"]:
            newEdoAlert = "ACTIVADO"
            print("newEdoAlert = ACTIVADO")
        else:
            newEdoAlert = "DESACTIVADO"

    updates_aire = {}
    aireSucio = False
    aireLimpio = False

    if ICA != lastEdoICA:
        updates_aire["tagAire"] = ICA
        updates_aire["alertamiento"] = lastEdoAlert

    if newEdoAlert != lastEdoAlert:
        updates_aire["alertamiento"] = newEdoAlert
        
        if newEdoAlert == "ACTIVADO":
            aireSucio = True
            
        elif newEdoAlert == "DESACTIVADO" and lastEdoAlert == "ACTIVADO":
            aireLimpio = True

    if updates_aire:
        refA.update(updates_aire)

    if aireSucio == True:
        alertICA(
            "😷 AIRE SUCIO", 
            "El aire presenta contaminación significativa. Usa cubrebocas y reduce tus actividades físicas.",
            "XXX",
            "malica"
        )
    elif aireLimpio == True:
        alertICA(
            "🍃 AIRE LIMPIO", 
            "El estado del aire es seguro nuevamente.",
            "XXX",
            "allclear"
        )

    requests.get("XXX") #heartbeat opcional
    #∘₊ ☆─── FINAL DE SECCIÓN 5 ───☆₊∘#
schedule.every(1).hour.at(":05").do(loopSentinel)
loopSentinel()

while True:
	schedule.run_pending()
	time.sleep(1)