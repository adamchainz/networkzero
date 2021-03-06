NetworkZero
===========

.. image:: https://travis-ci.org/tjguk/networkzero.svg?branch=master
    :target: https://travis-ci.org/tjguk/networkzero

Make it easy for learning groups to use simple networking in Python

..  note::

    **10th April 2016** This is under heavy development at the moment; things
    can and will change, possibly quite radically, over the next few days 
    and weeks. Please do take it for a spin, but don't base any long-term
    plans on the current API. TJG

    **21st April 2016** Still a lot of development going on. APIs changing
    and approaches shifting slightly. As before, please feel free to try
    out but not stable yet. TJG

    **5th May 2016** Closing in on freeze for 1.0

* Docs: http://networkzero.readthedocs.org/en/latest/

* Development: https://github.com/tjguk/networkzero

* Rough roadmap:

  * Stable 1.0 by 30th April
  * Perhaps use in London Python Dojo May 5th
  * Show to teachers at Twickenham coding evening 19th May

* Tests: to run the tests, run tox

At the time of writing, all tests pass on:

* Windows 8
* Debian Jessie
* Raspbian Jessie
* Mac OS/X 10.11

API
---

address below refers to an IP:Port string eg "192.168.1.5:4567"

Discovery
~~~~~~~~~

* address = advertise(name, address=None)

* address = discover(name, wait_for_s=FOREVER)

* [(name, address), ...] = discover_all()

Messaging
~~~~~~~~~

* reply = send_message_to(address, message, wait_for_reply_s=FOREVER)

* message = wait_for_message_from(address, [wait_for_s=FOREVER])

* send_notification_to(address, notification)

* wait_for_notification_from(address[, pattern=EVERYTHING][, wait_for_s=FOREVER])

Typical Usage
-------------

On computer (or process) A::

    import networkzero as nw0
    
    address = nw0.advertise("hello")
    while True:
        name = nw0.wait_for_message_from(address)
        nw0.send_message_to(address, "Hello, %s" % name)
        
On computer (or process) B and C and D...::

    import networkzero as nw0
    
    server = nw0.discover("hello")
    reply = nw0.send_message_to(server, "World")
    print(reply)
    reply = nw0.send_message_to(server, "Tim")
    print(reply)
