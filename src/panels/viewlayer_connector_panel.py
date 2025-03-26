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

    # New properties for selecting main and secondary output formats
    main_output_format: EnumProperty(
        name="Main Output Format",
        description="File format for the main output node (contains all passes except Depth, Position, Normal, and Cryptomatte)",
        items=[
            ('OPEN_EXR_MULTILAYER', "OpenEXR MultiLayer", "Save as multilayer OpenEXR file"),
            ('OPEN_EXR', "OpenEXR", "Save as OpenEXR file"),
            ('PNG', "PNG", "Save as PNG file"),
            ('JPEG', "JPEG", "Save as JPEG file")
        ],
        default='OPEN_EXR_MULTILAYER'
    )
    
    # EXR bit depth options for main output
    main_exr_bitdepth: EnumProperty(
        name="Main EXR Bit Depth",
        description="Bit depth for main output EXR files",
        items=[
            ('16', "Half Float (16-bit)", "Half precision floating point (faster, smaller files)"),
            ('32', "Full Float (32-bit)", "Full precision floating point (slower, but higher quality)")
        ],
        default='16'
    )
    
    # EXR compression options for main output
    main_exr_codec: EnumProperty(
        name="Main EXR Compression",
        description="Compression codec for main output EXR files",
        items=[
            ('NONE', "None", "No compression"),
            ('ZIPS', "ZIPS", "Lossless ZIP compression, one scanline at a time"),
            ('ZIP', "ZIP", "Lossless ZIP compression, in blocks of 16 scanlines"),
            ('PIZ', "PIZ", "Lossless wavelet compression"),
            ('PXR24', "PXR24", "Lossy compression with 24-bit float precision"),
            ('DWAA', "DWAA", "Lossy compression with adjustable quality, one scanline at a time"),
            ('DWAB', "DWAB", "Lossy compression with adjustable quality, in blocks of 32 scanlines")
        ],
        default='ZIP'
    )
    
    # Secondary output format
    secondary_output_format: EnumProperty(
        name="Secondary Output Format",
        description="File format for the secondary output node (contains only Depth, Position, Normal, and Cryptomatte passes)",
        items=[
            ('OPEN_EXR', "OpenEXR", "Save as OpenEXR file"),
            ('OPEN_EXR_MULTILAYER', "OpenEXR MultiLayer", "Save as multilayer OpenEXR file"),
            ('PNG', "PNG", "Save as PNG file"),
            ('JPEG', "JPEG", "Save as JPEG file")
        ],
        default='OPEN_EXR'
    )
    
    # EXR bit depth options for secondary output
    secondary_exr_bitdepth: EnumProperty(
        name="Secondary EXR Bit Depth",
        description="Bit depth for secondary output EXR files",
        items=[
            ('16', "Half Float (16-bit)", "Half precision floating point (faster, smaller files)"),
            ('32', "Full Float (32-bit)", "Full precision floating point (slower, but higher quality)")
        ],
        default='32'  # Default to full float for secondary since it often contains depth and position data
    )
    
    # EXR compression options for secondary output
    secondary_exr_codec: EnumProperty(
        name="Secondary EXR Compression",
        description="Compression codec for secondary output EXR files",
        items=[
            ('NONE', "None", "No compression"),
            ('ZIPS', "ZIPS", "Lossless ZIP compression, one scanline at a time"),
            ('ZIP', "ZIP", "Lossless ZIP compression, in blocks of 16 scanlines"),
            ('PIZ', "PIZ", "Lossless wavelet compression"),
            ('PXR24', "PXR24", "Lossy compression with 24-bit float precision"),
            ('DWAA', "DWAA", "Lossy compression with adjustable quality, one scanline at a time"),
            ('DWAB', "DWAB", "Lossy compression with adjustable quality, in blocks of 32 scanlines")
        ],
        default='ZIP'
    )
    
    # Toggle for enabling secondary output node
    use_secondary_output: BoolProperty(
        name="Use Secondary Output",
        description="Create a secondary output node for Depth, Position, Normal, and Cryptomatte passes",
        default=True
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
        box.label(text="Output Format Settings", icon='PREFERENCES')
        
        # Main output section
        row = box.row()
        row.label(text="Main Output Node:", icon='OUTPUT')
        row = box.row()
        row.prop(settings, "main_output_format")
        
        # Show bit depth and compression options for EXR formats only
        if settings.main_output_format in ['OPEN_EXR', 'OPEN_EXR_MULTILAYER']:
            row = box.row()
            row.prop(settings, "main_exr_bitdepth")
            
            row = box.row()
            row.prop(settings, "main_exr_codec")
        
        row = box.row()
        row.label(text="Contains all passes except Depth, Position, Normal, and Cryptomatte")
        
        # Secondary output section
        box.separator()
        row = box.row()
        row.prop(settings, "use_secondary_output")
        
        # Only show secondary output format if enabled
        if settings.use_secondary_output:
            row = box.row()
            row.prop(settings, "secondary_output_format")
            
            # Show bit depth and compression options for EXR formats only
            if settings.secondary_output_format in ['OPEN_EXR', 'OPEN_EXR_MULTILAYER']:
                row = box.row()
                row.prop(settings, "secondary_exr_bitdepth")
                
                row = box.row()
                row.prop(settings, "secondary_exr_codec")
            
            row = box.row()
            row.label(text="Contains only Depth, Position, Normal, and Cryptomatte passes")
        
        box.separator()
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