if __name__ == '__main__':
    from spadic.Ftdi import Ftdi
    from spadic.ftdi_stsxyter import FtdiStsxyter
    from spadic.shiftregister import SpadicShiftRegister
    from spadic.stsxyter import SpadicStsxyterRegisterAccess
    import logging
    logging.basicConfig(level='INFO',
                        filename='/tmp/spadictest.log', filemode='w')
    f = Ftdi()
    s = FtdiStsxyter(f).__enter__()
    r = SpadicStsxyterRegisterAccess(s, chip_address=7)
    sr = SpadicShiftRegister(r.write_registers, r.read_registers)
