# Copyright 2014 Open Source Robotics Foundation, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.




# [db] dan@danbrooks.net
#
# diarc topology data structures for Fabrik
# This renames some things into Fabrik terminology to be more conveient, and also
# adds some attributes we want to track.
#
#   Logical  = Renamed  -> Layout components
#   ----------------------------
#   Vertex   = Node     -> Block
#       {Queue, Service, Wormhole, Latch (invisible, used in hooks)}
#   Edge     = Exchange -> Band
#   Sink     = Consumer -> Snap - emitter
#   Source   = Producer -> Snap - collector
#            = Transfer -> Hook
#            = Feed     -> Flow
#

from diarc.topology import *
import logging
import hooklabel
import flowlabel

log = logging.getLogger('fabrik.fabrik_parser')

class FabrikGraph(Topology):
    '''Storage container for describing the fabrik graph and diagram'''
    def __init__(self):
        super(FabrikGraph, self).__init__()
        self._transfers = TypedList(Transfer)
        self._feeds = TypedList(Feed)
        self.hide_disconnected_snaps = False

    @property
    def nodes(self):
        '''return a dictionary of {vertex-name: vertex} for all nodes in the graph'''
        return dict([(v.name, v) for v in self.vertices])

    @property
    def queues(self):
        '''return a dictionary of {vertex-name: vertex} for all queues in the graph'''
        return dict([(v.name, v) for v in self.vertices if v.nodeType == 'queue'])

    @property
    def exchanges(self):
        '''return a dicitonary of {edge-name: edge} for all exchanges in the graph'''
        return dict(filter(lambda x: None not in x, [(e.name, e) for e in self.edges]))

    @property
    def transfers(self):
        '''return a list of transfers in the graph'''
        return self._transfers

    @property
    def hooks(self):
        '''return a dictionary of {hooklabel: hook} for all transfers in the graph'''
        return dict([(t.hook.hooklabel(), t.hook) for t in self.transfers])

    @property
    def feeds(self):
        '''return a list of all feeds in the graph'''
        return self._feeds

    @property
    def flows(self):
        '''return a dictionary of {flowlabel: flow} for all feeds in the graph'''
        return dict([(f.flow.flowlabel(), f.flow) for f in self.feeds])

    def nextFreeNodeIndex(self):
        """ returns the next available node index """
        return max(self.blocks.keys())+1 if len(self.blocks) > 0 else 0

    def nextFreeAltitude(self):
        '''returns the next available band altitude'''
        altitudes = [band.altitude for band in self.bands.values()] + [0]
        return max(altitudes)+1

class FabrikBlock(Block):
    '''A subclass of the Block: a visual representation of a Vertex '''
    def __init__(self, vertex):
        super(FabrikBlock, self).__init__(vertex)
        self._node = vertex

    def __str__(self):
        string = "<Block vertex=" + str(self.vertex.name) + ", index=" + \
                str(self.index) + ", type=" + self.node.nodeType + ">"
        return string

    @property
    def node(self):
        '''returns the node which is visually represented by this block'''
        return self._node

    @property
    def flows(self):
        '''returns a list of all flows that enter or exit this node'''
        return (x.flow for x in self._node.feeds)

    @property
    def flowsGoingOut(self):
        '''returns a list of all flows that this block is origin for'''
        return filter(lambda f: (f.origin.block == self), self.flows)

    @property
    def flowsComingIn(self):
        '''returns a list of all flows that this block is destination for'''
        return filter(lambda f: (f.dest.block == self), self.flows)
    
    @property
    def isFlowOrigin(self):
        '''returns true if this block is an origin node to one or more flows'''
        if self.flowsGoingOut:
            return True
        return False

    @property
    def isFlowDest(self):
        '''returns true if this block is a destination node to one or more flows'''
        if self.flowsComingIn:
            return True
        return False
    
class Node(Vertex):
    '''Subclass of Vertex, in which we track more Fabrik-related things'''
    def __init__(self, fg):
        typecheck(fg, FabrikGraph, "fg")
        super(Node, self).__init__(fg)
        self._block = FabrikBlock(self)
        # dumb placement - just get the next free index
        self.block.index = fg.nextFreeNodeIndex()

        self.name = None
        self.location = None
        self.nodeType = None

    def __str__(self):
        string = "<Node=" + str(self.name) + ", index=" + \
                    str(self.block.index) + ", type=" + self.nodeType + ">"
        return string

    @property
    def producers(self):
        '''Returns all sources from this node'''
        # NOTE: This must be a property function (instead of just saying
        # self.producers = self.sources in the constructor) because self.sources
        # just returns a static list once, and we need this to be dynamically
        # queried every time we ask. This is because Vertex.sources and Edge.sources
        # are just syntax sugar for functions that are being called.
        return self.sources

    @property
    def consumers(self):
        '''Returns all sinks from this node'''
        return self.sinks

    @property
    def feeds(self):
        """Returns an unordered list of outgoing feeds from this node and incoming feeds to it"""
        return filter(lambda x: (x.origin == self) or (x.dest == self), self._topology._feeds)

