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
        else:
            attrs.bgcolor = "gray"
            attrs.border_color = "black"
            attrs.label_color = "black"
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
