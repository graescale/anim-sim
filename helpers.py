#*******************************************************************************
# content = helper functions for animsim.
#
# version      = 0.4.1
# date         = 2023-05-13
#
# dependencies = Maya, numpy, scipy
#
# author = Grae Revell <grae.revell@gmail.com>
#*******************************************************************************

import numpy as np
import scipy.signal
import maya.cmds as cmds

#*******************************************************************************
# VARIABLES

ROOT = 'Anim_Sim'
TARGETS = 'Targets'
ANCHORS = 'Anchors'
CONNECTIONS = 'Connections'

def create_hierarchy():
    """ Creates initial folder structre
    
    Returns:
        None
    """

    if not cmds.objExists(ROOT):
        cmds.group(empty=True, name=ROOT)
    if not cmds.objExists(ANCHORS):
        cmds.group(empty=True, name=ANCHORS, parent=ROOT)
    if not cmds.objExists(TARGETS):
        cmds.group(empty=True, name=TARGETS, parent=ROOT)
    if not cmds.objExists(CONNECTIONS):
        cmds.group(empty=True, name=CONNECTIONS, parent=ROOT)

def create_dag(object, parent_node):
    """ Creates a dag node.

    Args:
        object (str): target object
        parent (str): object to become target's parent 
        suffix (str): string to append to object

    Returns:
        None
        """

    if not cmds.objExists(object):
        cmds.createNode('dagContainer', n=object, parent=parent_node)
        print('Created dag node:')
        print(object)
    else:
        print('Node already exists:')
        print(object)

# def add_attrs(object, name, type, typeType, parent_attr):
#     if typeType == 'attributeType':
#         cmds.addAttr(object, longName=name, attributeType=type, parent=parent_attr)
#     else:
#         cmds.addAttr(object, longName=name, dataType=type, parent=parent_attr)

def get_derivative(anim_data, degree, filter_data, window, order=3):
    """ Returns a list containing n degree derivative of supplied list.
    
    Args:
        anim_data (list): The data to get derivatives from.
        degree (int): The number of derivatives to calculate.
        filter_data (bool): Option to smooth the data after deriving.
        window (int): The filter window size.
        order (int): The filter polynomial order. Default 3

    Returns:
        list: The n degree derivative of anim_data
        """

    print('|get_derivative|')
    # Initialize data
    data_to_derive = anim_data
    deriv_result = []
    count = 1
    while count <= degree:
        deriv_result = np.diff(data_to_derive)        
        deriv_result = np.insert(deriv_result,0,0)
        data_to_derive = deriv_result
        count = count + 1
    if filter_data == True:
        deriv_result = scipy.signal.savgol_filter(deriv_result, window, order)            
    return deriv_result


def get_integral(anim_data, degree):
    """ Returns a list containing the n degree integral of the supplied list.
    
    Args:
        anim_data (list): The data to get derivatives from.
        degree (int): The number of derivatives to calculate.

    Returns:
        list: The n degree integral of anim_data
    """

    print('|get_integral|')

    # velocity(t) - velocity(t - 1) = acceleration(t)
    # velocity(t) = acceleration(t) + velocity(t -1)

    data_to_integrate = anim_data      
    count = 1
    while count <= degree:
        #print('Getting integral of degree: '+ str(count))
        # Initialize integral_result.
        integral_result = []
        # Append the first value in data_to_integrate to integral_result's first element     
        integral_result.append(data_to_integrate[0])
        for idx, i in enumerate(data_to_integrate):
            if idx > 0:
                integral_result.append(data_to_integrate[idx] + integral_result[idx - 1])
        count = count + 1
        data_to_integrate = integral_result
    return integral_result 


def smooth_data(data, window, order):
    """ Smooths list of numbers using Savitzky-Golay filter.
    
    Args:
        data (list): The numbers to smooth.
        window (int): The smoothing window size.
        order (int): The polynomial order to use in the smoothing method.
    Returns:
        list: Smoothed data.
    """

    print('|smooth_data|')

    return scipy.signal.savgol_filter(data, window, order) 


def create_anim_layer(object, layer_name, override):
    """ Creates an animation layer
    
    Args:
        layer_name (str): The name of layer to be created
    """

    print('|create_anim_layer|')
    if not cmds.animLayer(layer_name, query=True, exists=True):
        cmds.animLayer(layer_name)
    cmds.select(object)
    cmds.animLayer(layer_name, edit=True, addSelectedObjects=True, o=override)
