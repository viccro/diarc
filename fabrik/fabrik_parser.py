'''
Parser containing everything needed to parse FOO.ini.j2 files and create a FabrikGraph object.
Parser can also build a FabrikGraph based on current RabbitMQ APIs, though these only have
    queues, exchanges, and bindings (no services of any sort)
'''
import json
import ConfigParser
import os
import os.path
from diarc.util import typecheck
from fabrik_topology import FabrikGraph, ServiceBuddy, Queue, Exchange, Producer
from fabrik_topology import Consumer, Transfer, Feed
import logging
# Parses fabrik .ini.j2 files and returns a FabrikGraph object
#
# Assumed format of Topology sections:
#   publish_foo = {
#       "exchange-spec": { "name": "EXCHANGE_NAME", "durable": "true" },
#   (opt)                { "bindings": [ { "routing-keys": ["ROUTING-KEYS"],
#   (specifies a step forward)             "bind-tree": {
#                               "exchange-spec": { "name": "EXCHANGE-NAME", "durable": "true"}}}]}}
#
#   subscribe_foo = {
#       "queue-spec": "QUEUE_NAME",
#       "bindings": [ { "routing-keys": ["ROUTING-KEYS"],
#   (one step out)      "bind-tree": "EXCHANGE-NAME"}]}
#
#       OR
#
#   subscribe_foo = {
#       "queue_spec": { "name": "QUEUE_NAME", "arguments": {"x-dead-letter-exchange": "reject"}}
#       "bindings": ...

log = logging.getLogger('fabrik.fabrik_parser')

def get_files(path):
    '''Takes a directory path and returns a list of .ini.j2 files in that directory'''
    files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)) and \
                                            f.endswith('ini.j2')]
    return files

def build_topology_from_directory(path):
    '''Create a fabrik graph out of all files in the 'path' directory'''
    fabrik = FabrikGraph()

    for f in get_files(path):
        try:
            extract_features(path, f, fabrik)
        except Exception as ex:
            log.debug(str(ex))

    return fabrik

def extract_features(path, filename, fabrik):
    '''extract features from a given file and puts them in the fabrik topology'''
    typecheck(fabrik, FabrikGraph, "fg")
    config = ConfigParser.ConfigParser()
    try:
        config.read(os.path.join(path, filename))
        sub_options = [config.get('Topology', opt) for opt in config.options('Topology') \
                                                        if opt.startswith('subscribe_')]
        pub_options = [config.get('Topology', opt) for opt in config.options('Topology') \
                                                        if opt.startswith('publish_')]
    except:
        log.debug("Invalid file in specified path: "+ filename)
        return

    #Add Service Buddies to topology
    service_buddy_name = filename.replace('.ini.j2', '')
    service_buddy = ServiceBuddy(fabrik, service_buddy_name)
    #Add publishing bindings and exchanges
    set_pub_features(pub_options, fabrik, filename, service_buddy)
    set_sub_features(sub_options, fabrik, filename, service_buddy)
    return fabrik

def add_exchange(fabrik, exchangeName):
    '''Add exchanges and bindings for first step out in publishing (top level exchange-spec)'''
    return add_object_to_fabrik(fabrik, exchangeName, fabrik.exchanges, Exchange)

def add_queue(fabrik, queueName):
    '''Add queues and bindings for first step out in subscribing (top level exchange-spec)'''
    return add_object_to_fabrik(fabrik, queueName, fabrik.queues, Queue)

def add_object_to_fabrik(fabrik, objectName, existingObjects, Object):
    '''Checks whether object already exists in fabrik, to avoid duplications'''
    if objectName not in existingObjects.keys():
        return Object(fabrik, objectName)
    else:
        return existingObjects[objectName]

def add_transfer(fabrik, publishing_exchange, exchange, routingKeys):
    '''Add a transfer to the fabrik graph'''
    for transfer in fabrik.transfers:
        if (transfer.origin == publishing_exchange) and (transfer.dest == exchange) and \
            (transfer.routingKeys == routingKeys):
            return

    interExchTransfer = Transfer(fabrik, publishing_exchange, exchange, routingKeys)
    log.debug("Adding Transfer from "+interExchTransfer.origin.name+" to "+\
            interExchTransfer.dest.name+" with routing-keys"+str(routingKeys))

