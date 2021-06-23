from __future__ import absolute_import
import maya.cmds as cmds
from PySide2 import QtWidgets, QtCore, QtGui
from maya import OpenMayaUI as omui
from shiboken2 import wrapInstance
import pymel.core as pm
import os
import json
import logging
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

from MayaPicker.anim_picker import dragButton as drag
from MayaPicker.anim_picker.IK_FK_Matching import matchingSetupWindow
from MayaPicker.anim_picker.IK_FK_Matching import IK_FKMatchingController
from six.moves import range
from six.moves import reload_module
reload_module(drag)
reload_module(IK_FKMatchingController)


logging.basicConfig()
logger = logging.getLogger("picker")
logger.setLevel(logging.DEBUG)

# Where is this script?
SCRIPT_LOC = os.path.split(__file__)[0]
BASE_DIR = "C:/"
# BASE_DIR = "C:/Users/ninat/Documents/Python and Pipelines"

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

class pickerBaseUI(MayaQWidgetDockableMixin, QtWidgets.QDialog):
    """
    a class that creates a dockable qt character picker window
    Attributes
    -----------
    objects: {} -dictionary of objects in scene and what buttons they are connected to. They are separated by each tab. key- object name, value- array of buttons
    buttons: dragButton[] -array of references to buttons according to tab
    previousSelection: Str[] -array of last selection of objects in scene
    edit: boolean -bool indicating if edit window is showing
    tabwidget: tabsWindow -reference to window with all the tabs

    Methods
    -----------------
    init(parent = getMayaMainWindow())
    keyPressEvent(event) -deletes selected buttons when backspace or delete key is pressed in edit mode
    deleteBtns() -deletes selected buttons
    updateBtnSelect() -updates outline of buttons if objects they are connected to have been selected or deselected and checkboxes
    buildUI() -adds UI elements to window
    save() -saves current picker layout to a json file. Creates a popup for user to choose name and place of file
    load() -Opens File Dialog and loads chosen template (json) by adding tabs specified in json
    editChange() -Changes mode of the picker between editing and not editing. Changes edit column and edit button text based on the current mode
    clearLayout(layout) -clear all layouts and widgets in given layout
    updateDetails(type) -updates details based on mode
    stateChanged(obj,box) -deselects object when checkbox is unchecked
    newConnection(btnParent = None) -creates new draggable button connected to current selection and add it to tab
    newDragBtn(color, selected, name, parent, width, height, tabIndex) -create new draggable button and add to parent
    """
    def __init__(self, parent = getMayaMainWindow()):
        #ensure not more than one at the same time
        try:
            pm.deleteUI('PickerUI')
            logger.debug("delete UI")
        except:
            logger.debug("no prev UI")

        deleteControl("PickerUIWorkspaceControl")
        super(pickerBaseUI, self).__init__(parent)

        self.setWindowTitle("Picker UI") #set title
        self.setMinimumWidth(400) #set width
        self.setObjectName("PickerUI")
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        #get rid of help button on window
        self.setWindowFlags(self.windowFlags()^QtCore.Qt.WindowContextHelpButtonHint)

        self.objects = {} #dictionary of objects in scene and what buttons they are connected to. They are separated by each tab. key- object name, value- array of buttons
        self.buttons = [] #array of references to buttons according to tab
        self.previousSelection = cmds.ls(sl=True) #array of last selection of objects in scene
        self.edit=True #start with showing edit tools

        self.IK_FK_Controller = IK_FKMatchingController.MatchingController(False)

        self.buildUI() #add to UI elements to window

        #update which buttons are selected/outlined each time the selection in scene is changed
        sj = cmds.scriptJob(event= ["SelectionChanged", lambda: self.updateBtnSelect()], parent = "PickerUI")

        self.show(dockable=True)

    def keyPressEvent(self, event):
        """
        deletes selected buttons when backspace or delete key is pressed in edit mode
        :param event:
        :return: None
        """
        if (event.key() == QtCore.Qt.Key_Backspace or event.key() == QtCore.Qt.Key_Delete):
            self.deleteBtns()

    def deleteBtns(self):
        """
        deletes selected buttons
        :return: None
        """
        if self.edit:
            logger.debug("Deleting Selected Buttons")
            currTab = self.tabwidget.currentWidget()
            children =currTab.children()

            for btn in children: #for each button in the current tab
                if (isinstance(btn,drag.DragButton)) and btn.selected == True: #check if selected
                    for k in self.objects[currTab].keys(): #remove from objects dictionary
                        if btn in self.objects[currTab][k]:
                            self.objects[currTab][k].remove(btn)
                        if len(self.objects[currTab][k]) ==0:
                            del(self.objects[currTab][k])
                    logger.debug(self.objects)
                    logger.debug("deleting: "+ str(btn))
                    btn.deleteLater()

    def updateBtnSelect(self):
        """
        updates outline of buttons if objects they are connected to have been selected or deselected and checkboxes
        :return: None
        """
        logger.debug("update buttons")
        currSelection = cmds.ls(selection = True)
        currTab = self.tabwidget.currentWidget()

        minus = [] #list of objects deselected
        added = [] #list of objects added to selection

        for i in self.previousSelection:
            if i not in currSelection: #object has been deselected
                minus.append(i) #add to deselected list
        for j in currSelection:
            if j not in self.previousSelection: #object has been added to selection
                added.append(j)

        #updated the number of selected objects for each button asociated with an object in one of the lists
        for a in added:
            logger.debug("added "+a)
            if a in self.objects[currTab]:
                for btn in self.objects[currTab][a]:
                    btn.numSel+=1 #add one to the number of objects selected in the list of connections for the button
                    if btn.numSel == len(btn.connection): #change outline if the number selected is equal to the total number of objects connected to the button
                        btn.selected = True
                        btn.setChecked(True)

        for m in minus:
            logger.debug("minus "+m)
            if m in self.objects[currTab]:
                for btn in self.objects[currTab][m]:
                    btn.numSel-=1 #subtract one to the number of objects selected in the list of connections for the button
                    logger.debug(btn.numSel)
                    if btn.numSel < len(btn.connection): #change outline if the number selected is less than the total number of objects connected to the button
                        btn.selected = False
                        btn.setChecked(False)

        self.previousSelection= currSelection


        if(self.edit ==True):
            logger.debug("checkboxes")
            #updates the list of checkboxes
            self.clearLayout(self.vbox) #clear list
            sl = cmds.ls(sl = True) #get selection
            for obj in sl: #add a checkbox for each object in selection
                checkbox = QtWidgets.QCheckBox(obj)
                checkbox.setChecked(True)
                checkbox.stateChanged.connect(lambda state, o=obj, c=checkbox: self.stateChanged(o, c))
                self.vbox.addWidget(checkbox) #add to layout

    #adds UI elements to window
    def buildUI(self):
        """
        adds UI elements to window
        :return: None
        """
        outside = QtWidgets.QVBoxLayout(self)
        columns = QtWidgets.QHBoxLayout(self)
        layout = QtWidgets.QVBoxLayout(self)
        self.details_layout = QtWidgets.QVBoxLayout(self) #column with edit panel
        self.restriction = QtWidgets.QWidget() #restricts size of details_layout
        self.restriction.setLayout(self.details_layout)
        self.restriction.setFixedWidth(200)
        columns.addLayout(layout)
        columns.addWidget(self.restriction)
        outside.addLayout(columns)

        #tab widget
        self.tabwidget = tabsWindow(self) #QtWidgets.QTabWidget(tabsClosable = True, movable = True)
        layout.addWidget(self.tabwidget)
        #add base tab
        self.tabwidget.newTab(name ="Untitled", image = "")

        #add second column with details
        self.updateDetails("edit")

        #edit button
        layout_btns = QtWidgets.QHBoxLayout()
        editBtn = QtWidgets.QPushButton("Stop Editing")
        editBtn.clicked.connect(lambda: self.editChange(editBtn))
        layout_btns.addWidget(editBtn)

        #save button
        saveBtn = QtWidgets.QPushButton("Save")
        saveBtn.clicked.connect(self.save)
        layout_btns.addWidget(saveBtn)

        #load button
        loadBtn = QtWidgets.QPushButton("Load")
        loadBtn.clicked.connect(self.load)
        layout_btns.addWidget(loadBtn)

        #close button
        closeBtn = QtWidgets.QPushButton('Close')
        closeBtn.clicked.connect(self.close)
        layout_btns.addWidget(closeBtn)

        outside.addLayout(layout_btns) #add buttons to layout

    def save(self):
        """
        saves current picker layout to a json file. Creates a popup for user to choose name and place of file
        :return: None
        """
        data = {'tabs':{}} #dictionary storing all data
        logger.info("Saving File!!!!!!!!!!!!!!")
        for i in range(self.tabwidget.count()):
            #add information about each tab
            tab = self.tabwidget.tabText(i)
            logger.debug(tab)
            children =self.tabwidget.widget(i).children()
            data['tabs']["tab %d" % i] = {"name": str(tab), "buttons": {}, "image":self.tabwidget.widget(i).imageFile }
            btnNum = 1
            for w in children: #add information about each button in tab
                if (isinstance(w,drag.DragButton)):
                    info = {"name": w.text(), "color": w.color, "x":w.x(), "y":w.y(), "connections": w.connection, "width": w.width(), "height": w.height()}
                    logger.debug(info)
                    logger.debug(w.connection)
                    #add new button to list
                    data['tabs']["tab %d" % i]["buttons"]["button %d" % btnNum] = info
                    btnNum+=1
        outData = json.dumps(data) #create into json
        logger.debug(outData)
        filename, type = QtWidgets.QFileDialog.getSaveFileName(self, 'Save Template',BASE_DIR,"(*.json)") #open file dialog to chose location and name
        logger.info("saving as: " +filename)
        with open(filename, "w") as f:
            json.dump(data, f, indent = 4) #save json in location

    def load(self):
        """
        Opens File Dialog and loads chosen template (json) by adding tabs specified in json
        :return: None
        """
        logger.info("Loading File!!!!!!!!!!!")
        file,types = QtWidgets.QFileDialog.getOpenFileName(self, 'Open file',
   BASE_DIR,"Template Files(*.json)") #creates file dialog
        with open(file) as template_json:
            data = json.load(template_json) #json template data
            logger.debug(data)
            for tab in data["tabs"]:
                #create new tab for each specified in data
                tabInfo = data["tabs"][tab]
                newTab =self.tabwidget.newTab(tabInfo["name"], image = tabInfo["image"]) #make tab
                for btn in tabInfo["buttons"]: #make buttons in each tab
                    btnInfo = tabInfo["buttons"][btn]
                    newbtn = self.newDragBtn(btnInfo["color"], btnInfo["connections"],btnInfo["name"], newTab, btnInfo["width"], btnInfo["height"],newTab)
                    newbtn.move(btnInfo["x"],btnInfo["y"]) #move button to location on screen

    def editChange(self,editBtn):
        """
        Changes mode of the picker between editing and not editing. Changes edit column and edit button text based on the current mode
        :return: None
        """
        if self.edit ==True:
            self.updateDetails("normal") #update details column
            self.edit = False #switch boolean
            self.editBtn.setText("Edit") #update button text
        else:
            self.updateDetails("edit") #update details column
            self.edit= True #switch boolean
            self.editBtn.setText("Stop Editing") #update button text

    def clearLayout(self, layout):
        """
        clear all layouts and widgets in given layout
        :param layout: layout to clear
        :return: None
        """
        while layout.count(): #loop while layout has children
            child = layout.takeAt(0) #first child of layout
            if child.widget():
                child.widget().deleteLater() #delete widget
            elif child.layout():
                self.clearLayout(child.layout()) #delete layout

    def updateDetails(self, type):
        """
        updates details based on mode
        :param type: (str) mode of picker either 'normal' or 'edit'
        :return: None
        """
        layout = self.details_layout
        self.clearLayout(layout) #clear details column
        self.button_form = QtWidgets.QFormLayout()
        self.details_layout.addLayout(self.button_form)

        logger.debug("update details")
        if(type == "normal"):
            logger.debug("type normal")
            self.restriction.setFixedWidth(0) #make column disapear

        if(type =="edit"):
            logger.debug("type edit")
            self.restriction.setFixedWidth(200) #set column width

            #btn preview
            self.previewLabel = QtWidgets.QLabel()
            self.previewLabel.setMinimumHeight(50)
            self.previewLabel.setMinimumWidth(150)
            self.button_form.addRow(self.previewLabel)
            self.previewLabel.setStyleSheet("border: 1px solid black;")

            #name box
            self.nameBox = QtWidgets.QLineEdit(text = "Button")
            self.button_form.addRow("Name:", self.nameBox)
            #update preview button name
            self.nameBox.textChanged.connect(lambda: self.previewBtn.setText(self.nameBox.text()))

            #color drop down menu
            self.color = QtWidgets.QComboBox()
            self.color.addItem("Red")
            self.color.addItem("Green")
            self.color.addItem("Blue")
            self.color.addItem("Yellow")
            self.color.addItem("Orange")
            self.color.addItem("Purple")
            self.button_form.addRow("Color:", self.color)
            #update preview button color
            self.color.currentTextChanged.connect(lambda: self.previewBtn.setColor(self.color.currentText()))

            sizeLayout = QtWidgets.QHBoxLayout()
            widthLabel = QtWidgets.QLabel("Width")
            sizeLayout.addWidget(widthLabel)
            #width spinbox
            self.btnWidth = QtWidgets.QSpinBox(self, value = 50, minimum = 10, maximum =200)
            #update preview button width
            self.btnWidth.valueChanged.connect(lambda: self.previewBtn.resize(self.btnWidth.value(), self.btnHeight.value()))
            sizeLayout.addWidget(self.btnWidth)

            heightLabel = QtWidgets.QLabel("Height")
            sizeLayout.addWidget(heightLabel)
            #height spinbox
            self.btnHeight = QtWidgets.QSpinBox(self, value= 20, minimum = 10, maximum =200)
            #update preview button height
            self.btnHeight.valueChanged.connect(lambda: self.previewBtn.resize(self.btnWidth.value(), self.btnHeight.value()))
            sizeLayout.addWidget(self.btnHeight)

            self.details_layout.addLayout(sizeLayout)

            selectLabel = QtWidgets.QLabel("Current Selection:")
            self.details_layout.addWidget(selectLabel)

            self.scroll = QtWidgets.QScrollArea()             # Scroll Area which contains the widgets, set as the centralWidget
            self.widget = QtWidgets.QWidget()                 # Widget that contains the collection of Vertical Box
            self.vbox = QtWidgets.QVBoxLayout()               # The Vertical Box that contains the Horizontal Boxes of  labels and buttons

            sl = cmds.ls(sl = True)
            for obj in sl:
                checkbox = QtWidgets.QCheckBox(obj)
                checkbox.setChecked(True)
                checkbox.stateChanged.connect(lambda state, o=obj, c=checkbox: self.stateChanged(o, c))
                self.vbox.addWidget(checkbox)

            self.widget.setLayout(self.vbox)

            #Scroll Area Properties
            self.scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
            self.scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
            self.scroll.setWidgetResizable(True)
            self.scroll.setWidget(self.widget)

            self.details_layout.addWidget(self.scroll)

            #create new button button
            NewBtn = QtWidgets.QPushButton("New Button",self)
            NewBtn.clicked.connect(lambda: self.newConnection())
            self.details_layout.addWidget(NewBtn)

            #create new button button
            DelBtn = QtWidgets.QPushButton("Delete Buttons",self)
            DelBtn.clicked.connect(lambda: self.deleteBtns())
            self.details_layout.addWidget(DelBtn)

            self.details_layout.addSpacing(20)
            self.details_layout.addStretch()


            tab_form = QtWidgets.QFormLayout()
            #name box
            self.tabnameBox = QtWidgets.QLineEdit(text = "Body")
            tab_form.addRow("Name:", self.tabnameBox)
            self.details_layout.addLayout(tab_form)

            #new tab button
            createBtn = QtWidgets.QPushButton("New Tab")
            #createBtn.clicked.connect(lambda: self.tabwidget.addTab(imageTab(), self.tabnameBox.text()))
            createBtn.clicked.connect(lambda: self.tabwidget.newTab(self.tabnameBox.text()))
            self.details_layout.addWidget(createBtn)

            #rename tab button
            renameBtn = QtWidgets.QPushButton("Rename Tab")
            renameBtn.clicked.connect(self.tabwidget.renameTab)
            self.details_layout.addWidget(renameBtn)

            #button to choose image
            PictureBtn = QtWidgets.QPushButton("Choose Picture", self)
            PictureBtn.clicked.connect(self.tabwidget.setTabImage)
            self.details_layout.addWidget(PictureBtn)

            #button start matching mode
            self.MatchingModeBtn = QtWidgets.QPushButton("Matching Mode", self)
            self.MatchingModeBtn.clicked.connect(self.startMatchingMode)
            self.MatchingModeBtn.setCheckable(True)
            self.details_layout.addWidget(self.MatchingModeBtn)

            IKFKBtn = QtWidgets.QPushButton("IK to FK", self)
            IKFKBtn.clicked.connect(self.IK_FK_Controller.matchIkFkWin)
            self.details_layout.addWidget(IKFKBtn)

            FKIKBtn = QtWidgets.QPushButton("FK to IK", self)
            FKIKBtn.clicked.connect(self.IK_FK_Controller.matchFkIkWin)
            self.details_layout.addWidget(FKIKBtn)

            self.details_layout.addStretch()

            #create preview btn
            self.previewBtn = self.newConnection(btnParent=self.previewLabel)
            self.previewBtn.move((150/2)-10, (50/2)-10)

    def startMatchingMode(self):
        if(not self.MatchingModeBtn.isChecked()):
            logger.debug("end matching mode")
            self.IK_FK_Controller.turnOff()
        else:
            logger.debug("start matching mode")
            self.IK_FK_Controller.openSetupWindow()
            # self.matchingWindow = matchingSetupWindow.matchingSetupWindowUI()

    def stateChanged(self, obj, box):
        """
        deselects object when checkbox is unchecked
        :param obj: Object connected to checkbox
        :param box: checkbox
        :return: None
        """
        logger.debug("checkbox state changed")
        if(box.isChecked()==False):
            logger.debug("deselect: %s" % obj)
            cmds.select(obj, d=True) #deselect object
        else:
            logger.debug("%s is checked" % obj)

    def newConnection(self, btnParent = None):
        """
        create new button connected to current selection and add it to tab
        :param btnParent: tab to add button to
        :return: new draggable button
        """
        selected = cmds.ls(selection = True) #current selection

        if btnParent != None: #display button
            parent = btnParent
            selected = []
        else: #make parent current tab
            parent = tab = self.tabwidget.currentWidget()

        btnColor = self.color.currentText() #button color
        btnName = self.nameBox.text() #button name
        return self.newDragBtn(btnColor, selected, btnName, parent, self.btnWidth.value(), self.btnHeight.value(), self.tabwidget.currentWidget())

    def newDragBtn(self, color, selected, name, parent, width, height, tabIndex):
        """
        create new draggable button and add to parent
        :param color: color of button
        :param selected: list of objects of connected to button
        :param name: name of button
        :param parent: widget to add button to
        :param width: button width
        :param height: button height
        :param tabIndex: index of tab button is being added to
        :return: Draggable Button
        """
        btn = drag.DragButton(color, selected, self, name ) #create new draggable button
        btn.setParent(parent)
        btn.resize(width, height)
        btn.show() #show button
        logger.info("new button: %s" % name)

        #add to objects dictionary
        if selected != None:
            for i in selected:
                if(i in self.objects[tabIndex]):
                    self.objects[tabIndex][str(i)].append(btn) #add to array of buttons
                else:
                    self.objects[tabIndex][str(i)]=[btn] #create array of buttons
            logger.debug(self.objects)
        else:
            logger.error("nothing is being connected to button")

        return btn



