#!/usr/bin/env python3
"""
Larsan Repository - generador automático de addons.xml

Este script es el corazón de la automatización del repositorio.

Qué hace:
  1. Recorre la carpeta `zips/<addon_id>/` buscando todos los .zip disponibles.
  2. Para cada addon, se queda con el ZIP de la VERSIÓN MÁS ALTA (comparando
     el <addon version="..."> real dentro del addon.xml del zip, no el nombre
     del archivo).
  3. Extrae ese addon.xml y lo usa para reconstruir `addons.xml` (el índice
     que lee Kodi) y su checksum `addons.xml.md5`.
  4. Copia el ZIP más reciente de `repository.larsan` a la raíz del repo con
     un nombre de archivo ESTABLE (`repository.larsan.zip`), para que el
     enlace de descarga en README.md / index.html nunca se rompa aunque
     subas nuevas versiones.

Flujo de trabajo para ti (larsan9):
  - Generas el addon (o su nueva versión) donde quieras (Kodi, un ZIP hecho
    a mano, etc.).
  - Simplemente subes/arrastras ese .zip dentro de `zips/<addon_id>/`
    (creando la carpeta si el addon es nuevo). El nombre del archivo puede
    ser el que quieras, no se usa para nada salvo mostrarlo en los logs.
  - Hoy hay un GitHub Action (.github/workflows/update-repo.yml) que ejecuta
    este script automáticamente en cada push y hace commit de los cambios
    generados (addons.xml, addons.xml.md5, repository.larsan.zip).
  - Si prefieres ejecutarlo tú mismo en local: `python3 scripts/generate_addons_xml.py`
"""
import hashlib
import re
import shutil
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ZIPS_DIR = ROOT / "zips"
ADDONS_XML_PATH = ROOT / "addons.xml"
ADDONS_MD5_PATH = ROOT / "addons.xml.md5"
STABLE_REPO_ZIP_NAME = "repository.larsan.zip"


def version_key(version_str):
    """Convierte '1.2.10' en (1, 2, 10) para poder comparar versiones bien
    (evita que '1.10.0' se compare como menor que '1.9.0' por ser texto)."""
    parts = re.findall(r"\d+", version_str)
    return tuple(int(p) for p in parts) if parts else (0,)


def read_addon_xml_from_zip(zip_path: Path, addon_id: str):
    """Extrae el contenido de <addon_id>/addon.xml desde dentro de un zip."""
    with zipfile.ZipFile(zip_path, "r") as zf:
        candidates = [
            n for n in zf.namelist()
            if n.endswith("addon.xml") and (
                n == f"{addon_id}/addon.xml" or n.split("/")[0] == addon_id
            )
        ]
        if not candidates:
            # fallback: cualquier addon.xml de primer nivel dentro del zip
            candidates = [n for n in zf.namelist() if n.endswith("addon.xml")]
        if not candidates:
            raise ValueError(f"No se encontró addon.xml dentro de {zip_path}")
        with zf.open(candidates[0]) as f:
            return f.read().decode("utf-8")


def find_latest_version(addon_dir: Path, addon_id: str):
    """Devuelve (zip_path, version, addon_xml_text) del zip con mayor versión."""
    best = None
    for zip_path in sorted(addon_dir.glob("*.zip")):
        try:
            xml_text = read_addon_xml_from_zip(zip_path, addon_id)
            root = ET.fromstring(xml_text)
            version = root.attrib.get("version", "0.0.0")
        except Exception as e:
            print(f"  ! Aviso: no se pudo leer {zip_path.name}: {e}")
            continue
        if best is None or version_key(version) > version_key(best[1]):
            best = (zip_path, version, xml_text)
    return best


def main():
    if not ZIPS_DIR.exists():
        print(f"No existe la carpeta {ZIPS_DIR}, nada que hacer.")
        sys.exit(0)

    addon_blocks = []
    latest_repo_zip = None

    addon_dirs = sorted([d for d in ZIPS_DIR.iterdir() if d.is_dir()])
    if not addon_dirs:
        print("No hay carpetas de addons dentro de zips/.")
        sys.exit(0)

    for addon_dir in addon_dirs:
        addon_id = addon_dir.name
        print(f"Procesando addon: {addon_id}")
        result = find_latest_version(addon_dir, addon_id)
        if result is None:
            print(f"  ! No se encontraron zips válidos para {addon_id}, se omite.")
            continue

        zip_path, version, xml_text = result
        print(f"  -> versión más reciente: {version}  ({zip_path.name})")

        # limpiar declaración xml propia de cada addon.xml individual
        cleaned = re.sub(r"^\s*<\?xml[^>]*\?>\s*", "", xml_text).strip()
        addon_blocks.append(cleaned)

        if addon_id == "repository.larsan":
            latest_repo_zip = zip_path

    if not addon_blocks:
        print("No se generó ningún addon válido, abortando.")
        sys.exit(1)

    # --- Reconstruir addons.xml ---
    final_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        "<addons>\n" + "\n".join(addon_blocks) + "\n</addons>\n"
    )
    ADDONS_XML_PATH.write_text(final_xml, encoding="utf-8")

    md5 = hashlib.md5(final_xml.encode("utf-8")).hexdigest()
    ADDONS_MD5_PATH.write_text(md5, encoding="utf-8")

    print(f"\naddons.xml regenerado ({len(addon_blocks)} addon(s))")
    print(f"addons.xml.md5 -> {md5}")

    # --- Copiar el zip del repositorio con nombre estable en la raíz ---
    if latest_repo_zip is not None:
        stable_path = ROOT / STABLE_REPO_ZIP_NAME
        shutil.copyfile(latest_repo_zip, stable_path)
        print(f"{STABLE_REPO_ZIP_NAME} actualizado desde {latest_repo_zip.relative_to(ROOT)}")
    else:
        print("Aviso: no se encontró ningún zip de repository.larsan en zips/.")


if __name__ == "__main__":
    main()
