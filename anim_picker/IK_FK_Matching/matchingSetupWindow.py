import maya.cmds as cmds
from PySide2 import QtWidgets, QtCore, QtGui
from maya import OpenMayaUI as omui
import pymel.core as pm
import os
from shiboken2 import wrapInstance
import logging
from MayaPicker.anim_picker.IK_FK_Matching import IK_FKMatchingController

logging.basicConfig()
logger = logging.getLogger("matching")
logger.setLevel(logging.DEBUG)

def getMayaMainWindow():
    """
    :return: maya main window as a python object
    """
    win = omui.MQtUtil_mainWindow()
    ptr = wrapInstance(int(win), QtWidgets.QMainWindow)
    return ptr

def deleteControl(control):
    if cmds.workspaceControl(control, q=True, exists=True):
        cmds.workspaceControl(control,e=True, close=True)
        cmds.deleteUI(control,control=True)

class matchingSetupWindowUI(QtWidgets.QDialog):
    def __init__(self, IK_FKController, parent=getMayaMainWindow()):
                #ensure not more than one at the same time
        try:
            pm.deleteUI('MatchingUI')
            logger.debug("delete matching UI")
        except:
            logger.debug("no prev UI")

        # deleteControl("MatchingUIWorkspaceControl")
        super(matchingSetupWindowUI, self).__init__(parent)

        self.setWindowTitle("Matching UI") #set title
        self.setMinimumWidth(400) #set width
        self.setObjectName("MatchingUI")
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        #get rid of help button on window
        self.setWindowFlags(self.windowFlags()^QtCore.Qt.WindowContextHelpButtonHint)

        self.IK_FK_Controller = IK_FKController

        self.buildUI()

        self.loadPrevious()

        self.show()

    def buildUI(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout_form = QtWidgets.QFormLayout()

        self.boxes = []

        self.createBox("FK shoulder", layout_form)
        self.createBox("FK elbow", layout_form)
        self.createBox("FK wrist", layout_form)
        self.createBox("IK Pole Vector", layout_form)
        self.createBox("IK Hand", layout_form)
        self.createBox( "IK/FK Switch", layout_form)
        layout.addLayout(layout_form)

        startBtn = QtWidgets.QPushButton("Start")
        startBtn.clicked.connect(self.submit)
        layout.addWidget(startBtn)

    def createBox(self, limb, layout_form):
        limbLine = QtWidgets.QHBoxLayout(self)
        limbBox = QtWidgets.QLabel()
        limbBox.setMinimumWidth(200)
        self.boxes.append(limbBox)
        limbLine.addWidget(limbBox)
        limbLine.addStretch()
        enterSelectionBox = QtWidgets.QPushButton("enter")
        enterSelectionBox.setCheckable(True)
        enterSelectionBox.clicked.connect(lambda: self.enterSelection(limbBox, enterSelectionBox))
        limbLine.addWidget(enterSelectionBox)
        layout_form.addRow(limb+ ": ", limbLine)

    def enterSelection(self, partBox, enterBtn):
        if hasattr(self,"sj"):
            cmds.scriptJob(kill=self.sj)
        if hasattr(self, "oldBtn"):
            self.oldBtn.setChecked(False)
        self.oldBtn = enterBtn
        enterBtn.setChecked(True)
        self.sj = cmds.scriptJob(event= ["SelectionChanged", lambda: self.selected(partBox)], parent ="MatchingUI")
        print("enter for")
        print("")

    def selected(self, part):
        print("added selection")
        currSelection = cmds.ls(selection = True)
        part.setText(currSelection[0])

    def loadPrevious(self):
        print("trying to load")
        ns = ''
        if(len(pm.selected())>0):
            ns = pm.selected()[0].split(':')[0] if len(pm.selected()[0].split(':')) > 1 else ''
            print(ns)
        previous = self.IK_FK_Controller.loadIkFkCtrl(ns, 'arm', 'L')
        if(len(previous)!=0):
            self.boxes[0].setText(previous['fkshldr'])
            self.boxes[1].setText(previous['fkellbow'])
            self.boxes[2].setText(previous['fkwrist'])
            self.boxes[3].setText(previous['ikpv'])
            self.boxes[4].setText(previous['ikwrist'])
            self.boxes[5].setText(previous['switchCtrl'])


    def submit(self):
        #check if valid input
        #check if any are empty
        for limb in self.boxes:
            if limb.text() == "":
                print("enter all")
                return


        #check if any are the same

        #set all attributes
        for limb in self.boxes:
            self.IK_FK_Controller.arm.append(limb.text())
            print(limb.text())

        self.IK_FK_Controller.saveIKFkCtrls('arm',
                                            'L',
                                            self.boxes[0].text(),
                                            self.boxes[1].text(),
                                            self.boxes[2].text(),
                                            self.boxes[3].text(),
                                            self.boxes[4].text(),
                                            self.boxes[5].text(),
                                            'IK_FK',
                                            0,
                                            1,
                                            [0,0,0],
                                            '+X')

        self.IK_FK_Controller.turnOn()


