import bpy
import os  # Add this import
from bpy.types import PropertyGroup, Panel  # Add Panel here
from bpy.props import BoolProperty, EnumProperty, StringProperty, FloatProperty

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
    
    # New organizational settings
    clear_existing: BoolProperty(
        name="Clear Existing Nodes",
        description="Remove existing ViewLayer and Output nodes before creating new ones",
        default=True
    )
    
    auto_group: BoolProperty(
        name="Auto-Group Nodes",
        description="Automatically group ViewLayer nodes with their outputs",
        default=False
    )
    
    auto_organize: BoolProperty(
        name="Auto-Organize Nodes",
        description="Automatically arrange nodes in the compositor",
        default=True
    )
    
    node_spacing: FloatProperty(
        name="Node Spacing",
        description="Spacing between nodes",
        default=300.0,
        min=100.0,
        max=1000.0
    )
    
    sort_viewlayers: EnumProperty(
        name="Sort ViewLayers",
        description="Method to sort ViewLayers",
        items=[
            ('NONE', "No Sorting", "Use ViewLayers in their original order"),
            ('ALPHABETICAL', "Alphabetical", "Sort ViewLayers alphabetically"),
            ('CUSTOM', "Custom Order", "Sort ViewLayers by custom order")
        ],
        default='ALPHABETICAL'
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

        # Organizational options
        box = layout.box()
        box.label(text="Organization", icon='NODETREE')

        row = box.row()
        row.prop(settings, "clear_existing")

        row = box.row()
        row.prop(settings, "auto_group")

        row = box.row()
        row.prop(settings, "auto_organize")

        row = box.row()
        row.prop(settings, "node_spacing")

        row = box.row()
        row.prop(settings, "sort_viewlayers")

        # Organization action buttons
        row = layout.row(align=True)
        row.operator("compositor.organize_nodes", text="Organize Nodes", icon='GRAPH')
        row = layout.row(align=True)
        row.operator("compositor.group_viewlayer_nodes", text="Group Nodes", icon='NODETREE')
        row = layout.row(align=True)
        row.operator("compositor.connect_sorted_viewlayers", text="Connect Sorted ViewLayers", icon='SORTSIZE')