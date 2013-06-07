import mutti
from base import SpadicToggle

class DlmTriggerFrame(mutti.Frame):
    def __init__(self, spadic_controller, statusbar, _log=None):
        mutti.Frame.__init__(self, "DLM Trigger")
        self.control_panels = []

        dlm_list = mutti.VList()

        u = spadic_controller.hitlogic # TODO move these settings, they
                             # are actually not related to the hitlogic
        for d in [SpadicToggle(u, "analogtrigger", "Analog trigger",
                               min_width=20),
                  SpadicToggle(u, "triggerout", "Trigger output",
                               min_width=20),
                 ]:
            d._status = statusbar
            self.control_panels.append(d)
            dlm_list.adopt(d)
        self.adopt(dlm_list)

    def _set_all(self):
        for panel in self.control_panels:
            panel.set()

    def _get_all(self):
        for panel in self.control_panels:
            panel._get()

