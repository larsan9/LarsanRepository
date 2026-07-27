# -*- coding: utf-8 -*-
"""
Larsan Wizard - addon de prueba
Se usa unicamente para verificar que el repositorio Larsan
(https://github.com/larsan9/LarsanRepository) instala y actualiza
addons correctamente en Kodi.
"""
import sys
import xbmcgui
import xbmcaddon

ADDON = xbmcaddon.Addon()
ADDON_NAME = ADDON.getAddonInfo('name')
ADDON_VERSION = ADDON.getAddonInfo('version')


def main():
    xbmcgui.Dialog().notification(
        ADDON_NAME,
        "Repositorio Larsan funcionando correctamente (v{})".format(ADDON_VERSION),
        xbmcgui.NOTIFICATION_INFO,
        4000
    )
    xbmcgui.Dialog().ok(
        ADDON_NAME,
        "Si puedes ver este mensaje, el repositorio Larsan "
        "se ha instalado y funciona correctamente.\n\n"
        "Version instalada: {}".format(ADDON_VERSION)
    )


if __name__ == '__main__':
    main()
