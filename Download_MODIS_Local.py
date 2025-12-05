import os
import re
import requests
from datetime import datetime, timedelta
import time

# -----------------------------------------------
# CONFIGURACIÓN DEL USUARIO
# -----------------------------------------------

EDL_TOKEN = "Bearer eyJ0eXAiOiJKV1QiLCJvcmlnaW4iOiJFYXJ0aGRhdGEgTG9naW4iLCJzaWciOiJlZGxqd3RwdWJrZXlfb3BzIiwiYWxnIjoiUlMyNTYifQ.eyJ0eXBlIjoiVXNlciIsInVpZCI6Im1hcmlvZXN0ZWJhbiIsImV4cCI6MTc2OTUxODM0OSwiaWF0IjoxNzY0MzM0MzQ5LCJpc3MiOiJodHRwczovL3Vycy5lYXJ0aGRhdGEubmFzYS5nb3YiLCJpZGVudGl0eV9wcm92aWRlciI6ImVkbF9vcHMiLCJhY3IiOiJlZGwiLCJhc3N1cmFuY2VfbGV2ZWwiOjN9.rDHh16vgZLcboEuoQWQSj2acvMTSXaqLCIfvi1f4kamVb6YftEkU0tre4ERo-Ax3VhbAjI-plb855A9_MKcgbPWHB84EnTwfHBPMDmRavs9Lb90wINLpKsz1iYy7cxGn_g2OHwTy9_F7xWDmGQhxnod0ZBZQJuHJACSUbFJX1hP-qU65p1KXqJXOKMEZnmVvPozqemtiiddWgaWJ4UIk-lIH4mW8jkon-pymFVEfEIzHL3y7lReEVEED7qF2vfnZKPxP0zd_qvACRjyWYrXvBl1AzpU4qiXw8aewnnAcQPzcvt1Jk_OSfY_UUD4zmirT2xMzpE5ydd_3-Y0ws7MXTw"    # <<<<<< Pega tu token completo aquí
OUTPUT_DIR = "modis_downloads_prueba"

PRODUCT = "MOD09A1"
COLLECTION = "61"

START_DATE = "2010-01-01"
END_DATE   = "2010-02-31"

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

# -----------------------------------------------
# PREPARACIÓN
# -----------------------------------------------

os.makedirs(OUTPUT_DIR, exist_ok=True)

headers = {
    "Authorization": EDL_TOKEN
}

BASE_URL = "https://ladsweb.modaps.eosdis.nasa.gov/archive/allData"

def generate_8day_dates(start, end):
    """Genera fechas cada 8 días en rango."""
    d = start
    while d <= end:
        yield d
        d += timedelta(days=8)

start = datetime.fromisoformat(START_DATE)
end   = datetime.fromisoformat(END_DATE)

start_time = time.time()
print("\nIniciando proceso de descarga...\n")

# -----------------------------------------------
# DESCARGA PRINCIPAL
# -----------------------------------------------
for date in generate_8day_dates(start, end):
    year = date.year
    doy  = date.timetuple().tm_yday

    dstr = f"{doy:03d}"
    dir_url = f"{BASE_URL}/{COLLECTION}/{PRODUCT}/{year}/{dstr}/"

    print(f" Revisando {dir_url}")

    # Obtener HTML de la carpeta
    r = requests.get(dir_url, headers=headers)
    if r.status_code != 200:
        print(f" No se pudo acceder al directorio ({r.status_code})")
        continue

    html = r.text

    # Buscar archivos .hdf por tile con regex
    for tile in TILES:
        pattern = rf"MOD09A1\.A{year}{dstr}\.{tile}\..*?\.hdf"
        matches = re.findall(pattern, html)

        for filename in matches:
            file_url = dir_url + filename
            outpath = os.path.join(OUTPUT_DIR, filename)

            # Evitar re-descargar
            if os.path.exists(outpath):
                print(f"  ✓ Ya existe: {filename}")
                continue

            print(f"  ⬇ Descargando: {filename}")
            file = requests.get(file_url, headers=headers)

            with open(outpath, "wb") as f:
                f.write(file.content)

print(" Descarga completa.")

end_time = time.time()
elapsed = end_time - start_time

hours = int(elapsed // 3600)
minutes = int((elapsed % 3600) // 60)
seconds = int(elapsed % 60)

print("\n-------------------------------------------")
print("Tiempo total de ejecución:")
print(f" {hours:02d}:{minutes:02d}:{seconds:02d} (HH:MM:SS)")
print("-------------------------------------------\n")


