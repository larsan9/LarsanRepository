# Larsan Repository

Repositorio personal de addons para Kodi, mantenido por **larsan9**.

Repo: `https://github.com/larsan9/LarsanRepository`

## 📦 Instalación en Kodi

### Opción A — Instalar directamente el ZIP del repositorio

1. Descarga **`repository.larsan.zip`** (está en la raíz del repositorio; el nombre es fijo y siempre apunta a la última versión, aunque el repo se actualice).
2. Copia el ZIP a tu dispositivo (o a una carpeta accesible desde Kodi).
3. En Kodi: **Configuración → Complementos → Instalar desde archivo zip**.
4. Selecciona `repository.larsan.zip`.
5. Espera a la notificación *"Add-on repository.larsan instalado"*.

### Opción B — Añadir como fuente remota (recomendado, recibe actualizaciones automáticas)

1. En Kodi: **Configuración → Administrador de archivos → Añadir fuente**.
2. Introduce la URL raw de GitHub:
   ```
   https:///larsan9/github.io/LarsanRepository/
   ```
3. Ponle un nombre, por ejemplo `LarsanRepo`.
4. Ve a **Complementos → Instalar desde archivo zip → LarsanRepo → repository.larsan.zip**.
5. Luego entra en **Instalar desde repositorio → Larsan Repository** para ver los addons disponibles.

## 🧪 Verificar que funciona

Una vez instalado el repositorio, ve a:

**Instalar desde repositorio → Larsan Repository → Programas → Larsan Wizard**

Instálalo y ábrelo. Si ves un mensaje de confirmación indicando que el repositorio
funciona correctamente, ¡todo está en orden! ✅

## 🤖 Actualización automática (lo importante)

Este repositorio se mantiene **solo**. No hace falta tocar `addons.xml` a mano
ni calcular el MD5 nunca más.

**Tu único trabajo, de ahora en adelante, es:**

1. Sube (o arrastra por la web de GitHub) el `.zip` de la nueva versión del addon
   dentro de `zips/<addon_id>/` — creando la carpeta si el addon es nuevo.
   El nombre del archivo da igual, solo importa que el `addon.xml` de dentro
   tenga el `version="X.Y.Z"` correcto.
2. Haces commit / push a `main`.
3. Un **GitHub Action** (`.github/workflows/update-repo.yml`) se dispara solo,
   ejecuta `scripts/generate_addons_xml.py`, y este:
   - Detecta automáticamente la versión más alta de cada addon dentro de `zips/`.
   - Regenera `addons.xml` y `addons.xml.md5`.
   - Actualiza `repository.larsan.zip` en la raíz con la última versión del repo.
   - Hace commit de esos 3 archivos automáticamente.

En resumen: **solo subes el ZIP nuevo a `zips/<addon_id>/` y todo lo demás se regenera solo.**

Si quieres ejecutarlo tú mismo en local en vez de esperar al Action:
```bash
python3 scripts/generate_addons_xml.py
```

## 📁 Estructura del proyecto

```
LarsanRepository/
├── .github/workflows/update-repo.yml   # Automatización (GitHub Actions)
├── scripts/generate_addons_xml.py      # Script que regenera todo
├── repository.larsan/                  # Código fuente del addon "repositorio"
│   ├── addon.xml
│   ├── icon.png
│   └── changelog.txt
├── plugin.program.larsanwizard/        # Addon de prueba
│   ├── addon.xml
│   ├── default.py
│   └── icon.png
├── zips/                               # 👉 AQUÍ subes los zips nuevos
│   ├── repository.larsan/
│   │   └── repository.larsan-1.0.0.zip
│   └── plugin.program.larsanwizard/
│       └── plugin.program.larsanwizard-1.0.0.zip
├── addons.xml                          # Generado automáticamente
├── addons.xml.md5                      # Generado automáticamente
├── repository.larsan.zip               # Generado automáticamente (nombre estable)
├── index.html
└── README.md
```

## ➕ Añadir un addon completamente nuevo

Esto sí requiere un paso manual la primera vez (después, las nuevas versiones
son solo subir el zip):

1. Crea la carpeta del addon en la raíz (p. ej. `plugin.video.miaddon/`) con su `addon.xml` válido.
2. Comprime el contenido de esa carpeta en un `.zip` (que la carpeta del addon quede dentro del zip).
3. Súbelo a `zips/plugin.video.miaddon/` (carpeta nueva, mismo `addon_id`).
4. Haz commit y push a `main` → el Action hace el resto.

## ⚠️ Notas

- El icono de todos los addons es el logo de Larsan (`icon.png`, 512×512).
- El script compara **versiones reales** leídas del `addon.xml` dentro de cada zip
  (no el nombre del archivo), así que puedes dejar zips de versiones antiguas en
  la misma carpeta sin problema: siempre se usará la más alta.
- Si el Action falla por permisos de escritura, entra en
  **Settings → Actions → General → Workflow permissions** del repo en GitHub
  y marca **"Read and write permissions"**.
