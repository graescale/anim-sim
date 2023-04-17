#*******************************************************************************
# content = Simulates hovering motion.
#
# version      = 1.0.0
# date         = 2022-01-26
# how to       => anim_sim = animSim()
#
# dependencies = Maya
#
# to dos = Restructure workflow, simplify code
# author = Grae Revell <grae.revell@gmail.com>
#*******************************************************************************
import os
import sys

import helpers as h

import pymel.core as pm
import maya.cmds as cmds

#*******************************************************************************
# VARIABLES

ROTATION_LAYER = 'auto_rotation'
TRANSLATION_LAYER = 'auto_translation'

TITLE = os.path.splitext(os.path.basename(__file__))[0]
CURRENT_PATH = os.path.dirname(__file__)
IMG_PATH = CURRENT_PATH + "/img/{}.png"

#*******************************************************************************
# CLASS

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
        self.parent = None
        


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
        self.key_frames = cmds.keyframe(self.name + '_buffer_raw', attribute=['translate', 'rotate'], query=True, timeChange=True)

        # Make a dictionary containing lists of keyframe values for each attribute.
        anim_data = {}
        for attr in attributes:
            anim_data[attr] = cmds.keyframe(self.name + '_buffer_raw', attribute='.' + attr, query=True, valueChange=True)  
        return anim_data
    

    def create_world_space_buffer(self):
        print('|create_world_space_buffer|')
        print('Fidelity is:')
        print(self.fidelity)
        print('Auto Roll is:')
        print(self.auto_roll)
        buffer_raw = self.name + '_buffer_raw'

        pm.createNode('transform', n = buffer_raw, ss = True)
        cmds.setAttr(buffer_raw + '.rotateOrder', 2)
       
        if self.parent == None:
            print('No parent set.')
        else:
            cmds.parent( buffer_raw, self.parent )

        # Constrain buffer to object, bake it, delete constraint.
        cmds.parentConstraint(self.name, buffer_raw, name='buffer_constraint')
        time_range = (self.start_frame, self.end_frame)
        if self.auto_roll == True:
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
        extract_anim(self.name, 'translation')
        self.get_scene_data()
        raw_anim_data = self.get_anim_data(['translate' + axis_1, 'translate' + axis_2])
        self.raw_pos_axis_1 = raw_anim_data['translate' + axis_1]
        self.raw_pos_axis_2 = raw_anim_data['translate' + axis_2]
        self.pos_axis_1 = h.smooth_data(self.raw_pos_axis_1, self.fidelity, polyOrder)
        self.pos_axis_2 = h.smooth_data(self.raw_pos_axis_2, self.fidelity, polyOrder)
        self.accel_axis_1 = h.get_derivative(self.pos_axis_1, 2, True, self.fidelity)
        self.accel_axis_2 = h.get_derivative(self.pos_axis_2, 2, True, self.fidelity)
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
        
        cmds.animLayer(self.name + '_original_translation', edit=True, mute=True)
        # Get the local starting position
        self.start_pos_axis_1 = cmds.getAttr(self.name + '.translate' + axis_1, time=self.start_frame - self.fidelity)
        self.start_pos_axis_2 = cmds.getAttr(self.name + '.translate' + axis_2, time=self.start_frame - self.fidelity)
        self.pos_axis_1 = h.get_integral(self.rot_axis_1, 2)
        self.pos_axis_2 = h.get_integral(self.rot_axis_2, 2)
        self.copy_to_translation(self.scale, axis_1, axis_2)

