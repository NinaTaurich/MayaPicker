
from __future__ import absolute_import
from six.moves import reload_module

def load():
    from . import pickerUI
    reload_module(pickerUI)
    return pickerUI.pickerBaseUI()
