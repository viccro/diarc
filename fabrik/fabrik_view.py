from qt_view import qt_view
from qt_view import SpacerContainer
import logging
import hooklabel
from python_qt_binding.QtGui import QPen, QBrush, QGraphicsView, QGraphicsScene, QGraphicsAnchorLayout
from python_qt_binding.QtGui import QSizePolicy, QColor, QGraphicsWidget
from python_qt_binding.QtCore import Qt
from python_qt_binding.QtCore import pyqtSignal as Signal
import python_qt_binding.QtGui
import sys
from diarc.view import View, ViewItemAttributes
from diarc.util import TypedDict, typecheck

log = logging.getLogger('fabrik.fabrik_view')

class HookItemAttributes(ViewItemAttributes):
    def __init__(self):
        super(HookItemAttributes, self).__init__()
        self._bgcolor = "#ffffff"
        self._border_color = "#ffffff"
        self._label_color = "#000000"

    @property
    def bgcolor(self):
        return QColor(self._bgcolor)

    @bgcolor.setter
    def bgcolor(self, value):
        self._bgcolor = value

    @property
    def border_color(self):
        return QColor(self._border_color)
        
    @border_color.setter
    def border_color(self, value):
        self._border_color = value
            
    @property
    def label_color(self):
        return QColor(self._label_color)

    @label_color.setter
    def label_color(self, value):
        self._label_color = value


'''class FlowItemAttributes(ViewItemAttributes):
    def __init__(self):
        super(FlowItemAttributes, self).__init__()
        self._bgcolor = "#ffffff"
        self._border_color = "#000000"
        self._label_color = "#000000"

    @property
    def bgcolor(self):
        return QColor(self._bgcolor)

    @bgcolor.setter
    def bgcolor(self, value):
        self._bgcolor = value

    @property
    def border_color(self):
        return QColor(self._border_color)
        
    @border_color.setter
    def border_color(self, value):
        self._border_color = value
            
    @property
    def label_color(self):
        return QColor(self._label_color)

    @label_color.setter
    def label_color(self, value):
        self._label_color = value
'''
class HookSpacer(SpacerContainer.SpacerContainer.Spacer):
    def __init__(self,parent):
        super(HookSpacer, self).__init__(parent)
        self._layout_manager = parent.parent
        self._view = parent.parent.view()
        self._adapter = parent.parent.adapter()
        self.dragOver = False

        #Qt Properties
        self.setSizePolicy(QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred))
        self.collapseWidth()
        self.setAcceptDrops(False)
        
    @property
    def bottomBand(self):
        if self.itemA._altitude < self.itemB._altitude:
            return self.itemA
        return self.itemB

    @property
    def topBand(self):
        if self.itemA.altitude < self.itemB.altitude:
            return self.itemB
        return self.itemA

    @property
    def latch(self):
        return self.latch

    def link(self):
        #TODO
        l = self.parent.parent.layout()
        try:
            l.addAnchor(self, Qt.AnchorBottom, self.bottomBand, Qt.AnchorTop)
            print "linked"
        except:
            print "Nope: "+str(self.bottomBand.index)
        l.addAnchor(self, Qt.AnchorTop, self.topBand, Qt.AnchorBottom)
        l.addAnchor(self, Qt.AnchorLeft, self.latch, Qt.AnchorLeft)
        l.addAnchor(self, Qt.AnchorRight, self.latch, Qt.AnchorRight)

    def paint(self, painter, option, widget):
        painter.setPen(Qt.NoPen)
        painter.drawRect(self.rect())

class HookItem(QGraphicsWidget,HookItemAttributes):
    def __init__(self, parent, hook_label):
        super(HookItem, self).__init__(parent)
        HookItemAttributes.__init__(self)
        self._hook_label = hook_label
        self._layout_manager = typecheck(parent, FabrikLayoutManagerWidget, "parent")
        self._view = parent.view()
        self._adapter = parent.adapter()