def extract_anim(object, transform):
    """ Extracts base anim to new layer and groups with additional anim layers.

    Args:
        object (obj): The object with animation curves to extract
        transform (str): The transformation type (rotation or translation)

    """

    print('|extract_anim|')
    additional_layers = []
    BASE_ANIM_LAYER = 'BaseAnimation'
    ORIGINAL_LAYER_GROUP = 'Original_Animation'
    EXTRACT_LAYER = object + transform

    if transform == "rotation":
        attrs = ['rx', 'ry', 'rz']
    if transform == "translation":
        attrs = ['tx', 'ty', 'tz']
    
    # Get a list of selected layers
    anim_layers = cmds.ls(type='animLayer')
    for layer in anim_layers:
        if cmds.animLayer(layer, sel=True, query=True)
        additional_layers.append(layer)

    if not cmds.animLayer(EXTRACT_LAYER, query=True, exists=True):
        cmds.animLayer(EXTRACT_LAYER)
    for layer in anim_layers:
        cmds.animLayer(layer, edit=True, sel=False, prf=False)
    cmds.animLayer(BASE_ANIM_LAYER, edit=True, sel=True, prf=True)
    cmds.copyKey(object, animation='objects', option='keys')
    cmds.animLayer(EXTRACT_LAYER, edit=True, sel=True, prf=True)
    cmds.animLayer(EXTRACT_LAYER, edit=True, addSelectedObjects=True)
    cmds.pasteKey(object, animation='objects', option='replaceCompletely')
    cmds.animLayer(BASE_ANIM_LAYER, edit=True, sel=True, prf=True)
    cmds.animLayer(EXTRACT_LAYER, edit=True, sel=False, prf=False)
    cmds.keyframe(object, at=attrs, edit=True, time=(None,None), absolute=True, valueChange=0)
    cmds.cutKey(object, animation='objects', option='keys')
    #cmds.animLayer(EXTRACT_LAYER, edit=True, moveLayerBefore=self.rot_layer_name)

    # Parent the base animation and additional layers
    cmds.animLayer(ORIGINAL_LAYER_GROUP)
    cmds.animLayer(EXTRACT_LAYER, edit=True, parent=ORIGINAL_LAYER_GROUP)
    for layer in additional_layers:
        cmds.animLayer(layer, edit=True, parent=ORIGINAL_LAYER_GROUP)

    #def anchor(self):
        # Get the anchor times
        # Turn off auto_translation and turn on _original_translation



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
        axis1_mult = 1
        axis2_mult = 1
        h.create_anim_layer(self.name, self.rot_layer_name)
        cmds.animLayer(self.rot_layer_name, edit=True, sel=True, prf=True)
        if cmds.animLayer(self.rot_layer_name, query=True, sel=True):
            print(self.rot_layer_name + ' is the current layer')
        else:
            print(self.rot_layer_name + ' is NOT the current layer')
        if axis_1 == 'X' and axis_2 == 'Y':
            print('X and Y are true')
            axis_1 = 'Z'
            axis1_mult = -1
            axis_2 = 'X'
            axis2_mult = -1
        if axis_1 == 'X' and axis_2 == 'Z':
            axis_1 = 'Z'
            axis1_mult = -1
            axis_2 = 'X'
        if axis_1 == 'Y' and axis_2 == 'Z':
            axis_1 = 'Z'
            axis_2 = 'X'
        self.rot_axis_1 = self.accel_axis_1
        self.rot_axis_2 = self.accel_axis_2
        # Zip key_frames and rotation values lists into tuples and then into a dictionary
        self.rot_axis_1_dict = dict(zip(self.key_frames, self.rot_axis_1))
        self.rot_axis_2_dict = dict(zip(self.key_frames, self.rot_axis_2))
        for key in self.rot_axis_1_dict:
            cmds.setKeyframe(self.name, time=key, at='rotate' + axis_1, value=(self.rot_axis_1_dict[key] * scale * axis1_mult) )
            cmds.setKeyframe(self.name, time=key, at='rotate' + axis_2, value=(self.rot_axis_2_dict[key] * scale * axis2_mult) )
  

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
        h.create_anim_layer(self.name, self.trans_layer_name)
        cmds.animLayer(self.trans_layer_name, edit=True, sel=True, prf=True)
        # Zip key_frames and position values lists into tuples and then into a dictionary
        self.pos_axis_1_dict = dict(zip(self.key_frames, self.pos_axis_1))
        self.pos_axis_2_dict = dict(zip(self.key_frames, self.pos_axis_2))
        for key in self.pos_axis_1_dict:
            cmds.setKeyframe(self.name, animLayer=self.trans_layer_name, time=key, at='translate' + axis_1, value=(self.pos_axis_1_dict[key] + self.start_pos_axis_1) )
            cmds.setKeyframe(self.name, animLayer=self.trans_layer_name, time=key, at='translate' + axis_2, value=(self.pos_axis_2_dict[key] + self.start_pos_axis_2) )