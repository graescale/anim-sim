#*******************************************************************************
# content = Launches UI for Anim Sim.
#
# version      = 1.0.0
# date         = 2022-01-26
# how to       => import as_launch
#
# dependencies = Maya, Qt, anim_sim
#
# author = Grae Revell <grae.revell@gmail.com>
#*******************************************************************************

# Qt
from Qt import QtWidgets, QtGui, QtCore, QtCompat
from anim_sim import *

#*******************************************************************************
# UI
class AnimSim:
    def __init__(self):

        self.flyer = None
        
        path_ui = CURRENT_PATH + "/" + TITLE + ".ui"
        self.wgAnimSim = QtCompat.loadUi(path_ui)
        
        # ICONS
        self.wgAnimSim.setWindowIcon(QtGui.QPixmap(IMG_PATH.format("helicopter-icon-21952")))
 
        #***********************************************************************
        # SIGNAL
        
        # SELECT
        self.wgAnimSim.btnTarget.clicked.connect(self.press_btnTarget)
        self.wgAnimSim.btnParent.clicked.connect(self.press_btnParent)

        # PAGE SELECT
        self.wgAnimSim.btnPgBuild.clicked.connect(self.press_btnPgBuild)
        self.wgAnimSim.btnPgAnchor.clicked.connect(self.press_btnPgAnchor)
        self.wgAnimSim.btnPgConnect.clicked.connect(self.press_btnPgConnect)
        
        # PARAMETERS

        self.wgAnimSim.sldScale.valueChanged.connect(self.press_sldScale)
        self.wgAnimSim.sldFidelity.valueChanged.connect(self.press_sldFidelity)

        # CONNECTIONS
        #self.wgAnimSim.wgConnectInputs.currentTextChanged.connect(self.wgConnections)
        self.wgAnimSim.btnAddItem.clicked.connect(self.press_btn_AddItem)

        # ANCHORS
        self.wgAnimSim.btnAddRemoveAnchor.clicked.connect(self.press_btnAddRemoveAnchor)
        self.wgAnimSim.btnRemoveAllAnchor.clicked.connect(self.press_btnRemoveAllAnchor)
        self.wgAnimSim.btnRebuild.clicked.connect(self.press_btnRebuild)

        # SIM
        self.wgAnimSim.btnBuild.clicked.connect(self.press_btnBuild)

        
        self.wgAnimSim.show()

    #***************************************************************************
    # PRESS

    def update_selections(self):
        objects = cmds.listRelatives(TARGETS, children=True, fullPath=True)
        #clear the combo list
        self.wgAnimSim.cbxName.clear()
        self.wgAnimSim.cbxName.addItems(objects)
        #add objects to the combo list

    def press_btnPgBuild(self):
        self.wgAnimSim.stackedWidget.setCurrentWidget(self.wgAnimSim.pgBuild)

    def press_btnPgAnchor(self):
        self.wgAnimSim.stackedWidget.setCurrentWidget(self.wgAnimSim.pgAnchor)

    def press_btnPgConnect(self):
        self.wgAnimSim.stackedWidget.setCurrentWidget(self.wgAnimSim.pgConnect)        

    def press_btnTarget(self):
        if len(cmds.ls(sl=True)) == 1:
            target = cmds.ls( sl=True )[0]
            self.flyer = Flyer(target)
            self.flyer.create_hierarchy()
            self.flyer.create_dag(target, TARGETS)
            #self.wgAnimSim.cbxName.addItem(target)
            #self.wgAnimSim.lblCurrentTarget.setText(target)
        #else:
        #    self.wgAnimSim.lblCurrentTarget.setText("Please choose a single object.") 

    def press_btnParent(self):
        if len(cmds.ls(sl=True)) == 1:
            parent = cmds.ls(sl=True)[0]
            self.flyer.parent = parent
            self.wgAnimSim.lblCurrentParent.setText(parent)
        else:
            self.wgAnimSim.lblCurrentParent.setText("Please choose a single object.")

    def press_sldScale(self):
        self.wgAnimSim.lblScale.setText(str(self.wgAnimSim.sldScale.value()))

    def press_sldFidelity(self):
        self.wgAnimSim.lblFidelity.setText(str(self.wgAnimSim.sldFidelity.value()))

    #def wgConnections(self):
        #self.wgAnimSim.lblCurrentItem.setText(str(self.wgAnimSim.wgConnectInputs.currentItem().text()))

    def press_btn_AddItem(self):
        if len(cmds.ls(sl=True)) >= 1:
            sel_objects = cmds.ls(sl=True)
        print('sel_objects is:')
        print(sel_objects)
        #for obj in sel_objects:
        self.wgAnimSim.wgConnections.addItems(sel_objects)

    def press_btnAddRemoveAnchor(self):
        plane = list(str(self.wgAnimSim.cbxMotionPlane.currentText()))
        self.flyer.set_anchor(plane[0], plane[1])

    def press_btnRemoveAllAnchor(self):
        self.flyer.remove_anchors()

    def press_btnBuild(self):
        plane = list(str(self.wgAnimSim.cbxMotionPlane.currentText()))
        self.flyer.scale = self.wgAnimSim.sldScale.value()
        self.flyer.fidelity = self.wgAnimSim.sldFidelity.value()
        self.flyer.auto_roll = self.wgAnimSim.chkAutoRoll.isChecked()

        if (self.flyer.fidelity % 2) == 0:
            print('fidelity value must be an odd number')
        else:
            self.flyer.derive_rotation(plane[0], plane[1], 3)
            self.flyer.integrate_translation(plane[0], plane[1])
    
    def press_btnRebuild(self):
        plane = list(str(self.wgAnimSim.cbxMotionPlane.currentText()))
        self.flyer.scale = self.wgAnimSim.sldScale.value()
        self.flyer.fidelity = self.wgAnimSim.sldFidelity.value()
        self.flyer.auto_roll = self.wgAnimSim.chkAutoRoll.isChecked()       
        self.flyer.anchor_rebuild(plane[0], plane[1])

    # def press_btnRotation(self):
    #     plane = list(str(self.wgAnimSim.cbxMotionPlane.currentText()))
    #     self.flyer.scale = self.wgAnimSim.sldScale.value()
    #     self.flyer.fidelity = self.wgAnimSim.sldFidelity.value()
    #     self.flyer.auto_roll = self.wgAnimSim.chkAutoRoll.isChecked()

    #     if (self.flyer.fidelity % 2) == 0:
    #         print('fidelity value must be an odd number')
    #     else:
    #         self.flyer.derive_rotation(plane[0], plane[1], 3)

    # def press_btnTranslation(self):
    #     plane = list(str(self.wgAnimSim.cbxMotionPlane.currentText()))
    #     self.flyer.scale = self.wgAnimSim.sldScale.value()
    #     self.flyer.autoRoll = self.wgAnimSim.chkAutoRoll.isChecked()
    #     self.flyer.integrate_translation(plane[0], plane[1])         
 
#*******************************************************************
# START
#if __name__ == "__main__":
anim_simUI = AnimSim()

