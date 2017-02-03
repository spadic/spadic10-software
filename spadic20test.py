import logging
from spadic import Spadic
logging.basicConfig(level='DEBUG',
                    filename='/tmp/spadictest.log', filemode='w')
s = Spadic().__enter__()
