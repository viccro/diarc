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

from diarc.view import View
from diarc.view import BlockItemAttributes
from diarc.view import BandItemAttributes
from diarc.view import SnapItemAttributes
from diarc.base_adapter import BaseAdapter
from fabrik_topology import *
import sys
import logging
import argparse
import random

log = logging.getLogger('fabrik.fabrik_adapter')

class FabrikAdapter(BaseAdapter):
    """Implements a Fabrik specific version of the adapter.
    Contains no qt code"""
    def __init__(self, model, view):
        super(FabrikAdapter, self).__init__(model, view)

        # These are caching lists so I can remember what I had last time I drew.
        # That way, if something becomes outdated, I have a thing to compare against.
        # These lists are updated at the end of _update_view()
        self._cached_block_item_indexes = list()
        self._cached_band_item_altitudes = list()
        self._cached_snap_item_snapkeys = list()
        self._cached_hook_item_labels = list()
        self._cached_flow_item_labels = list()

        self._color_mapper = ColorMapper()

    def get_block_item_attributes(self, block_index):
        """ Default method for providing some stock settings for blocks """
        block = self._topology.blocks[block_index]
        attrs = BlockItemAttributes()
        if block._vertex.nodeType == 'sb':
            attrs.bgcolor = "blue"
            attrs.border_color = "black"
            attrs.label_color = "white"
        elif block._vertex.nodeType == 'queue':
            attrs.bgcolor = "red"
            attrs.border_color = "black"
            attrs.label_color = "black"
        elif block._vertex.nodeType == 'wh':
            attrs.bgcolor = "gray"
            attrs.border_color = "black"
            attrs.label_color = "black"
        else:
            attrs.bgcolor = "white"
            attrs.border_color = "white"
            attrs.label_color = "white"
        attrs.border_width = 1
        attrs.label = str(block._vertex.name)
        attrs.spacerwidth = 20
        return attrs

    def get_band_item_attributes(self, band_altitude):
        """ Default method for providing some stock settings for bands """
        band = self._topology.bands[band_altitude]
        attrs = BandItemAttributes()
        attrs.bgcolor = self._color_mapper.get_unique_color(band._edge.name)
        attrs.border_color = "black"
        attrs.label = str(band._edge.name)
        attrs.label_color = "black"
        attrs.width = 15
        return attrs

    def get_snap_item_attributes(self, snapkey):
        """ Default method for providing some stock settings for snaps """
        snap = self._topology.snaps[snapkey]
        attrs = SnapItemAttributes()
        if snap._connection.node.nodeType == "queue":
            attrs.bgcolor = "red"
            attrs.label_color = "black"
        elif snap._connection.node.nodeType == 'sb':
            attrs.bgcolor = "blue"
            attrs.label_color = "white"
        else:
            attrs.bgcolor = "gray"
            attrs.label_color = "black"
        attrs.border_color = "black"
        attrs.border_width = 0
        attrs.label = str(snap._connection.routingKeys)
        attrs.width = 20
        return attrs

    def get_hook_item_attributes(self, hooklabel):
        """Default method for providing some stock settings for hooks"""
        hook = self._topology.hooks[hooklabel]
        attrs = BandItemAttributes()
        attrs.bgcolor = "black"
        attrs.border_color = "green"
        attrs.label = str(hook._routing_keys)
        return attrs

    def get_flow_item_attributes(self, flowlabel):
        """Default method for providing some stock settings for flows"""
        flow = self._topology.flows[flowlabel]
        attrs = BandItemAttributes()
        attrs.bgcolor = "black"
        attrs.border_color = "green"
        attrs.label = str(flow._routing_keys)
        attrs
        return attrs

    def move_block(self, originalIdx, destinationIdx):
        if originalIdx < destinationIdx:
            self.reorder_blocks_no_update(originalIdx, destinationIdx, destinationIdx+1)
        else:
            self.reorder_blocks_no_update(originalIdx, destinationIdx - 1, destinationIdx)

    def reorder_blocks_no_update(self,srcIdx,lowerIdx,upperIdx):
        """ reorders the index values of blocks and triggers the view to redraw.
        This also requires updating the corresponding block_items.
        """ 
        blocks = self._topology.blocks

        lastIdx = None
        currIdx = srcIdx
        # If we are moving to the right, lowerIdx is the target index.
        # Clear the dragged block's index, then shift all effected block
        # indices left.
        # NOTE: See issue #12
        if lowerIdx is not None and lowerIdx > srcIdx:
            while isinstance(currIdx,int) and currIdx < (upperIdx or lowerIdx+1): # In case upperIdx is None, use lower+1
                nextIdx = blocks[currIdx].rightBlock.index if blocks[currIdx].rightBlock else None
                blocks[currIdx].index = lastIdx
                lastIdx = currIdx
                currIdx = nextIdx
            assert lastIdx == lowerIdx, "%r %r"%(lastIdx,upperIdx)

        # If we are moving to the left, upperIdx is the target index.
        # Clear the dragged blocks index, then shift all effected blocks right
        elif upperIdx is not None and upperIdx < srcIdx:
            while isinstance(currIdx,int) and currIdx > lowerIdx:
                nextIdx = blocks[currIdx].leftBlock.index if blocks[currIdx].leftBlock else None
                blocks[currIdx].index = lastIdx
                lastIdx = currIdx
                currIdx = nextIdx
            assert lastIdx == upperIdx, "%r %r"%(lastIdx,upperIdx)

        # Otherwise we are just dragging to the side a bit and nothing is 
        # really moving anywhere. Return immediately to avoid trying to give
        # the block a new index and unnecessary extra linking actions.
        else:
            return False
        # Finally give the moved object its desired destination. Then make 
        # the TopologyWidget relink all the objects again.
        blocks[srcIdx].index = lastIdx
        return True

    def flow_arrangement_enforcer(self):
        """Forces an acceptable order of blocks to permit drawing of flows"""
        blocks = self._topology.blocks
        log.debug("Enforcing Flow Arrangement")

        maxBlockIdx = max([x for x in blocks])
        currentIdx = 0
        while currentIdx < maxBlockIdx:
            offsetIdx = 0
            #is the current block a destination? 
            if not blocks[currentIdx].isFlowDest:
                #if it's not an origin, keep going.
                if not blocks[currentIdx].isFlowOrigin:
                    pass
                #If it *is* an origin, what is its destination?
                else:
                    destIdx = map(lambda x: x.dest.block.index, blocks[currentIdx].flowsGoingOut)
                    if len(destIdx) > 1:
                        pass
                        #TODO
                    else:
                        destBlock = blocks[destIdx[0]]
                        flowsGoingInToDestBlock = destBlock.flowsComingIn
                        originsOfFlowsGoingInToDestBlock = map(lambda f: f.origin.block, flowsGoingInToDestBlock)
                        for o in originsOfFlowsGoingInToDestBlock:
                            #Don't move the one we're sitting on (or ones we've already processed)!
                            if o.index > (currentIdx+offsetIdx):
                                #Move each origin of the flows going into the dest block in front of it...
                                offsetIdx += 1
                                self.move_block(o.index, currentIdx+offsetIdx)
                        #Double check that your dest block hasn't moved:
                        offsetIdx += 1
                        self.move_block(destBlock.index, currentIdx+offsetIdx)
            #If it *is* a destination, shunt it to the end and keep going.
            else:
                self.move_block(currentIdx, maxBlockIdx)
                currentIdx -= 1
            #Refresh current block indices
            blocks = self._topology.blocks
            currentIdx += (offsetIdx + 1)
        log.debug("Finished Enforcing Flow Arrangement")
        blocks = self._topology.blocks

    def reorder_blocks(self,srcIdx,lowerIdx,upperIdx):
        if self.reorder_blocks_no_update(srcIdx, lowerIdx, upperIdx):
            self.flow_arrangement_enforcer()
            self._update_view()

    def _update_view(self):
        """ updates the view - compute each items neigbors and then calls linking. """

        # Determine what items are in the model
        blocks = self._topology.blocks
        bands = self._topology.bands
        snaps = self._topology.snaps
        hooks = self._topology.hooks
        flows = self._topology.flows

        # Delete outdated BlockItems still in the view but no longer in the topology
        old_block_item_indexes = list(set(self._cached_block_item_indexes) - set(blocks.keys()))
        for index in old_block_item_indexes:
            self._view.remove_block_item(index)
            self._cached_block_item_indexes.remove(index)

        # Add new BlockItems for blocks in model that are not in view
        for index in blocks:
            if not self._view.has_block_item(index):
                self._view.add_block_item(index)
                self._cached_block_item_indexes.append(index)

        # Update the BlockItem cache list
