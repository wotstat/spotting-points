__version__ = '{{VERSION}}'


def init():
  from wotstat_spotting_points import bootstrap
  bootstrap.init(__version__)


def fini():
  from wotstat_spotting_points import bootstrap
  bootstrap.fini()
