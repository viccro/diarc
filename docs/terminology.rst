What is diarc?
==============

Diarc is short for di-graph arcgraph.
It is a python package used for describing and drawing a multiple-input, multiple-output, directional graph as a modified arcgraph.
Diarc provides some built-in tools, as well as an API that can be used to extend its functionality. 

Terminology
===========

Drawing the diagram is done by giving three different kinds of descriptions of the graph: connections, layout, and graphics.
Connection descriptions provide the topology of the graph using Logical Objects.
Layout describes where pieces of the graph should be drawn with respect to other pieces of the graph using Relative Objects.
Together, Logical and Relative Objects are paired to form a Diarc Topology - a data structure which provides a 1-1 mapping that specifies an exact diagram to be drawn.
Additionally, by changing only Relative Objects, a single graph can be redrawn many different ways. 
Finally, Visual Objects created using a graphical toolkit are created to mirror the properties of Relative Objects and draw the graph to the screen.



Logical (Connection) Objects
----------------------------

Logical objects are used to define the graph, without specifying how it should be drawn. 
They are defined in diarc.topology and fabrik.fabrik_topology


.. _Vertex: 

Vertex_
 A vertex in the graph, connected to other vertices through edges.

.. _Edge:

Edge_
 A directional edge in the graph. Edges have inputs (sources) and outputs (sinks).

.. _Connection:

Connection_
 Links a single vertex to a single edge in a single direction (either a source_ or a sink_). 
 A vertex can have many connections, but is limited to a max of two per edge (one Source and one Sink). 
 An edge can have an unlimited number of connections.

.. _Source:

Source_
 A Connection_ between a vertex_ and an edge_ that designates the edge as leaving the vertex.

.. _Sink:

Sink_
 A Connection_ between a vertex_ and an edge_ that designates the edge as entering the vertex.

.. _Transfer:

Transfer_
 A Transfer allows for connections to be made from one edge_ to another without going through a vertex_.

.. _Feed:

Feed_
 A feed allows for connections to be made linking one vertex_ to another without passing through an edge_.

Relative (Layout) Objects
-------------------------

 Relative objects are used to define how a graph is laid out. 
 These objects are usually created automatically along with Logical Objects, but are not assigned the values that specify their positioning.
 Defined in diarc.topology and fabrik.fabrik_topology

.. _Block: 

Block_
 Corresponds to a Vertex in a 1-1 relationship. 
 Blocks are drawn in a single horizontal line across the middle of the graph.
 The order in which blocks are drawn is determined by their index number - a unique integer value that must be greater or equal to zero. 
 Blocks are drawn in order of increasing index value from left to right.

.. _Node:

Node_
 Subclass of a block_, which is used in the Fabrik specific layout.
 Nodes are split into three types: Queues, Service Buddies, and Latches. Queues and Service Buddies are directly related to objects in the topology configuration files of Fabrik. Latches correspond to Hooks in a 1-1 relationship, and serve to allocate horizontal space for the HookItem to be drawn. The latch BlockItem will not be drawn on the diagram, but will serve as a space holder.
 Queues which are origins for a flow are sorted automatically to immediately precede the SB which is the destination. Because of this, moving a queue horizontally by dragging has limited application, and will drag the entire cluster of nodes which are interconnected by flow.

.. _Band:

Band_
 Correspond to an Edge. 
 This is represented by a line arcing between Snaps inside Blocks. 
 These lines are drawn above and/or below the line of blocks, depending on the direction of the edge. 
 Bands drawn above the blocks are called "positive bands" and represent and edge traveling from from left to right. 
 In other words, the edge's sources are to the left of the edge's sinks. Bands drawn below the blocks are called "negative bands" and represent edges with sources to the right of the sinks. 
 An Edge_ will always have two Bands (one positive and one negative).
 Each Band_ is drawn such that the arc reaches a certain distance away from the line of blocks.
 This distance is called the Band's altitude, and is represented by a non-zero unique integer.
 Positive bands have positive altitudes, while negative bands have negative altitudes.
 Since bands can overlap each other, they need also need to specify the order in which they are layered.
 This is done using a bands rank, a positive integer value that must be unique among bands on the same side of the Blocks.

.. _FabrikBand:

FabrikBand_
 Subclass of a Band_, which is used in the Fabrik specific layout. Instead of an edge_ having both a positive and a negative band_ , an edge_ will only have one (positive altitude) FabrikBand_. 

.. _Snap: 

Snap_
 Corresponds to a Connection_ in a 1-1 relationship.
 Snaps are split into two groups, Emitters (for Sources) and Collectors (for Sinks).
 Snaps are drawn inside their Vertex's Block, with Emitters on the left and Collectors on the right.
 Within these groups, the order of the snaps is determined by the snaps 'order', a positive integer that must be unique among its groups.
 A snaps absolute location is denoted by a combination of the block it resides in, whether it is in the collectors or emitters, and its order value.
 This is designated by a unique identifier called a snapkey, denoted as <blockindex><[E]mitter|[C]ollector><snaporder>.
 For example, the second snap from the left in the collector of block with index 5 is denoted as "5c2".
 
.. _Hook:

Hook_
 Corresponds to a Transfer_ in a 1-1 relationship; used in the Fabrik specific layout. 
 Hooks each have their own Latch node, which serves as a space holder for them in the horizontal layout. They can be moved horizontally by dragging their latch block side to side.
 Hooks are drawn in the band section, as a vertical bar which connects two bands (an origin and a destination band). 
 A hook is referred to by a unique identifier called a hooklabel, denoted as <origin_band_altitude>_<dest_band_altitude>_<latch_index>.
 They take the color and rank (z-value on the page) of their origin band.
 
.. _Flow:

Flow_
 Corresponds to a Feed_ in a 1-1 relationship; used in the Fabrik specific layout.
 Flows control grouping of node ordering (see Node_ for more information), and are drawn as a gray box that connects origin nodes to destination nodes.
 A flow is referred to by a unique identifier called a flowlabel, denoted as <origin_node_index, dest_node_index>.
 Flow clusters can be dragged to move them, and the queues within a flow's cluster can be rearranged. However, the gray flow box itself is fixed between its nodes.


Visual (Graphical) Objects
--------------------------

Visual Objects are often specified using a graphical library such as Qt. 
They specify everything from color and size to actual positioning on the screen. 
Defined in diarc.view and fabrik.fabrik_view

.. _BlockItem:

BlockItem_
 Corresponds to a single Block_ (and Vertex_).

.. _FabrikBlockItem:

FabrikBlockItem_
 Subclass of BlockItem, corresponding to a single Node_ (and Vertex_).
 Used in Fabrik diagrams.

.. _BandItem:

BandItem_
 Corresponds to a single Band_ (and Edge_).

.. _FabrikBandItem:

FabrikBandItem_
 Subclass of BandItem, corresponding to a single Band_ (and Edge_).
 Used in Fabrik diagrams.

.. _SnapItem:

SnapItem_
 Corresponds to a single Snap_ (and Connection_).

.. _FabrikSnapItem:

FabrikSnapItem_
 Subclass of SnapItem, corresponding to a single Snap_ (and Connection_).
 Used in Fabrik diagrams.

.. _HookItem:

HookItem_
 Corresponds to a single Hook_ (and Transfer_).
 Used in Fabrik diagrams.

.. _FlowItem:

FlowItem_
 Corresponds to a single Flow_ (and Feed_).
 Used in Fabrik diagrams.
