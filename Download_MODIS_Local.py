import os
import re
import requests
from datetime import datetime, timedelta
import time

################################################# Importante ---> el código lista solo los compuestos existentes de 8 días dentro del rango real

# CONFIGURACIÓN DEL USUARIO


EDL_TOKEN = "Bearer eyJ0eXAiOiJKV1QiLCJvcmlnaW4iOiJFYXJ0aGRhdGEgTG9naW4iLCJzaWciOiJlZGxqd3RwdWJrZXlfb3BzIiwiYWxnIjoiUlMyNTYifQ.eyJ0eXBlIjoiVXNlciIsInVpZCI6Im1hcmlvZXN0ZWJhbiIsImV4cCI6MTc2OTUxODM0OSwiaWF0IjoxNzY0MzM0MzQ5LCJpc3MiOiJodHRwczovL3Vycy5lYXJ0aGRhdGEubmFzYS5nb3YiLCJpZGVudGl0eV9wcm92aWRlciI6ImVkbF9vcHMiLCJhY3IiOiJlZGwiLCJhc3N1cmFuY2VfbGV2ZWwiOjN9.rDHh16vgZLcboEuoQWQSj2acvMTSXaqLCIfvi1f4kamVb6YftEkU0tre4ERo-Ax3VhbAjI-plb855A9_MKcgbPWHB84EnTwfHBPMDmRavs9Lb90wINLpKsz1iYy7cxGn_g2OHwTy9_F7xWDmGQhxnod0ZBZQJuHJACSUbFJX1hP-qU65p1KXqJXOKMEZnmVvPozqemtiiddWgaWJ4UIk-lIH4mW8jkon-pymFVEfEIzHL3y7lReEVEED7qF2vfnZKPxP0zd_qvACRjyWYrXvBl1AzpU4qiXw8aewnnAcQPzcvt1Jk_OSfY_UUD4zmirT2xMzpE5ydd_3-Y0ws7MXTw"    # <<<<<< Pega tu token completo aquí
OUTPUT_DIR = "modis_downloads_prueba"

PRODUCT = "MOD09A1"
COLLECTION = "61"

START_DATE = "2009-12-20" ## Download error depending on MODIS DOYS. If they do not match -->> won't download
END_DATE   = "2010-01-10" ## Now, we just filter the DOYs available for ur range of dates ... See below in Spanish

# Tiles que cubren Colombia, Ecuador, Perú, Bolivia, Noroeste Brasil
TILES = [
    "h09v09","h10v11","h11v11","h12v11", "h14v09",
    "h10v07","h11v07","h12v07","h13v08", "h14v10",
    "h10v08","h11v08","h12v08","h13v09", "h14v11",
    "h10v09","h11v09","h12v09","h13v10", "h13v12"
    "h10v10","h11v10","h12v10","h13v11"
]

#TILES = [
#    "h08v07","h09v07","h10v07","h11v07","h12v07",
#    "h08v08","h09v08","h10v08","h11v08","h12v08",
#    "h08v09","h09v09","h10v09","h11v09","h12v09",
#    "h08v10","h09v10","h10v10","h11v10","h12v10",
#    "h08v11","h09v11","h10v11","h11v11","h12v11"
#]

def generate_valid_modis_dates(start, end):
    """
    Produce SOLO los DOYs MODIS existentes (cada 8 días)
    Dentro del rango de fechas reales dado por el usuario. 
    P.e. para que incluya el último día de 2009 toca darle un rango : 2009.12.20 
    YYYY.MM.DD así, nos aseguramos de coger el último día disponible del año 2009
    """
    # MOD09A1 empieza normalmente en DOY 001, 009, 017...
    # Buscaremos DOYs desde 1 a 365/366 en cada año

    current_year = start.year
    last_year = end.year

    while current_year <= last_year:
        # Para cada año, iteramos DOYs válidos (1-366)
        doy = 1
        while doy <= 366:
            try:
                modis_day = datetime(current_year, 1, 1) + timedelta(days=doy - 1)
            except:
                break  # Año no tiene 366 días

            # MODIS solo sirve DOYs MÚLTIPLOS DE 8 + 1 → 1, 9, 17, 25...
            if ((doy - 1) % 8) != 0:
                doy += 1
                continue

            # checamos si está dentro del rango del usuario
            if start <= modis_day <= end:
                yield current_year, doy

            doy += 1

        current_year += 1


def safe_request(url, headers):
    """Evita errores 404 silenciosamente."""
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        return r
    return None



# PREPARACIÓN


os.makedirs(OUTPUT_DIR, exist_ok=True)
headers = {"Authorization": EDL_TOKEN}

start = datetime.fromisoformat(START_DATE)
end   = datetime.fromisoformat(END_DATE)

start_time = time.time()
print("\nIniciando proceso de descarga...\n")


# DESCARGA PRINCIPAL


for year, doy in generate_valid_modis_dates(start, end):

    dstr = f"{doy:03d}"
    dir_url = f"https://ladsweb.modaps.eosdis.nasa.gov/archive/allData/{COLLECTION}/{PRODUCT}/{year}/{dstr}/"

    print(f" Revisando {dir_url}")

    r = safe_request(dir_url, headers)
    if r is None:
        print("  No existe este DOY (no hay compuesto).")
        continue

    html = r.text

    for tile in TILES:
        pattern = rf"{PRODUCT}\.A{year}{dstr}\.{tile}\..*?\.hdf"
        matches = re.findall(pattern, html)

        for filename in matches:
            file_url = dir_url + filename
            outpath = os.path.join(OUTPUT_DIR, filename)

            if os.path.exists(outpath):
                print(f"  ✓ Ya existe: {filename}")
                continue

            print(f"  ⬇ Descargando: {filename}")
            file = requests.get(file_url, headers=headers)

            with open(outpath, "wb") as f:
                f.write(file.content)

print("\n Descarga completa.")

elapsed = time.time() - start_time
h = int(elapsed//3600)
m = int((elapsed%3600)//60)
s = int(elapsed%60)

print("\n-------------------------------------------")
print("Tiempo total de ejecución:")
print(f" {h:02d}:{m:02d}:{s:02d} (HH:MM:SS)")
print("-------------------------------------------\n")

