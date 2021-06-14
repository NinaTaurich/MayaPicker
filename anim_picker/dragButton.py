from __future__ import absolute_import
import maya.cmds as cmds
from PySide2 import QtWidgets, QtCore, QtGui
import logging
logger = logging.getLogger("picker")

class DragButton(QtWidgets.QPushButton):
    """
    A class creating a draggable button
    Attributes
    -----------
    connection: str[] -list of objects that are connected to the button
    numSel: Int -number of objects in connections list that are currently selected in the scene
    color: Str -The color of the button
    selected: Boolean -True if all objects in scene are selected
    parentUI: imageTab -reference to the parent imageTab

    Methods
    -----------------
    init (color, selection, baseUI)
    updateNumSel() -updates numSel variable to be the number of selected objects that are within the list of connected objects
    setColor(newColor) -Sets color of button
    selectList() -selects the objects in list of connected objects
    mousePressEvent(event) -if button is clicked set start location
    mouseMoveEvent(event) -move button with mouse
    mouseReleaseEvent (event)- release button
    """
    def __init__(self, color, selection, baseUI, *args, **kwargs):
        super(DragButton,self).__init__(*args, **kwargs)
        self.setCheckable(True)

        self.connection = selection #list of objects
        self.numSel=0 #number of objects in list selected in the scene
        self.updateNumSel()  #update numSel based on objects selected in scene

        self.clicked.connect(self.selectList) #select objects when clicked
        self.color = color #button color

        self.parentUI = baseUI

        self.setColor(color) #set the color of the button

    def updateNumSel(self):
        """
        updates numSel variable to be the number of selected objects that are within the list of connected objects
        :return: None
        """
        currSel =cmds.ls(sl=True)
        self.numSel =0

        self.selected = False

        #check if each connected object is selected
        for o in self.connection:
            if o in currSel:
                self.numSel+=1
            if(self.numSel==len(self.connection)): #highlight button if all objects in list are selected
                self.selected = True
                self.setChecked(True) #highlight with wight
                break
        if(not self.selected):
            self.setChecked(False) #don't highlight

    def setColor(self, newColor):
        """
        Set color of button
        :param newColor: (str) color of button
        :return: None
        """
        #set color of button
        if newColor == "Red":
            self.setStyleSheet("QPushButton{background-color: red; border: 1px solid black}" 
                               "QPushButton:checked{background-color: red; border: 1px solid white}")
        elif newColor == "Blue":
            self.setStyleSheet("QPushButton{background-color: blue; border: 1px solid black}" 
                               "QPushButton:checked{background-color: blue; border: 1px solid white}")
        elif newColor == "Green":
            self.setStyleSheet("QPushButton{background-color: green; border: 1px solid black}" 
                               "QPushButton:checked{background-color: green; border: 1px solid white}")
        elif newColor == "Yellow":
            self.setStyleSheet("QPushButton{background-color: yellow; border: 1px solid black; color: black}" 
                               "QPushButton:checked{background-color: yellow; border: 1px solid white; color: black}")
        elif newColor == "Orange":
            self.setStyleSheet("QPushButton{background-color: orange; border: 1px solid black}" 
                               "QPushButton:checked{background-color: orange; border: 1px solid white}")
        elif newColor == "Purple":
            self.setStyleSheet("QPushButton{background-color: purple; border: 1px solid black}" 
                               "QPushButton:checked{background-color: purple; border: 1px solid white}")
        else:
            self.setStyleSheet("QPushButton{background-color: grey; border: 1px solid black}" 
                               "QPushButton:checked{background-color: grey; border: 1px solid white}")


    def selectList(self):
        """
        select objects in list of connected objects
        :return: None
        """
        logger.debug("select!")
        add = False

        if(cmds.getModifiers()==1): #add to selection if shift is pressed
            logger.debug("shift")
            add = True
        if(self.selected==False): #select objects in connections list
            self.setChecked(True) #set white outline
            self.selected=True
            if(add == False): #deselect everything first
                try:
                    cmds.select(self.connection[0])
                except:
                    logger.error(self.connection[0] +" doesn't exist in scene")
            for obj in self.connection: #select objects in list
                try:
                    cmds.select(obj, add = True)
                except:
                    logger.error(obj +" doesn't exist in scene")
        else: #deselect objects in connections list
            self.setChecked(False) #set black outline
            self.selected=False
            for obj in self.connection: #deselects objects
                try:
                    cmds.select(obj, deselect= True)
                except:
                    logger.error("Nothing deselected. Objects don't exist in scene")


    def mousePressEvent(self, event):
        """
        if button is clicked set start location
        :param event:
        :return: None
        """
        if (self.parentUI.edit): #draggable if in edit mode
            self.__mousePressPos = None
            self.__mouseMovePos = None
            if event.button() == QtCore.Qt.LeftButton:
                self.__mousePressPos = event.globalPos()
                self.__mouseMovePos = event.globalPos()

        super(DragButton, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """
        move button with mouse
        :param self:
        :param event:
        :return: None
        """

        if (self.parentUI.edit): #draggable if in edit mode
            if event.buttons() == QtCore.Qt.LeftButton:
                # adjust offset from clicked point to origin of widget
                currPos = self.mapToGlobal(self.pos())
                globalPos = event.globalPos()
                diff = globalPos - self.__mouseMovePos
                newPos = self.mapFromGlobal(currPos + diff)
                self.move(newPos)

                self.__mouseMovePos = globalPos

        super(DragButton, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """
        release button
        :param self:
        :param event:
        :return: None
        """
        if (self.parentUI.edit):#draggable if in edit mode
            if self.__mousePressPos is not None:
                moved = event.globalPos() - self.__mousePressPos
                if moved.manhattanLength() > 3: #set down if moved a distance larger than 3
                    event.ignore()
                    self.setDown(False)
                    return
        super(DragButton, self).mouseReleaseEvent(event)

