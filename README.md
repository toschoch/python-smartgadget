Sensirion Smartgadget MQTT Broadcast
===============================
author: Tobias Schoch

Overview
--------

Reads temperature and humidity values from a Sensirion Smartgadget BLE device and broadcasts them to a MQTT broker


Change-Log
----------
##### 0.0.3
* added dummy .secrets file for local drone execution
* added tagging stage and secrets
* named drone pipeline
* added git in the correct image now
* add git to the image before build and test
* add .drone.yml file for ci
* add another --entrypoint try
* another try
* remove latest
* latest image tag
* fixed isTag() and versions code in jenkinsfile
* removed entrypoint from jenkinsfile devpi image
* override entrypoint
* remove ash from arguments
* test with command ash
* use the devpi client image from docker
* does not work with shitty jenkins docker support
* make devpi client upload image more general purpose
* try entrypoint only as command seem to interfere with .inside()
* make jenkins not complain if the binaries do not exist
* fixed entrypoint and command for devpi upload image

##### 0.0.2
* fixed string interpolation in Jenkinsfile
* add Jeninksfile
* basic driver for smart gadget
* dummy change back
* dummy change
* remove the bluepy
* fixed paho typo in requirements file
* add requirements install in test env
* addey pyyaml
* add basic project structure and .drome.yml
* update readme

##### 0.0.1
* initial version


Installation / Usage
--------------------

To install use pip:

    pip install git@dietzi.ddns.net:Tobi/python-smartgadgetmqtt.git


Or clone the repo:

    git clone git@dietzi.ddns.net:Tobi/python-smartgadgetmqtt.git
    python setup.py install
    
Contributing
------------

TBD

Example
-------

TBD