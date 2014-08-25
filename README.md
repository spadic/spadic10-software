# SPADIC 1.0 control software for Susibo/CBMnet readout

## Changes:

* v1.1.7 (2013-12-10)
  The fit residual is now plotted in SpadicScope. Added the option to set
  the number of samples used for fitting (0 turns fitting off).

* v1.1.6 (2013-09-03)
  Added a new package spadic.tools, which contains SpadicDataMonitor and
  SpadicScope. SpadicDataMonitor reads all the data and discards all
  messages coming in faster than a specified rate. This way, the data
  output can be monitored without having to consume each message.
  SpadicScope is a data plotting tools based on Qt (pyqtgraph) which uses
  SpadicDataMonitor.

* v1.1.5 (2013-08-23)
  The installation will not fail if libFTDI is not installed. Only the
  server part not be available in this case, but the client part can still
  be used.

* v1.1.2--4 (2013-08-22)
  Improvements in the caching of register file and shift register contents
  in the respective client components, so that configuration changes from
  other clients are noticed without requesting unnecessarily much data
  from the server.

* v1.1.1 (2013-08-20)
  The RF/SR/DLM server components can now accept multiple connections,
  which means that the configuration can be read out, but also modified,
  by several clients in parallel. The data readout server components are
  still limited to one connection each.

* v1.1.0 (2013-08-14)
  Split the software in server and client parts. Allows to write arbitrary
  custom clients without modification of the server part. The server
  listens on five consecutive ports, handling
  - register file access (settings of the digital part of the chip),
  - shift register access (settings of the analog part of the chip),
  - DLM access,
  - channel group A readout, and
  - channel group B readout, respectively.

* v1.0.4--7 (2013-07/08)
  Various improvements.

* v1.0.3 (2013-06-10)
  Added first version of terminal-based control user interface (using
  the "mutti" library).

* v1.0.2 (2013-05-07)
  Using threads for register reading, allowing much faster bulk readout.

* v1.0.0 (2013-05-06)
  First version using CBMnet communication.


## Requirements:

* Python 2.7 or newer (but not Python 3.x)


* libFTDI v0.20 or newer with Python bindings
  (not needed on client-only computers)

  Homepage: http://www.intra2net.com/en/developer/libftdi/

  Quick installation guide:

  ```sh
  $ git clone git://developer.intra2net.com/libftdi /tmp/libftdi
  $ cd /tmp/libftdi
  $ mkdir build; cd build
  $ cmake ..
  $ make
  $ make install
  ```

* mutti (Michael's User Text Terminal Interface)

  ```sh
  $ git clone https://github.com/mkrieger1/mutti.git /tmp/mutti
  $ cd /tmp/mutti
  $ python setup.py install [--user]
  ```
