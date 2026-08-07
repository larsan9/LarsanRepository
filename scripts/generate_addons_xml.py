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
  5. Regenera `index.html` (raíz, zips/ y zips/<addon_id>/): listados planos
     con enlaces <a href>, para que Kodi pueda navegarlos vía "Añadir fuente".
  6. Regenera `home.html`: la landing visual, con la lista de addons y
     versiones siempre actualizada.

Flujo de trabajo para ti (larsan9):
  - Generas el addon (o su nueva versión) donde quieras (Kodi, un ZIP hecho
    a mano, etc.).
  - Simplemente subes/arrastras ese .zip dentro de `zips/<addon_id>/`
    (creando la carpeta si el addon es nuevo). El nombre del archivo puede
    ser el que quieras, no se usa para nada salvo mostrarlo en los logs.
  - Hoy hay un GitHub Action (.github/workflows/update-repo.yml) que ejecuta
    este script automáticamente en cada push y hace commit de los cambios
    generados (addons.xml, addons.xml.md5, repository.larsan.zip, index.html,
    home.html).
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

# Etiqueta legible por addon_id, usada solo en home.html
ADDON_LABELS = {
    "repository.larsan": "Repositorio",
    "plugin.program.larsanwizard": "Programa de prueba",
}


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


# ------------------------------------------------------------------
# index.html planos (navegación por "Añadir fuente" en Kodi)
# ------------------------------------------------------------------

def _write_plain_index(dir_path: Path, entries: list):
    links = "\n".join(f'<a href="{e}">{e}</a><br>' for e in entries)
    html = f"<!DOCTYPE html><html><head><meta charset='UTF-8'></head><body>\n{links}\n</body></html>"
    (dir_path / "index.html").write_text(html, encoding="utf-8")


def generate_directory_indexes(addon_dirs):
    """Genera index.html plano en raíz, zips/ y cada zips/<addon_id>/."""
    root_entries = ["home.html", "addons.xml", "addons.xml.md5", STABLE_REPO_ZIP_NAME, "zips/"]
    root_entries += [
        f"{d.name}/" for d in ROOT.iterdir()
        if d.is_dir() and d.name not in ("zips", ".github", "scripts")
    ]
    _write_plain_index(ROOT, sorted(set(root_entries)))

    _write_plain_index(ZIPS_DIR, sorted(f"{d.name}/" for d in addon_dirs))

    for addon_dir in addon_dirs:
        zips = sorted(p.name for p in addon_dir.glob("*.zip"))
        if zips:
            _write_plain_index(addon_dir, zips)

    print("index.html (navegación Kodi) regenerados.")


# ------------------------------------------------------------------
# home.html (landing visual, con lista de addons siempre actualizada)
# ------------------------------------------------------------------

