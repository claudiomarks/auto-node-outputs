import bpy
from bpy.props import PointerProperty
from .operators.connect_viewlayers_to_output import COMPOSITOR_OT_connect_viewlayers_to_output
from .operators.additional_operators import COMPOSITOR_OT_setup_nodes, COMPOSITOR_OT_clear_viewlayer_outputs
from .panels.viewlayer_connector_panel import COMPOSITOR_PT_viewlayer_connector, ViewLayerConnectorSettings

bl_info = {
    "name": "Auto Node Outputs",
    "author": "Claude",
    "version": (1, 1),
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