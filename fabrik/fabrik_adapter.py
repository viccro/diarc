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

log = logging.getLogger('diarc.base_adapter')

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
            attrs.border_color = "blue"
            attrs.label_color = "blue"
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
        return attrs

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

        # Update the SnapItem cache list
#         self._cached_snap_item_snapkeys = snaps.keys()

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
        log.debug("bands")
        sys.stdout.flush()
        # Compute top and bottom bands, rank, leftmost, and rightmost snaps
        for altitude in bands:
            band = bands[altitude]
            top_alt = band.topBand.altitude if band.topBand else None
            bot_alt = band.bottomBand.altitude if band.bottomBand else None
            emitters = band.emitters
            collectors = band.collectors
            #TODO hooks = band.hooks
            emitters.sort(lambda x,y: x.block.index - y.block.index)
            collectors.sort(lambda x,y: x.block.index - y.block.index)
            
            left_snap = None
            right_snap = None
            # Skip bands that don't have an item 
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
            self._view.set_band_item_settings(altitude, band.rank, top_alt, bot_alt, left_snapkey, right_snapkey )

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
