import mutti
from .base import SpadicToggle

class LedFrame(mutti.Frame):
    def __init__(self, spadic_controller, statusbar, _log=None):
        mutti.Frame.__init__(self, "User LEDs")
        self.control_panels = []

        led_list = mutti.VList()

        u = spadic_controller.led
        for d in [SpadicToggle(u, "userpin1", "Userpin 1",
                               min_width=20),
                  SpadicToggle(u, "userpin2", "Userpin 2",
                               min_width=20),
                 ]:
            d._status = statusbar
            d._log = _log
            self.control_panels.append(d)
            led_list.adopt(d)
        self.adopt(led_list)

    def _set_all(self):
        for panel in self.control_panels:
            panel.set()

    def _get_all(self):
        for panel in self.control_panels:
            panel._get()

