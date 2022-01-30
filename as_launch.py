#*******************************************************************************
# content = Launches UI for Anim Sim.
#
# version      = 1.0.0
# date         = 2022-01-26
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
        #self.scale = None
        #self.fidelity  = None
        #self.autoPrePost = 1
        self.flyer = None
        
        path_ui = CURRENT_PATH + "/" + TITLE + ".ui"
        self.wgAnimSim = QtCompat.loadUi(path_ui)
        
        # ICONS
        self.wgAnimSim.setWindowIcon(QtGui.QPixmap(IMG_PATH.format("helicopter-icon-21952")))
        self.wgAnimSim.lblRotDownArrow.setPixmap(QtGui.QPixmap(IMG_PATH.format("double_down_arrow_icon")))
        self.wgAnimSim.lblTransDownArrow.setPixmap(QtGui.QPixmap(IMG_PATH.format("double_down_arrow_icon")))

        #***********************************************************************
        # SIGNAL
        
        # SELECT
        self.wgAnimSim.btnTarget.clicked.connect(self.press_btnTarget)
        self.wgAnimSim.btnParent.clicked.connect(self.press_btnParent)
        
        # PARAMETERS
        #self.wgAnimSim.cbxMotionPlane.currentIndexChanged.connect(self.press_cbxMotionPlane)
        self.wgAnimSim.sldScale.valueChanged.connect(self.press_sldScale)
        self.wgAnimSim.sldFidelity.valueChanged.connect(self.press_sldFidelity)

        # SYNC
        self.wgAnimSim.btnRotation.clicked.connect(self.press_btnRotation)
        self.wgAnimSim.btnTranslation.clicked.connect(self.press_btnTranslation)
        
        self.wgAnimSim.show()

    #***************************************************************************
    # PRESS

    def press_btnTarget(self):
        if len(cmds.ls(sl=True)) == 1:
            target = cmds.ls( sl=True )[0]
            self.flyer = Flyer(target)
            self.wgAnimSim.lblCurrentTarget.setText(target)
        else:
            self.wgAnimSim.lblCurrentTarget.setText("Please choose a single object.") 

    def press_btnParent(self):
        if len(cmds.ls(sl=True)) == 1:
            parent = cmds.ls(sl=True)[0]
            self.flyer.parent = parent
            self.wgAnimSim.lblCurrentParent.setText(parent)  
        else:
            self.wgAnimSim.lblCurrentParent.setText("Please choose a single object.")
 
    #def press_cbxMotionPlane(self):
    #    self.wgAnimSim.lblCurrentTarget.setText("cbxMotionPlane changed")

    def press_sldScale(self):
        self.wgAnimSim.lblScale.setText(str(self.wgAnimSim.sldScale.value()))

    def press_sldFidelity(self):
        self.wgAnimSim.lblFidelity.setText(str(self.wgAnimSim.sldFidelity.value()))

    def press_btnRotation(self):
        plane = list(str(self.wgAnimSim.cbxMotionPlane.currentText()))
        self.flyer.scale = self.wgAnimSim.sldScale.value()
        self.flyer.fidelity = self.wgAnimSim.sldFidelity.value()
        self.flyer.autoRoll = self.wgAnimSim.chkAutoRoll.isChecked()

        if (self.flyer.fidelity % 2) == 0:
            print('fidelity value must be an odd number')
        else:
            self.flyer.derive_rotation(plane[0], plane[1], 3)

    def press_btnTranslation(self):
        print('|integrate_translation_callback|')
        plane = list(str(self.wgAnimSim.cbxMotionPlane.currectText()))
        self.flyer.scale = self.wgAnimSim.sldScale.value()
        self.flyer.autoRoll = self.wgAnimSim.chkAutoRoll.isChecked()
        self.flyer.integrate_translation(plane[0], plane[1])         
 
#*******************************************************************
# START
if __name__ == "__main__":
    anim_simUI = AnimSim()