def add_feed(fabrik, origin_node, dest_node, routingKeys=None):
    '''Add a feed to the fabrik graph'''
    for feed in fabrik.feeds:
        if (feed.origin == origin_node) and (feed.dest == dest_node):
            return
    node_to_node = Feed(fabrik, origin_node, dest_node, routingKeys)
    log.debug("Adding Feed from "+node_to_node.origin.name+" to "+node_to_node.dest.name +\
                " with routing-keys "+str(routingKeys))

def set_pub_features(pub_options, fabrik, filename, service_buddy):
    '''Pulls out appropriate features from config "options" and adds them to the fabrik topology'''
    for opt in pub_options:
        try:
            pubDict = json.loads(opt)
        except:
            log.debug("Invalid json in file "+filename)
            return
        try:
            exchangeName = pubDict['exchange-spec'].get(u'name')
        except:
            exchangeName = pubDict['exchange-spec']
 
        exchange = add_exchange(fabrik, exchangeName)
        Producer(fabrik, service_buddy, exchange)

        if 'bindings' in pubDict.keys():
            parse_pub_bindings(fabrik, pubDict['bindings'], exchange)

def parse_pub_bindings(fabrik, bindings, publishing_exchange):
    '''Add exchanges and bindings for next steps out (recursively parsing bindings)'''
    for binding in bindings:
        if 'bindings' in binding['bind-tree']:
            routingKeys = binding['routing-keys']
            newBindings = binding['bind-tree']['bindings']
            try:
                newPubExchangeName = binding['bind-tree']['exchange-spec'].get('name')
            except:
                newPubExchangeName = binding['bind-tree']['exchange-spec']
            new_pub_ex = add_exchange(fabrik, newPubExchangeName)
            parse_pub_bindings(fabrik, newBindings, new_pub_ex)
            add_transfer(fabrik, publishing_exchange, new_pub_ex, routingKeys)
        else: #base-case
            exchangeName = binding['bind-tree']
            if 'routing-keys' in binding:
                routingKeys = binding['routing-keys']
            elif 'routing-key' in binding:
                routingKeys = binding['routing-key']
            exchange = add_exchange(fabrik, exchangeName)
            add_transfer(fabrik, publishing_exchange, exchange, routingKeys)

def set_sub_features(sub_options, fabrik, filename, sb):
    '''Pulls out necessary features from config options and adds them to the fabrik topology'''
    for opt in sub_options:
        routingKeys = None
        try:
            subDict = json.loads(opt)
        except:
            log.debug("Invalid json in file "+filename)
            exit(-1)

        try:
            queueName = subDict['queue-spec'].get(u'name')
        except:
            queueName = subDict['queue-spec']
        queue = add_queue(fabrik, queueName)
        if 'bindings' in subDict.keys():
            routingKeys = subDict['bindings'][0].get(u'routing-keys')
            parse_sub_bindings(fabrik, subDict['bindings'], queue)
        add_feed(fabrik, queue, sb, routingKeys)


def parse_sub_bindings(fabrik, bindings, subscribing_queue):
    '''Add exchanges and bindings for next steps out (recursively parsing bindings)'''
    for binding in bindings:
        if 'bindings' in binding['bind-tree']:
            routingKeys = binding['routing-keys']
            newBindings = binding['bind-tree']['bindings']
            try:
                newSubExchangeName = binding['bind-tree']['exchange-spec'].get('name')
            except:
                newSubExchangeName = binding['bind-tree']['exchange-spec']
            newSubExchange = add_exchange(fabrik, newSubExchangeName)
            Consumer(fabrik, subscribing_queue, newSubExchangeName, routingKeys)
            parse_sub_bindings(fabrik, newBindings, newSubExchange)
        else: #base-case
            try:
                exchangeName = binding['bind-tree']['exchange-spec']['name']
            except:
                exchangeName = binding['bind-tree']

            if 'routing-keys' in binding:
                routingKeys = binding['routing-keys']
            elif 'routing-key' in binding:
                routingKeys = binding['routing-key']
            exchange = add_exchange(fabrik, exchangeName)
            Consumer(fabrik, subscribing_queue, exchange, routingKeys)

