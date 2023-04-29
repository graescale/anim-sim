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
# VARIABLES
LAYER_NAME = 'Anim_Sim'
TARGETS = 'Targets'
ROOT_NAME = 'AnimSim'
ROOT_TYPE = 'compound'
NUM_CHILDREN = 6
NUM_ATTRIBUTES = {
            'fidelity': 'short',
            'Scale': 'long',
            'auto_roll': 'bool'
        }
STR_ATTRIBUTES = {
            'Name': 'string',
            'parent': 'string',
            'motion_plane': 'stringArray',
}
#*******************************************************************************
# UI
class AnimSim:
    def __init__(self):
        self.flyer = None
        self.target = ''
        self.target_group = TARGETS

        path_ui = CURRENT_PATH + "/" + TITLE + ".ui"
        self.wgAnimSim = QtCompat.loadUi(path_ui)

        #***********************************************************************
        # ICONS
        self.wgAnimSim.setWindowIcon(QtGui.QPixmap(IMG_PATH.format("helicopter-icon-21952")))
 
        #***********************************************************************
        # SIGNAL
        
        # SELECT
        self.wgAnimSim.cbxName.currentTextChanged.connect(self.cbxName_changed)
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
        
        #***********************************************************************
        # INITIALIZE
        h.create_hierarchy()
        self.update_selections()
        self.update_flyer_attrs()
        
    #***************************************************************************
    # PRESS
    def press_btnPgBuild(self):
        self.wgAnimSim.stackedWidget.setCurrentWidget(self.wgAnimSim.pgBuild)


    def press_btnPgAnchor(self):
        self.wgAnimSim.stackedWidget.setCurrentWidget(self.wgAnimSim.pgAnchor)


    def press_btnPgConnect(self):
        self.wgAnimSim.stackedWidget.setCurrentWidget(self.wgAnimSim.pgConnect)        


    def press_btnTarget(self):
        h.create_hierarchy()
        sel = cmds.ls(sl=True)[0]
        if cmds.objExists(sel + '_target'):
            self.wgAnimSim.lblStatus.setText("Target already exists.")
        elif len(cmds.ls(sl=True)) == 1:
            self.make_flyer(sel)
            self.target = self.flyer.Name + '_target'
            h.create_dag(self.target, self.target_group)
            self.update_selections()
            self.create_attributes()
        else:
            self.wgAnimSim.lblStatus.setText("Please choose a single object.") 


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
        self.flyer.set_anchor(self.flyer.motion_plane[0], self.flyer.motion_plane[1])


    def press_btnRemoveAllAnchor(self):
        self.flyer.remove_anchors()


    def press_btnBuild(self):
        self.update_flyer_attrs()
        if (self.flyer.fidelity % 2) == 0:
            self.wgAnimSim.lblStatus.setText('Fidelity value must be an odd number')
        else:
            target_name = self.flyer.Name + '_target'
            self.flyer.derive_rotation(self.flyer.motion_plane[0], self.flyer.motion_plane[1], 3)
            self.flyer.integrate_translation(self.flyer.motion_plane[0], self.flyer.motion_plane[1])
            self.write_parameters()


    def press_btnRebuild(self):
        self.flyer.Scale = self.wgAnimSim.sldScale.value()
        self.flyer.fidelity = self.wgAnimSim.sldFidelity.value()
        self.flyer.auto_roll = self.wgAnimSim.chkAutoRoll.isChecked()       
        self.flyer.anchor_rebuild(self.flyer.motion_plane[0], self.flyer.motion_plane[1])

    #***************************************************************************
    # PROCESS   
    def make_flyer(self, dagObject):
        if not self.flyer:
            self.flyer = Flyer(dagObject)
        elif self.flyer.Name != dagObject:
            self.flyer = Flyer(dagObject)
        else:
            print('%s already exists.' % self.flyer.Name)


    def update_flyer_attrs(self):
        print('|update_flyer_attrs|')
        if self.wgAnimSim.cbxName.currentText():
            current_sel = self.wgAnimSim.cbxName.currentText()
            if not self.flyer:
                self.make_flyer(current_sel)
            elif self.flyer.Name != current_sel:
                print('self.flyer did not match current selection.')
                self.make_flyer(current_sel)
            self.target = self.flyer.Name + '_target'
            self.flyer.motion_plane = list(str(self.wgAnimSim.cbxMotionPlane.currentText()))
            self.flyer.Scale = self.wgAnimSim.sldScale.value()
            self.flyer.fidelity = self.wgAnimSim.sldFidelity.value()
            self.flyer.auto_roll = self.wgAnimSim.chkAutoRoll.isChecked()
            self.flyer.layer_name = self.flyer.Name + LAYER_NAME

        else:
            print('Selection box is empty. Nothing to update.')


    def cbxName_changed(self):
        objects = cmds.listRelatives(TARGETS, children=True, fullPath=False)
        if objects:
            self.read_parameters(self.wgAnimSim.cbxName.currentText())


    def read_parameters(self, selection):
        """ Reads target attributes and writes to self properties.

        Args:
            target (str): target dag object with AnimSim attributes

        Returns:
            None
            """
        print('|read_parameters|')
        motion_plane_list = {
            '[\'X\', \'Z\']': 0,
            '[\'X\', \'Y\']': 1,
            '[\'Y\', \'Z\']': 2,
        }
        target = selection + '_target'
        self.wgAnimSim.cbxMotionPlane.setCurrentIndex(motion_plane_list[cmds.getAttr(target + '.motionPlane')])
        if target + '.parent':
            self.wgAnimSim.lblCurrentParent.setText(cmds.getAttr(target + '.parent'))
        self.wgAnimSim.sldScale.setValue(cmds.getAttr(target + '.Scale'))
        self.press_sldScale()
        self.wgAnimSim.sldFidelity.setValue(cmds.getAttr(target + '.fidelity'))
        self.press_sldFidelity()
        #self.wgAnimSim.chkAutoRoll.setCheckState(cmds.getAttr(self.target + '.auto_roll'))


    def write_parameters(self):
        """ Writes parameters to target attributes

        Args:
            None

        Returns:
            None
            """

        print('|write_parameters|')
        cmds.setAttr(self.target + '.Name', self.flyer.Name, type='string')
        if self.flyer.parent:
            cmds.setAttr(self.target + '.parent', self.flyer.parent, type='string')
        cmds.setAttr(self.target + '.motionPlane', self.flyer.motion_plane, type='string')
        cmds.setAttr(self.target + '.fidelity', self.flyer.fidelity)
        cmds.setAttr(self.target + '.Scale', self.flyer.Scale)
        cmds.setAttr(self.target + '.auto_roll', self.flyer.auto_roll)


    def update_selections(self):
        """ Updates the Selections combobox

        Args:
            None

        Returns:
            None
            """

        print('|update_selections|')
        objects = cmds.listRelatives(TARGETS, children=True, fullPath=False)
        self.wgAnimSim.cbxName.clear()
        if objects:
            for target in objects:
                self.wgAnimSim.cbxName.addItem(target.split('_')[0])
                count = self.wgAnimSim.cbxName.count()
                self.wgAnimSim.cbxName.setCurrentIndex(count - 1)


    def create_attributes(self):

        PARAMS = [
            {'Name': ['string', 'dt', self.flyer.Name]},
            {'parent': ['string', 'dt', self.flyer.parent]},
            {'motionPlane': ['string', 'dt', self.flyer.motion_plane]},
            {'fidelity': ['long', 'at', self.flyer.fidelity]},
            {'Scale': ['long', 'at', self.flyer.Scale]},
            {'auto_roll': ['bool', 'at', self.flyer.auto_roll]}
        ]
        cmds.addAttr(self.target, numberOfChildren=NUM_CHILDREN, longName=ROOT_NAME, attributeType=ROOT_TYPE)
        for dict in PARAMS:
            for key in dict:
                if dict[key][1] == 'at':
                    cmds.addAttr(self.target, longName=key, attributeType=dict[key][0], parent=ROOT_NAME)
                if dict[key][1] == 'dt':
                    cmds.addAttr(self.target, longName=key, dataType=dict[key][0], parent=ROOT_NAME)

    #def initialize(self):
        # Populate the selection combo box
        # If any
 
#*******************************************************************
# START
#if __name__ == "__main__":
anim_simUI = AnimSim()
