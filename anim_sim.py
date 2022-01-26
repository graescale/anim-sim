#*******************************************************************************
# content = Simulates hovering motion.
#
# version      = 0.4.1
# date         = 2021-12-19
# how to       => anim_sim = animSim()
#
# dependencies = Maya
#
# to dos = Restructure workflow, simplify code
# author = Grae Revell <grae.revell@gmail.com>
#*******************************************************************************
import os
import sys

# Qt
from Qt import QtWidgets, QtGui, QtCore, QtCompat
from helpers import *

import pymel.core as pm
import maya.cmds as cmds

#*******************************************************************************
# VARIABLES

ROTATION_LAYER = 'auto_rotation_layer'
TRANSLATION_LAYER = 'auto_translation_layer'

TITLE = os.path.splitext(os.path.basename(__file__))[0]
CURRENT_PATH = os.path.dirname(__file__)
IMG_PATH = CURRENT_PATH + "/img/{}.png"

#*******************************************************************************
# CLASS
#
# The main reason I used a class here is becuase the user may need to run the
# script on multiple Maya objects. By creating a class I can store and access
# all the relevant data in a single object and create as many instances of it as
# necessary.
# 

class Flyer:
    def __init__(self, name):
        self.name = name
        self.start_frame = ''
        self.end_frame = ''
        self.key_frames = []
        self.pos_axis_1 = []
        self.pos_axis_2 = []
        self.start_pos_axis_1 = 0
        self.start_pos_axis_2 = 0
        self.accel_axis_1 = []
        self.accel_axis_2 = []
        self.rot_axis_1 = []
        self.rot_axis_2 = []
        self.rot_axis_1_dict = {}
        self.rot_axis_2_dict = {}
        self.rot_layer_name = ROTATION_LAYER
        self.trans_layer_name = TRANSLATION_LAYER
        self.fidelity = 0
        self.scale = 0
        self.auto_roll = None
        self.parent = ''
        


#*******************************************************************************
# COLLECT  

    def get_scene_data(self):
        print('|get_scene_data|')
        self.start_frame = int(cmds.playbackOptions(min=True,q=True))
        self.end_frame = int(cmds.playbackOptions(max=True,q=True))


    def get_anim_data(self, attributes):
        """ Return dictionary of lists of keyframe values for given attributes.
        
        Args:
            attributes (list): The requested transfromation attributes
        
        Returns:
            dictionary: animation data lists
        """

        print('|get_anim_data|')
        self.create_world_space_buffer()
        # Make a list of the key_frames to be used later in both modes.
        self.key_frames = cmds.keyframe(self.name + '_buffer_raw',
                                        attribute=['translate', 'rotate'],
                                        query=True,
                                        timeChange=True)

        # Make a dictionary containing lists of keyframe values for each attribute.
        anim_data = {}
        for attr in attributes:
            anim_data[attr] = cmds.keyframe(self.name + '_buffer_raw',
                                            attribute='.' + attr,
                                            query=True,
                                            valueChange=True)  
        return anim_data
    

    def create_world_space_buffer(self):
        print('|create_world_space_buffer|')
        buffer_raw = self.name + '_buffer_raw'

        pm.createNode('transform', n = buffer_raw, ss = True)
        cmds.setAttr(buffer_raw + '.rotateOrder', 2)
       
        if (self.parent is not None):           
            cmds.parent( buffer_raw, self.parent )
        else:
            print('No parent set.')

        # Constrain buffer to object, bake it, delete constraint.
        cmds.parentConstraint(self.name, buffer_raw, name='buffer_constraint')
        time_range = (self.start_frame, self.end_frame)
        if self.autoRoll == True:
            # Automatically add pre / post roll from the fidelity value
            time_range = (self.start_frame - self.fidelity, self.end_frame + self.fidelity)
        cmds.bakeResults(buffer_raw + '.translate', buffer_raw + '.rotate', t=time_range, sb=1)
        cmds.delete('buffer_constraint')

 
#*******************************************************************************
# PROCESS
        

    def derive_rotation(self, axis_1, axis_2, polyOrder=3 ):
        """ Derives object's rotation from its translation.
        
        Args:
            axis_1 (str): 1st translation axis
            axis_2 (str): 2nd translation axis
            polyOrder (int): The filter polynomial order. Default is 3

        Returns:
            None

        """

        print('|derive_rotation|')
        self.get_scene_data()
        raw_anim_data = self.get_anim_data(['translate' + axis_1, 'translate' + axis_2])

        self.raw_pos_axis_1 = raw_anim_data['translate' + axis_1]
        self.raw_pos_axis_2 = raw_anim_data['translate' + axis_2]
        self.pos_axis_1 = self.smoothData(self.raw_pos_axis_1, self.fidelity, polyOrder)
        self.pos_axis_2 = self.smoothData(self.raw_pos_axis_2, self.fidelity, polyOrder)
        self.accel_axis_1 = self.get_derivative(self.pos_axis_1, 2, True, self.fidelity)
        self.accel_axis_2 = self.get_derivative(self.pos_axis_2, 2, True, self.fidelity)  

        self.copy_to_rotation(self.scale, axis_1, axis_2)
        cmds.delete(self.name + '_buffer_raw')


    def integrate_translation(self, axis_1, axis_2):
        """ Derives object's translation from its rotation.
        
        Args:
            axis_1 (str): 1st rotation axis
            axis_2 (str): 2nd rotation axis
            scale (str): Value multiplier
        
        Returns:
            None
        """

        print('|integrate_translation|') 
        self.get_scene_data()
        raw_anim_data = self.get_anim_data(['rotate' + axis_1, 'rotate' + axis_2, 'translate' + axis_1, 'translate' + axis_2])
        self.rot_axis_1 = raw_anim_data['rotate' + axis_1]
        self.rot_axis_2 = raw_anim_data['rotate' + axis_2]   

        # Get the local starting position
        self.start_pos_axis_1 = cmds.getAttr( self.name + '.translate' + axis_1, time=self.start_frame - self.autoRoll )
        self.start_pos_axis_2 = cmds.getAttr( self.name + '.translate' + axis_2, time=self.start_frame - self.autoRoll )

        # Swap axes because the integral of the rotation in axis_1 is the translation in axis_2
        self.pos_axis_2 = self.get_integral(self.rot_axis_1, 2)
        self.pos_axis_1 = self.get_integral(self.rot_axis_2, 2)

        self.copy_to_translation(scale, axis_1, axis_2)
        cmds.delete(self.name + '_buffer_raw')

