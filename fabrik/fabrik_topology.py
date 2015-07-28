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

    @property
    def flows(self):
        return dict([(f.flow.flowlabel(), f.flow) for f in self.feeds])

    def nextFreeNodeIndex(self):
        """ returns the next available node index """
        return max(self.blocks.keys())+1 if len(self.blocks)>0 else 0
    
    def nextFreeAltitudes(self):
        """ returns a 2-tuple of (posAltitude,negAltitude) of the avaliable altitudes """
        altitudes = [band.altitude for band in self.bands.values()] + [0]
        return (max(altitudes)+1,min(altitudes)-1)

class FabrikBlock(Block):
    def __init__(self, vertex):
        super(FabrikBlock, self).__init__(vertex)
        self._node = vertex

    def __str__(self):
        string =  "<Block vertex=" + str(self.vertex.name) + ", index=" + str(self.index) + ", type=" + self.node.nodeType + ">"
        return string

    @property
    def node(self):
        return self._node

    @property
    def flows(self):
        return map(lambda x: x.flow, self._node.feeds)

    @property
    def flowsGoingOut(self):
        return filter(lambda f: (f.origin.block == self), self.flows)

    @property 
    def flowsComingIn(self):
        return filter(lambda f: (f.dest.block == self), self.flows)

    @property
    def isFlowOrigin(self):
        if self.flowsGoingOut:
            return True
        return False

    @property
    def isFlowDest(self):
        if self.flowsComingIn:
            return True
        return False

class Node(Vertex):
    def __init__(self,fg):
        typecheck(fg,FabrikGraph,"fg")
        super(Node,self).__init__(fg)
        self._block = FabrikBlock(self)
        # dumb placement - just get the next free index
        if self.feeds is None:
            self.block.index = fg.nextFreeNodeIndex()
        else:
            print "Woah there"
            self.block.index = fg.nextFreeNodeIndex()

        self.name = None
        self.location = None
        self.nodeType = None

    def __str__(self):
        string =  "<Node=" + str(self.name) + ", index=" + str(self.block.index) + ", type=" + self.nodeType + ">"
        return string

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

    @property
    def feeds(self):
        """Returns an unordered list of outgoing feeds from this node and incoming feeds to it"""
        return filter(lambda x: (x.origin == self) or (x.dest == self), self._topology._feeds)

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
        log.debug( "Adding Latch " + str(name))

class FabrikEdge(Edge):
    def __init__(self, topology):
        super(FabrikEdge, self).__init__(topology)

    @property
    def transfers(self):
        """ returns list of all source connections to this edge """
        return filter(lambda x: x.edge == self, self._topology._transfers)

class Exchange(FabrikEdge):
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

    def __str__(self):
        string =  "<Exchange=" + str(self.name) + ">"
        return string

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

    @property
    def hooks(self):
        transfers = self.edge.transfers
        if transfers:
            return {t.hook.hooklabel(): t.hook for t in transfers}
        else:
            return dict()

    def __str__(self):
        return "<FabrikBand item: " + self._edge.name + " (altitude " + str(self.altitude) + ")>"

class FabrikSnap(Snap):
    """ Visual Representation of a Source or Sink.
        Snaps are layedout horizontally inside of an Emitter or Collector of a Block.
        A Snap provides a mapping between a Source/Sink and one or two Bands associated with a single Edge.
        Visual Layout Paramters
        Order - 0-indexed order in which to draw snaps within an Emitter or Collector 
    """

    def __init__(self,connection):
        self._connection = typecheck(connection,FabrikConnection,"connection")
        self._order = None

    def snapkey(self):
        """ generates the snapkey for this snap """
        return gen_snapkey(self.block.index, "collector" if self.isSink() else "emitter", self._order)

    def _release(self):
        """ This should only be called by a Connection.release() """
        logging.debug("releasing snap %r"%self)
        # the connection should 
        logging.debug("... removing reference to connection")
        self._connection = None

    def isUsed(self):
        return True

    @property
    def posBandLink(self):
        return self._connection.edge._pBand

    @property
    def negBandLink(self):
        return self._connection.edge._pBand

    @property
    def block(self):
        return self._connection.vertex.block

    @property
    def connection(self):
        return self._connection

    @property
    def bandLinks(self):
        return filter(lambda x: isinstance(x,Band), [self.posBandLink,self.negBandLink])

    def isSource(self):
        return isinstance(self._connection,Source)

    def isSink(self):
        return isinstance(self._connection,Sink)

    def isLinked(self):
        """ returns true if this snap is connected to at least one sink, else false. """
        return True if self.posBandLink or self.negBandLink else False

    def isUsed(self):
        """ returns true if topology.hide_disconnected_snaps is True and isLinked is True, 
        or if topology.hide_disconnected_snaps is false. Otherwise, return true.
        """
        if self._connection._topology.hide_disconnected_snaps:
            return True if self.isLinked() else False
        else:
            return True

    @property
    def leftSnap(self):
        """ Returns the snap directly to the left of this snap within either an 
        emitter or collector. Returns None if this is leftmost snap. 
        """
        snaps = self.block.emitter if self.isSource() else self.block.collector
        if isinstance(self._order,int) and self._order > min(snaps.keys()):
            return snaps[max([s for s in snaps.keys() if s < self._order])]
        else:
            return None

    @property
    def rightSnap(self):
        """ Returns the snap directly to the right of this snap within either 
        an emitter or collector. Returns None if this is rightmost snap.
        """
        snaps = self.block.emitter if self.isSource() else self.block.collector
        if isinstance(self._order,int) and self._order < max(snaps.keys()):
            return snaps[min([s for s in snaps.keys() if s > self._order])]


