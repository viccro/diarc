# from PySide.QtCore import *
# from PySide.QtGui import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import sys



class MyBlock(QGraphicsWidget):
    """ Visual Block, with right hand spacer """
    def __init__(self,parent,block):
        super(MyBlock,self).__init__(parent=parent)
        self.parent = parent
        self.block = block
        self.block.visual = self
        self.setContentsMargins(5,5,5,5)
        self.rightSpacer = MyBlock.Spacer(self)

        # We want to have a little space above and below the Emitter/Collector,
        # Set up top and bottom margin to give that space. 
        self._topMargin = MyBlockHorizontalSpacer(self)
        self._botMargin = MyBlockHorizontalSpacer(self)
        # TODO: Set up left and right margins as well

        # Set up Emitter and Collector Containers. They will sit inside the 
        # block margins
        self.myEmitter = MyEmitter(self)
        self.myCollector = MyCollector(self)

    def link(self):
        l = self.parent.layout()
        l.addAnchor(self,Qt.AnchorTop, self._topMargin, Qt.AnchorTop)
        l.addAnchor(self,Qt.AnchorLeft, self._topMargin, Qt.AnchorLeft)
        l.addAnchor(self,Qt.AnchorRight, self._topMargin, Qt.AnchorRight)
        l.addAnchor(self,Qt.AnchorBottom, self._botMargin, Qt.AnchorBottom)
        l.addAnchor(self,Qt.AnchorLeft, self._botMargin, Qt.AnchorLeft)
        l.addAnchor(self,Qt.AnchorRight, self._botMargin, Qt.AnchorRight)

        l.addAnchor(self._topMargin, Qt.AnchorBottom, self.myEmitter, Qt.AnchorTop)
        l.addAnchor(self._botMargin, Qt.AnchorTop, self.myEmitter, Qt.AnchorBottom)
        l.addAnchor(self._topMargin, Qt.AnchorBottom, self.myCollector, Qt.AnchorTop)
        l.addAnchor(self._botMargin, Qt.AnchorTop, self.myCollector, Qt.AnchorBottom)
        l.addAnchor(self, Qt.AnchorLeft, self.myCollector, Qt.AnchorLeft)
        l.addAnchor(self, Qt.AnchorRight, self.myEmitter, Qt.AnchorRight)
        l.addAnchor(self.myCollector, Qt.AnchorRight, self.myEmitter, Qt.AnchorLeft)

        # Link with your own right spacer
        l.addAnchor(self,Qt.AnchorRight,self.rightSpacer,Qt.AnchorLeft)
        l.addAnchor(self,Qt.AnchorVerticalCenter,self.rightSpacer,Qt.AnchorVerticalCenter)

        # Link with Block to right (when available)
        if self.block.rightBlock and self.block.rightBlock.visual:
            print "block",self.block.index,"linking right to",self.block.rightBlock.index
            l.addAnchor(self.rightSpacer,Qt.AnchorRight,self.block.rightBlock.visual,Qt.AnchorLeft)
            l.addAnchor(self.rightSpacer,Qt.AnchorVerticalCenter,self.block.rightBlock.visual,Qt.AnchorVerticalCenter)

        # Link with spacer of Block to left (when available)
        if self.block.leftBlock and self.block.leftBlock.visual:
            print "block",self.block.index,"linking left to",self.block.leftBlock.index
            l.addAnchor(self,Qt.AnchorLeft,self.block.leftBlock.visual.rightSpacer,Qt.AnchorRight)
            l.addAnchor(self,Qt.AnchorVerticalCenter,self.block.leftBlock.visual.rightSpacer,Qt.AnchorVerticalCenter)

    def mousePressEvent(self,event):
        pos = event.pos()
        print "Block:",self.block.index
        self.setCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        drag = QDrag(event.widget())
        mimeData = QMimeData()
        mimeData.setText(str(self.block.index))
        drag.setMimeData(mimeData)
        drag.start()

    def mouseReleaseEvent(self,event):
        print "hi",
        self.setCursor(Qt.ArrowCursor)

    def paint(self,painter,option,widget):
        painter.setPen(Qt.red)
        painter.drawRect(self.rect())

    class Spacer(QGraphicsWidget):
        """ Spacer between blocks, associated with the block to its left.
        Spacers are targets for dragging blocks to new positions.
        """
        def __init__(self,parent):
            super(MyBlock.Spacer,self).__init__(parent=parent)
            self.parent = parent
            self.setSizePolicy(QSizePolicy(QSizePolicy.MinimumExpanding,QSizePolicy.Preferred))
            self.setPreferredWidth(15)
            self.setMinimumWidth(15)
            self.dragOver = False
            self.setAcceptDrops(True)

        def dragEnterEvent(self,event):
            if event.mimeData().hasText():
                event.setAccepted(True)
                self.dragOver = True
            else:
                event.setAccepted(False)

        def dragLeaveEvent(self,event):
            self.dragOver = False

        def dropEvent(self,event):
            self.dragOver = False
            # Dragged Index
            srcIdx = int(event.mimeData().text()) 
            # Left Index
            lowerIdx = self.parent.block.index 
            # Right Index - or your index + 1 if you are the right most block already
            upperIdx = self.parent.block.rightBlock.index if self.parent.block.rightBlock else None
            blocks = self.parent.block._topology.blocks     # generated dictionary - note keys don't change

            print "Move index",str(srcIdx),"between",str(lowerIdx),"and",str(upperIdx)
            b = self.parent.block._topology.blocks[0]
            while True:
                print b.index,
                b = b.rightBlock
                if b is None:
                    break
            print ""

            # IF there is an empty space, take it!
            #TODO: alternatively, test if index+1 in blocks.keys()?
            if lowerIdx+1 < upperIdx:
                blocks[srcIdx].index = lowerIdx+1
                print "Case 1"
                self.parent.parent.link()    

            # If we are moving to the right, lowerIdx is the target index.
            # Clear the dragged block's index, then shift all effected block
            # indices left.
            elif lowerIdx > srcIdx:
                print "Case 2"
                srcBlock = blocks[srcIdx]
                lastBlock = srcBlock
                currBlock = lastBlock.rightBlock

                # TODO: This algorithm is messy and hard to understand what is going on.
                # This seems to mainly be due to the fact that I am trying to shift the
                # actual values, whatever they happen to be (not necessarily consecutive).
                # Consecutive numbers would probably be a lot cleaner, but the topology 
                # supports skipping values (for flexibility).
                # Is there a better way?
                lastIdx = None
                currIdx = srcIdx
                while isinstance(currIdx,int) and currIdx < (upperIdx or lowerIdx+1): # In case upperIdx is None, use lower+1
                    # Get the next blocks index, or upperIdx if you are at right most block
                    nextIdx = blocks[currIdx].rightBlock.index if blocks[currIdx].rightBlock else None
                    blocks[currIdx].index = lastIdx
                    print "%s -> %s"%(str(currIdx),str(lastIdx))
                    lastIdx = currIdx
                    currIdx = nextIdx
                if not lastIdx == lowerIdx:
                    print "last=%r lower=%r"%(lastIdx,lowerIdx)
                    exit(0)
                blocks[srcIdx].index = lastIdx
                self.parent.parent.link()    


                



        def paint(self,painter,option,widget):
            painter.setPen(Qt.NoPen)
            painter.drawRect(self.rect())




