from PyQt4.QtCore import *
from PyQt4.QtGui import *
from util import *
import sys


class SpacerContainer(QGraphicsWidget):
    """ A SpacerContainer is a specialized widget for creating artifical
    spacing between other widgets "inside" it. These spaces consist of Spacer
    objects, which are usually drawn blank to give the same effect as margins.
    Items and spacers occur in a linear arrangement, but the direction is unspecified.
    The items and spacers are intended to be linked together using an AnchoredLayout,
    as part of a two level layout process. The first level is called 'linking',
    in which we actually reassign new AnchoredLayout properties to objects that
    are defined to be beside each other. The second level is for the layout mechanism
    to perform the acutal layout, with items being children of the SpacerContainer's 
    parent object and Spacers being children of the SpacerContainer itself. 
    Spacer objects can be used as targets for drag and drop operations.
    This code is a generalization of repeated code used in qtview.

    
    +--------+          +---------+          +--------+
    | Item A | Spacer A | Current | Spacer B | Item B |
    +--------+          +---------+          +--------+

    +--------+        +--------+
    | Item A | Spacer | Item B |
    +--------+        +--------+
    """
    def __init__(self,parent):
        super(SpacerContainer,self).__init__(parent=parent)
        # Parent needs to be of type "DrawingBoard" to make sure that 
#         self.parent = typecheck(parent,DrawingBoard,"parent")
        self.parent = parent
        self._spacers = list()
        # We need to know what specific type of spacer we are using, since
        # all new spacers are instantiated inside getSpacerA or getSpacerB. 
        self._spacerType = None #SpacerContainer.Spacer

    def getSpacerA(self,item):
        """ Return the current spacer, or create a new one, in the direction of 
        the current item's 'itemA'. This is used by SpacerContainer.Item objects
        during the linking process.
        """
        # Determine if the item is currently being used
        isUsed = item.isUsed()
        # Find spacers where item is itemB (making this spacer A)
        ret = filter(lambda x: x.itemB == item, self._spacers)
        # Delete old unused spacers. Remove them from the QLayout system so 
        # they don't try to draw anymore and from our list of spacers so we
        # don't try to search it anymore.
        for spacer in ret:
            if (not spacer.itemA == item.itemA()) or (not isUsed):
                spacer.setParent(None)
                self._spacers.remove(spacer)
        ret = filter(lambda x: x.itemB == item, self._spacers)
        # Once we have deleted old spacers, make sure we are using the band.
        # If we are not, don't return anything (just None)
        if not isUsed:
            return None
        # Return existing spacer if only one exists. There should not be extras
        if len(ret) == 1 and ret[0].itemA == item.itemA():
            return ret[0]
        elif len(ret) >= 1:
            raise Exception("To many spacers found %d"%len(ret))
        # No existing spacers fit - create a new spacer in direction A
        spacer = self.spacerType(self)
        spacer.itemB = item
        spacer.itemA = item.itemA()
        self._spacers.append(spacer)
        return spacer

    def getSpacerB(self,item):
        """ Finds the spacer for an item in direction b """
        # Determine if the item is currently being used
        isUsed = item.isUsed()
        # Find spacers where item is itemA (making this spacer B)
        ret = filter(lambda x: x.itemA == item, self._spacers)
        # Delete old unused spacers. Remove them from the QLayout system so 
        # they don't try to draw anymore and from our list of spacers so we
        # don't try to search it anymore.
        for spacer in ret:
            if (not spacer.itemB == item.itemB()) or (not isUsed):
                spacer.setParent(None)
                self._spacers.remove(spacer)
        # TODO: This next line may not be needed
        ret = filter(lambda x: x.itemA == item, self._spacers)
        # Once we have deleted old spacers, make sure we are using the band.
        # If we are not, don't return anything (just None)
        if not isUsed:
            return None
        # Return existing spacer if only one exists. There should not be extras
        if len(ret) == 1 and ret[0].itemB == item.itemB():
            return ret[0]
        elif len(ret) >= 1:
            raise Exception("To many spacers found %d"%len(ret))
        # No existing spacers fit - create a new spacer in direction B
        spacer = self.spacerType(self)
        spacer.itemA = item
        spacer.itemB = item.itemB()
        self._spacers.append(spacer)
        return spacer

    def _get_spacerType(self):
        if isinstance(self._spacerType,types.NoneType):
            raise Exception("you must set the spacerType for the SpacerContainer %r"%type(self)) 
        return self._spacerType
    def _set_spacerType(self,spacerType):
#         self._spacerType = typecheck(spacerType,SpacerContainer.Spacer,"spacerType")
        self._spacerType = spacerType
    spacerType = property(_get_spacerType,_set_spacerType)



    class Spacer(QGraphicsWidget):
        """ A Spacer between two items. 
        Spacers are automatically created and removed by the SpacerContainer to
        seperate adjacent Items. You must create your own Spacer object that 
        implements the link() method to define how the spacers connect to the
        Items on either side of it. The implementation may also contain hooks
        for receiving drag and drop events. 
        """
        def __init__(self,parent):
            self.parent = typecheck(parent,SpacerContainer,"parent")
            self.parent = parent
            super(SpacerContainer.Spacer,self).__init__(parent=parent)
            self.itemA = None
            self.itemB = None

        def layout(self):
            """ Returns the QGraphicsLayout that is being used. """
            return self.parent.parent.layout()

        def link(self):
            """ Must be implemented by the subclass. This method should consist
            of self.layout().addAnchor(self, ..., self.itemA/B, ...) calls anchoring
            the sides of itemA and itemB to this spacer. 
            """
            raise Exception("You must implement the linking to the spacersA and B")


    class Item(QGraphicsWidget):
        """ An Item with spacers around it. """
        def __init__(self,parent,container):
#             self.parent = typecheck(parent,DrawingBoard,"parent")
            self.parent = parent
            self.container = typecheck(container,SpacerContainer,"container")
            super(SpacerContainer.Item,self).__init__(parent=parent)

        def itemA(self):
            raise Exception("You must implement a way to return itemA")

        def itemB(self):
            raise Exception("You must implement a way to return itemB")

        def isUsed(self):
            """ return if the item is currently being used or not - determines
            if the item will be visible or not 
            """
            raise Exception("You must implement a way to return if the item is used")

        def link(self):
            """ This method manages the spacer objects linked on either side of 
            the item. When the spacers link() method is called, the anchored
            layout will hook into the object.
            """
            l = self.parent.layout()
            # Calculate Spacers A and B - deleteing old spacers to this item
            # when necessary, reusing existing spacers if possible, and otherwise
            # creating new spacers
            spacerA = self.container.getSpacerA(self)
            spacerB = self.container.getSpacerB(self)
            if isinstance(spacerA,types.NoneType) or isinstance(spacerB,types.NoneType):
                self.setVisible(False)
                return
            self.setVisible(True)
            spacerA.link()
            spacerB.link()



