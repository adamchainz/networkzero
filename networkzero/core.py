# -*- coding: utf-8 -*-
import fnmatch
import logging
import random
import re
import shlex
import socket

from . import config

def get_logger(name):
    #
    # For now, this is just a hand-off to logging.getLogger
    # Later, though, we might want to add a null handler etc.
    #
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    return logger

def _setup_debug_logging():
    logger = logging.getLogger("networkzero")
    handler = logging.FileHandler("network.log", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s"))
    handler.setLevel(logging.DEBUG)
    logger.addHandler(handler)

def _get_root_logger():
    logger = get_logger("networkzero")
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
    handler.setLevel(logging.WARN)
    logger.addHandler(handler)
    return logger

_root_logger = _get_root_logger()
_logger = get_logger(__name__)

#
# Common exceptions
#
class NetworkZeroError(Exception): 
    pass

class SocketAlreadyExistsError(NetworkZeroError): 
    pass

class SocketTimedOutError(NetworkZeroError):
    
    def __init__(self, n_seconds):
        self.n_seconds = n_seconds
    
    def __str__(self):
        return "Gave up waiting after %s seconds; this connection is now unusable" % self.n_seconds

class SocketInterruptedError(NetworkZeroError):
    
    def __init__(self, after_n_seconds):
        self.after_n_seconds = after_n_seconds
    
    def __str__(self):
        return "Interrupted after %s seconds; this connection is now unusable" % self.after_n_seconds

class InvalidAddressError(NetworkZeroError):
    pass

#
# Ports in the range 0xc000..0xffff are reserved
# for dynamic allocation
#
PORT_POOL = list(config.DYNAMIC_PORTS)

def split_address(address):
    if ":" in address:
        ip, _, port = address.partition(":")
    else:   
        if address.isdigit():
            ip, port = "", address
        else:
            ip, port = address, ""
    return ip, port

def is_valid_ip(ip):
    return bool(re.match("^\d{,3}\.\d{,3}\.\d{,3}\.\d{,3}$", ip))

def is_valid_port(port, port_range=range(65536)):
    try:
        return int(port) in port_range
    except ValueError:
        return False

def is_valid_address(address, port_range=range(65536)):
    ip, port = split_address(address)
    return is_valid_ip(ip) and is_valid_port(port, port_range)

def address_sorter(prefer):
    return 

_ip4 = None
def find_valid_ip4(prefer=None):
    #
    # Order the list of possible addresses on the machine: if any
    # address pattern is given as a preference (most -> least)
    # give it that weighting, otherwise treat all addresses
    # numerically. If no preference is given, prefer the most
    # likely useful local address range.
    #
    if prefer is None:
        prefer = ["192.168.*"]
    def sorter(ip4):
        octets = [int(i) for i in ip4.split(".")]
        for n, pattern in enumerate(prefer):
            if fnmatch.fnmatch(ip4, pattern):
                return n, octets
        else:
            return n + 1, octets
    
    global _ip4
    #
    # Find the list of valid IP addresses on this machine
    #
    addrinfo = socket.getaddrinfo(None, 0, socket.AF_INET)    
    #
    # Pick an arbitrary one of the IP addresses matching the address
    #
    addresses = [ip for ip, port in [a[-1] for a in addrinfo]]
    if not addresses:
        raise InvalidAddressError("No valid address found")
    else:
        _ip4 = min(addresses, key=sorter)        
    
    return _ip4 

def address(address=None, prefer=None):
    """Convert one of a number of inputs into a valid ip:port string.
    
    Elements which are not provided are filled in as follows:
        
        * IP Address: the system is asked for the set of IP addresses associated 
          with the machine and the first one is used.
        * Port number: a random port is selected from the pool of dynamically-available 
          port numbers.
      
    This means you can pass any of: nothing; an IP address; a port number; both
    
    If an IP address is supplied but is invalid, an InvalidAddressError
    exception is raised.
    
    :param address: (optional) Any of: an IP address, a port number, or both
    :param prefer: (optional) a more->less preferred list of IP matches
    
    :returns: a valid ip:port string for this machine
    """
    address = str(address or "").strip()
    #
    # If the address is an ip:port pair, split into its component parts.
    # Otherwise, try to determine whether we're looking at an IP
    # or at a port and leave the other one blank
    #
    ip, port = split_address(address)
    
    #
    # If the port has been supplied, make sure it's numeric and that it's a valid
    # port number. If it hasn't been supplied, remove a random one from the pool
    # of possible dynamically-allocated ports and use that.
    #
    if port:
        try:
            port = int(port)
        except ValueError:
            raise InvalidAddressError("Port %s must be a number" % port)
        if port not in config.VALID_PORTS:
            raise InvalidAddressError("Port %d must be in range %d - %d" % (
                port, min(config.VALID_PORTS), max(config.VALID_PORTS))
            )
    else:
        random.shuffle(PORT_POOL)
        port = PORT_POOL.pop()

    if not ip:
        if _ip4:
            ip = _ip4
        else:
            ip = find_valid_ip4(prefer)
    
    return "%s:%s" % (ip, port)

split_command = shlex.split