class imageTab(QtWidgets.QWidget):
    def __init__(self, img = None, *args, **kwargs):
        super(imageTab,self).__init__(*args, **kwargs)
       #  if(img == None):
       #      file,types = QtWidgets.QFileDialog.getOpenFileName(self, 'Choose Image',
       # BASE_DIR,"Image files (*.jpg *.gif *.png)") #file dialog to choose image
       #      logger.debug(file)
       #      self.imageFile = file
       #  else:
        if (img ==None):
            logger.error("no image")
            self.imageFile = ""
        else:
            self.imageFile = img
        #set image
        self.image = QtWidgets.QLabel(self)
        self.image.setPixmap(QtGui.QPixmap(self.imageFile))

    def importImg(self):
        """
        opens file dialog for user to choose image. Sets tab's image
        :return: None
        """
        logger.info("import image "+ str(self))
        file,types = QtWidgets.QFileDialog.getOpenFileName(self, 'Choose Image',
   BASE_DIR,"Image files (*.jpg *.gif *.png)")
        logger.debug(file)
        self.imageFile = file
        self.image.setPixmap(QtGui.QPixmap(file))
        self.image.adjustSize()




class tabsWindow(QtWidgets.QTabWidget):
    """
    A class that creates a window with tabs
    Attributes
    ----------
    baseUI: pickerBaseUI
        reference to connected pickerBaseUI
    totalTabs: Int
        total number of tabs

    Methods
    ----------
    setTabImage()
        sets image for current tab
    newTab(name, image)
        Add new tab to picker with given name and image
    closeTab(index)
        closes tab at given index
    renameTab()
        renames current tab to be current text in name box
    updateTabBtns()
        called when tab is changed and updates button outlines of new current tab
    """
    def __init__(self, baseUI, *args, **kwargs):
        super(tabsWindow,self).__init__(tabsClosable = True, movable = True,*args, **kwargs)
        self.baseUI= baseUI
        self.totalTabs = 0 #number of tabs
        self.tabCloseRequested.connect(lambda index: self.closeTab(index)) #closes tab
        self.currentChanged.connect(lambda index: self.updateTabBtns()) #updates btns in new current window

    def renameTab(self):
        """
        renames current tab to be current text in name box
        :return: None
        """
        tabname = self.baseUI.tabnameBox.text() #new name text
        tabIndex = self.currentIndex() #index of current tab
        self.setTabText(tabIndex, tabname) #rename tab

    def closeTab(self, index):
        """
        closes given tab
        :param index: (int) index of tab to close
        :return: None
        """
        currTab = self.widget(index)
        logger.debug("trying to close tab: "+ str(index))
        logger.debug(self.baseUI.objects[currTab])
        logger.debug("total tabs: "+ str(self.totalTabs))
        self.baseUI.objects.pop(currTab) #remove tab from objects dictionary
        self.removeTab(index) #remove tab from widget
        self.totalTabs -=1 #decrease number of total tabs

    def setTabImage(self):
        #logger.debug("current index" + str(self.tabwidget.currentIndex()))
        self.currentWidget().importImg()

    def newTab(self, name, image =None):
        """
        Add new tab to picker with given name and image
        :param name: (str) name of tab
        :param image: (str) location of image in computer
        :return: new tab widget
        """
        newT = imageTab(image) #create widget
        self.addTab(newT, name) #adds tab to tab widget
        self.totalTabs +=1 #increase total tabs count
        self.baseUI.objects[newT]= {} #add to objects dictionary
        return newT

    def updateTabBtns(self):
        """
        called when tab is changed and updates button outlines of new current tab
        :return: None
        """
        index = self.currentIndex()
        try:
            children = self.widget(index).children()
        except:
            logger.debug("UpdateTabBtns: tab has no buttons")
        for c in children:
            if (isinstance(c,drag.DragButton)):
                c.updateNumSel() #update outline of button




