from abc import ABCMeta as ABC, abstractmethod as abstract
from socket import socket as Socket, AF_INET, SOCK_DGRAM, SOL_SOCKET, SO_REUSEADDR, SO_BROADCAST, timeout as SocketTimeout, error as SocketError
from autobus2 import constants, net
from threading import Thread
import json
from traceback import print_exc
import time


class Discoverer(object):
    """
    A class capable of discovering services available remotely and making a
    particular bus aware of those services.
    
    This class is abstract; one of its subclases must be used instead. Bus
    instances, by default, install a BroadcastDiscoverer when they are created.
    
    When a discoverer is started, it should start attempting to discover
    services, however it goes about doing that. When it discovers one, it
    should call bus.discovered(self, host, port, service_id, info_object).
    When one disappears, it should call bus.undiscovered, passing in the same
    parameters. If the info object changes, the discoverer should just call
    bus.discovered again with the new info object.
    """
    @abstract
    def startup(self, bus):
        """
        """
    
    @abstract
    def shutdown(self):
        """
        """


"""
So, how should discovery work?

Well, basically we need something where, when we receive a packet indicating
that a service is available, then we add it to a list and if it wasn't in the
list then we tell the bus about it. If it was in the list but with a different
info object, we tell the bus about it again.

If we receive a message saying that a service has disappeared, we check to see
if it's in our list. If it is, then we tell the bus that it's disappeared and
remove it from our list.

So then we check every few seconds to see when the last time we received a
"I'm alive" message from any individual service was, every few seconds. If it's
been more than, say, a minute, we ask the bus to connect to that service. If
it's unable to do so after, say, ten seconds, then we remove the service.
"""


class BroadcastDiscoverer(object):
    """
    An implementation of Discoverer that listens for UDP broadcasts sent by
    other BroadcastPublisher instances on the network.
    """
    def startup(self, bus):
        self.bus = bus
        self.sender, self.receiver = create_broadcast_sockets()
        Thread(target=self.receive_loop).start()
    
    def shutdown(self):
        pass
    
    def receive_loop(self):
        


class Publisher(object):
    """
    A class capable of publishing information about services available to a
    particular Bus instance.
    
    This class is abstract; one of its subclasses must be used instead. Bus
    instances, by default, install a BroadcastPublisher when they are created.
    """
    @abstract
    def startup(self, bus):
        """
        Called by Bus instances when a publisher is installed onto them. The
        only argument is the bus onto which this publisher was installed.
        """
    
    @abstract
    def shutdown(self):
        """
        Called by Bus instances when a publisher is about to be removed. The
        bus will first call the publisher's remove function for every service
        it had previously added before calling shutdown.
        """
    
    @abstract
    def add(self, service):
        """
        Called to let this publisher know that a new service is available.
        """
    
    @abstract
    def remove(self, service):
        """
        Called to let this publisher know that a service is no longer available.
        """


class BroadcastPublisher(Publisher):
    """
    An implementation of Publisher that uses UDP broadcasts to let others know
    about available services. BroadcastDiscoverer is the matching discoverer
    that knows how to receive these broadcasts.
    """
    def __init__(self):
        self.running = True
        self.services = {}
        self.last_time = 0
    
    def startup(self, bus):
        if not self.running:
            raise Exception("BroadcastPublishers can't be re-used.")
        self.bus = bus
        self.sender, self.receiver = create_broadcast_sockets()
        Thread(target=self.receive_loop).start()
    
    def shutdown(self):
        print "Shutting down"
        self.running = False
        net.shutdown(self.receiver)
    
    def run_recurring(self):
        if self.last_time + constants.broadcast_interval < time.time():
            self.last_time = time.time()
            self.broadcast_services()
            
    def receive_loop(self):
        while True:
            message = None
            try:
                message = self.receiver.recvfrom(16384)[0]
            except SocketError:
                pass
            if not self.running:
                net.shutdown(self.sender)
                return
            self.run_recurring()
            if not message:
                continue
            try:
                message = json.loads(message)
                if message["command"] == "query":
                    self.broadcast_services()
            except:
                print "Couldn't read message"
                print_exc()
                continue
    
    def broadcast_services(self):
        with self.bus.lock:
            for service in self.services.values():
                self.send_add(service)
    
    def send_add(self, service):
        broadcast = {"command": "add", "port": self.bus.port,
                    "service": service.id, "info": service.info}
        broadcast = json.dumps(broadcast)
        self.sender.sendto(broadcast, 
                ("127.255.255.255", constants.broadcast_port))
        self.sender.sendto(broadcast, 
                ("255.255.255.255", constants.broadcast_port))
    
    def send_remove(self, service):
        broadcast = {"command": "remove", "port": self.bus.port,
                    "service": service.id}
        broadcast = json.dumps(broadcast)
        self.sender.sendto(broadcast, 
                ("127.255.255.255", constants.broadcast_port))
        self.sender.sendto(broadcast, 
                ("255.255.255.255", constants.broadcast_port))

    def add(self, service):
        with self.bus.lock:
            print "Service added: " + service.id
            self.services[service.id] = service
            self.send_add(service)
        
    
    def remove(self, service):
        with self.bus.lock:
            print "Service removed: " + service.id
            del self.services[service.id]
            self.send_remove(service)


def create_broadcast_sockets():
    sender = Socket(AF_INET, SOCK_DGRAM)
    sender.setsockopt(SOL_SOCKET, SO_REUSEADDR, True)
    sender.setsockopt(SOL_SOCKET, SO_BROADCAST, True)
    sender.bind(("", 0))
    receiver = Socket(AF_INET, SOCK_DGRAM)
    receiver.settimeout(constants.broadcast_receiver_timeout)
    receiver.setsockopt(SOL_SOCKET, SO_REUSEADDR, True)
    receiver.setsockopt(SOL_SOCKET, SO_BROADCAST, True)
    receiver.bind(("", constants.broadcast_port))
    return sender, receiver































