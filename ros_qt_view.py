from view import *
from qt_view import *

class RosView(QGraphicsView, View):
    """ This is a Qt based stand-alone widget that provides a visual rendering 
    of a Topology. It provides a window into a self contained GraphicsScene in
    which we draw the topology. 
    It also implements the View interface as a passthrough to the LayoutManager.
    """
    def __init__(self):
        super(RosView, self).__init__(None)
        View.__init__(self)

        # Qt properties - Enable click-n-drag paning and initialize Scene
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setScene(QGraphicsScene(self))
        
        # Add the LayoutManagerWidget to the scene
        self.layout_manager = LayoutManagerWidget(self)
        self.scene().addItem(self.layout_manager)

        self.resize(1024,768)
        self.show()

    def update_view(self):
        self.layout_manager.link()

    def add_block_item(self, index):
        """ Allows the adapter to create a new BlockItem """
        return self.layout_manager.add_block_item(index)

    def remove_block_item(self, index):
        pass

    def get_block_item(self, index):
        """ Returns a BlockItem with specified index to the the adapter """
        return self.layout_manager.get_block_item(index)

    def add_band_item(self, altitude, rank):
        """ Create a new drawable object to correspond to a Band. """
        return self.layout_manager.add_band_item(altitude, rank)

    def remove_band_item(self, altitude):
        """ Remove the drawable object to correspond to a band """ 
        return self.layout_manager.remove_band_item(altitude)

    def get_band_item(self, altitude):
        """ Returns the BandItem with the given altitude """
        return self.layout_manager.get_band_item(altitude)

    def add_snap_item(self, block_index, container, order):
        return self.layout_manager.add_snap_item(block_index, container, order)

    def remove_snap_item(self, block_index, container, order):
        return self.layout_manager.remove_snap_item(block_index, container, order)

    def get_snap_item(self, block_index, container, order):
        return self.layout_manager.get_snap_item(block_index, container, order)



    def wheelEvent(self,event):
        """ Implements scrollwheel zooming """
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        scaleFactor = 1.15
        if event.delta() > 0:
            self.scale(scaleFactor, scaleFactor)
        else:
            self.scale(1.0/scaleFactor, 1.0/scaleFactor)

