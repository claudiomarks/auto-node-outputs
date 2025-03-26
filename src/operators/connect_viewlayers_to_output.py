import bpy
import os
from bpy.types import Operator

class COMPOSITOR_OT_connect_viewlayers_to_output(Operator):
    """Connect all ViewLayers in the file to File Output nodes"""
    bl_idname = "compositor.connect_viewlayers_to_output"
    bl_label = "Connect ViewLayers to File Output"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        if not context.scene.use_nodes:
            context.scene.use_nodes = True
        
        settings = context.scene.viewlayer_connector_settings
        tree = context.scene.node_tree
        
        if not bpy.data.is_saved:
            self.report({'WARNING'}, "Please save the file first")
            return {'CANCELLED'}
            
        base_filename = os.path.splitext(bpy.path.basename(bpy.data.filepath))[0]
        
        viewlayers = context.scene.view_layers
        if not viewlayers:
            self.report({'WARNING'}, "No ViewLayers found in the scene")
            return {'CANCELLED'}
        
        start_x = 0
        start_y = 0
        spacing_y = -300
        
        # Track progress for UI feedback
        wm = context.window_manager
        wm.progress_begin(0, len(viewlayers))
        
        for idx, viewlayer in enumerate(viewlayers):
            wm.progress_update(idx)
            
            viewlayer_name = viewlayer.name
            rl_node = tree.nodes.new('CompositorNodeRLayers')
            rl_node.name = f"ViewLayer_{viewlayer_name}"
            rl_node.label = viewlayer_name
            rl_node.layer = viewlayer_name
            rl_node.location = (start_x, start_y + (idx * spacing_y))
            
            # Main output node (standard settings)
            output_node = tree.nodes.new('CompositorNodeOutputFile')
            output_node.name = f"Output_{viewlayer_name}"
            output_node.label = f"Output {viewlayer_name}"
            output_node.location = (rl_node.location.x + 400, rl_node.location.y)
            
            # Use the custom output path from settings
            output_path = settings.custom_output_path
            if not output_path.endswith(os.sep):
                output_path += os.sep
            output_node.base_path = output_path + base_filename + "_" + viewlayer_name
            
            # Set file format from settings
            output_node.format.file_format = settings.file_format
            
            # Clear existing inputs
            while len(output_node.inputs) > 1:
                output_node.inputs.remove(output_node.inputs[-1])
            
            # Create a separate 32-bit EXR output for specific passes
            extra_output_node = tree.nodes.new('CompositorNodeOutputFile')
            extra_output_node.name = f"ExtraOutput_{viewlayer_name}"
            extra_output_node.label = f"Extra Output {viewlayer_name}"
            extra_output_node.location = (rl_node.location.x + 800, rl_node.location.y)
            
            # Set 32-bit EXR format
            extra_output_node.format.file_format = 'OPEN_EXR'
            extra_output_node.base_path = output_path + base_filename + f"_{viewlayer_name}_extra"
            
            # Specific passes to extract
            extra_passes = ['Position', 'Normal', 'Depth']
            
            # Add Cryptomatte passes if they exist
            cryptomatte_passes = [out for out in rl_node.outputs if out.name.startswith('Cryptomatte')]
            
            # Combine extra passes
            all_extra_passes = extra_passes + [p.name for p in cryptomatte_passes]
            
            # Connect passes to the main and extra output nodes
            first_main_connection = True
            first_extra_connection = True
            
            for output in rl_node.outputs:
                if output.enabled:
                    # Determine if this is an extra pass
                    is_extra_pass = output.name in all_extra_passes
                    
                    # Connect to main output if not extra pass or including all passes
                    if not is_extra_pass or settings.include_all_passes:
                        if first_main_connection:
                            output_node.file_slots[0].path = output.name
                            tree.links.new(output, output_node.inputs[0])
                            first_main_connection = False
                        else:
                            output_node.file_slots.new(output.name)
                            tree.links.new(output, output_node.inputs[-1])
                    
                    # Connect to extra output if it's an extra pass
                    if is_extra_pass:
                        if first_extra_connection:
                            extra_output_node.file_slots[0].path = output.name
                            tree.links.new(output, extra_output_node.inputs[0])
                            first_extra_connection = False
                        else:
                            extra_output_node.file_slots.new(output.name)
                            tree.links.new(output, extra_output_node.inputs[-1])
        
        wm.progress_end()
        self.report({'INFO'}, f"Connected {len(viewlayers)} ViewLayers to File Output nodes")

        # Group the nodes if that option is enabled
        if settings.auto_group:
            from ..utils.node_utils import group_viewlayer_nodes
            group_viewlayer_nodes(tree)

        # Organize the nodes if that option is enabled
        if settings.auto_organize:
            from ..utils.node_utils import arrange_nodes
            arrange_nodes(tree, 'HIERARCHY')
        return {'FINISHED'}