#*******************************************************************************
# APPLY


    def copy_to_rotation(self, scale, axis_1, axis_2):
        """ Copies acceleration values to the object's rotation on a separate layer.
        
        Args:
            scale (int): Value multiplier
            axis_1 (str): 1st translation axis
            axis_2 (str): 2nd translation axis
        
        Returns:
            None
        """

        print('|copy_to_rotation|')
        create_anim_layer(self, self.rot_layer_name)
        cmds.animLayer(self.rot_layer_name, edit=True, sel=True, prf=True)

        self.rot_axis_1 = self.accel_axis_2
        self.rot_axis_2 = self.accel_axis_1

        # Zip key_frames and rotation values lists into tuples and then into a dictionary
        self.rot_axis_1_dict = dict(zip(self.key_frames, self.rot_axis_1))
        self.rot_axis_2_dict = dict(zip(self.key_frames, self.rot_axis_2))
        for key in self.rot_axis_1_dict:
            cmds.setKeyframe(self.name, time=key, at='rotate' + axis_1, value=(self.rot_axis_1_dict[key] * scale) )
            cmds.setKeyframe(self.name, time=key, at='rotate' + axis_2, value=(self.rot_axis_2_dict[key] * -scale) )
  

    def copy_to_translation(self, scale, axis_1, axis_2):
        """ Copies generated values to the object's translation on a separate layer.
        
        Args:
            scale (int): Value multiplier
            axis_1 (str): 1st rotation axis
            axis_2 (str): 1st rotation axis
        
        Returns:
            None
        """

        print('|copy_to_translation|')
        create_anim_layer(self, self.trans_layer_name)
        cmds.animLayer(self.trans_layer_name, edit=True, sel=True, prf=True)

        # Zip key_frames and position values lists into tuples and then into a dictionary
        self.pos_axis_1_dict = dict(zip(self.key_frames, self.pos_axis_1))
        self.pos_axis_2_dict = dict(zip(self.key_frames, self.pos_axis_2))

        for key in self.pos_axis_1_dict:
            cmds.setKeyframe(self.name, animLayer=self.trans_layer_name, time=key, at='translate' + axis_1, value=(self.pos_axis_1_dict[key] / -scale + self.start_pos_axis_1) )
            cmds.setKeyframe(self.name, animLayer=self.trans_layer_name, time=key, at='translate' + axis_2, value=(self.pos_axis_2_dict[key] / scale + self.start_pos_axis_2) )

#*******************************************************************************
# UI
class AnimSim:
    def __init__(self):
        self.scale = None
        self.fidelity  = None
        self.autoPrePost = 1
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
        self.wgAnimSim.cbxMotionPlane.currentIndexChanged.connect(self.press_cbxMotionPlane)
        self.wgAnimSim.sldScale.valueChanged.connect(self.press_sldScale)
        self.wgAnimSim.sldFidelity.valueChanged.connect(self.press_sldFidelity)
        self.wgAnimSim.chkAutoRoll.stateChanged.connect(self.press_chkAutoRoll)

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
 
    def press_cbxMotionPlane(self):
        self.wgAnimSim.lblCurrentTarget.setText("cbxMotionPlane changed")

    def press_sldScale(self):
        self.wgAnimSim.lblScale.setText(str(self.wgAnimSim.sldScale.value()))

    def press_sldFidelity(self):
        self.wgAnimSim.lblFidelity.setText(str(self.wgAnimSim.sldFidelity.value()))

    def press_btnRotation(self):
        plane = list(str(self.wgAnimSim.cbxMotionPlane.currectText()))
        self.flyer.scale = self.wgAnimSim.sldScale.value()
        self.flyer.fidelity = self.wgAnimSim.sldFidelity.value()
        self.autoRoll = self.wgAnimSim.chkAutoRoll.isChecked()

        if (fidelity % 2) == 0:
            print('fidelity value must be an odd number')
        else:
            self.flyer.derive_rotation(plane[0], plane[1], 3)

    def press_btnTranslation(self):
        print('|integrate_translation_callback|')
        plane = list(str(self.wgAnimSim.cbxMotionPlane.currectText()))
        self.flyer.scale = self.wgAnimSim.sldScale.value()
        self.autoRoll = self.wgAnimSim.chkAutoRoll.isChecked()
        self.flyer.integrate_translation(plane[0], plane[1])         
 