class Queue(Node):
    '''A node representation of a RabbitMQ queue, in the Fabrik system'''
    def __init__(self, fg, name=None):
        typecheck(fg, FabrikGraph, "fg")
        super(Queue, self).__init__(fg)
        self.nodeType = "queue"
        self.name = name
        log.debug("Adding Queue " + str(name))

class ServiceBuddy(Node):
    '''A node representation of a Fabrik service buddy'''
    def __init__(self, fg, name=None):
        typecheck(fg, FabrikGraph, "fg")
        super(ServiceBuddy, self).__init__(fg)
        self.nodeType = "sb"
        self.name = name
        log.debug("Adding ServiceBuddy " + str(name))

class Wormhole(Node):
    '''A node representation of a connection to another vhost in the Fabrik system'''
    def __init__(self, fg, name=None):
        typecheck(fg, FabrikGraph, "fg")
        super(Wormhole, self).__init__(fg)
        self.nodeType = "wh"
        self.name = name
        log.debug("Adding Wormhole " + str(name))

class Latch(Node):
    '''A node placeholder for a transfer; see Transfer'''
    def __init__(self, fg, name=None):
        typecheck(fg, FabrikGraph, "fg")
        super(Latch, self).__init__(fg)
        self.nodeType = "latch"
        self.name = name
        log.debug("Adding Latch " + str(name))

class FabrikEdge(Edge):
    '''A Fabrik subclass of an Edge, in which we track useful things'''
    def __init__(self, topology):
        super(FabrikEdge, self).__init__(topology)

    @property
    def transfers(self):
        """ returns list of all source connections to this edge """
        return (t for t in self._topology._transfers if t.edge ==self)

class Exchange(FabrikEdge):
    '''It's unclear why I didn't just collapse this and FabrikEdge. Oops.'''
    def __init__(self, fg, name=None):
        typecheck(fg, FabrikGraph, "fg")
        super(Exchange, self).__init__(fg)

        self._pBand = FabrikBand(self, True)

        # Dumb placement - just get the enxt free altitudes
        self.posBand.altitude = fg.nextFreeAltitude()
        self.posBand.rank = self.posBand.altitude

        self.name = name
        log.debug("Adding Exchange " + str(name))

    def __str__(self):
        string = "<Exchange=" + str(self.name) + ">"
        return string

    @property
    def transfers(self):
        """an unordered list of transfers entering and exiting this exchange"""
        return filter(lambda x: x.origin == self or x.dest == self, self._topology._transfers)

    @property
    def producers(self):
        '''a list of all producers connected to this exchange'''
        # NOTE: See note on Node class about why this MUST be a property.
        return self.sources

    @property
    def consumers(self):
        '''a list of all consumers connected to this exchange'''
        # NOTE: See note on Node class about why this MUST be a property.
        return self.sinks

class FabrikBand(Band):
    '''A Fabrik variant of a Band, the visual representation of an Exchange'''
    def __init__(self, edge, isPositive):
        super(FabrikBand, self).__init__(edge, isPositive)

    def isUsed(self):
        '''No longer used.'''
        return True

    def __str__(self):
        return "<FabrikBand item: " + self._edge.name + " (altitude " + str(self.altitude) + ")>"

    @property
    def hooks(self):
        '''dict of {hooklabel: hook} for all hooks connected to this band'''
        transfers = self.edge.transfers
        if transfers:
            return {t.hook.hooklabel(): t.hook for t in transfers}
        else:
            return dict()

    @property
    def collectors(self):
        """ returns list of sink snaps that reach this band """
        if self.edge.sinks:
            return [s.snap for s in self.edge.sinks]
        else:
            return list()

    @property
    def emitters(self):
        """ returns list of sink snaps that reach this band """
        if self.edge.sources:
            return [s.snap for s in self.edge.sources]
        else:
            return list()

class Producer(Source):
    def __init__(self, fg, node, exchange, routingKeys=None):
        typecheck(fg, FabrikGraph, "fg")
        typecheck(node, Node, "node")
        typecheck(exchange, Exchange, "exchange")
        super(Producer, self).__init__(fg, node, exchange)
        # Dumb placement
        self.snap.order = max(filter(lambda x: isinstance(x, int),
                                     [prod.snap.order for prod in node.producers] + [-1]))+1

        self.bandwidth = None
        self.routingKeys = routingKeys
        log.debug("Adding Producer: " + str(node.name)+" to "+str(exchange.name)+ \
                    " with routing-keys "+str(routingKeys))

    def __str__(self):
        return "<Producer: "+self.node.name+"(node) -> "+self.exchange.name+"(exch)>"

    @property
    def exchange(self):
        # NOTE: See note on Node class about why this MUST be a property.
        return self.edge

    @property
    def node(self):
        # NOTE: See note on Node class about why this MUST be a property.
        return self.vertex

