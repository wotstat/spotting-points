# -*- coding: utf-8 -*-
import logging

from .controller import SpottingPointsController

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
    try:
        g_modsListApi.addModification(
            id=MOD_ID, name='Включить/выключить габаритные точки',
            description='Габаритные и обзорные точки танка в ангаре',
            icon='', enabled=True, login=False, lobby=True,
            callback=instance.toggle)
    except Exception:
        instance.destroy()
        raise
    controller = instance
    _modsList = g_modsListApi
    log.info('Loaded %s; display disabled', version)


def fini():
    global controller, _modsList
    if controller is None:
        return
    controller.destroy()
    controller = None
    _modsList.removeModification(MOD_ID)
    _modsList = None
