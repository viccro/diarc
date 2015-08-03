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

""" flowlabels are abbreviations that can be used to identify a flow. Flows do
    not have a single unique attribute, which makes them difficult to identify.
    flows solve that problem.

    flowlabels have 2 parts:
        origin node index
        destination node index

    Example:
        flowlabel 1_2 means the flow from the node at index 1 to the node at index 2
"""
import re
def parse_flowlabel(flowlabel):
    """ Parses a flowlabel into a tuple """
    result = re.findall("(^\d+)(_)(\d+$)", flowlabel)
    if len(result) == 0:
        raise Exception("Invalid flowlabel %s"%flowlabel)
    return (int(result[0][0]), int(result[0][2]))

def gen_flowlabel(origin_index, destination_index):
    """ generate a flowlabel """
    return "%d_%d"%(origin_index, destination_index)