class Consumer(Sink):
    def __init__(self, fg, node, exchange, routingKeys=None):
        typecheck(fg, FabrikGraph, "fg")
        typecheck(node, Node, "node")
        typecheck(exchange, Exchange, "topic")
        super(Consumer, self).__init__(fg, node, exchange)

        # Dumb placement
        self.snap.order = max(filter(lambda x: isinstance(x, int),
                                     [con.snap.order for con in node.consumers] + [-1]))+1

        self.bandwidth = None
        self.routingKeys = routingKeys
        log.debug("Adding Consumer: " + str(exchange.name)+" to "+\
                    str(node.name)+" with routing-keys "+str(routingKeys))

    def __str__(self):
        return "<Consumer: "+self.node.name+"(node) <- "+self.exchange.name+"(exch)>"

    @property
    def exchange(self):
        # NOTE: See note on Node class about why this MUST be a property.
        return self.edge

    @property
    def node(self):
        # NOTE: See note on Node class about why this MUST be a property.
        return self.vertex

class Feed(object):
    """An object that represents messages flowing from a node to another node;
    Seen, for example, from a queue to a serivce buddy"""
    def __init__(self, fg, node_origin, node_dest, routingKeys=None):
        self._topology = typecheck(fg, FabrikGraph, "fg")
        self._origin = typecheck(node_origin, Node, "origin")
        self._dest = typecheck(node_dest, Node, "dest")
        self._flow = Flow(self, routingKeys)
        self._routingKeys = routingKeys
        for feed in node_origin.feeds + node_dest.feeds:
            if (node_origin == feed.origin) and\
                (node_dest == feed.dest) and \
                (routingKeys == feed.routingKeys):
                raise Exception("Duplicate node feed! "+node_origin.name+\
                        "->"+node_dest.name+", routing-keys: "+str(routingKeys))
        self._topology._feeds.append(self)

    @property
    def origin(self):
        return self._origin

    @property
    def dest(self):
        return self._dest

    @property
    def flow(self):
        return self._flow

    @property
    def routingKeys(self):
        return self._routingKeys

class Transfer(object):
    """An object that represents messages flowing from one exchange to another"""
    def __init__(self, fg, exchange_origin, exchange_dest, routingKeys=None):
        self._topology = typecheck(fg, FabrikGraph, "fg")
        self._origin = typecheck(exchange_origin, Exchange, "origin")
        self._dest = typecheck(exchange_dest, Exchange, "dest")
        self._hook = Hook(self, routingKeys)
        self._hook_label = self._hook.hooklabel
        self._routingKeys = routingKeys
        for transfer in exchange_origin.transfers + exchange_dest.transfers:
            if (exchange_origin == transfer.origin) and \
                    (exchange_dest == transfer.dest) and \
                    (routingKeys == transfer.routingKeys):
                raise Exception("Duplicate exchange transfer! "+exchange_origin.name+\
                        "->"+exchange_dest.name+", routing-keys:"+str(transfer.routingKeys))
        self._topology._transfers.append(self)
        self._latch = Latch(self._topology, str(self._origin.name) + "->" + str(self._dest.name))

    @property
    def origin(self):
        return self._origin

    @property
    def dest(self):
        return self._dest

    @property
    def hook(self):
        return self._hook

    @property
    def latch(self):
        return self._latch

    @property
    def routingKeys(self):
        return self._routingKeys

class Hook(object):
    """Visual representation of a transfer"""
    def __init__(self, transfer, routing_keys=None):
        self._transfer = typecheck(transfer, Transfer, "transfer")
        self._order = None
        self._routing_keys = routing_keys

    def hooklabel(self):
        return hooklabel.gen_hooklabel(self.origin.posBand.altitude, self.dest.posBand.altitude, \
                                       self.latch.block.index)

    @property
    def latch(self):
        return self._transfer.latch

    @property
    def origin(self):
        return self._transfer._origin

    @property
    def dest(self):
        return self._transfer._dest

    def isUsed(self):
        return True if self._transfer else False

    def _release(self):
        logging.debug("releasing hook %r"%self)
        logging.debug("... removing reference to transfer.")
        self._transfer = None

class Flow(object):
    """Visual representation of a feed"""
    def __init__(self, feed, routing_keys=None):
        self._feed = typecheck(feed, Feed, "feed")
        self._order = None
        self._routing_keys = routing_keys

    def flowlabel(self):
        return flowlabel.gen_flowlabel(self.origin.block.index, self.dest.block.index)

    @property
    def origin(self):
        return self._feed.origin

    @property
    def dest(self):
        return self._feed.dest

    def isUsed(self):
        return True if self._feed else False

    def _release(self):
        logging.debug("releasing flow %r"%self)
        logging.debug("... removing reference to feed.")
        self._feed = None