#        print parent.get_hook_item(hook_label)

        self.originAltitude, self.destAltitude, self.latchIndex = hooklabel.parse_hooklabel(self._hook_label)

        #Deal with the parsed things.
        self.origin_band_item = self._layout_manager.get_band_item(self.originAltitude)
        self.dest_band_item = self._layout_manager.get_band_item(self.destAltitude)
        self._container = self.latch

        #Locational specifications: info about the latch, snap items to the left/right, etc
        #pbands, nbands

        #Qt Properties
        self.setSizePolicy(QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred))
#        self.set_width(20)
        self.setPreferredHeight(20)
        self.setMinimumHeight(20)

    @property
    def itemA(self):
        return self.origin_band_item

    @property
    def itemB(self):
        return self.dest_band_item

    
    def bottomBand(self):
#        print "Bottom Band"
        if self.itemA.altitude < self.itemB.altitude:
            return self.itemA
        return self.itemB

    @property
    def topBand(self):
        if self.itemA.altitude < self.itemB.altitude:
            return self.itemB
        return self.itemA

    @property
    def latch(self):
        return self._layout_manager.get_block_item(self.latchIndex)

    def release(self):
        self.setVisible(False)

    def set_attributes(self, attrs):
        self.setVisible(True)
        self.update(self.rect())
        return

    def link(self):
        #TODO
        l = self._layout_manager
        print dir(self)
        try:
            l.addAnchor(self, Qt.AnchorBottom, self.bottomBand, Qt.AnchorTop)
            print "linked Item"
        except:
            print "Nope: Item: ", self.bottomBand().altitude
        l.addAnchor(self, Qt.AnchorTop, self.topBand, Qt.AnchorBottom)
        l.addAnchor(self, Qt.AnchorLeft, self.latch, Qt.AnchorLeft)
        
        return

    def mousePressEvent(self, event):
        """ Captures the mouse press event for dragging """
        pass

    def mouseReleaseEvent(self, event):
        pass #TODO

    def mouseMoveEvent(self, event):
        pass #TODO

    def paint(self, painter, option, widget):
        #Paint background
        brush = QBrush()
        brush.setStyle(Qt.SolidPattern)
        brush.setColor(self.bgcolor)
        painter.fillRect(self.rect(),brush)
        #Paint border
        border_pen = QPen()
        border_pen.setBrush(self.border_color)
        border_pen.setStyle(Qt.SolidLine)
        border_pen.setWidth(self.border_width)
        painter.setPen(border_pen)
        rect = self.geometry()
        #Label
        painter.setPen(self.label_color)
        painter.rotate(-90)
        fm = painter.fontMetrics()
        elided = fm.elidedText(self.label, Qt.ElideRight, rect.height())
        twidth = fm.width(elided)
        painter.drawText(-twidth-(rect.height()-twidth)/2, rect.width()-2, elided)

