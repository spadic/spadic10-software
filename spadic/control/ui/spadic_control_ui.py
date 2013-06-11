import curses
import mutti
from base import SpadicToggle
from hitlogic import HitLogicFrame
from filter import FilterFrame
from dlmtrigger import DlmTriggerFrame
from led import LedFrame
from adcbias import AdcBiasFrame
from frontend import FrontendFrame


class SpadicControlUI(mutti.Screen):
    def __init__(self, spadic_controller, _log=None):
        mutti.Screen.__init__(self)
        c = spadic_controller
        self.controller = c
        self.control_panels = []
        self._log = _log
        self._directmode = False

        tabs = mutti.Tabs()
        tabs._log = _log

        #--------------------------------------------------------------------
        # Global digital settings
        #--------------------------------------------------------------------
        hitlogic_filter_list = mutti.VList()

        # hit logic
        hitlogic_frame = HitLogicFrame(c, self.statusbar, _log)
        hitlogic_filter_list.adopt(hitlogic_frame)
        self.control_panels.append(hitlogic_frame)
        # filter
        filter_frame = FilterFrame(c, self.statusbar, _log)
        hitlogic_filter_list.adopt(filter_frame)
        self.control_panels.append(filter_frame)

        tabs.adopt(hitlogic_filter_list, "Global digital settings")

        #--------------------------------------------------------------------
        # Global analog settings
        #--------------------------------------------------------------------
        global_analog_list = mutti.VList()

        adcbias_frame = AdcBiasFrame(c, self.statusbar, _log)
        global_analog_list.adopt(adcbias_frame)
        self.control_panels.append(adcbias_frame)

        frontend_frame = FrontendFrame(c, self.statusbar, _log)
        global_analog_list.adopt(frontend_frame)
        self.control_panels.append(frontend_frame)

        tabs.adopt(global_analog_list, "Global analog settings")

        #--------------------------------------------------------------------
        # miscellaneous settings
        #--------------------------------------------------------------------
        misc_list = mutti.VList()

        # DLM trigger
        dlmtrigger_frame = DlmTriggerFrame(c, self.statusbar, _log)
        misc_list.adopt(dlmtrigger_frame)
        self.control_panels.append(dlmtrigger_frame)

        # User LEDs
        led_frame = LedFrame(c, self.statusbar, _log)
        misc_list.adopt(led_frame)
        self.control_panels.append(led_frame)

        tabs.adopt(misc_list, "Misc. settings")

        self.adopt(tabs)


    def _set_all(self):
        for panel in self.control_panels:
            panel._set_all()

    def _get_all(self):
        for panel in self.control_panels:
            panel._get_all()

    def _apply_all(self):
        self._set_all()
        self.controller.apply()

    def _update_all(self):
        #self.controller.update()
        self._get_all()

    def _reset(self):
        self.controller.reset()
        self.controller.apply()

    def _handle_key(self, key):
        key = mutti.Screen._handle_key(self, key)
        if key is not None:
            if key == curses.KEY_F3:
                self._directmode = not self._directmode
            elif key == curses.KEY_F4:
                self._apply_all()
            elif key == curses.KEY_F5:
                self._update_all()
            elif key == curses.KEY_F6:
                self._reset()
            else:
                return key
        else:
            if self._directmode:
                self._apply_all()