class MyBlockHorizontalSpacer(QGraphicsWidget):
    def __init__(self,parent):
        super(MyBlockHorizontalSpacer,self).__init__(parent=parent)
        self.setSizePolicy(QSizePolicy(QSizePolicy.MinimumExpanding,QSizePolicy.MinimumExpanding))
        self.setPreferredHeight(15)
        self.setMinimumHeight(15)

#     def paint(self,painter,option,widget):
#         painter.setPen(Qt.blue)
#         painter.drawRect(self.rect())

class MyContainer(QGraphicsWidget):
    """ Emitter or Collector """
    def __init__(self,parent):
        super(MyContainer,self).__init__(parent=parent)
        self.parent = parent
        self.setSizePolicy(QSizePolicy(QSizePolicy.MinimumExpanding,QSizePolicy.Preferred))
#         self.setPreferredWidth(15)
        self.setMinimumWidth(15)

    def paint(self,painter,option,widget):
        painter.setPen(Qt.green)
        painter.drawRect(self.rect())

    def mousePressEvent(self,event):
        pos = event.pos()
        print "Emitter" if isinstance(self,MyEmitter) else "Collector" if isinstance(self,MyCollector) else "Container"
        super(MyContainer,self).mousePressEvent(event)

    def mouseReleaseEvent(self,event):
        print "hi"
        self.setCursor(Qt.ArrowCursor)
        super(MyContainer,self).mouseReleaseEvent(event)




