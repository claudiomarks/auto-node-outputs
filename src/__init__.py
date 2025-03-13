import bpy
from .operators.connect_viewlayers_to_output import COMPOSITOR_OT_connect_viewlayers_to_output
from .panels.viewlayer_connector_panel import COMPOSITOR_PT_viewlayer_connector

bl_info = {
    "name": "Auto Node Outputs",
    "author": "Claude",
    "version": (1, 0),
    "blender": (4, 3, 0),
    "location": "Compositor > Node",
    "description": "Automatically connect ViewLayers to File Output nodes",
    "category": "Compositing",
}

def register():
    bpy.utils.register_class(COMPOSITOR_OT_connect_viewlayers_to_output)
    bpy.utils.register_class(COMPOSITOR_PT_viewlayer_connector)

def unregister():
    bpy.utils.unregister_class(COMPOSITOR_OT_connect_viewlayers_to_output)
    bpy.utils.unregister_class(COMPOSITOR_PT_viewlayer_connector)

if __name__ == "__main__":
    register()