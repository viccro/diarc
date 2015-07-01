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
# Renaming Looks like this
#   Vertex  = Node {Queue, Service, Shovel}
#   Edge    = Exchange
#   Sink    = Consumer
#   Source  = Producer
#
from diarc.topology import *

class FabrikGraph(Topology):
    def __init__(self):
        super(FabrikGraph,self).__init__()

    @property
    def nodes(self):
        return dict([(v.name,v) for v in self.vertices])

    @property
    def exchanges(self):
        return dict(filter(lambda x: None not in x, [(topic.name,topic) for topic in self.edges]))

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
#        self.pid = None
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
        
class ServiceBuddy(Node):
    def __init__(self,fg,name=None):
        typecheck(fg,FabrikGraph,"fg")
        super(ServiceBuddy,self).__init__(fg)
        self.nodeType = "sb"
        self.name = name
        print "Adding ServiceBuddy " + str(name)

class Wormhole(Node):
    def __init__(self,fg,name=None):
        typecheck(fg,FabrikGraph,"fg")
        super(Wormhole,self).__init__(fg)
        self.nodeType = "wh"
        


class Exchange(Edge):
    def __init__(self,fg,name=None):
        typecheck(fg,FabrikGraph,"fg")
        super(Exchange,self).__init__(fg)
        
        # Dumb placement - just get the enxt free altitudes
        self.posBand.altitude,self.negBand.altitude = fg.nextFreeAltitudes()
        self.posBand.rank = self.posBand.altitude
        self.negBand.rank = self.posBand.altitude

        self.name = name
        print "Adding Exchange " + str(name)

    @property
    def producers(self):
        # NOTE: See note on Node class about why this MUST be a property.
        return self.sources

    @property
    def consumers(self):
        # NOTE: See note on Node class about why this MUST be a property.
        return self.sinks




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

    @property
    def topic(self):
        # NOTE: See note on Node class about why this MUST be a property.
        return self.edge

    @property
    def node(self):
        # NOTE: See note on Node class about why this MUST be a property.
        return self.vertex


