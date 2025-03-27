import bpy
from bpy.props import PointerProperty
from .operators.connect_viewlayers_to_output import COMPOSITOR_OT_connect_viewlayers_to_output
from .operators.additional_operators import COMPOSITOR_OT_setup_nodes, COMPOSITOR_OT_clear_viewlayer_outputs
from .panels.viewlayer_connector_panel import COMPOSITOR_PT_viewlayer_connector, ViewLayerConnectorSettings
from .operators.organizational_operators import (
    COMPOSITOR_OT_organize_nodes, 
    COMPOSITOR_OT_group_viewlayer_nodes, 
    COMPOSITOR_OT_connect_sorted_viewlayers,
    COMPOSITOR_OT_group_by_prefix_in_frames
)

bl_info = {
    "name": "Auto Node Outputs",
    "author": "Claudin",
    "version": (1, 6, 7),
    "blender": (4, 3, 0),
    "location": "Compositor > Node > ViewLayer Export",
    "description": "Automatically connect ViewLayers to File Output nodes",
    "category": "Compositing",
}

classes = (
    ViewLayerConnectorSettings,
    COMPOSITOR_OT_connect_viewlayers_to_output,
    COMPOSITOR_OT_setup_nodes,
    COMPOSITOR_OT_clear_viewlayer_outputs,
    COMPOSITOR_OT_organize_nodes,
    COMPOSITOR_OT_group_viewlayer_nodes, 
    COMPOSITOR_OT_connect_sorted_viewlayers,
    COMPOSITOR_OT_group_by_prefix_in_frames,
    COMPOSITOR_PT_viewlayer_connector,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.viewlayer_connector_settings = PointerProperty(type=ViewLayerConnectorSettings)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.viewlayer_connector_settings

if __name__ == "__main__":
    register()