'''
class FlowItem(SpacerContainer.SpacerContainer.Item, FlowItemAttributes):
    def __init__(self, parent, flow_label):
        HookItemAttributes.__init__(self)
        #parse_hook_label(hook_label)
        self._flow_label = flow_label
        self._layout_manager = typecheck(parent, FabrikLayoutManagerWidget, "parent")
        self._view = parent.view()
        self._adapter = parent.adapter()

        #Deal with the parsed things.
        #self.origin_node = 
        #self.dest_node = 

        #Locational specifications: info about the spacer items to the left/right, etc

        #Qt Properties
        
        #Create a linkage

    def release(self):
        return

    def set_attributes(self, attrs):
        return

    def link(self):
        return

    def mousePressEvent(self, event):
        """ Captures the mouse press event for dragging """
        pass

    def mouseReleaseEvent(self, event):
        pass #TODO

    def mouseMoveEvent(self, event):
        pass #TODO

    def paint(self, painter, option, widget):
        return
        #Paint background
        brush = QBrush()
        brush.setStyle(Qt.SolidPattern)
        brush.setColor(self.bgcolor)
        painter.fillRect(self.rect(),brush)
        #Paint border
        border_pen = QPen()
        border_pen.setBrush(self.border_color)
        border_pen.setStyle(Qt.SolidLine)
        border_pen.setWidth(self.border_width)
        painter.setPen(border_pen)
        rect = self.geometry()
        #Label
        painter.setPen(self.label_color)
        painter.rotate(-90)
        fm = painter.fontMetrics()
        elided = fm.elidedText(self.label, Qt.ElideRight, rect.height())
        twidth = fm.width(elided)
        painter.drawText(-twidth-(rect.height()-twidth)/2, rect.width()-2, elided)

    def itemA(self):
        pass #TODO

    def itemB(self):
        pass #TODO
'''
class FabrikView(QGraphicsView, View):
    """ This is a Qt based stand-alone widget that provides a visual rendering 
    of a Topology. It provides a window into a self contained GraphicsScene in
    which we draw the topology. 
    It also implements the View interface as a passthrough to the LayoutManager.
    """
    # Qt Signals. The following signals correspond to diarc.View() API calls that
    # are called from outside the main qt thread. Rather then call the implementations
    # defined in layout_manager directly, we call them from these signals so that
    # the call happens from the correct thread.
    __update_view_signal = Signal()

    __add_block_item_signal = Signal(int)
    __remove_block_item_signal = Signal(int)
    __set_block_item_settings_signal = Signal(int, object, object)
    __set_block_item_attributes_signal = Signal(int, qt_view.BlockItemAttributes)

    __add_band_item_signal = Signal(int, int)
    __remove_band_item_signal = Signal(int)
    __set_band_item_settings_signal = Signal(int, int, object, object, str, str)
    __set_band_item_attributes_signal = Signal(int, qt_view.BandItemAttributes)

    __add_snap_item_signal = Signal(str)
    __remove_snap_item_signal = Signal(str)
    __set_snap_item_settings_signal = Signal(str, object, object, object, object)
    __set_snap_item_attributes_signal = Signal(str, qt_view.SnapItemAttributes)
    
    __add_hook_item_signal = Signal(str)
    __remove_hook_item_signal = Signal(str)
    __set_hook_item_settings_signal = Signal(str)
    __set_hook_item_attributes_signal = Signal(str, HookItemAttributes)
    '''
    __add_flow_item_signal = Signal(str)
    __remove_flow_item_signal = Signal(str)
    __set_flow_item_settings_signal = Signal(str)
    __set_flow_item_attributes_signal = Signal(str, FlowItemAttributes)
    '''
    def __init__(self):
        super(FabrikView, self).__init__(None)
        View.__init__(self)

        # Qt properties - Enable click-n-drag paning and initialize Scene
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setScene(QGraphicsScene(self))

        # Enable for debuging
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        
        # Add the LayoutManagerWidget to the scene
        self.layout_manager = FabrikLayoutManagerWidget(self)
        self.scene().addItem(self.layout_manager)

        # Hook up the signals and slots
        self.__update_view_signal.connect(self.layout_manager.link)

        self.__add_block_item_signal.connect(self.layout_manager.add_block_item)
        self.__remove_block_item_signal.connect(self.layout_manager.remove_block_item)
        self.__set_block_item_settings_signal.connect(self.layout_manager.set_block_item_settings)
        self.__set_block_item_attributes_signal.connect(self.layout_manager.set_block_item_attributes)

        self.__add_band_item_signal.connect(self.layout_manager.add_band_item)
        self.__remove_band_item_signal.connect(self.layout_manager.remove_band_item)
        self.__set_band_item_settings_signal.connect(self.layout_manager.set_band_item_settings)
        self.__set_band_item_attributes_signal.connect(self.layout_manager.set_band_item_attributes)

        self.__add_snap_item_signal.connect(self.layout_manager.add_snap_item)
        self.__remove_snap_item_signal.connect(self.layout_manager.remove_snap_item)
        self.__set_snap_item_settings_signal.connect(self.layout_manager.set_snap_item_settings)
        self.__set_snap_item_attributes_signal.connect(self.layout_manager.set_snap_item_attributes)
        
        self.__add_hook_item_signal.connect(self.layout_manager.add_hook_item)
        self.__remove_hook_item_signal.connect(self.layout_manager.remove_hook_item)
        self.__set_hook_item_settings_signal.connect(self.layout_manager.set_hook_item_settings)
        self.__set_hook_item_attributes_signal.connect(self.layout_manager.set_hook_item_attributes)
        '''
        self.__add_flow_item_signal.connect(self.layout_manager.add_flow_item)
        self.__remove_flow_item_signal.connect(self.layout_manager.remove_flow_item)
        self.__set_flow_item_settings_signal.connect(self.layout_manager.set_flow_item_settings)
        self.__set_flow_item_attributes_signal.connect(self.layout_manager.set_flow_item_attributes)
        '''
        self.resize(1024,768)
        self.show()

    def update_view(self):
        self.__update_view_signal.emit()

    def add_block_item(self, index):
        """ Allows the adapter to create a new BlockItem """
        self.__add_block_item_signal.emit(index)

    def has_block_item(self, index):
        return self.layout_manager.has_block_item(index)

    def remove_block_item(self, index):
        self.__remove_block_item_signal.emit(index)

    def set_block_item_settings(self, index, left_index, right_index):
        return self.__set_block_item_settings_signal.emit(index, left_index, right_index)

    def set_block_item_attributes(self, index, attributes):
        self.__set_block_item_attributes_signal.emit(index, attributes)

    def add_band_item(self, altitude, rank):
        """ Create a new drawable object to correspond to a Band. """
        self.__add_band_item_signal.emit(altitude, rank)

    def has_band_item(self, altitude):
        return self.layout_manager.has_band_item(altitude)

    def remove_band_item(self, altitude):
        """ Remove the drawable object to correspond to a band """ 
        self.__remove_band_item_signal.emit(altitude)

    def set_band_item_settings(self, altitude, rank, top_band_alt, bot_band_alt,
                                leftmost_snapkey, rightmost_snapkey):
        self.__set_band_item_settings_signal.emit(altitude, rank, top_band_alt, bot_band_alt, leftmost_snapkey, rightmost_snapkey)

    def set_band_item_attributes(self, altitude, attributes):
        self.__set_band_item_attributes_signal.emit(altitude, attributes)

    def add_snap_item(self, snapkey):
        self.__add_snap_item_signal.emit(snapkey)

    def has_snap_item(self, snapkey):
        return self.layout_manager.has_snap_item(snapkey)

    def remove_snap_item(self, snapkey): 
        self.__remove_snap_item_signal.emit(snapkey)

    def set_snap_item_settings(self, snapkey, left_order, right_order, pos_band_alt, neg_band_alt):
        self.__set_snap_item_settings_signal.emit(snapkey, left_order, right_order, pos_band_alt, neg_band_alt)

    def set_snap_item_attributes(self, snapkey, attributes):
        self.__set_snap_item_attributes_signal.emit(snapkey, attributes)
    
    def add_hook_item(self, hook_label):
        self.__add_hook_item_signal.emit(hook_label)

    def has_hook_item(self, hook_label):
        return self.layout_manager.has_hook_item(hook_label)

    def remove_hook_item(self, hook_label): 
        self.__remove_hook_item_signal.emit(hook_label)

    def set_hook_item_settings(self, hook_label):
        self.__set_hook_item_settings_signal.emit(hook_label) #TODO - what settings?

    def set_hook_item_attributes(self, hook_label, attributes):
        self.__set_hook_item_attributes_signal.emit(hook_label, attributes)
    '''
    def add_flow_item(self, flow_label):
        self.__add_flow_item_signal.emit(flow_label)

    def has_flow_item(self, flow_label):
        return self.layout_manager.has_flow_item(flow_label)

    def remove_flow_item(self, flow_label): 
        self.__remove_flow_item_signal.emit(flow_label)

    def set_flow_item_settings(self, flow_label):
        self.__set_flow_item_settings_signal.emit(flow_label) #TODO - what settings?

    def set_flow_item_attributes(self, flow_label, attributes):
        self.__set_flow_item_attributes_signal.emit(flow_label, attributes)
    '''
    def wheelEvent(self,event):
        """ Implements scrollwheel zooming """
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        scaleFactor = 1.15
        if event.delta() > 0:
            self.scale(scaleFactor, scaleFactor)
        else:
            self.scale(1.0/scaleFactor, 1.0/scaleFactor)

