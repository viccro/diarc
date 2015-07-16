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

log = logging.getLogger('fabrik.fabrik_parser')

class FabrikGraph(Topology):
    def __init__(self):
        super(FabrikGraph,self).__init__()
        self._transfers = TypedList(Transfer)
        self._feeds = TypedList(Feed)
        self.hide_disconnected_snaps = False

    @property
    def nodes(self):
        return dict([(v.name,v) for v in self.vertices])

    @property
    def queues(self):
        return dict([(v.name,v) for v in self.vertices if (v.nodeType == 'queue')])

    @property
    def exchanges(self):
        return dict(filter(lambda x: None not in x, [(topic.name,topic) for topic in self.edges]))

    @property
    def transfers(self):
        return self._transfers

    @property
    def hooks(self):
        return dict([(t.hook.hooklabel(), t.hook) for t in self.transfers])

    @property
    def feeds(self):
        return self._feeds

    def nextFreeNodeIndex(self):
        """ returns the next available node index """
        return max(self.blocks.keys())+1 if len(self.blocks)>0 else 0
    
    def nextFreeAltitudes(self):
        """ returns a 2-tuple of (posAltitude,negAltitude) of the avaliable altitudes """
        altitudes = [band.altitude for band in self.bands.values()] + [0]
        return (max(altitudes)+1,min(altitudes)-1)



class Node(Vertex):
    def __init__(self,fg):
        typecheck(fg,FabrikGraph,"fg")
        super(Node,self).__init__(fg)
        
        # dumb placement - just get the next free index
        self.block.index = fg.nextFreeNodeIndex()

        self.name = None
        self.location = None
        self.nodeType = None

    @property
    def producers(self):
        # NOTE: This must be a property function (instead of just saying 
        # self.producers = self.sources in the constructor) because self.sources
        # just returns a static list once, and we need this to be dynamically
        # queried every time we ask. This is because Vertex.sources and Edge.sources
        # are just syntax sugar for functions that are being called.
        return self.sources

    @property
    def consumers(self):
        return self.sinks


class Queue(Node):
    def __init__(self,fg,name=None):
        typecheck(fg,FabrikGraph,"fg")
        super(Queue,self).__init__(fg)
        self.nodeType = "queue"        
        self.name = name
        log.debug( "Adding Queue " + str(name))
        
class ServiceBuddy(Node):
    def __init__(self,fg,name=None):
        typecheck(fg,FabrikGraph,"fg")
        super(ServiceBuddy,self).__init__(fg)
        self.nodeType = "sb"
        self.name = name
        log.debug("Adding ServiceBuddy " + str(name))

class Wormhole(Node):
    def __init__(self,fg,name=None):
        typecheck(fg,FabrikGraph,"fg")
        super(Wormhole,self).__init__(fg)
        self.nodeType = "wh"
        self.name = name
        log.debug( "Adding Wormhole " + str(name))

class Latch(Node):
    def __init__(self, fg, name=None):
        typecheck(fg,FabrikGraph, "fg")
        super(Latch,self).__init__(fg)
        self.nodeType = "latch"
        self.name = name
        log.debug( "Adding Latch" + str(name))

class Exchange(Edge):
    def __init__(self,fg,name=None):
        typecheck(fg,FabrikGraph,"fg")
        super(Exchange,self).__init__(fg)

        self._pBand = FabrikBand(self,True)
        self._nBand = FabrikBand(self,False)

        # Dumb placement - just get the enxt free altitudes
        self.posBand.altitude,self.negBand.altitude = fg.nextFreeAltitudes()
        self.posBand.rank = self.posBand.altitude
        self.negBand.rank = self.posBand.altitude

        self.name = name
        log.debug("Adding Exchange " + str(name))

    @property
    def transfers(self):
        """Returns an unordered list of outgoing transfers from this exchange"""
        return filter(lambda x: x.origin == self, self._topology._transfers)

    @property
    def producers(self):
        # NOTE: See note on Node class about why this MUST be a property.
        return self.sources

    @property
    def consumers(self):
        # NOTE: See note on Node class about why this MUST be a property.
        return self.sinks



