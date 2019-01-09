Python API for Sensirion BLE Smartgadget
========================================
[![Build Status](https://drone.github.dietzi.mywire.org/api/badges/toschoch/python-smartgadget/status.svg)](https://drone.github.dietzi.mywire.org/toschoch/python-smartgadget)

author: Tobias Schoch 

Overview
--------

Provides functions to scan for and access nearby [Sensirion BLE Smartgadgets][1] through the [BluePy][2] BLE interface for Python. Temperature and humdity readings as well as logging functionality is supported.

Change-Log
----------
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