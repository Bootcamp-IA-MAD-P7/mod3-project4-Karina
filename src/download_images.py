import os
import requests
from ddgs import DDGS

juegos = {
    "league_of_legends": "league of legends logo",
    "valorant": "valorant logo",
    "fortnite": "fortnite logo",
    "genshin_impact": "genshin impact logo",
    "minecraft": "minecraft logo",
    "vrchat": "vrchat logo"
}

def descargar_imagen(url, ruta):
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            with open(ruta, "wb") as f:
                f.write(response.content)
            return True
    except:
        pass
    return False

for carpeta, busqueda in juegos.items():
    ruta = f"dataset/images/train/{carpeta}"
    os.makedirs(ruta, exist_ok=True)
    
    # Contar imágenes ya existentes
    existentes = len(os.listdir(ruta))
    print(f"\n📥 {carpeta} ({existentes} ya descargadas)")

    descargadas = existentes
    with DDGS() as ddgs:
        resultados = ddgs.images(busqueda, max_results=150)
        for r in resultados:
            if descargadas >= 80:
                break
            ext = r["image"].split(".")[-1].split("?")[0]
            if ext not in ["jpg", "jpeg", "png", "webp"]:
                ext = "jpg"
            nombre = f"{ruta}/{descargadas + 1:04d}.{ext}"
            if descargar_imagen(r["image"], nombre):
                descargadas += 1
                print(f"  ✅ {descargadas}/80", end="\r")

    print(f"  ✅ {carpeta}: {descargadas} imágenes")

print("\n✅ Descarga completada!")
