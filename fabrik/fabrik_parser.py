import json
import ConfigParser
import os
import os.path
#import xml.etree.ElementTree as ET
#import xml.dom.minidom
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

    #Add publishing bindings and exchanges
    set_pub_features(pub_options, fabrik, filename, sb)
    #TODO: set_sub_features(sub_options, fabrik)

def set_pub_features(pub_options, fabrik, filename, sb):
    '''Pulls out appropriate features from config "options" and adds them to the fabrik topology'''
    for opt in pub_options:
        try:
            pubDict = json.loads(opt)
        except:
            print "Invalid json in file "+filename
            exit(-1)

    #Add exchanges and bindings for first step out in publishing (top level exchange-spec)
        try:
            exchangeName = pubDict['exchange-spec'].get(u'name')
            if exchangeName not in fabrik.exchanges.keys():
                exchange = Exchange(fabrik,pubDict['exchange-spec'].get(u'name'))
            else: 
                exchange = fabrik.exchanges[exchangeName]
            producer = Producer(fabrik, sb, exchange)
        except:
            exchange = Exchange(fabrik, pubDict['exchange-spec'])
            producer = Producer(fabrik, sb, exchange)
    
    #Add exchanges and bindings for next steps out (recursively parsing bindings)
#TODO:        parse_bindings()

def parse_bindings(bindings):
    print bindings

mypath = '/Users/206790/Projects/fabrik-config-management/provisioning/roles/core/templates/etc/fabrik/' 
filename = 'process.ini.j2'
build_topology(mypath)
