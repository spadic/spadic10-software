if __name__ == '__main__':
    from spadic.Ftdi import Ftdi
    from spadic.ftdi_stsxyter import FtdiStsxyter
    from spadic.shiftregister import SpadicShiftRegister
    from spadic.registerfile import SpadicRegisterFile
    from spadic.stsxyter import SpadicStsxyterRegisterAccess
    import logging
    logging.basicConfig(level='INFO',
                        filename='/tmp/spadictest.log', filemode='w')
    f = Ftdi()
    s = FtdiStsxyter(f).__enter__()
    r = SpadicStsxyterRegisterAccess(s, chip_address=7)
    sr = SpadicShiftRegister(r.write_registers, r.read_registers)

    def rf_write_gen(name, addr):
        def write(value):
            r.write_registers([(addr, value)])
        return write

    def rf_read_gen(name, addr):
        def read():
            return next(r.read_registers([addr]))
        return read

    rf = SpadicRegisterFile(rf_write_gen, rf_read_gen)