class MyEmitter(MyContainer):
     def paint(self,painter,option,widget):
        painter.setPen(Qt.blue)
        painter.drawRect(self.rect())
   
class MyCollector(MyContainer):
     def paint(self,painter,option,widget):
        painter.setPen(Qt.green)
        painter.drawRect(self.rect())
   




class MySnap(QGraphicsWidget):
    def __init__(self,parent,snap):
        super(MySnap,self).__init__(parent=parent)
        self.parent = parent
        # The parent here should be a MyContainer
        self.setSizePolicy(QSizePolicy(QSizePolicy.Preferred,QSizePolicy.Preferred))
        self.setPreferredWidth(20)
        self.setPreferredHeight(40)
        # Link with the snap
        self.snap = snap
        self.snap.visual = self

        self.rightSpacer = MySnap.Spacer(self)

    def link(self):
        """ Link this snap with objects surrounding it. """
        l = self.parent.layout()

        # Link with your own right spacer
        l.addAnchor(self, Qt.AnchorRight, self.rightSpacer, Qt.AnchorLeft)
        l.addAnchor(self, Qt.AnchorVerticalCenter, self.rightSpacer, Qt.AnchorVerticalCenter)

        # Determine what container (emitter or collector) you are in, so that 
        # you can link to its edges if necessary
        container = self.snap.block.visual.myEmitter if self.snap.isSource() else self.snap.block.visual.myCollector

        # Link with snap to right (if it exists) or to the left side of container
        #TODO: replace AnchorVerticalCenter with AnchorTop and again with AnchorBottom
        if self.snap.rightSnap and self.snap.rightSnap.visual:
            l.addAnchor(self.rightSpacer, Qt.AnchorRight, self.snap.rightSnap.visual, Qt.AnchorLeft)
            l.addAnchor(self.rightSpacer, Qt.AnchorVerticalCenter, self.snap.rightSnap.visual, Qt.AnchorVerticalCenter)
        else:
            l.addAnchor(self.rightSpacer, Qt.AnchorRight, container, Qt.AnchorRight)
            l.addAnchor(self.rightSpacer, Qt.AnchorVerticalCenter, container, Qt.AnchorVerticalCenter)

        # Link with spacer of Snap to left (if it exists), or to the right side
        # of your container
        if self.snap.leftSnap and self.snap.leftSnap.visual:
            l.addAnchor(self, Qt.AnchorLeft, self.snap.leftSnap.visual.rightSpacer, Qt.AnchorRight)
            l.addAnchor(self, Qt.AnchorVerticalCenter, self.snap.leftSnap.visual.rightSpacer, Qt.AnchorVerticalCenter)
        else:
            l.addAnchor(self, Qt.AnchorLeft, container, Qt.AnchorLeft)
            l.addAnchor(self, Qt.AnchorVerticalCenter, container, Qt.AnchorVerticalCenter)

    def mousePressEvent(self,event):
        pos = event.pos()
        print "Snap:",self.snap.order
        super(MySnap,self).mousePressEvent(event)

    def mouseReleaseEvent(self,event):
        print "hi"
        self.setCursor(Qt.ArrowCursor)
        super(MySnap,self).mouseReleaseEvent(event)



    def paint(self,painter,option,widget):
        painter.setPen(Qt.red)
        painter.drawRect(self.rect())


    class Spacer(QGraphicsWidget):
        """ Snap Spacer """
        def __init__(self,parent):
            super(MySnap.Spacer,self).__init__(parent=parent)
            self.setSizePolicy(QSizePolicy(QSizePolicy.MinimumExpanding,QSizePolicy.Preferred))
            self.setPreferredWidth(15)
            self.setMinimumWidth(15)

        def paint(self,painter,option,widget):
            painter.setPen(Qt.NoPen)
            painter.drawRect(self.rect())