class FabrikConnection(object):
    """ A base class for connecting a vertex to an edge, but without specifing 
	the nature of the connection (input or output). Rather then using this 
    	class directly, Source or Sink objects should be used.
    """
    def __init__(self,topology,vertex,edge):
        self._topology = typecheck(topology,Topology,"topology")
        self._vertex = typecheck(vertex,Vertex,"vertex")
        self._edge = typecheck(edge,Edge,"edge")
        if (not isinstance(self,FabrikSource)) and (not isinstance(self,FabrikSink)):
            raise Exception("Do not create connections directly! Use Source or Sink")
        self._snap = FabrikSnap(self)

    def release(self):
        """ Removes this connection between a vertex and an edge from the topology.
        This does NOT release either the vertex or the edge objects, it simply
	removes this particular reference to them. 
        """
        logging.debug("... releasing associated snap")
        # Release and remove the reference to your snap
        self._snap._release()
        self._snap = None
        logging.debug("... deleting pointer to vertex and edge")
        # Remove references to vertex and edge
        self._vertex = None
        self._edge = None
	
    @property
    def snap(self):
        return self._snap

    @property
    def edge(self): 
        return self._edge

    @property
    def vertex(self): 
        return self._vertex

    @property
    def block(self):
        return self.vertex.block	

class FabrikSource(FabrikConnection):
    """ A logical connection from a Vertex to an Edge. Graphically represented 
    by a Snap object.
    """
    def __init__(self,topology,vertex,edge):
        super(FabrikSource,self).__init__(topology,vertex,edge)
        # Check to make sure there is not already a source going from this vertex to this edge
        for source in vertex.sources + edge.sources:
            if vertex == source.vertex and edge == source.edge:
                raise Exception("Duplicate FabrkSource!")
        self._topology._sources.append(self)

    def release(self):
        logging.debug("Releasing FabrikSource %r"%self)
        super(FabrikSource,self).release()
        # Remove yourself from the topology
        logging.debug("... removing from topology")
        self._topology._sources.remove(self)
        self._topology = None

class FabrikSink(FabrikConnection):
    """ A logical connection from an Edge to a Vertex. Graphically represented
    by a Snap object. 
    """
    def __init__(self,topology,vertex,edge):
        super(FabrikSink,self).__init__(topology,vertex,edge)
        # Check to make sure there is not already a sink going from this edge to this vertex
        for sink in vertex.sinks + edge.sinks:
            if vertex == sink.vertex and edge == sink.edge:
                raise Exception("Duplicate FabrikSink!")
        print "WUB"
        self._topology._sinks.append(self)

    def release(self):
        logging.debug("Releasing FabrikSink %r"%self)
        super(FabrikSink,self).release()
        # Remove youself from the topology
        logging.debug("... removing from topology")
        self._topology._sinks.remove(self)
        self._topology = None	

class Producer(FabrikSource):
    def __init__(self,fg,node,exchange,routingKeys = None):
        typecheck(fg,FabrikGraph,"fg")
        typecheck(node,Node,"node") 
        typecheck(exchange, Exchange, "exchange")
        super(Producer,self).__init__(fg,node,exchange)
        # Dumb placement
        self.snap.order = max(filter(lambda x: isinstance(x,int), [prod.snap.order for prod in node.producers] + [-1]))+1

        self.bandwidth = None
        self.routingKeys = routingKeys
        log.debug("Adding Producer: " + str(node.name)+" to "+str(exchange.name)+" with routing-keys "+str(routingKeys))

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

class Consumer(FabrikSink):
    def __init__(self,fg,node,exchange, routingKeys = None):
        typecheck(fg,FabrikGraph,"fg")
        typecheck(node,Node,"node")
        typecheck(exchange,Exchange,"topic")
        super(Consumer,self).__init__(fg,node,exchange)

        # Dumb placement
        self.snap.order = max(filter(lambda x: isinstance(x,int), [con.snap.order for con in node.consumers] + [-1]))+1

        self.bandwidth = None
        self.routingKeys = routingKeys
        log.debug("Adding Consumer: " + str(exchange.name)+" to "+str(node.name)+" with routing-keys "+str(routingKeys))

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
    def __init__(self, fg, node_origin, node_dest, routingKeys = None):
        self._topology = typecheck(fg, FabrikGraph, "fg")
        self._origin = typecheck(node_origin, Node, "origin")
        self._dest = typecheck(node_dest, Node, "dest")
        self._flow = Flow(self, routingKeys)
        self._routingKeys = routingKeys
        for feed in node_origin.feeds + node_dest.feeds:
            if (node_origin == feed.origin) and (node_dest == feed.dest) and (routingKeys == feed.routingKeys):
                raise Exception("Duplicate node feed! "+node_origin.name+"->"+node_dest.name+", routing-keys: "+str(routingKeys))
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
    def __init__(self, fg, exchange_origin, exchange_dest, routingKeys = None):
        self._topology = typecheck(fg, FabrikGraph, "fg")
        self._origin = typecheck(exchange_origin, Exchange, "origin")
        self._dest = typecheck(exchange_dest, Exchange, "dest")
        self._hook = Hook(self,routingKeys)
        self._hook_label = self._hook.hooklabel
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
    def __init__(self, transfer, routing_keys = None):
        self._transfer = typecheck(transfer, Transfer, "transfer")
        self._order = None    
        self._routing_keys = routing_keys
    
    def hooklabel(self):
        return hooklabel.gen_hooklabel(self.origin.posBand.altitude, self.dest.posBand.altitude, self.latch.block.index)

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
    def __init__(self, feed, routing_keys = None):
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

