import mutti
from base import SpadicToggle
from hitlogic import HitLogicFrame
from dlmtrigger import DlmTriggerFrame


class SpadicControlUI(mutti.Screen):
    def __init__(self, spadic_controller, _log=None):
        mutti.Screen.__init__(self)
        c = spadic_controller
        self._log = _log

        tabs = mutti.Tabs()
        tabs._log = _log

        # Hit Logic + DLM trigger settings
        hitlogic_dlm_list = mutti.VList()
        u = c.hitlogic

        hitlogic_frame = HitLogicFrame(c, self.statusbar, _log)
        hitlogic_dlm_list.adopt(hitlogic_frame)

        dlmtrigger_frame = DlmTriggerFrame(c, self.statusbar, _log)
        hitlogic_dlm_list.adopt(dlmtrigger_frame)

        tabs.adopt(hitlogic_dlm_list, "Global digital settings")
        self.adopt(tabs)