class FabrikBlockItem(qt_view.BlockItem):
    def __init__(self, parent, block_index):
        super(FabrikBlockItem, self).__init__(parent, block_index)

    def paint(self,painter,option,widget):
        """Overwrites BlockItem.paint so that we can fill in the block rectangles"""
        brush = QBrush()
        brush.setStyle(Qt.SolidPattern)
        brush.setColor(self.bgcolor)
        painter.fillRect(self.rect(),brush)
        border_pen = QPen()
        border_pen.setBrush(self.border_color)
        border_pen.setStyle(Qt.SolidLine)
        border_pen.setWidth(self.border_width)
        painter.setPen(border_pen)
        painter.drawRect(self.rect())

class FabrikBandItem(qt_view.BandItem):
    def __init__(self, parent, altitude, rank):
        super(FabrikBandItem, self).__init__(parent, altitude, rank)

    def link(self):
        sys.stdout.flush()
        # Assign the vertical anchors
        super(qt_view.BandItem,self).link()
        # Assign the horizontal Anchors
        l = self.parent.layout()
        l.addAnchor(self, Qt.AnchorLeft, self._layout_manager.block_container, Qt.AnchorLeft) #TODO: return to left_most_snap after hooks work
        l.addAnchor(self, Qt.AnchorRight, self._layout_manager.block_container, Qt.AnchorRight)

