import bpy
from bpy.types import Panel

class COMPOSITOR_PT_viewlayer_connector(Panel):
    """Panel for ViewLayer to File Output connector"""
    bl_label = "ViewLayer Connector"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "ViewLayer Export"
    bl_context = "objectmode"
    
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'CompositorNodeTree'
    
    def draw(self, context):
        layout = self.layout
        layout.operator("compositor.connect_viewlayers_to_output")