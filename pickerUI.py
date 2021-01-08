import maya.cmds as cmds
from PySide2 import QtWidgets, QtCore, QtGui
from maya import OpenMayaUI as omui
from shiboken2 import wrapInstance
import pymel.core as pm
import os
import json

from picker import dragButton as drag
reload(drag)

# Where is this script?
SCRIPT_LOC = os.path.split(__file__)[0]

def getMayaMainWindow():
    """
    :return: maya main window as a python object
    """
    win = omui.MQtUtil_mainWindow()
    ptr = wrapInstance(long(win), QtWidgets.QMainWindow)
    return ptr

#TODO: save and load
    #save width and height
    #error if image doesn't exist
    #dont delete previous when loading
    #save pic in same file
    #or save as zip
    #add environmental parameter
#TODO: channel boxes
#TODO: preview of button
#TODO: delete buttons
#TODO: show selection when creating button
    #ability to deselect
#TODO: drag select
#TODO: make dockable
#TODO: tabs
    #center image
    #when no tabs have a create tab msg


class pickerBaseUI(QtWidgets.QDialog):
    def __init__(self, parent = getMayaMainWindow()):
        #ensure not more than one at the same time
        try:
            pm.deleteUI('PickerUI')
            print("delete UI")
        except:
            print("no prev UI")

        super(pickerBaseUI, self).__init__(parent)

        self.setWindowTitle("Picker UI") #set title
        self.setMinimumWidth(400) #set width
        self.setObjectName("PickerUI")
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        #get rid of help button on window
        self.setWindowFlags(self.windowFlags()^QtCore.Qt.WindowContextHelpButtonHint)

        self.objects = {} #dictionary of objects in scene and what buttons they are connected to. They are separated by each tab. key- object name, value- array of buttons
        self.buttons = [] #list of references to buttons according to tab
        self.previousSelection = cmds.ls(sl=True)
        self.totalTabs = 0 #numbere of tabs

        self.buildUI()
        self.sj = cmds.scriptJob(event= ["SelectionChanged", lambda: self.updateBtnSelect()], parent = "PickerUI")
        self.show()

    def keyPressEvent(self, event):
        """
        deletes selected buttons when backspace or delete key is pressed in edit mode
        :param event:
        :return: None
        """
        if (event.key() == QtCore.Qt.Key_Backspace or event.key() == QtCore.Qt.Key_Delete):
            self.deleteBtns()

    def deleteBtns(self):
        if self.edit:
            print("Deleting Selected Buttons")
            currTab = self.tabwidget.currentWidget()
            children =currTab.children()

            for btn in children: #for each button in the current tab
                if (isinstance(btn,drag.DragButton)) and btn.selected == True: #check if selected
                    for k in self.objects[currTab].keys(): #remove from objects dictionary
                        if btn in self.objects[currTab][k]:
                            self.objects[currTab][k].remove(btn)
                        if len(self.objects[currTab][k]) ==0:
                            del(self.objects[currTab][k])
                    print(self.objects)
                    print("deleting: "+ str(btn))
                    btn.deleteLater()

    def updateBtnSelect(self):
        """
        updates outline of buttons if objects they are connected to have been selected or deselected
        :return: None
        """
        print("update buttons")
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
            print("added "+a)
            if a in self.objects[currTab]:
                for btn in self.objects[currTab][a]:
                    btn.numSel+=1 #add one to the number of objects selected in the list of connections for the button
                    if btn.numSel == len(btn.connection): #change outline if the number selected is equal to the total number of objects connected to the button
                        btn.selected = True
                        btn.setChecked(True)

        for m in minus:
            print("minus "+m)
            if m in self.objects[currTab]:
                for btn in self.objects[currTab][m]:
                    btn.numSel-=1 #subtract one to the number of objects selected in the list of connections for the button
                    print(btn.numSel)
                    if btn.numSel < len(btn.connection): #change outline if the number selected is less than the total number of objects connected to the button
                        btn.selected = False
                        btn.setChecked(False)

        self.previousSelection= currSelection


        if(self.edit ==True):
            print("checkboxes")
            #updates the list of checkboxes
            self.clearLayout(self.vbox) #clear list
            sl = cmds.ls(sl = True) #get selection
            for obj in sl: #add a checkbox for each object in selection
                checkbox = QtWidgets.QCheckBox(obj)
                checkbox.setChecked(True)
                checkbox.stateChanged.connect(lambda state, o=obj, c=checkbox: self.state_changed(o, c))
                self.vbox.addWidget(checkbox) #add to layout

    def updateTabBtns(self):
        """
        called when tab is changed and updates button outlines of new current tab
        :return: None
        """
        index = self.tabwidget.currentIndex()
        children = self.tabwidget.widget(index).children()
        for c in children:
            if (isinstance(c,drag.DragButton)):
                c.updateNumSel() #update outline of button

    def buildUI(self):
        outside = QtWidgets.QVBoxLayout(self)
        self.columns = QtWidgets.QHBoxLayout(self)
        self.layout = QtWidgets.QVBoxLayout(self)
        self.details_layout = QtWidgets.QVBoxLayout(self)
        self.restriction = QtWidgets.QWidget()
        self.restriction.setLayout(self.details_layout)
        self.restriction.setFixedWidth(200)
        self.columns.addLayout(self.layout)
        self.columns.addWidget(self.restriction)
        outside.addLayout(self.columns)

        #tab widget
        self.tabwidget = QtWidgets.QTabWidget(tabsClosable = True, movable = True)
        self.layout.addWidget(self.tabwidget)
        self.tabwidget.tabCloseRequested.connect(lambda index: self.closeTab(index))
        self.tabwidget.currentChanged.connect(lambda index: self.updateTabBtns())
        #add base tab
        #self.tabwidget.addTab(imageTab(img = ""), "Untitled")
        self.newTab(name ="Untitled", image = "")

        #add second column with details
        #start with showing edit tools
        self.updateDetails("edit")
        self.edit = True

        #edit button
        layout_btns = QtWidgets.QHBoxLayout()
        self.editBtn = QtWidgets.QPushButton("Stop Editing")
        self.editBtn.clicked.connect(self.editChange)
        layout_btns.addWidget(self.editBtn)

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
        print("Saving File!!!!!!!!!!!!!!")
        for i in range(self.tabwidget.count()):
            #add information about each tab
            tab = self.tabwidget.tabText(i)
            print(tab)
            children =self.tabwidget.widget(i).children()
            data['tabs']["tab %d" % i] = {"name": str(tab), "buttons": {}, "image":self.tabwidget.widget(i).imageFile }
            btnNum = 1
            for w in children: #add information about each button in tab
                if (isinstance(w,drag.DragButton)):
                    info = {"name": w.text(), "color": w.color, "x":w.x(), "y":w.y(), "connections": w.connection, "width": w.width(), "height": w.height()}
                    print(info)
                    print(w.connection)
                    #add new button to list
                    data['tabs']["tab %d" % i]["buttons"]["button %d" % btnNum] = info
                    btnNum+=1
        outData = json.dumps(data) #create into json
        print(outData)
        filename, type = QtWidgets.QFileDialog.getSaveFileName(self, 'Save Template','c:\\',"(*.json)") #open file dialog to chose location and name
        print("saving as: " +filename)
        with open(filename, "w") as f:
            json.dump(data, f, indent = 4) #save json in location

    def load(self):
        """
        Opens File Dialog and loads chosen template (json) by adding tabs specified in json
        :return: None
        """
        print("Loading File!!!!!!!!!!!")
        file,types = QtWidgets.QFileDialog.getOpenFileName(self, 'Open file',
   'c:\\',"Template Files(*.json)") #creates file dialog
        with open(file) as template_json:
            data = json.load(template_json) #json template data
            print(data)
            for tab in data["tabs"]:
                #create new tab for each specified in data
                tabInfo = data["tabs"][tab]
                newTab =self.newTab(tabInfo["name"], image = tabInfo["image"]) #make tab
                for btn in tabInfo["buttons"]: #make buttons in each tab
                    btnInfo = tabInfo["buttons"][btn]
                    newbtn = self.newDragBtn(btnInfo["color"], btnInfo["connections"],btnInfo["name"], newTab, btnInfo["width"], btnInfo["height"],newTab)
                    newbtn.move(btnInfo["x"],btnInfo["y"]) #move button to location on screen


    def editChange(self):
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

        print("update details")
        if(type == "normal"):
            print("type normal")
            self.restriction.setFixedWidth(0) #make column disapear

        if(type =="edit"):
            print("type edit")
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
                checkbox.stateChanged.connect(lambda state, o=obj, c=checkbox: self.state_changed(o, c))
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
            createBtn.clicked.connect(lambda: self.newTab(self.tabnameBox.text()))
            self.details_layout.addWidget(createBtn)

            #rename tab button
            renameBtn = QtWidgets.QPushButton("Rename Tab")
            renameBtn.clicked.connect(self.renameTab)
            self.details_layout.addWidget(renameBtn)

            #button to choose image
            PictureBtn = QtWidgets.QPushButton("Choose Picture", self)
            PictureBtn.clicked.connect(self.tabwidget.currentWidget().importImg)
            self.details_layout.addWidget(PictureBtn)
            self.details_layout.addStretch()

            #create preview btn
            self.previewBtn = self.newConnection(btnParent=self.previewLabel)
            self.previewBtn.move((150/2)-10, (50/2)-10)

    def newTab(self, name, image =None):
        """
        Add new tab to picker with given name and image
        :param name: (str) name of tab
        :param image: (str) location of image in computer
        :return: new tab widget
        """
        newT = imageTab(image) #create widget
        self.tabwidget.addTab(newT, name) #adds tab to tab widget
        self.totalTabs +=1 #increase total tabs count
        self.objects[newT]= {} #add to objects dictionary
        return newT

    def closeTab(self, index):
        """
        closes given tab
        :param index: (int) index of tab to close
        :return: None
        """
        currTab = self.tabwidget.widget(index)
        print("trying to close tab: "+ str(index))
        print(self.objects[currTab])
        print("total tabs: "+ str(self.totalTabs))
        self.objects.pop(currTab) #remove tab from objects dictionary
        self.tabwidget.removeTab(index) #remove tab from widget
        self.totalTabs -=1 #decrease number of total tabs


    def renameTab(self):
        """
        renames current tab to be current text in name box
        :return: None
        """
        tabname = self.tabnameBox.text() #new name text
        tabIndex = self.tabwidget.currentIndex() #index of current tab
        self.tabwidget.setTabText(tabIndex, tabname) #rename tab

    def state_changed(self, obj, box):
        """
        deselects object when checkbox is unchecked
        :param obj: Object connected to checkbox
        :param box: checkbox
        :return: None
        """
        if(box.isChecked()==False):
            print("deselect: %s" % obj)
            cmds.select(obj, d=True) #deselect object
        else:
            print("%s is checked" % obj)

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
        btn = drag.DragButton(color, selected, name ) #create new draggable button
        btn.setParent(parent)
        btn.resize(width, height)
        btn.show() #show button
        print("new button: %s" % name)

        #add to objects dictionary
        if selected != None:
            for i in selected:
                if(i in self.objects[tabIndex]):
                    self.objects[tabIndex][str(i)].append(btn) #add to array of buttons
                else:
                    self.objects[tabIndex][str(i)]=[btn] #create array of buttons
            print(self.objects)
        else:
            print("nothing is being connected to button")

        return btn



class imageTab(QtWidgets.QWidget):
    def __init__(self, img = None, *args, **kwargs):
        super(imageTab,self).__init__(*args, **kwargs)
        if(img == None):
            file,types = QtWidgets.QFileDialog.getOpenFileName(self, 'Choose Image',
       'c:\\',"Image files (*.jpg *.gif *.png)") #file dialog to choose image
            print(file)
            self.imageFile = file
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
        file,types = QtWidgets.QFileDialog.getOpenFileName(self, 'Choose Image',
   'c:\\',"Image files (*.jpg *.gif *.png)")
        print(file)
        self.imageFile = file
        self.image.setPixmap(QtGui.QPixmap(file))
        self.image.adjustSize()





