def onoff(value):
    return 'ON' if value else 'OFF'

def checkvalue(v, vmin, vmax, name):
    if v < vmin or v > vmax:
        raise ValueError('valid %s range: %i..%i' %
                         (name, vmin, vmax))


class ControlUnitBase:
    def write(self, *args, **kwargs):
        self.set(*args, **kwargs)
        self.apply()

    def read(self):
        self.update()
        return self.get()

