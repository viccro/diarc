from qt_view import qt_view
import logging
from python_qt_binding.QtGui import QPen, QBrush, QGraphicsView, QGraphicsScene
from python_qt_binding.QtCore import Qt
from python_qt_binding.QtCore import pyqtSignal as Signal
import python_qt_binding.QtGui
import sys
from diarc.view import View


log = logging.getLogger('fabrik.fabrik_view')

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

class FabrikLayoutManagerWidget(qt_view.LayoutManagerWidget):
    def __init__(self, view):
        super(FabrikLayoutManagerWidget, self).__init__(view)
        log.debug("Initialized Fabrik Layout Manager")

    def add_block_item(self, index):
        log.debug("... Adding FabrikBlockItem %d"%index)
        """create a new FabrikBlockItem"""
        if index in self._block_items:
            raise qt_view.DuplicateItemExistsError("Block Item with index %d already exists"%(index))
        item = FabrikBlockItem(self, index)
        self._block_items[index] = item
        return item

#app = python_qt_binding.QtGui.QApplication(sys.argv)
#view = FabrikView()