HOME_TEMPLATE_HEAD = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Larsan Repository — Repositorio de addons para Kodi</title>
<style>
:root{{--bg:#0f1420;--card:#161d2e;--accent:#4f8cff;--accent2:#7c5cff;--text:#e7ecf5;--muted:#94a1b8;--border:#232b40;}}
*{{box-sizing:border-box;}}
body{{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
background:radial-gradient(1200px 600px at 20% -10%, #1a2338 0%, var(--bg) 55%);color:var(--text);line-height:1.6;}}
header{{padding:64px 24px 40px;text-align:center;}}
.logo{{width:120px;height:120px;border-radius:24px;background:#000;display:flex;align-items:center;justify-content:center;
margin:0 auto 20px;box-shadow:0 10px 30px rgba(0,0,0,.5);overflow:hidden;}}
.logo img{{width:100%;height:100%;object-fit:cover;}}
h1{{font-size:2.2rem;margin:0 0 8px;}}
.subtitle{{color:var(--muted);max-width:560px;margin:0 auto;}}
main{{max-width:880px;margin:0 auto;padding:0 24px 80px;}}
.card{{background:var(--card);border:1px solid var(--border);border-radius:16px;padding:28px 30px;margin-bottom:24px;}}
.card h2{{margin-top:0;font-size:1.25rem;display:flex;align-items:center;gap:10px;}}
.badge{{display:inline-block;background:rgba(79,140,255,.15);color:var(--accent);border:1px solid rgba(79,140,255,.4);
padding:2px 10px;border-radius:999px;font-size:.75rem;font-weight:600;}}
code, pre{{background:#0b1120;border:1px solid var(--border);border-radius:8px;color:#9fe3c7;font-size:.9rem;}}
code{{padding:2px 6px;}} pre{{padding:16px;overflow-x:auto;}}
ol, ul{{padding-left:22px;color:var(--text);}}
a.btn{{display:inline-block;margin-top:8px;padding:12px 22px;border-radius:10px;
background:linear-gradient(135deg,var(--accent),var(--accent2));color:white;text-decoration:none;font-weight:600;}}
a.btn.secondary{{background:transparent;border:1px solid var(--border);color:var(--text);}}
.addon-list{{display:grid;gap:14px;margin-top:10px;}}
.addon{{display:flex;justify-content:space-between;align-items:center;background:#0f1626;border:1px solid var(--border);
border-radius:12px;padding:14px 18px;}}
.addon .name{{font-weight:600;}} .addon .meta{{color:var(--muted);font-size:.85rem;}}
footer{{text-align:center;color:var(--muted);padding:30px 24px;font-size:.85rem;}} footer a{{color:var(--accent);}}
</style>
</head>
<body>
<header>
  <div class="logo"><img src="repository.larsan/icon.png" alt="Larsan"></div>
  <h1>Larsan Repository</h1>
  <p class="subtitle">Repositorio personal de addons para Kodi mantenido por <strong>larsan9</strong>.</p>
</header>
<main>
  <div class="card">
    <h2>🚀 Instalación rápida <span class="badge">Kodi</span></h2>
    <ol>
      <li>Descarga <code>{repo_zip_name}</code>.</li>
      <li>En Kodi: <strong>Configuración → Complementos → Instalar desde archivo zip</strong>.</li>
      <li>Selecciona el ZIP descargado y espera la confirmación.</li>
      <li>Ve a <strong>Instalar desde repositorio → Larsan Repository</strong> para ver los addons disponibles.</li>
    </ol>
    <a class="btn" href="{repo_zip_name}">Descargar {repo_zip_name}</a>
    <a class="btn secondary" href="https://github.com/larsan9/LarsanRepository">Ver en GitHub</a>
  </div>

  <div class="card">
    <h2>🌐 Instalar como fuente remota</h2>
    <p>Añade esta URL como fuente en el gestor de archivos de Kodi para recibir actualizaciones automáticas:</p>
    <pre>https://larsan9.github.io/LarsanRepository/</pre>
    <p>Esta página (home.html) es solo la vista para navegador. El listado navegable para Kodi vive en <code>index.html</code>.</p>
  </div>

  <div class="card">
    <h2>🤖 Repositorio autoactualizable</h2>
    <p>Cada nueva versión de un addon se sube como ZIP a <code>zips/&lt;addon_id&gt;/</code>. Un GitHub Action
    detecta el cambio, regenera <code>addons.xml</code>, su checksum, este mismo <code>{repo_zip_name}</code>,
    los índices de navegación y esta página con la lista de addons actualizada. No hace falta editar nada a mano.</p>
  </div>

  <div class="card">
    <h2>📦 Addons disponibles</h2>
    <div class="addon-list">
"""

HOME_TEMPLATE_TAIL = """
    </div>
  </div>

  <div class="card">
    <h2>🧪 Verificar instalación</h2>
    <p>Instala <strong>Larsan Wizard</strong> desde el repositorio y ábrelo. Si aparece un mensaje de confirmación,
    el repositorio está funcionando correctamente.</p>
  </div>
</main>
<footer>
  Larsan Repository — mantenido por larsan9 · <a href="https://github.com/larsan9/LarsanRepository">github.com/larsan9/LarsanRepository</a>
</footer>
</body>
</html>
"""


def generate_home_html(addon_infos):
    """addon_infos: lista de tuplas (addon_id, version) detectadas al procesar cada zip."""
    cards = []
    for addon_id, version in addon_infos:
        label = ADDON_LABELS.get(addon_id, "Addon")
        cards.append(
            f'      <div class="addon"><div><div class="name">{addon_id}</div>'
            f'<div class="meta">{label} · v{version}</div></div></div>'
        )
    html = HOME_TEMPLATE_HEAD.format(repo_zip_name=STABLE_REPO_ZIP_NAME)
    html += "\n".join(cards)
    html += HOME_TEMPLATE_TAIL
    (ROOT / "home.html").write_text(html, encoding="utf-8")
    print("home.html regenerado con la lista de addons actual.")


def main():
    if not ZIPS_DIR.exists():
        print(f"No existe la carpeta {ZIPS_DIR}, nada que hacer.")
        sys.exit(0)

    addon_blocks = []
    addon_infos = []
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
        addon_infos.append((addon_id, version))

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

    # --- Regenerar páginas web (index.html técnico + home.html visual) ---
    generate_directory_indexes(addon_dirs)
    generate_home_html(addon_infos)


if __name__ == "__main__":
    main()
