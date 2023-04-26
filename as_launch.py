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
        objects = cmds.listRelatives('Targets', children=True, fullPath=True)
        print('objects are:')
        print(objects)
        self.wgAnimSim.cbxName.clear()
        for target in objects:
            print('target is:')
            print(target)
            self.wgAnimSim.cbxName.addItem(self.flyer.Name)
        #self.wgAnimSim.cbxName.addItems(objects)

    def press_btnPgBuild(self):
        self.wgAnimSim.stackedWidget.setCurrentWidget(self.wgAnimSim.pgBuild)

    def press_btnPgAnchor(self):
        self.wgAnimSim.stackedWidget.setCurrentWidget(self.wgAnimSim.pgAnchor)

    def press_btnPgConnect(self):
        self.wgAnimSim.stackedWidget.setCurrentWidget(self.wgAnimSim.pgConnect)        

    def press_btnTarget(self):
        sel = cmds.ls(sl=True)[0]
        if cmds.objExists(sel + '_target'):
            self.wgAnimSim.lblStatus.setText("Target already exists.")
        elif len(cmds.ls(sl=True)) == 1:
            self.flyer = Flyer(sel)
            self.target = self.flyer.Name + '_target'
            h.create_hierarchy()
            h.create_dag(self.target, self.target_group)
            self.update_selections()
            self.init_attributes()
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
        self.flyer.motion_plane = list(str(self.wgAnimSim.cbxMotionPlane.currentText()))
        self.flyer.Scale = self.wgAnimSim.sldScale.value()
        self.flyer.fidelity = self.wgAnimSim.sldFidelity.value()
        self.flyer.auto_roll = self.wgAnimSim.chkAutoRoll.isChecked()
        if (self.flyer.fidelity % 2) == 0:
            self.wgAnimSim.lblStatus.setText('Fidelity value must be an odd number')
        else:
            target_name = self.flyer.Name + '_target'

            self.flyer.derive_rotation(self.flyer.motion_plane[0], self.flyer.motion_plane[1], 3)
            self.flyer.integrate_translation(self.flyer.motion_plane[0], self.flyer.motion_plane[1])
            print(self.target)
            self.write_parameters()

    def init_attributes(self):

        PARAMS = [
            {'Name': ['string', 'dt', self.flyer.Name]},
            {'parent': ['string', 'dt', self.flyer.parent]},
            {'motion_plane': ['string', 'dt', self.flyer.motion_plane]},
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

    def press_btnRebuild(self):
        self.flyer.Scale = self.wgAnimSim.sldScale.value()
        self.flyer.fidelity = self.wgAnimSim.sldFidelity.value()
        self.flyer.auto_roll = self.wgAnimSim.chkAutoRoll.isChecked()       
        self.flyer.anchor_rebuild(self.flyer.motion_plane[0], self.flyer.motion_plane[1])

    def write_parameters(self):
        """ Writes parameters to target attributes

        Args:
            None

        Returns:
            None
            """
        print('|write_parameters')
        cmds.setAttr(self.target + '.Name', self.flyer.Name, type='string')
        if self.flyer.parent:
            cmds.setAttr(self.target + '.parent', self.flyer.parent, type='string')
        cmds.setAttr(self.target + '.motion_plane', self.flyer.motion_plane, type='string')
        cmds.setAttr(self.target + '.fidelity', self.flyer.fidelity)
        cmds.setAttr(self.target + '.Scale', self.flyer.Scale)
        cmds.setAttr(self.target + '.auto_roll', self.flyer.auto_roll)

        #attr_type = cmds.attributeQuery(attr, node=target, attributeType=True)
        #cmds.setAttr(target + '.motion_plane', self.flyer.motion_plane, )
        # attrs = cmds.attributeQuery('AnimSim', node=target, lc=True)
        # for attr in attrs:
        #     attr_path = target + '.' + attr
        #     attr_value = self.flyer + '.' + attr
        #     attr_type = cmds.attributeQuery(attr, node=target, attributeType=True)
        #     cmds.setAttr(attr_path, attr_value, attr_type)

    #def initialize(self):
        # Populate the selection combo box
        # If any
 
#*******************************************************************
# START
#if __name__ == "__main__":
anim_simUI = AnimSim()
