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

""" hooklabels are abbreviations that can be used to identify a hook. Hooks do
    not have a single unique attribute, which makes them difficult to identify.
    hooklabels solve that problem.

    Hooklabels have 3 parts:
        origin band altitude
        destination band altitude
        latch index

    Example:
        hooklabel 1_2_3 means the hook from the band at altitude 1 to altitude 2,
        and its latch is at index 3.
"""
import re
def parse_hooklabel(hooklabel):
    """ Parses a snapkey into a 3-tuple """
    result = re.findall("(^-?\d+)(_)(-?\d+)(_)(\d+$)", hooklabel)
    if len(result) == 0:
        raise Exception("Invalid hooklabel %s"%hooklabel)
    return (int(result[0][0]), int(result[0][2]), int(result[0][4]))

def gen_hooklabel(origin_alt, destination_alt, latch_index):
    """ generate a snapkey """
    return "%d_%d_%d"%(origin_alt, destination_alt, latch_index)
