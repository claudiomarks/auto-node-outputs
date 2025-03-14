import bpy
from bpy.types import Operator
from bpy.props import EnumProperty
from ..utils.node_utils import arrange_nodes, clear_all_viewlayer_nodes, group_viewlayer_nodes, sort_viewlayers

class COMPOSITOR_OT_organize_nodes(Operator):
    """Organize nodes in the compositor"""
    bl_idname = "compositor.organize_nodes"
    bl_label = "Organize Nodes"
    bl_options = {'REGISTER', 'UNDO'}
    
    organize_type: EnumProperty(
        name="Organization Type",
        items=[
            ('GRID', "Grid", "Arrange nodes in a grid pattern"),
            ('FLOW', "Flow", "Arrange nodes in a left-to-right flow"),
            ('HIERARCHY', "Hierarchy", "Arrange nodes in a hierarchical layout")
        ],
        default='HIERARCHY'
    )
    
    def execute(self, context):
        if not context.scene.use_nodes:
            self.report({'WARNING'}, "Compositor nodes are not enabled")
            return {'CANCELLED'}
        
        tree = context.scene.node_tree
        arrange_nodes(tree, self.organize_type)
        
        self.report({'INFO'}, f"Organized nodes using {self.organize_type} layout")
        return {'FINISHED'}

class COMPOSITOR_OT_group_viewlayer_nodes(Operator):
    """Group each ViewLayer node with its corresponding output node"""
    bl_idname = "compositor.group_viewlayer_nodes"
    bl_label = "Group ViewLayer Nodes"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        if not context.scene.use_nodes:
            self.report({'WARNING'}, "Compositor nodes are not enabled")
            return {'CANCELLED'}
        
        tree = context.scene.node_tree
        groups_created = group_viewlayer_nodes(tree)
        
        if groups_created > 0:
            self.report({'INFO'}, f"Created {groups_created} node groups")
        else:
            self.report({'WARNING'}, "No ViewLayer nodes found to group")
        
        return {'FINISHED'}

class COMPOSITOR_OT_connect_sorted_viewlayers(Operator):
    """Connect ViewLayers to outputs in sorted order"""
    bl_idname = "compositor.connect_sorted_viewlayers"
    bl_label = "Connect Sorted ViewLayers"
    bl_options = {'REGISTER', 'UNDO'}
    
    sort_type: EnumProperty(
        name="Sort Type",
        items=[
            ('ALPHABETICAL', "Alphabetical", "Sort ViewLayers alphabetically"),
            ('CUSTOM', "Custom Order", "Sort ViewLayers by custom order")
        ],
        default='ALPHABETICAL'
    )
    
    def execute(self, context):
        if not context.scene.use_nodes:
            context.scene.use_nodes = True
        
        settings = context.scene.viewlayer_connector_settings
        tree = context.scene.node_tree
        
        # Sort the viewlayers
        sorted_viewlayers = sort_viewlayers(context.scene, self.sort_type)
        
        if not sorted_viewlayers:
            self.report({'WARNING'}, "No ViewLayers found in the scene")
            return {'CANCELLED'}
        
        # Clear existing nodes if the option is enabled
        if settings.clear_existing:
            clear_all_viewlayer_nodes(tree)
        
        # Now connect the sorted viewlayers
        # This is similar to the connect_viewlayers_to_output operator
        # but uses the sorted list instead
        
        start_x = 0
        start_y = 0
        spacing_y = -300
        
        for idx, viewlayer in enumerate(sorted_viewlayers):
            viewlayer_name = viewlayer.name
            rl_node = tree.nodes.new('CompositorNodeRLayers')
            rl_node.name = f"ViewLayer_{viewlayer_name}"
            rl_node.label = viewlayer_name
            rl_node.layer = viewlayer_name
            rl_node.location = (start_x, start_y + (idx * spacing_y))
            
            output_node = tree.nodes.new('CompositorNodeOutputFile')
            output_node.name = f"Output_{viewlayer_name}"
            output_node.label = f"Output {viewlayer_name}"
            output_node.location = (rl_node.location.x + 400, rl_node.location.y)
            
            # Use settings from the panel
            output_node.format.file_format = settings.file_format
            output_node.base_path = settings.custom_output_path
            
            # Connect the nodes
            first_connection = True
            for output in rl_node.outputs:
                if output.enabled and (settings.include_all_passes or output.name == 'Image'):
                    if first_connection:
                        output_node.file_slots[0].path = output.name
                        tree.links.new(output, output_node.inputs[0])
                        first_connection = False
                    else:
                        output_node.file_slots.new(output.name)
                        tree.links.new(output, output_node.inputs[-1])
        
        # Group the nodes if that option is enabled
        if settings.auto_group:
            group_viewlayer_nodes(tree)
        
        # Organize the nodes if that option is enabled
        if settings.auto_organize:
            arrange_nodes(tree, 'HIERARCHY')
        
        self.report({'INFO'}, f"Connected {len(sorted_viewlayers)} ViewLayers in {self.sort_type} order")
        return {'FINISHED'}