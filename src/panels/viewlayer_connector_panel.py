import bpy
from bpy.types import Panel, PropertyGroup
from bpy.props import BoolProperty, EnumProperty, StringProperty
import os

# Settings class to store user preferences
class ViewLayerConnectorSettings(PropertyGroup):
    include_all_passes: BoolProperty(
        name="Include All Passes",
        description="Connect all available passes from the ViewLayer",
        default=True
    )
    
    file_format: EnumProperty(
        name="File Format",
        description="Output file format",
        items=[
            ('OPEN_EXR_MULTILAYER', "OpenEXR MultiLayer", "Save as multilayer OpenEXR file"),
            ('OPEN_EXR', "OpenEXR", "Save as OpenEXR file"),
            ('PNG', "PNG", "Save as PNG file"),
            ('JPEG', "JPEG", "Save as JPEG file")
        ],
        default='OPEN_EXR_MULTILAYER'
    )
    
    custom_output_path: StringProperty(
        name="Output Directory",
        description="Directory to save output files",
        default="//renders/",
        subtype='DIR_PATH'
    )

class COMPOSITOR_PT_viewlayer_connector(Panel):
    """Panel for ViewLayer to File Output connector"""
    bl_label = "ViewLayer Export"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "ViewLayer Export"
    bl_context = "objectmode"
    
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'CompositorNodeTree'
    
    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon='RENDERLAYERS')
    
    def draw(self, context):
        layout = self.layout
        settings = context.scene.viewlayer_connector_settings
        
        # Status box - shows information about current setup
        box = layout.box()
        row = box.row()
        if context.scene.use_nodes:
            row.label(text="Compositor nodes: Enabled", icon='CHECKMARK')
        else:
            row.label(text="Compositor nodes: Disabled", icon='CANCEL')
            row = box.row()
            row.operator("compositor.setup_nodes", text="Enable Nodes", icon='NODETREE')
            return
            
        row = box.row()
        viewlayer_count = len(context.scene.view_layers)
        row.label(text=f"ViewLayers: {viewlayer_count}", icon='RENDERLAYERS')
        
        # Show current file path status
        row = box.row()
        if bpy.data.is_saved:
            basename = os.path.splitext(bpy.path.basename(bpy.data.filepath))[0]
            row.label(text=f"File: {basename}", icon='FILE_BLEND')
        else:
            row.label(text="File not saved", icon='ERROR')
            row = box.row()
            row.label(text="Save file before connecting nodes")
        
        # Settings section
        box = layout.box()
        box.label(text="Settings", icon='PREFERENCES')
        
        row = box.row()
        row.prop(settings, "file_format")
        
        row = box.row()
        row.prop(settings, "include_all_passes")
        
        row = box.row()
        row.prop(settings, "custom_output_path")
        
        # Preview section
        preview_box = layout.box()
        preview_box.label(text="Preview", icon='PRESET')
        
        for idx, viewlayer in enumerate(context.scene.view_layers):
            if idx < 3:  # Only show first 3 for preview
                row = preview_box.row()
                row.label(text=viewlayer.name, icon='RENDER_RESULT')
            elif idx == 3:
                row = preview_box.row()
                row.label(text=f"... and {viewlayer_count - 3} more")
                break
        
        # Action buttons section
        layout.separator()
        row = layout.row(align=True)
        connect_op = row.operator("compositor.connect_viewlayers_to_output", 
                                 text="Connect All ViewLayers", 
                                 icon='NODETREE')
        
        row = layout.row(align=True)
        clear_op = row.operator("compositor.clear_viewlayer_outputs", 
                               text="Clear Existing Nodes", 
                               icon='TRASH')
        
        # Help box
        help_box = layout.box()
        help_box.label(text="Help", icon='QUESTION')
        row = help_box.row()
        row.scale_y = 0.7
        row.label(text="This will create File Output nodes for each")
        row = help_box.row()
        row.scale_y = 0.7
        row.label(text="ViewLayer and connect available passes.")