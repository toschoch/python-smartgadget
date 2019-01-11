Python API for Sensirion BLE Smartgadget
========================================
[![Build Status](https://drone.github.dietzi.mywire.org/api/badges/toschoch/python-smartgadget/status.svg)](https://drone.github.dietzi.mywire.org/toschoch/python-smartgadget)

author: Tobias Schoch 

Overview
--------

Provides functions to scan for and access nearby [Sensirion BLE Smartgadgets][1] through the [BluePy][2] BLE interface for Python. Temperature and humdity readings as well as logging functionality is supported.

Change-Log
----------
##### 1.0.0
* add a test for the scanner
* fixed not existing time_ns() -> time()
* removed mutable default argument, cannot pass store anymore to scanner
* code reformatting
* removed unnesseary declaration
* made compatible with python 3.5
* added basic tests
* remove the pip-reqs, etc again
* changed build env to python:3
* glib-dev for alpine
* build-base for alpine
* fixed build env in drone and import
* added build status to readme
* updated readme
* update readme
* renamed project
* moved everything not related to the smartgadget driver to the docker application
* renamed modules
* working scheduler setup for repeated scanning the devices and data download
* fixed for arbitrary subscribed services
* connect to two devices instantaneously
* working download for one FloatService
* redesigned for correct service / characteristics
* redesigned for working download
* separated into scanner module and device module

##### 0.0.3
* added dummy .secrets file for local drone execution
* added tagging stage and secrets

##### 0.0.2
* add requirements install in test env
* add basic project structure and .drone.yml
* update readme

##### 0.0.1
* initial version


Installation / Usage
--------------------

To install use pip:

    pip install https://github.com/toschoch/python-smartgadget.git


Or clone the repo:

    git clone https://github.com/toschoch/python-smartgadget.git
    python setup.py install
    

Example
-------

```python
from smartgadget.scanner import SmartGadgetScanner

scanner = SmartGadgetScanner()

gadgets = scanner.scan(5) # scan 5 seconds for nearby gadgets

for addr, gadget in gadgets.items():
    gadget.connect()
    print("Gadget ({}): {:.1f}{}".format(addr, 
                                         gadget.readTemperature(), 
                                         gadget.Temperature.unit))
 
```


[1]: https://www.sensirion.com/de/umweltsensoren/feuchtesensoren/development-kit/
[2]: https://github.com/IanHarvey/bluepy