class FabrikLayoutManagerWidget(qt_view.LayoutManagerWidget):
    def __init__(self, view):
        super(FabrikLayoutManagerWidget, self).__init__(view)
        self._hook_items = TypedDict(str,HookItem)    # altitude    #TypedList(BandItem)
       # self._flow_items = TypedDict(str,FlowItem)  # snapkey  #TypedList(SnapItem)
        log.debug("Initialized Fabrik Layout Manager")

    def add_block_item(self, index):
        log.debug("... Adding FabrikBlockItem %d"%index)
        """create a new FabrikBlockItem"""
        if index in self._block_items:
            raise qt_view.DuplicateItemExistsError("Block Item with index %d already exists"%(index))
        item = FabrikBlockItem(self, index)
        self._block_items[index] = item
        return item

    def add_band_item(self, altitude, rank):
        """ Create a new drawable object to correspond to a Band. """
        log.debug("... Adding FabrikBandItem with altitude %d"%altitude)
        if altitude in self._band_items:
            raise DuplicateItemExistsError("BandItem with altitude %d already exists"%(altitude))
        item = FabrikBandItem(self, altitude, rank)
        self._band_items[altitude] = item
        return item

    def set_band_item_settings(self, altitude, rank,
                               top_band_alt, bot_band_alt,
                               leftmost_snapkey, rightmost_snapkey):
        item = self._band_items[altitude]
        item.rank = rank
        item.top_band = self._band_items[top_band_alt] if top_band_alt is not None else None
        item.bot_band = self._band_items[bot_band_alt] if bot_band_alt is not None else None
        if leftmost_snapkey == '':
            item.left_most_snap = self.bandStack
        else:
            item.left_most_snap = self._snap_items[str(leftmost_snapkey)]
        if rightmost_snapkey == '':
            item.right_most_snap = self.bandStack
        else:
            item.right_most_snap = self._snap_items[str(rightmost_snapkey)]

    def add_hook_item(self, hook_label):
        #hook_label gets passed in as a QString, since it goes across a signal/slot interface
        hook_label = str(hook_label)
        log.debug("... Adding FabrikHookItem %s"%hook_label)
        if hook_label in self._hook_items:
            raise DuplicateItemExistsError("HookItem with hook_label %s already exists"%(hook_label))
        item = HookItem(self, hook_label)
        self._hook_items[hook_label] = item
        return item

    def remove_hook_item(self, hook_label):
        #hook_label gets passed in as a QString, since it goes across a signal/slot interface
        hook_label = str(hook_label)
        log.debug("... Removing HookItem %s"%hook_label)
        self._hook_items[hook_label].release() #TODO
        self._hook_items.pop(hook_label) 

    def set_hook_item_settings(self, hook_label):
        #hook_label gets passed in as a QString, since it goes across a signal/slot interface
        hook_label = str(hook_label)
        #TODO: what settings?
        return

    def set_hook_item_attributes(self, hook_label, attributes):
        #hook_label gets passed in as a QString, since it goes across a signal/slot interface
        hook_label = str(hook_label)
        self._hook_items[hook_label].set_attributes(attributes)

    def has_hook_item(self, hook_label):
        return True if hook_label in self._hook_items else False

    def get_hook_item(self, hook_label):
        #hook_label gets passed in as a QString, since it goes across a signal/slot interface
        hook_label = str(hook_label)
        return self._hook_items[hook_label]
    '''
    def add_flow_item(self, flow_label):
        #flow_label gets passed in as a QString, since it goes across a signal/slot interface
        flow_label = str(flow_label)
        log.debug("... Adding FabrikFlowItem %s"%flow_label)
        if flow_label in self._flow_items:
            raise DuplicateItemExistsError("FlowItem with flow_label %s already exists"%(flow_label))
        item = FlowItem(self, flow_label)
        self._flow_items[flow_label] = item
        return item

    def remove_flow_item(self, flow_label):
        #flow_label gets passed in as a QString, since it goes across a signal/slot interface
        flow_label = str(flow_label)
        log.debug("... Removing FlowItem %s"%flow_label)
        self._flow_items[flow_label].release() #TODO
        self._flow_items.pop(flow_label) 

    def set_flow_item_settings(self, flow_label):
        #flow_label gets passed in as a QString, since it goes across a signal/slot interface
        flow_label = str(flow_label)
        #TODO: what settings?

    def set_flow_item_attributes(self, flow_label, attributes):
        #flow_label gets passed in as a QString, since it goes across a signal/slot interface
        flow_label = str(flow_label)
        self._flow_items[flow_label].set_attributes(attributes)

    def has_flow_item(self, flow_label):
        return True if flow_label in self._flow_items else False


    def get_flow_item(self, flow_label):
        #flow_label gets passed in as a QString, since it goes across a signal/slot interface
        flow_label = str(flow_label)
        return self._flow_items[flow_label]
    '''

    def link(self):
        log.debug("*** Begining Linking ***")
        sys.stdout.flush()
        # Create a new anchored layout. Until I can figure out how to remove
        # objects from the layout, I need to make a new one each time
        l = QGraphicsAnchorLayout()
        l.setSpacing(0.0)
        self.setLayout(l)

        # Anchor BandStack to Layout, and BlockContainer to BandStack
        self.layout().addAnchor(self.block_container, Qt.AnchorTop, self.layout(), Qt.AnchorTop)
        self.layout().addAnchor(self.block_container, Qt.AnchorLeft, self.layout(), Qt.AnchorLeft)
        self.layout().addAnchor(self.bandStack, Qt.AnchorLeft, self.block_container, Qt.AnchorLeft)
        self.layout().addAnchor(self.bandStack, Qt.AnchorRight, self.block_container, Qt.AnchorRight)

        # Link block items
        for item in self._block_items.values():
            item.link()

        # Link band items
        for item in self._band_items.values():
            item.link()

        # Link Snap Items
        for item in self._snap_items.values():
            item.link()

        # Link Hook Items
        for item in self._hook_items.values():
            item.link()

        log.debug("*** Finished Linking ***\n")
        sys.stdout.flush()

class DuplicateItemExistsError(Exception):
    pass

app = python_qt_binding.QtGui.QApplication(sys.argv)
view = FabrikView()