#         self._cached_block_item_indexes = blocks.keys()



        # Delete outdated BandItems still in the view but not in the topology
        old_band_item_altitudes = list(set(self._cached_band_item_altitudes) - set(bands.keys()))
        for altitude in old_band_item_altitudes:
            self._view.remove_band_item(altitude)
            self._cached_band_item_altitudes.remove(altitude)

        # Delete BandItems that exist, but are not being used, and add BandItems
        # that are being used, but are not yet in the view
        for altitude in bands:
            band = bands[altitude]
            isUsed = True #TODO band.isUsed()
            if isUsed and not self._view.has_band_item(altitude):
                self._view.add_band_item(altitude,band.rank)
                self._cached_band_item_altitudes.append(altitude)
            elif not isUsed and self._view.has_band_item(altitude):
                self._view.remove_band_item(altitude)
                self._cached_band_item_altitudes.remove(altitude)

        # Update the BandItem cache list
#         self._cached_band_item_altitudes = bands.keys()

        # Delete outdated SnapItems still in the view but no longer in the topology
        old_snap_item_snapkeys = list(set(self._cached_snap_item_snapkeys) - set(snaps.keys()))
        for snapkey in old_snap_item_snapkeys:
            self._view.remove_snap_item(snapkey)
            self._cached_snap_item_snapkeys.remove(snapkey)

        # Delete SnapItems that exist, but are not being used, and add SnapItems
        # that are being used, but are not yet in the view
        for snapkey in snaps:
            snap = snaps[snapkey]
            isUsed = snap.isUsed()
            if isUsed and not self._view.has_snap_item(snapkey):
                self._view.add_snap_item(snapkey)
                self._cached_snap_item_snapkeys.append(snapkey)
            elif not isUsed and self._view.has_snap_item(snapkey):
                self._view.remove_snap_item(snapkey)
                self._cached_snap_item_snapkeys.remove(snapkey)
       
        # Delete outdated SnapItems still in the view but no longer in the topology
        old_hook_item_labels = list(set(self._cached_hook_item_labels) - set(hooks.keys()))
        for hooklabel in old_hook_item_labels:
            self._view.remove_hook_item(hooklabel)
            self._cached_hook_item_labels.remove(hooklabel)

        # Delete HookItems that exist, but are not being used, and add HookItems
        # that are being used, but are not yet in the view
        for hooklabel in hooks:
            hook = hooks[hooklabel]
            isUsed = hook.isUsed()
            if isUsed and not self._view.has_hook_item(hooklabel):
                self._view.add_hook_item(hooklabel)
                self._cached_hook_item_labels.append(hooklabel)
            elif not isUsed and self._view.has_hook_item(hooklabel):
                self._view.remove_hook_item(hooklabel)
                self._cached_hook_item_labels.remove(hooklabel)

        # Delete outdated FlowItems still in teh view but no longer in teh topology
        old_flow_item_labels = list(set(self._cached_flow_item_labels) - set(flows.keys()))
        for flowlabel in old_flow_item_labels:
            self._view.remove_flow_item(flowlabel)
            self._cached_flow_item_labels.remove(flowlabel)

        # Delete FlowItems that exist, but are not being used, and add FlowItems
        # that are being used, but are not yet in the view
        for flowlabel in flows:
            flow = flows[flowlabel]
            isUsed = flow.isUsed()
            if isUsed and not self._view.has_flow_item(flowlabel):
                self._view.add_flow_item(flowlabel)
                self._cached_flow_item_labels.append(flowlabel)
            elif not isUsed and self._view.has_flow_item(flowlabel):
                self._view.remove_flow_item(flowlabel)
                self._cached_flow_item_labels.remove(flowlabel)
                        




        log.debug("*** Computing neighbors ***")
        sys.stdout.flush()
        log.debug("Blocks and snaps")
        sys.stdout.flush()
        # Compute left and right blocks
        for index in blocks:
            block = blocks[index]
            left_index = block.leftBlock.index if block.leftBlock is not None else None
            right_index = block.rightBlock.index if block.rightBlock is not None else None
            self._view.set_block_item_settings(index, left_index, right_index)
            # Compute left and right snaps, and what bands are being touched
            emitter = blocks[index].emitter
            collector = blocks[index].collector
            for snap in emitter.values() + collector.values():
                order = snap.order
                containername = "emitter" if snap.isSource() else "collector"
                # TODO: This assertion check should be commented out eventually
                if not snap.isUsed():
                    items = [item for item in self._view.layout_manager._snap_items if item.snap_order == order]
                    items = [item for item in items if item.container.strType() == containername]
                    items_orders = [item.snap_order for item in items if item.block_index == snap.block.index]
                    assert(order not in items_orders)
                    continue
                left_order = snap.leftSnap.order if snap.leftSnap is not None else None
                right_order = snap.rightSnap.order if snap.rightSnap is not None else None
                pos_alt = snap.posBandLink.altitude if snap.posBandLink else None
                neg_alt = snap.negBandLink.altitude if snap.negBandLink else None
                self._view.set_snap_item_settings(snap.snapkey(), left_order, right_order, pos_alt, neg_alt)
        log.debug("Bands")
        sys.stdout.flush()
        # Compute top and bottom bands, rank, leftmost, and rightmost snaps
        for altitude in bands:
            band = bands[altitude]
            top_alt = band.topBand.altitude if band.topBand else None
            bot_alt = band.bottomBand.altitude if band.bottomBand else None
            emitters = band.emitters
            collectors = band.collectors
            emitters.sort(lambda x,y: x.block.index - y.block.index)
            collectors.sort(lambda x,y: x.block.index - y.block.index)

            left_snap = None
            right_snap = None
            try:
                if band.isPositive:
                    left_snap = emitters[0]
                    right_snap = collectors[-1]
                else:
                    left_snap = collectors[0]
                    right_snap = emitters[-1]
            except:
                pass
            left_snapkey = left_snap.snapkey() if left_snap is not None else None
            right_snapkey = right_snap.snapkey() if right_snap is not None else None

            #Also compute leftmost and rightmost hooks:
            _hooks = band.hooks
            left_hook_latch = None
            right_hook_latch = None
            
            latches = {h.latch.block.index: h.hooklabel() for h in _hooks.values()}  

            if latches:
                left_hook_latch = min(sorted(latches))
                right_hook_latch = max(sorted(latches))
    
                left_hook_label = latches[left_hook_latch] if left_hook_latch is not None else None
                right_hook_label = latches[right_hook_latch] if right_hook_latch is not None else None
    
                left_hook = hooks[left_hook_label]
                right_hook = hooks[left_hook_label]
                #Figure out which object is furthest left/right (hook or snap):
            if left_snap is not None:
                if left_hook_latch is not None:     #Both snaps and latches
                    left_snap_index = left_snap.block.index
                    left_hook_index = left_hook_latch
                    right_snap_index = right_snap.block.index
                    right_hook_index = right_hook_latch
    
                    left_most_item = left_snapkey if (left_snap_index < left_hook_index) else left_hook_label
                    right_most_item = right_snapkey if (right_snap_index > right_hook_index) else right_hook_label
                else: #Snaps but no latches        
                    left_most_item = left_snapkey
                    right_most_item = right_snapkey
            else: 
                if left_hook_latch is not None:     #latches but not snaps
                    left_most_item = left_hook_label
                    right_most_item = right_hook_label
                else: #Neither
                    left_most_item = None
                    right_most_item = None

            self._view.set_band_item_settings(altitude, band.rank, top_alt, bot_alt, left_most_item, right_most_item )

        #Don't need hook neighbor information, because they're 1:1 with latch-blocks
        #Flow information will be linked in with block sorting

        log.debug("*** Finished Computing neighbors ***")
        log.debug("*** Assigning Attributes ***")

        # Update block visual attribtutes
        for index in self._cached_block_item_indexes:
            attributes = self.get_block_item_attributes(index)
            self._view.set_block_item_attributes(index,attributes)

        # Update band visual attributes
        for altitude in self._cached_band_item_altitudes:
            attributes = self.get_band_item_attributes(altitude)
            self._view.set_band_item_attributes(altitude, attributes)

        # Update snap visual attribtutes
        for snapkey in self._cached_snap_item_snapkeys:
            attributes = self.get_snap_item_attributes(snapkey)
            self._view.set_snap_item_attributes(snapkey, attributes)

        # Update hook visual attributes
        for hooklabel in hooks:
            attributes = self.get_hook_item_attributes(hooklabel)
            self._view.set_hook_item_attributes(hooklabel, attributes)

        # Update flow visual attributes
        for flowlabel in flows:
            attributes = self.get_flow_item_attributes(flowlabel)
            self._view.set_flow_item_attributes(flowlabel, attributes)

        

        log.debug("*** Finished Assigning Attributes ***")
        self._view.update_view()


