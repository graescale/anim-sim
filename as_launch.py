#*******************************************************************************
# content = Launches UI for Anim Sim.
#
# version      = 1.0.0
# date         = 2023-05-13
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
        self.selection = ''
        self.target = ''
        self.target_group = TARGETS
        self.flyers = {}

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
        self.selection = cmds.ls(sl=True)[0]
        if cmds.objExists(self.selection + '_target'):
            self.wgAnimSim.lblStatus.setText("Target already exists.")
        elif len(cmds.ls(sl=True)) == 1:
            self.make_flyer(self.selection)
            self.target = self.flyers[self.selection].name + '_target'
            h.create_dag(self.target, self.target_group)
            self.update_selections()
            self.create_attributes()
            self.wgAnimSim.lblCurrentParent.setText('(optional)')
            self.wgAnimSim.lblStatus.setText('Added target: %s' % self.selection)
        else:
            self.wgAnimSim.lblStatus.setText("Please choose a single object.") 


    def press_btnParent(self):
        if len(cmds.ls(sl=True)) == 1:
            parent = cmds.ls(sl=True)[0]
            self.flyers[self.selection].parent = parent
            self.wgAnimSim.lblCurrentParent.setText(parent)
            self.wgAnimSim.lblStatus.setText('Added parent: %s' % parent)
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
        current_time = self.flyers[self.selection].set_anchor(self.flyers[self.selection].motion_plane[0],self.flyers[self.selection].motion_plane[1])
        if current_time:
            self.wgAnimSim.lblStatus.setText('Added anchor at frame: %s' % current_time)
        else:
            self.wgAnimSim.lblStatus.setText('anchor removed')

    def press_btnRemoveAllAnchor(self):
        self.flyers[self.selection].remove_anchors()


    def press_btnBuild(self):
        self.update_flyer_attrs()
        if (self.flyers[self.selection].fidelity % 2) == 0:
            self.wgAnimSim.lblStatus.setText('Fidelity value must be an odd number')
        else:
            target_name = self.flyers[self.selection].name + '_target'
            self.flyers[self.selection].derive_rotation(self.flyers[self.selection].motion_plane[0], self.flyers[self.selection].motion_plane[1], 3)
            self.flyers[self.selection].integrate_translation(self.flyers[self.selection].motion_plane[0], self.flyers[self.selection].motion_plane[1])
            self.write_parameters()
            self.wgAnimSim.lblStatus.setText('Layer created: %s' % self.flyers[self.selection].layer_name)


    def press_btnRebuild(self):
        self.flyers[self.selection].Scale = self.wgAnimSim.sldScale.value()
        self.flyers[self.selection].fidelity = self.wgAnimSim.sldFidelity.value()
        self.flyers[self.selection].auto_roll = self.wgAnimSim.chkAutoRoll.isChecked()       
        self.flyers[self.selection].anchors_rebuild(self.flyers[self.selection].motion_plane[0], self.flyers[self.selection].motion_plane[1])

    #***************************************************************************
    # PROCESS   
    def make_flyer(self, dagObject):
        print('|make_flyer|')
        print('dagObject is %s' % dagObject)
        self.flyers[dagObject] = Flyer(dagObject)
        
        #setattr(self, 'foo', Flyer(dagObject))
        # if not self.flyer:
        #     self.flyer = Flyer(dagObject)
        # elif self.flyer.name != dagObject:
        #     self.flyer = Flyer(dagObject)
        # else:
        #     print('%s already exists.' % self.flyer.name)


    def update_flyer_attrs(self):
        """ Copies UI values to instance attributes.

        Args:
            None

        Returns:
            None
            """     

        print('|update_flyer_attrs|')
        if self.wgAnimSim.cbxName.currentText():
            self.selection = self.wgAnimSim.cbxName.currentText()
            try:
                self.flyers[self.selection]
            except:
                self.make_flyer(self.selection)
            #elif self.flyer.name != current_sel:
            #    print('self.flyer did not match current selection.')
            #    self.make_flyer(current_sel)
            self.target = self.flyers[self.selection].name + '_target'
            self.flyers[self.selection].motion_plane = list(str(self.wgAnimSim.cbxMotionPlane.currentText()))
            self.flyers[self.selection].Scale = self.wgAnimSim.sldScale.value()
            self.flyers[self.selection].fidelity = self.wgAnimSim.sldFidelity.value()
            self.flyers[self.selection].auto_roll = self.wgAnimSim.chkAutoRoll.isChecked()
            self.flyers[self.selection].layer_name =  self.flyers[self.selection].name + '_' + LAYER_NAME

        else:
            print('Selection box is empty. Nothing to update.')


    def cbxName_changed(self):
        objects = cmds.listRelatives(TARGETS, children=True, fullPath=False)
        if objects:
            self.selection = self.wgAnimSim.cbxName.currentText()
            self.read_parameters(self.wgAnimSim.cbxName.currentText())


    def read_parameters(self, selection):
        """ Reads DAG object attributes and writes to UI fields.

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
        cmds.setAttr(self.target + '.Name', self.flyers[self.selection].name, type='string')
        if self.flyers[self.selection].parent:
            cmds.setAttr(self.target + '.parent', self.flyers[self.selection].parent, type='string')
        cmds.setAttr(self.target + '.motionPlane', self.flyers[self.selection].motion_plane, type='string')
        cmds.setAttr(self.target + '.fidelity', self.flyers[self.selection].fidelity)
        cmds.setAttr(self.target + '.Scale', self.flyers[self.selection].Scale)
        cmds.setAttr(self.target + '.auto_roll', self.flyers[self.selection].auto_roll)


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
                target_tmp = target.split('_')
                target_tmp.pop()
                self.wgAnimSim.cbxName.addItem(target_tmp[0])
                #self.wgAnimSim.cbxName.addItem(target.split('_')[0])
                count = self.wgAnimSim.cbxName.count()
                self.wgAnimSim.cbxName.setCurrentIndex(count - 1)
        


    def create_attributes(self):

        PARAMS = [
            {'Name': ['string', 'dt', self.flyers[self.selection].name]},
            {'parent': ['string', 'dt', self.flyers[self.selection].parent]},
            {'motionPlane': ['string', 'dt', self.flyers[self.selection].motion_plane]},
            {'fidelity': ['long', 'at', self.flyers[self.selection].fidelity]},
            {'Scale': ['long', 'at', self.flyers[self.selection].Scale]},
            {'auto_roll': ['bool', 'at', self.flyers[self.selection].auto_roll]}
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
