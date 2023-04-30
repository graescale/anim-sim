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
TITLE = os.path.splitext(os.path.basename(__file__))[0]
CURRENT_PATH = os.path.dirname(__file__)
IMG_PATH = CURRENT_PATH + "/img/{}.png"

ANCHORS = 'Anchors'
ANCHOR_LAYER = 'Anchor_Offset'

#*******************************************************************************
# CLASS
class Flyer:
    def __init__(self, name):
        self.Name = name
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
        self.layer_name = ''
        self.fidelity = 0
        self.Scale = 0
        self.auto_roll = None
        self.parent = None
        self.anchors = []
        self.anchor_display_layer = None
        self.anchor_layer = ''
        self.motion_plane = ''
        

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
        self.key_frames = cmds.keyframe(self.Name + '_buffer_raw', attribute=['translate', 'rotate'], query=True, timeChange=True)

        # Make a dictionary containing lists of keyframe values for each attribute.
        anim_data = {}
        for attr in attributes:
            anim_data[attr] = cmds.keyframe(self.Name + '_buffer_raw', attribute='.' + attr, query=True, valueChange=True)  
        return anim_data


    def create_world_space_buffer(self):
        print('|create_world_space_buffer|')
        print('Fidelity is:')
        print(self.fidelity)
        print('Auto Roll is:')
        print(self.auto_roll)
        buffer_raw = self.Name + '_buffer_raw'

        pm.createNode('transform', n = buffer_raw, ss = True)
        cmds.setAttr(buffer_raw + '.rotateOrder', 2)
       
        if self.parent == None:
            print('No parent set.')
        else:
            cmds.parent( buffer_raw, self.parent )

        # Constrain buffer to object, bake it, delete constraint.
        cmds.parentConstraint(self.Name, buffer_raw, name='buffer_constraint')
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
        #self.extract_anim(self.Name, 'translation')
        if cmds.animLayer(self.layer_name, query=True, exists=True):
            cmds.delete(self.layer_name)
        self.get_scene_data()
        raw_anim_data = self.get_anim_data(['translate' + axis_1, 'translate' + axis_2])
        self.raw_pos_axis_1 = raw_anim_data['translate' + axis_1]
        self.raw_pos_axis_2 = raw_anim_data['translate' + axis_2]
        self.pos_axis_1 = h.smooth_data(self.raw_pos_axis_1, self.fidelity, polyOrder)
        self.pos_axis_2 = h.smooth_data(self.raw_pos_axis_2, self.fidelity, polyOrder)
        self.accel_axis_1 = h.get_derivative(self.pos_axis_1, 2, True, self.fidelity)
        self.accel_axis_2 = h.get_derivative(self.pos_axis_2, 2, True, self.fidelity)
        self.copy_rot_to_layer(self.Scale, axis_1, axis_2)
        cmds.delete(self.Name + '_buffer_raw')


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

        # Get the local starting position
        if cmds.animLayer(self.layer_name, query=True, exists=True):
            cmds.animLayer(self.layer_name, edit=True, mute=True)
        self.start_pos_axis_1 = cmds.getAttr(self.Name + '.translate' + axis_1, time=self.start_frame - self.fidelity)
        print('self.start_pos_axis_1 is %s' % self.start_pos_axis_1)
        self.start_pos_axis_2 = cmds.getAttr(self.Name + '.translate' + axis_2, time=self.start_frame - self.fidelity)
        if cmds.animLayer(self.layer_name, query=True, exists=True):
            cmds.animLayer(self.layer_name, edit=True, mute=False)
        self.pos_axis_1 = h.get_integral(self.rot_axis_1, 2)
        self.pos_axis_2 = h.get_integral(self.rot_axis_2, 2)
        self.copy_trans_to_layer(self.Scale, axis_1, axis_2)


    def set_anchor(self, axis_1, axis_2):

        print('|set_anchor|')
        self.anchor_display_layer = self.Name + '_anchors'
        current_time = str(cmds.currentTime(query=True)).split('.')[0]
        print('current_time is: ' + current_time)
        anchor_name = self.Name + '_' + str(current_time) + '_anchor'
        print('anchor_name is: ' + anchor_name)
        if anchor_name not in self.anchors:
            cmds.select(self.Name)
            anchor = cmds.duplicate(name=anchor_name)[0]
            self.anchors.append(anchor)
            cmds.parent(anchor, ANCHORS)
            try:
                cmds.editDisplayLayerMembers(self.anchor_display_layer, query=True)
            except:
                cmds.createDisplayLayer(name=self.anchor_display_layer)
            cmds.editDisplayLayerMembers(self.anchor_display_layer, anchor, noRecurse=True)    
        else:
            cmds.delete(anchor_name)
            self.anchors.remove(anchor_name)


    def remove_anchors(self):

        self.anchors = []
        cmds.delete(ANCHORS)
        cmds.delete(self.anchor_display_layer)

        # Get the anchor times
        # Turn off auto_translation and turn on _original_translation



