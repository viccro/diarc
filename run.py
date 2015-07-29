#!/usr/bin/env python
# Usage:
# ./run.py topology_plot data/v5.xml

import sys
sys.dont_write_bytecode = True
import inspect
import logging
import argparse

def asciiview(args=None):
    from diarc import parser
    from ascii_view import ascii_view
    from diarc import base_adapter
    topology = parser.parseFile(args[0])
    view = ascii_view.AsciiView()
    adapter = base_adapter.BaseAdapter(topology, view)
    adapter._update_view()

def qtview(args=None):
    try:
        import python_qt_binding.QtGui
    except Exception as e:
        print "Error: python_qt_binding not installed."
        print "Please install using `sudo pip install python_qt_binding`"
        print str(e)
        exit(-1)
    from diarc import parser
    from qt_view import qt_view
    from diarc import base_adapter
    topology = parser.parseFile(args[0])
    app = python_qt_binding.QtGui.QApplication(sys.argv)
    view = qt_view.QtView()
    adapter = base_adapter.BaseAdapter(topology, view)
    adapter._update_view()
    view.activateWindow()
    view.raise_()
    sys.exit(app.exec_())

def rosview(args=None):
    try:
        import python_qt_binding.QtGui
    except:
        print "Error: python_qt_binding not installed."
        print "Please install using `sudo pip install python_qt_binding`"
        exit(-1)
    import qt_view
    import ros.ros_adapter
    app = python_qt_binding.QtGui.QApplication([])
    view = qt_view.QtView()
    adapter = ros.ros_adapter.RosAdapter(view)
    adapter.update_model()
    view.activateWindow()
    view.raise_()
    sys.exit(app.exec_())

def fabrikview(args=None):
    try:
        import python_qt_binding.QtGui
    except:
        print "Error: python_qt_binding not installed."
        print "Please install using `sudo pip install python_qt_binding`"
        exit(-1)
    from fabrik import fabrik_view
    from fabrik import fabrik_adapter
    from fabrik import fabrik_parser
    if args.path and args.filename:
        topology = fabrik_parser.build_topology(args.path)
        app = python_qt_binding.QtGui.QApplication([])
        view = fabrik_view.FabrikView(args.filename)
        adapter = fabrik_adapter.FabrikAdapter(topology, view)
        adapter.flow_arrangement_enforcer()
        adapter._update_view()
        view.activateWindow()
        view.raise_()
        sys.exit(app.exec_())

if __name__=="__main__":
    available_views = dict(inspect.getmembers(sys.modules[__name__],inspect.isfunction))
    
    logging.basicConfig(level=logging.DEBUG)
    log = logging.getLogger('main')

    parser = argparse.ArgumentParser()

    viewNameHelp = "Views available:" + str(available_views.keys())
    parser.add_argument('viewName', help=viewNameHelp)

    pathHelp = "path to the directory containing .ini.j2 configuration files"
    parser.add_argument('--path', help=pathHelp)

    fileHelp = "name of the file where the png of the diagram will be saved"
    parser.add_argument('--filename', help = fileHelp)
    '''
    ec2Help = "ec2 id"
    parser.add_argument('--ec2_id', help=ec2Help)
    
    regionHelp = "region name"
    parser.add_argument('--region', help=regionHelp)

    silverHelp = "Array of silver products"
    parser.add_argument('--silver_products', help=silverHelp)
    '''
    args = parser.parse_args()
    
#    try:
    available_views[args.viewName](args)
    #except Exception as e:
        #print e
        #print "'./run.py -h' for help"
