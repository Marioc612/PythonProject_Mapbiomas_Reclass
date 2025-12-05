import rasterio
import geopandas as gpd
import numpy as np
from rasterio.features import rasterize
from pathlib import Path
from tqdm import tqdm
import multiprocessing as mp

# ===================================================================
# VARIABLES GLOBALES, usadas por los workers

ZONAS_GLOBAL = None
TABLA_GLOBAL = None
TIF_PATH_GLOBAL = None


# ===================================================================
# Inicialización por worker

def init_worker(zonas, tabla_global, tif_path):
    global ZONAS_GLOBAL, TABLA_GLOBAL, TIF_PATH_GLOBAL
    ZONAS_GLOBAL = zonas
    TABLA_GLOBAL = tabla_global
    TIF_PATH_GLOBAL = tif_path


# ===================================================================
# Procesa UNA ventana del raster

def process_window(args):
    ji, window = args

    # Reabrir el raster en cada worker (robusto)
    with rasterio.open(TIF_PATH_GLOBAL) as src:
        arr = src.read(1, window=window)
        win_transform = src.window_transform(window)

    # Estado intermedio
    out = arr.astype(np.float32)

    # Procesar cada zona especial
    for zona in ZONAS_GLOBAL:

        geoms = zona["geoms"]
        tabla = zona["tabla"]

        # Rasterizar máscara de la zona (por ventana)
        mask_z = rasterize(
            [(geom, 1) for geom in geoms],
            out_shape=(window.height, window.width),
            transform=win_transform,
            fill=0,
            dtype=np.uint8
        )

        # Aplicar reclasificación específica SOLO dentro de la máscara
        for original, nuevo in tabla.items():
            out[(arr == original) & (mask_z == 1)] = nuevo

    # Reclasificación global
    for original, nuevo in TABLA_GLOBAL.items():
        out[out == original] = nuevo

    # Conversión segura a uint8
    out = np.where(np.isnan(out), 255, out)
    out = np.clip(out, 0, 255)

    return ji, window, out.astype(np.uint8)


# ===================================================================
# PROGRAMA PRINCIPAL

if __name__ == "__main__":

    # Carpetas
    folder_in = Path("Reclass_in")
    folder_out = Path("Reclass_output")
    folder_out.mkdir(exist_ok=True)

    # ===================================================================
    # TABLA GLOBAL DE RECLASIFICACIÓN
    tabla_peru = {4: 3}  # regla específica

    tabla_col = {12: 4}

    tabla_global = {
        3: 1, 5: 1,  # 1 = Evergreen Forest
        6: 2,  # 2 = Floodable Forest
        81: 3, 82: 3,  # 3 = Andean Herbaceous Complex
        49: 4, 66: 4,  # 4 = Shrublands
        4: 5, 13: 5,  # 5 = Savannas
        14: 6, 15: 6, 18: 6, 9: 6, 21: 6, 19: 6, 39: 6,  # 6 = Croplands
        20: 6, 40: 6, 62: 6, 41: 6, 36: 6, 46: 6, 47: 6,
        35: 6, 48: 6, 74: 6, 72: 6, 31: 6,
        12: 7, 50: 7,  # 7 = Grasslands
        0: 8, 33: 8, 29: 8, 70: 8,  # 8 = Other
        26: 9, 11: 9  # 9 = Wetlands
    }

    # ===================================================================
    # CARGAR TODAS LAS ZONAS ESPECIALES

    # --- ZONA 1: PERÚ ---
    shp_peru = gpd.read_file("nivel-politico-1.shp")
    g_peru = shp_peru[shp_peru["name_es"] == "Peru"]

    # --- ZONA 2: PATCH DE COLOMBIA ---
    shp_col = gpd.read_file("Orinoquia_dissolved.shp")

    # Puedes agregar más zonas:
    # shp_ecu = gpd.read_file(...)
    # tabla_ecu = {...}

    print("\n=== Reclasificando mosaicos con N máscaras ===")

    # ===================================================================
    # PROCESAR CADA RASTER

    for tif_path in folder_in.glob("*.tif"):

        print(f"\nProcesando: {tif_path.name}")
        output_path = folder_out / f"{tif_path.stem}_reclass.tif"

        # Ver si el TIFF está corrupto
        try:
            with rasterio.open(tif_path) as src:
                pass
        except Exception as e:
            print(f" Archivo corrupto: {tif_path.name}")
            print("   Error:", e)
            continue

        # Preparar geometrías reproyectadas
        with rasterio.open(tif_path) as src:

            CRS = src.crs

            # reproyectar
            peru_geoms = [geom for geom in g_peru.to_crs(CRS).geometry]
            col_geoms = [geom for geom in shp_col.to_crs(CRS).geometry]

            # construir lista de zonas
            zonas = [
                {"nombre": "Peru", "geoms": peru_geoms, "tabla": tabla_peru},
                {"nombre": "Colombia", "geoms": col_geoms, "tabla": tabla_col},
            ]

            # Copiar perfil
            profile = src.profile.copy()
            profile.update(
                dtype=rasterio.uint8,
                nodata=255,
                tiled=True,
                compress="LZW",
                blockxsize=256,
                blockysize=256
            )

            windows = list(src.block_windows(1))

        # Crear salida
        with rasterio.open(output_path, "w", **profile) as dst:

            num_procs = mp.cpu_count()

            with mp.Pool(
                    processes=num_procs,
                    initializer=init_worker,
                    initargs=(zonas, tabla_global, str(tif_path))
            ) as pool:
                tasks = [(ji, window) for ji, window in windows]

                for ji, window, out_arr in tqdm(
                        pool.imap(process_window, tasks),
                        total=len(tasks),
                        desc=f"Reclasificando {tif_path.name}"
                ):
                    dst.write(out_arr, 1, window=window)

        print(f" Guardado: {output_path}")


    print("PROCESO COMPLETO — Reclasificación con múltiples máscaras")
