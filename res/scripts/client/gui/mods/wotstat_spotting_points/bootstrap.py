# -*- coding: utf-8 -*-
import logging

from .controller import SpottingPointsController
from .marker_view import registerMarkerView, unregisterMarkerView
from .settings_view import registerSettingsView, showSettings, unregisterSettingsView

MOD_ID = 'wotstat.spotting-points'
log = logging.getLogger('WOTSTAT_SPOTTING_POINTS')
controller = None
_modsList = None


def init(version):
    global controller, _modsList
    if controller is not None:
        return
    try:
        from gui.modsListApi import g_modsListApi
    except ImportError:
        log.error('ModsList API is required to enable Spotting Points')
        return
    instance = SpottingPointsController()
    settingsRegistered = False
    markerRegistered = False
    try:
        registerMarkerView()
        markerRegistered = True
        registerSettingsView()
        settingsRegistered = True
        g_modsListApi.addModification(
            id=MOD_ID, name='Настройки габаритных и обзорных точек',
            description='Открыть окно настроек точек, направляющих и башни',
            icon='', enabled=True, login=False, lobby=True,
            callback=lambda: showSettings(instance))
    except Exception:
        if settingsRegistered:
            unregisterSettingsView()
        if markerRegistered:
            unregisterMarkerView()
        instance.destroy()
        raise
    controller = instance
    _modsList = g_modsListApi
    log.info('Loaded %s; display disabled', version)


def fini():
    global controller, _modsList
    instance = controller
    modsList = _modsList
    controller = None
    _modsList = None
    try:
        if modsList is not None:
            modsList.removeModification(MOD_ID)
    finally:
        try:
            unregisterSettingsView()
        finally:
            try:
                unregisterMarkerView()
            finally:
                if instance is not None:
                    instance.destroy()
