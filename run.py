#!/usr/bin/env python
# Usage:
# ./run.py topology_plot data/v5.xml

import sys
sys.dont_write_bytecode = True
import inspect
import logging
import argparse

def asciiview(args=None):
    '''Creates a standard diarc topology and displays it in ascii'''
    from diarc import parser
    from ascii_view import ascii_view
    from diarc import base_adapter
    topology = parser.parseFile(args[0])
    view = ascii_view.AsciiView()
    adapter = base_adapter.BaseAdapter(topology, view)
    adapter._update_view()

def qtview(args=None):
    '''Creates a standard diarc topology and displays it in QT'''
    try:
        import python_qt_binding.QtGui
    except Exception as exception:
        print "Error: python_qt_binding not installed."
        print "Please install using `sudo pip install python_qt_binding`"
        print str(exception)
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
    '''Creates a ROS specific graph and displays it in QT'''
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
    '''Creates a Fabrik specific graph and displays it in QT'''
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
        topology = fabrik_parser.build_topology_from_directory(args.path)
        app = python_qt_binding.QtGui.QApplication([])
        view = fabrik_view.FabrikView(args.filename)
        adapter = fabrik_adapter.FabrikAdapter(topology, view)
        adapter.flow_arrangement_enforcer()
        adapter._update_view()
        view.activateWindow()
        view.raise_()
        sys.exit(app.exec_())

def rabbitview(args=None):
    try:
        import python_qt_binding.QtGui
    except:
        print "Error: python_qt_binding not installed."
        print "Please install using `sudo pip install python_qt_binding`"
        exit(-1)
    from fabrik import fabrik_view, fabrik_adapter, fabrik_parser
    if args.url and args.user and args.pw and args.filename:
        topology = fabrik_parser.build_topology_from_api(args.url, args.user, args.pw)
        app = python_qt_binding.QtGui.QApplication([])
        view = fabrik_view.FabrikView(args.filename)
        adapter = fabrik_adapter.FabrikAdapter(topology, view)
        adapter.flow_arrangement_enforcer()
        adapter._update_view()
        view.activateWindow()
        view.raise_()
        sys.exit(app.exec_())
    else:
        print "rabbitview requires a url, username, password, and filename for saving the image.\n"
        print "Run run.py -h for more information on syntax"



if __name__ == "__main__":
    available_views = dict(inspect.getmembers(sys.modules[__name__], inspect.isfunction))

    logging.basicConfig(level=logging.DEBUG)
    log = logging.getLogger('main')

    arg_parser = argparse.ArgumentParser()

    viewNameHelp = "Views available:" + str(available_views.keys())
    arg_parser.add_argument('viewName', help=viewNameHelp)

    pathHelp = "path to the directory containing .ini.j2 configuration files"
    arg_parser.add_argument('--path', help=pathHelp)

    fileHelp = "name of the file where the png of the diagram will be saved"
    arg_parser.add_argument('--filename', help=fileHelp)

    urlHelp = "url for base api directory in RabbitMQ (ie 'http://localhost:8083/api/')"
    arg_parser.add_argument('--url', help=urlHelp)

    userHelp = "username for RabbitMQ api"
    arg_parser.add_argument('--user', help=userHelp)

    pwHelp = "password for RabbitMQ api"
    arg_parser.add_argument('--pw', help=pwHelp)

    '''
    ec2Help = "ec2 id"
    parser.add_argument('--ec2_id', help=ec2Help)

    regionHelp = "region name"
    parser.add_argument('--region', help=regionHelp)

    silverHelp = "Array of silver products"
    parser.add_argument('--silver_products', help=silverHelp)
    '''
    args = arg_parser.parse_args()
    available_views[args.viewName](args)