class ColorMapper(object):
    def __init__(self):
        self._choices = list()
        # Reds
        self._choices.extend(["IndianRed", "DarkSalmon", "Crimson"])
        # Pinks
        self._choices.extend(["HotPink", "DeepPink"])
        # Oranges
        self._choices.extend(["Coral", "OrangeRed", "DarkOrange"])
        # Yellows
        self._choices.extend(["Gold", "DarkKhaki"])
        # Purples
        self._choices.extend(["Thistle", "Orchid", "MediumPurple", "DarkOrchid", "Purple", "Indigo", "DarkSlateBlue"])
        # Greens
        self._choices.extend(["LawnGreen", "LimeGreen", "MediumSeaGreen", "ForestGreen", "OliveDrab", "Olive", "DarkOliveGreen", "DarkCyan"])
        # Blues
        self._choices.extend(["PaleTurquoise", "Turquoise", "CadetBlue", "SteelBlue", "DodgerBlue"])
        # Browns
        #         self._choices.extend(["Cornsilk","Tan","RosyBrown","SandyBrown","Goldenrod","DarkGoldenrod","SaddleBrown"])
        self._used_colors = dict()

    def get_unique_color(self, name):
        if name not in self._used_colors:
            if len(self._choices) > 0:
                self._used_colors[name] = random.choice(self._choices)
                self._choices.remove(self._used_colors[name])
            else:
                self._used_colors[name] = "Gray"
        return self._used_colors[name]
        
    def release_unique_color(self, name):
        if name in self._used_colors:
            if not self._used_colors[name] == "Gray":
                self._choices.append(self._used_colors[name])
                self._used_colors.pop(name)
        else:
            rospy.logwarn("Unknown name mapped to color!")
