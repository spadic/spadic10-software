import mutti
from base import SpadicToggle
from hitlogic import HitLogicFrame
from filter import FilterFrame
from dlmtrigger import DlmTriggerFrame
from led import LedFrame
from adcbias import AdcBiasFrame


class SpadicControlUI(mutti.Screen):
    def __init__(self, spadic_controller, _log=None):
        mutti.Screen.__init__(self)
        c = spadic_controller
        self._log = _log

        tabs = mutti.Tabs()
        tabs._log = _log

        #--------------------------------------------------------------------
        # Global digital settings
        #--------------------------------------------------------------------
        hitlogic_filter_list = mutti.VList()

        # hit logic
        hitlogic_frame = HitLogicFrame(c, self.statusbar, _log)
        hitlogic_filter_list.adopt(hitlogic_frame)
        # filter
        filter_frame = FilterFrame(c, self.statusbar, _log)
        hitlogic_filter_list.adopt(filter_frame)

        tabs.adopt(hitlogic_filter_list, "Global digital settings")

        #--------------------------------------------------------------------
        # Global analog settings
        #--------------------------------------------------------------------
        adcbias_frame = AdcBiasFrame(c, self.statusbar, _log)

        tabs.adopt(adcbias_frame, "Global analog settings")

        #--------------------------------------------------------------------
        # miscellaneous settings
        #--------------------------------------------------------------------
        misc_list = mutti.VList()

        # DLM trigger
        dlmtrigger_frame = DlmTriggerFrame(c, self.statusbar, _log)
        misc_list.adopt(dlmtrigger_frame)

        # User LEDs
        led_frame = LedFrame(c, self.statusbar, _log)
        misc_list.adopt(led_frame)

        tabs.adopt(misc_list, "Misc. settings")

        self.adopt(tabs)

