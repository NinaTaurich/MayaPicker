import maya.cmds as cmds
from PySide2 import QtWidgets, QtCore, QtGui

class DragButton(QtWidgets.QPushButton):
    def __init__(self, color, selection, *args, **kwargs):
        super(DragButton,self).__init__(*args, **kwargs)
        self.setCheckable(True)

        self.connection = selection #list of objects
        self.numSel=0 #number of objects in list selected in the world
        self.updateNumSel()  #update numSel based on objects selected in world

        self.clicked.connect(self.selectList) #select objects when clicked
        self.color = color #button color

        self.setColor(color) #set the color of the button

    def updateNumSel(self):
        """
        updates numSel variable
        :return: None
        """
        currSel =cmds.ls(sl=True)
        self.numSel =0

        self.selected = False

        for o in self.connection:
            if o in currSel:
                self.numSel+=1
            if(self.numSel==len(self.connection)):
                self.selected = True
                self.setChecked(True)
                break
        if(not self.selected):
            self.setChecked(False)

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

    def selectList(self):
        """
        select objects in list
        :return: None
        """
        print("select!")
        add = False

        if(cmds.getModifiers()==1): #add to selection if shift is pressed
            print("shift")
            add = True
        if(self.selected==False):
            self.setChecked(True) #set white outline
            self.selected=True
            if(add == False): #deselect everything
                    cmds.select(self.connection[0])
            for obj in self.connection: #select objects in list
                cmds.select(obj, add = True)
        else:
            self.setChecked(False) #set black outline
            self.selected=False
            for obj in self.connection: #add objects to world selection
                cmds.select(obj, deselect= True)


    def mousePressEvent(self, event):
        self.__mousePressPos = None
        self.__mouseMovePos = None
        if event.button() == QtCore.Qt.LeftButton:
            self.__mousePressPos = event.globalPos()
            self.__mouseMovePos = event.globalPos()

        super(DragButton, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
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
        if self.__mousePressPos is not None:
            moved = event.globalPos() - self.__mousePressPos
            if moved.manhattanLength() > 3:
                event.ignore()
                self.setDown(False)
                return
        super(DragButton, self).mouseReleaseEvent(event)

