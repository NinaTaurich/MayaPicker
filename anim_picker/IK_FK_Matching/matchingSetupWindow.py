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

    #overrides close event for window if closed before submitting
    def closeEvent(self, event):
        if(not self.IK_FK_Controller.ifOn):
            self.IK_FK_Controller.turnOff()
        event.accept()

    def buildUI(self):
        """
        adds UI elements to window
        :return: None
        """
        layout = QtWidgets.QVBoxLayout(self)

        self.limbs = {} #dictionary with array of inputs for each limb
        tabWidget = QtWidgets.QTabWidget()

        #tab for right arm
        self.boxes = []
        rightArm = QtWidgets.QWidget()
        ra_layout_form = QtWidgets.QFormLayout()
        self.createBox("FK shoulder", ra_layout_form)
        self.createBox("FK elbow", ra_layout_form)
        self.createBox("FK wrist", ra_layout_form)
        self.createBox("IK Pole Vector", ra_layout_form)
        self.createBox("IK Hand", ra_layout_form)
        self.createBox( "IK/FK Switch", ra_layout_form)
        self.createBox("IK/FK Attr", ra_layout_form, attribute= True)
        rightArm.setLayout(ra_layout_form)
        tabWidget.addTab(rightArm, "Right Arm")
        self.limbs["R_arm"] = self.boxes

        #tab for left arm
        self.boxes = []
        leftArm = QtWidgets.QWidget()
        la_layout_form = QtWidgets.QFormLayout()
        self.createBox("FK shoulder", la_layout_form)
        self.createBox("FK elbow", la_layout_form)
        self.createBox("FK wrist", la_layout_form)
        self.createBox("IK Pole Vector", la_layout_form)
        self.createBox("IK Hand", la_layout_form)
        self.createBox( "IK/FK Switch", la_layout_form)
        self.createBox("IK/FK Attr", la_layout_form, attribute= True)
        leftArm.setLayout(la_layout_form)
        tabWidget.addTab(leftArm, "Left Arm")
        self.limbs["L_arm"] = self.boxes

        layout.addWidget(tabWidget)

        startBtn = QtWidgets.QPushButton("Start")
        startBtn.clicked.connect(self.submit)
        layout.addWidget(startBtn)

    def createBox(self, label, layout_form, attribute = False):
        """
        Creates a box for a new input with given name. Adds button that when pressed enters selected object
        label _________________ |enter|
        :param label: String name of input
        :param layout_form: Form layout to add box to
        :param attribute: Bool True enters selected attribute False enters selected control
        :return: None
        """
        limbLine = QtWidgets.QHBoxLayout(self) #Horizontal layout
        limbBox = QtWidgets.QLabel() #holds name of control entered
        limbBox.setMinimumWidth(200)
        self.boxes.append(limbBox) #add to list of items, section
        limbLine.addWidget(limbBox)
        limbLine.addStretch()
        enterSelectionBox = QtWidgets.QPushButton("enter")
        if (attribute == False):
            #enter first selected object
            enterSelectionBox.clicked.connect(lambda: self.enterSelection(limbBox))
        else:
            #enter first selected attribute
            enterSelectionBox.clicked.connect(lambda: self.enterChannelboxSelection(limbBox))
        limbLine.addWidget(enterSelectionBox)
        layout_form.addRow(label + ": ", limbLine)

    def enterSelection(self, partBox):
        """
        enters first object selected into given Qlabel
        :param partBox: QLabel that is filled with selected object
        :return:
        """
        currSelection = cmds.ls(selection = True)
        if(len(currSelection)>0):
            partBox.setText(currSelection[0])
        else:
            logger.warning("Select one control and press enter")

    def enterChannelboxSelection(self, partBox):
        """
        enters first attribute selected into given Qlabel
        :param partBox: QLabel that is filled with selected attribute
        :return:
        """
        channelBox = pm.mel.eval('global string $gChannelBoxName; $temp=$gChannelBoxName;')	#fetch maya's main channelbox
        selected_attrs = cmds.channelBox( channelBox, q = True, sma = True )
        if not selected_attrs:
            logger.warning('Highlight only the IK/FK Switch Attribute in the Channelbox')
            return []
        if len(selected_attrs) is not 1:
            pm.warning('Highlight only the IK/FK Switch Attribute in the Channelbox')
            return []
        partBox.setText(selected_attrs[0])



    def loadPrevious(self):
        """
        fills out form with previous inputs if any
        :return: None
        """
        ns = '' #namespace
        #get namespace
        if(len(pm.selected())>0):
            ns = pm.selected()[0].split(':')[0] if len(pm.selected()[0].split(':')) > 1 else ''
            print(ns)

        for k in self.limbs.keys(): #enter previous selection for each limb
            side, limb = k.split("_")
            previous = self.loadIkFkCtrl(ns, limb, side) #get previous
            if(len(previous)!=0):
                #enter previous
                self.limbs[k][0].setText(previous['fkshldr'])
                self.limbs[k][1].setText(previous['fkellbow'])
                self.limbs[k][2].setText(previous['fkwrist'])
                self.limbs[k][3].setText(previous['ikpv'])
                self.limbs[k][4].setText(previous['ikwrist'])
                self.limbs[k][5].setText(previous['switchCtrl'])
                self.limbs[k][6].setText(previous['switchAttr'])


    def submit(self):
        """
        saves entered controls and starts matching mode
        :return: None
        """
        keys = ['fkshldr', 'fkellbow','fkwrist' ,'ikpv', 'ikwrist', 'switchCtrl', 'switchAttr']

        for k in self.limbs.keys(): #for each limb
            #check if valid input
            #check if any are empty
            isComplete =True
            for box in self.limbs[k]:
                if box.text() == "":
                    logger.error("not all parts entered for "+ k)
                    isComplete = False
                    break
            if(not isComplete):
                continue
                #skip the rest of code

            #enter attributes
            i = 0
            self.IK_FK_Controller.limb[k] = {}
            for box in self.limbs[k]:
                self.IK_FK_Controller.limb[k][keys[i]] = box.text()
                print(box.text())
                i+=1

            #store for later
            side, limb = k.split("_")
            self.saveIKFkCtrls(limb,
                                                side,
                                                self.limbs[k][0].text(),
                                                self.limbs[k][1].text(),
                                                self.limbs[k][2].text(),
                                                self.limbs[k][3].text(),
                                                self.limbs[k][4].text(),
                                                self.limbs[k][5].text(),
                                                self.limbs[k][6].text(),
                                                0,
                                                1,
                                                [0,0,0],
                                                '+X')

        self.IK_FK_Controller.turnOn()


    """
    The code below are copyright of Monika Gelbmann 2021 and released under the MIT license
    """
    def saveIKFkCtrls(self, limb, side, fkshldr, fkellbow, fkwrist, ikpv, ikwrist, switchCtrl, switchAttr, switch0isfk, switchAttrRange, rotOffset, bendKneeAxis):
        '''
        limb = 'arm'/'leg
        side = 'R'/'L'
        '''
        sel = pm.selected()
        ns = fkwrist.split(':')[0] if len(fkwrist.split(':')) > 1 else ''
        storenode = ns + '__' + side + '_' + limb + '_IKFKSTORE'
        logger.info('Storenode is %s'%storenode)
        if pm.objExists(storenode) == False:
            storenode = pm.createNode('transform', n=storenode)
        else:
            message =  'Do you want to replace existing store node?'
            confirm = pm.confirmDialog( title='Replace existing', message=message, button=['Yes','No'],
                              defaultButton='Yes', cancelButton='No', dismissString='No' )
            if confirm == 'Yes':
                logger.info('deleting existing store node')
                pm.delete(storenode)
                storenode = pm.createNode('transform', n=storenode)
            else:
                pm.select(sel)
                return

        storenode = pm.PyNode(storenode)
        storedic = {'fkwrist': fkwrist, 'fkellbow': fkellbow, 'fkshldr':fkshldr, 'ikwrist':ikwrist, 'ikpv':ikpv, 'switchCtrl':switchCtrl, 'switchAttr':switchAttr, 'switch0isfk':switch0isfk, 'attrRange':switchAttrRange, 'rotOffset':rotOffset, 'side':side, 'bendKneeAxis':bendKneeAxis}
        for attrName, value in storedic.items():
            pm.addAttr(storenode, ln=attrName, dt='string', k=1)
            storenode.attr(attrName).set('%s'%value)

        pm.select(sel)
        return storenode


    def loadIkFkCtrl(self, ns, limb, side):
        '''
        ns = 'namespace'
        limb = 'arm'/'leg
        side = 'R'/'L'
        '''

        storenodeRegex = ns + '__' + side + '_' + limb + '_IKFKSTORE'
        logger.info('loading %s '%storenodeRegex)
        storenode = pm.ls(storenodeRegex)
        if len(storenode) == 0:
            possible = cmds.ls("*__" + side + '_' + limb + '_IKFKSTORE')
            if(len(possible)>0):
                storenode = possible[0]
            else:
                logger.info( 'No storenode found'           )
                return {}
        else:
            storenode = storenode[0]
        ns = storenode.split('__')[0]
        storenode = ns + '__' + side + '_' + limb + '_IKFKSTORE'

        if pm.objExists(storenode) == False:
            return {}
        storenode = pm.PyNode(storenode)

        storedic = {'fkwrist': '', 'fkellbow': '', 'fkshldr':'', 'ikwrist':'', 'ikpv':'', 'switchCtrl':'', 'switchAttr':'', 'switch0isfk':'', 'attrRange':'', 'rotOffset':'', 'bendKneeAxis':'+X'}
        for attrName, value in storedic.items():
            try:
                storedic[attrName] = storenode.attr(attrName).get()
            except:
                pm.warning('Missing Attribute %s. Please Save Store Node again.'%attrName)
                storedic[attrName] = value

        logger.info('StoreNode found is %s'%storedic)
        return storedic