class MyArc(QGraphicsWidget):
    def __init__(self,parent):
        super(MyArc,self).__init__(parent=parent)
 
    def paint(self,painter,option,widget):
        painter.setPen(Qt.red)
        painter.drawRect(self.rect())






class DrawingBoard(QGraphicsWidget):
    def __init__(self):
        super(DrawingBoard,self).__init__(parent=None)
        self.setAcceptedMouseButtons(Qt.LeftButton)
        self.resize(0,0)
        self.topology = None
    def autoLayout(self,topology):
        self.topology = topology
        lastBlock = None
        self.visualBlocks = list()
        self.visualSnaps = list()
        for index,block in topology.blocks.items():
            print "adding block",index
            vertexBlock = MyBlock(self,block)
            self.visualBlocks.append(vertexBlock)
            for snap in block.emitter.values()+block.collector.values():
                mySnap = MySnap(self,snap)
                self.visualSnaps.append(mySnap)
        self.link()
        
    def link(self):
        l = QGraphicsAnchorLayout()
        l.setSpacing(0)
        self.setLayout(l)


        # Anchor the first block against the layout
        blocks = self.topology.blocks
        first = min(blocks.keys())
        self.layout().addAnchor(blocks[first].visual, Qt.AnchorTop, self.layout(), Qt.AnchorTop)
        self.layout().addAnchor(blocks[first].visual, Qt.AnchorLeft, self.layout(), Qt.AnchorLeft)
#         self.layout().addAnchor(self.visualBlocks[0],Qt.AnchorTop,self.layout(),Qt.AnchorTop)
#         self.layout().addAnchor(self.visualBlocks[0],Qt.AnchorLeft,self.layout(),Qt.AnchorLeft)

        # Start anchoring the other blocks
        for b in self.visualBlocks:
            b.link()
        for s in self.visualSnaps:
            s.link()
        self.layout().invalidate()
        
        

    def paint(self,painter,option,widget):
        painter.setPen(Qt.blue)
        painter.drawRect(self.rect())


class GraphView(QGraphicsView):
    def __init__(self):
        super(GraphView,self).__init__(parent=None)
        self.setScene(QGraphicsScene(self))
        # We might want to do this later to speed things up
        self.drawingBoard = DrawingBoard()

        self.scene().addItem(self.drawingBoard)
        # Basically, I'm not sure how to tell a widget where to go inside a scene.
        # But widgets placed inside widgets seem to be pretty reliable.

        # Set the size of the window
        self.resize(1024,768)

        # Show the window
        self.show()

    def autoLayout(self,topology):
        self.drawingBoard.autoLayout(topology)

    def mousePressEvent(self,event):
        pos = event.pos()
        print pos.x(),pos.y()
        super(GraphView,self).mousePressEvent(event)

    def mouseReleaseEvent(self,event):
        pos = event.pos()
        print pos.x(),pos.y()
        super(GraphView,self).mouseReleaseEvent(event)