class FabrikBand(Band):
    def __init__(self, edge, isPositive):
        super(FabrikBand, self).__init__(edge, isPositive)

    def isUsed(self):
        return True


class Producer(Source):
    def __init__(self,fg,node,exchange,routingKeys = None):
        typecheck(fg,FabrikGraph,"fg")
        typecheck(node,Node,"node") 
        typecheck(exchange, Exchange, "exchange")
        super(Producer,self).__init__(fg,node,exchange)
        # Dumb placement
        self.snap.order = max(filter(lambda x: isinstance(x,int), [prod.snap.order for prod in node.producers] + [-1]))+1

        self.bandwidth = None
        self.routingKeys = routingKeys
        log.debug("Adding Producer: " + str(node.name)+" to "+str(exchange.name))

    @property
    def exchange(self):
        # NOTE: See note on Node class about why this MUST be a property.
        return self.edge

    @property
    def node(self):
        # NOTE: See note on Node class about why this MUST be a property.
        return self.vertex

class Consumer(Sink):
    def __init__(self,fg,node,exchange, routingKeys = None):
        typecheck(fg,FabrikGraph,"fg")
        typecheck(node,Node,"node")
        typecheck(exchange,Exchange,"topic")
        super(Consumer,self).__init__(fg,node,exchange)

        # Dumb placement
        self.snap.order = max(filter(lambda x: isinstance(x,int), [con.snap.order for con in node.consumers] + [-1]))+1

        self.bandwidth = None
        self.routingKeys = routingKeys
        log.debug("Adding Consumer: " + str(exchange.name)+" to "+str(node.name))

    @property
    def topic(self):
        # NOTE: See note on Node class about why this MUST be a property.
        return self.edge

    @property
    def node(self):
        # NOTE: See note on Node class about why this MUST be a property.
        return self.vertex

class Feed(object):
    """An object that represents messages flowing from a node to another node;
    Seen, for example, from a queue to a serivce buddy"""
    def __init__(self, fg, node_origin, node_dest):
        self._topology = typecheck(fg, FabrikGraph, "fg")
        self._origin = typecheck(node_origin, Node, "origin")
        self._dest = typecheck(node_dest, Node, "dest")
        self._topology._feeds.append(self)

    @property
    def origin(self):
        return self._origin

    @property
    def dest(self):
        return self._dest

class Transfer(object):
    """An object that represents messages flowing from one exchange to another"""
    def __init__(self, fg, exchange_origin, exchange_dest, routingKeys = None):
        self._topology = typecheck(fg, FabrikGraph, "fg")
        self._origin = typecheck(exchange_origin, Exchange, "origin")
        self._dest = typecheck(exchange_dest, Exchange, "dest")
        self._hook = Hook(self)
        self._routingKeys = routingKeys
        for transfer in exchange_origin.transfers + exchange_dest.transfers:
            if (exchange_origin == transfer.origin) and (exchange_dest == transfer.dest) and (routingKeys == transfer.routingKeys):
                raise Exception("Duplicate exchange transfer! "+exchange_origin.name+"->"+exchange_dest.name+", routing-keys:"+str(transfer.routingKeys))
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
    def __init__(self, transfer):
        self._transfer = typecheck(transfer, Transfer, "transfer")
        self._order = None    
    
    def hooklabel(self):
        return hooklabel.gen_hooklabel(self.origin.posBand.altitude, self.dest.posBand.altitude, self.latch.block.index)

    def posBandLink(self):
#TODO something
        pBand = self._transfer.origin.posBand
        return pBand

    def negBandLink(self):
#TODO something
        nBand = self._transfer.origin.negBand
        return nBand

    @property
    def latch(self):
        return self._transfer.latch

    @property
    def origin(self):
        return self._transfer._origin

    @property
    def dest(self):
        return self._transfer._dest

    @property
    def bandLinks(self):
        return filter(lambda x: isinstance(x,Band), [self.posBandLink, self.negBandLink])

    #TODO leftHook rightHook?

#class Flow(