#*******************************************************************************
# APPLY
    def copy_rot_to_layer(self, scale, axis_1, axis_2):
        """ Copies acceleration values to the object's rotation on a separate layer.
        
        Args:
            scale (int): Value multiplier
            axis_1 (str): 1st translation axis
            axis_2 (str): 2nd translation axis
        
        Returns:
            None
        """

        print('|copy_rot_to_layer|')
        axis1_mult = 1
        axis2_mult = 1
        h.create_anim_layer(self.Name, self.layer_name, True)
        cmds.animLayer(self.layer_name, edit=True, sel=True, prf=True)
        if axis_1 == 'X' and axis_2 == 'Y':
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
            cmds.setKeyframe(self.Name, time=key, at='rotate' + axis_1, value=(self.rot_axis_1_dict[key] * scale * axis1_mult) )
            cmds.setKeyframe(self.Name, time=key, at='rotate' + axis_2, value=(self.rot_axis_2_dict[key] * scale * axis2_mult) )
  

    def copy_trans_to_layer(self, scale, axis_1, axis_2):
        """ Copies generated values to the object's translation on a separate layer.
        
        Args:
            scale (int): Value multiplier
            axis_1 (str): 1st rotation axis
            axis_2 (str): 1st rotation axis
        
        Returns:
            None
        """

        print('|copy_trans_to_layer|')
        cmds.animLayer(self.layer_name, edit=True, sel=True, prf=True)
        # Zip key_frames and position values lists into tuples and then into a dictionary
        self.pos_axis_1_dict = dict(zip(self.key_frames, self.pos_axis_1))
        self.pos_axis_2_dict = dict(zip(self.key_frames, self.pos_axis_2))
        print('start_pos_axis_1 is %s' % self.start_pos_axis_1)
        print ('self.pos_axis_1_dict at frame 1 is %s' % self.pos_axis_1_dict[1])
        for key in self.pos_axis_1_dict:
            cmds.setKeyframe(self.Name, animLayer=self.layer_name, time=key, at='translate' + axis_1, value=(self.pos_axis_1_dict[key] + self.start_pos_axis_1) )
            cmds.setKeyframe(self.Name, animLayer=self.layer_name, time=key, at='translate' + axis_2, value=(self.pos_axis_2_dict[key] + self.start_pos_axis_2) )


    def anchors_rebuild(self, axis_1, axis_2):
        """ Creates offset layer to match animation to anchors and derives rotation.
        
        Args:
            axis_1 (str): 1st rotation axis
            axis_2 (str): 1st rotation axis
        
        Returns:
            None
        """
        
        print('|anchors_rebuild|')
        self.anchor_layer = self.Name + ANCHOR_LAYER
        anim_layers = cmds.ls(type='animLayer')
        cmds.animLayer(self.anchor_layer)
        cmds.select(self.Name)
        cmds.animLayer(self.anchor_layer, edit=True, addSelectedObjects=True)
        for layer in anim_layers:
            cmds.animLayer(layer, edit=True, sel=False, prf=False)
        cmds.animLayer(self.anchor_layer, edit=True, sel=True, prf=True)
        for anchor in self.anchors:
            anchor_frame = anchor.split('_')[1]
            cmds.currentTime(anchor_frame)          
            cmds.matchTransform(self.Name, anchor, position=True)
            cmds.setKeyframe(self.Name, at=['translate' + axis_1, 'translate' + axis_2])
        for channel in list(['X', 'Y', 'Z']):
            cmds.setAttr(self.anchor_display_layer + '|' + self.Name + '.translate' + channel, lock=True)
        self.derive_rotation(axis_1, axis_2)
        for channel in list(['X', 'Y', 'Z']):
            cmds.setAttr(self.anchor_display_layer + '|' + self.Name + '.translate' + channel, lock=False)