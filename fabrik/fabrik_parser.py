import json
import ConfigParser
import os
import os.path
from fabrik_topology import *

# Parses fabrik .ini.j2 files and returns a FabrikGraph object
#
# Assumed format of Topology sections:
#   publish_foo = {
#       "exchange-spec": { "name": "EXCHANGE_NAME", "durable": "true" },
#   (opt)                { "bindings": [ { "routing-keys": ["ROUTING-KEYS"], 
#   (specifies a step forward)             "bind-tree": { "exchange-spec": { "name": "EXCHANGE-NAME", "durable": "true"}}}]}}
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
#
# TODO:
# - Process the "step out" pieces in each set of options
# - Take in parameters for:
#   * array of silver_products
#   * ec2_id
#   * region
# - Run jinja2 on files before using them
# - x-dead-letter-exchange arguments
# - options for muting certain exchanges (trace, for example)


def get_files(path):
    '''Takes a directory path and returns a list of .ini.j2 files in that directory'''
    files = [ f for f in os.listdir(path) if (os.path.isfile(os.path.join(path,f)) and f.endswith('ini.j2')) ]
    return files

def build_topology(path):
    fabrik = FabrikGraph()
    
    for f in get_files(path):
        try:
            extract_features(path,f, fabrik)
        except Exception as ex:
            print str(ex)

    print fabrik 
    return fabrik

def extract_features(path, filename, fabrik):
    '''extract features from a given file and puts them in the fabrik topology'''
    typecheck(fabrik,FabrikGraph,"fg")
    config = ConfigParser.ConfigParser()
    try:
        config.read(os.path.join(path,filename))
        sub_options = [config.get('Topology', opt) for opt in config.options('Topology') if opt.startswith('subscribe_')]
        pub_options = [config.get('Topology', opt) for opt in config.options('Topology') if opt.startswith('publish_')]
    except:
        print "Invalid file in specified path: "+ filename
        return
#        exit(-1)

    #Add Service Buddies to topology
    service_buddy_name = filename.replace('.ini.j2','')
    sb = ServiceBuddy(fabrik, service_buddy_name)
    print sb.name
    #Add publishing bindings and exchanges
    set_pub_features(pub_options, fabrik, filename, sb)
    set_sub_features(sub_options, fabrik, filename, sb)
    return fabrik

def set_pub_features(pub_options, fabrik, filename, sb):
    '''Pulls out appropriate features from config "options" and adds them to the fabrik topology'''
    for opt in pub_options:
        try:
            pubDict = json.loads(opt)
        except:
            print "Invalid json in file "+filename
            exit(-1)

        try:
            exchangeName = pubDict['exchange-spec'].get(u'name')
        except:
            exchangeName = pubDict['exchange-spec']
        
        exchange = add_exchange(fabrik, exchangeName)
        producer = Producer(fabrik, sb, exchange)

        if 'bindings' in pubDict.keys():
            parse_pub_bindings(fabrik,pubDict['bindings'], exchange)

def add_exchange(fabrik, exchangeName):
    '''Add exchanges and bindings for first step out in publishing (top level exchange-spec)'''
    return add_object_to_fabrik(fabrik, exchangeName, fabrik.exchanges, Exchange)

def add_queue(fabrik, queueName):
    '''Add queues and bindings for first step out in subscribing (top level exchange-spec)'''
    return add_object_to_fabrik(fabrik, queueName, fabrik.queues, Queue)

def add_object_to_fabrik(fabrik, objectName, existingObjects, Object):
    '''Add exchanges and bindings for first step out in publishing (top level exchange-spec)'''
    if objectName not in existingObjects.keys():
        return Object(fabrik,objectName)
    else: 
        return existingObjects[objectName]

def parse_pub_bindings(fabrik, bindings, publishing_exchange):
    '''Add exchanges and bindings for next steps out (recursively parsing bindings)'''
    for b in bindings:
        if 'bindings' in b['bind-tree']:
            routingKeys = b['routing-keys']
            newBindings = b['bind-tree']['bindings']
            try:
                newPubExchangeName = b['bind-tree']['exchange-spec'].get('name')
            except:
                newPubExchangeName = b['bind-tree']['exchange-spec']
            newPEx = add_exchange(fabrik, newPubExchangeName)
            parse_pub_bindings(fabrik, newBindings, newPEx) 
            #TODO: Consumer stuff
        else: #base-case
            exchangeName = b['bind-tree']
            if 'routing-keys' in b:
                routingKeys = b['routing-keys']
            elif 'routing-key' in b:
                routingKeys = b['routing-key']
            exchange = add_exchange(fabrik,exchangeName)
        #TODO: Consumer(fabrik, publishing_exchange, exchange)

def set_sub_features(sub_options, fabrik, filename, sb):
    '''Pulls out necessary features from config options and adds them to the fabrik topology'''
    for opt in sub_options:
        try:
            subDict = json.loads(opt)
        except:
            print "Invalid json in file "+filename
            exit(-1)

        try:
            queueName = subDict['queue-spec'].get(u'name')
        except:
            queueName = subDict['queue-spec']
        queue = add_queue(fabrik, queueName)

#    consumer = Consumer( ) TODO: queue -> sb is not how it works right now!
        if 'bindings' in subDict.keys():
            parse_sub_bindings(fabrik, subDict['bindings'], queue)


def parse_sub_bindings(fabrik, bindings, subscribing_queue):
    '''Add exchanges and bindings for next steps out (recursively parsing bindings)'''
    for b in bindings:
        if 'bindings' in b['bind-tree']:
            routingKeys = b['routing-keys']
            newBindings = b['bind-tree']['bindings']
            try:
                newSubExchangeName = b['bind-tree']['exchange-spec'].get('name')
            except:
                newSubExchangeName = b['bind-tree']['exchange-spec']
            newSubExchange = add_exchange(fabrik, newSubExchangeName)
            parse_sub_bindings(fabrik, newBindings, newSubExchange) 
            #TODO: Consumer stuff
        else: #base-case
            try:
                exchangeName = b['bind-tree']['exchange-spec']['name']
            except:
                exchangeName = b['bind-tree']

            if 'routing-keys' in b:
                routingKeys = b['routing-keys']
            elif 'routing-key' in b:
                routingKeys = b['routing-key']
            exchange = add_exchange(fabrik,exchangeName)
            Consumer(fabrik, subscribing_queue, exchange, routingKeys) 

mypath = '/Users/206790/Projects/fabrik-config-management/provisioning/roles/core/templates/etc/fabrik/' 
filename = 'process.ini.j2'
build_topology(mypath)
