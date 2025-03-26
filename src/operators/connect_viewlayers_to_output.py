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
        
        # Get the selected output formats from settings
        main_format = settings.main_output_format
        use_secondary = settings.use_secondary_output
        secondary_format = settings.secondary_output_format
        
        # Get compression codec settings
        main_compression = settings.main_exr_codec
        secondary_compression = settings.secondary_exr_codec
        
        # Define the specific passes that should go to secondary output
        # These passes will ONLY go to the secondary output node if it's enabled
        secondary_passes = ['Depth', 'Position', 'Normal']
        
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
            
            # Create lists to track what outputs go to which node
            # We'll collect all outputs first, then connect them
            main_outputs = []
            secondary_outputs = []
            
            # Gather all available outputs and sort them
            for output in rl_node.outputs:
                if not output.enabled:
                    continue
                    
                # Check if this is a pass for secondary output
                if output.name in secondary_passes or output.name.startswith('Cryptomatte'):
                    secondary_outputs.append(output)
                else:
                    main_outputs.append(output)
            
            # Main output node with user-selected format
            main_output_node = tree.nodes.new('CompositorNodeOutputFile')
            main_output_node.name = f"MainOutput_{viewlayer_name}"
            main_output_node.label = f"Main Output {viewlayer_name}"
            main_output_node.location = (rl_node.location.x + 400, rl_node.location.y)
            
            # Use the custom output path from settings
            output_path = settings.custom_output_path
            if not output_path.endswith(os.sep):
                output_path += os.sep
            main_output_node.base_path = output_path + base_filename + "_" + viewlayer_name
            
            # Set file format based on user selection
            main_output_node.format.file_format = main_format
            
            # Apply compression codec settings for EXR formats
            if main_format in ['OPEN_EXR', 'OPEN_EXR_MULTILAYER']:
                main_output_node.format.exr_codec = main_compression
            
            # Clear existing inputs for main output
            while len(main_output_node.inputs) > 1:
                main_output_node.inputs.remove(main_output_node.inputs[-1])
            
            # Create a secondary output node if enabled
            secondary_output_node = None
            if use_secondary:
                secondary_output_node = tree.nodes.new('CompositorNodeOutputFile')
                secondary_output_node.name = f"SecondaryOutput_{viewlayer_name}"
                secondary_output_node.label = f"Secondary Output {viewlayer_name}"
                secondary_output_node.location = (rl_node.location.x + 800, rl_node.location.y)
                
                # Set user-selected format for the secondary output
                secondary_output_node.format.file_format = secondary_format
                
                # Apply compression codec settings for EXR formats
                if secondary_format in ['OPEN_EXR', 'OPEN_EXR_MULTILAYER']:
                    secondary_output_node.format.exr_codec = secondary_compression
                
                secondary_output_node.base_path = output_path + base_filename + f"_{viewlayer_name}_secondary"
                
                # Clear existing inputs for secondary output
                while len(secondary_output_node.inputs) > 1:
                    secondary_output_node.inputs.remove(secondary_output_node.inputs[-1])
                    
                # Connect secondary passes to secondary output node
                first_connection = True
                for output in secondary_outputs:
                    if first_connection:
                        secondary_output_node.file_slots[0].path = output.name
                        tree.links.new(output, secondary_output_node.inputs[0])
                        first_connection = False
                    else:
                        secondary_output_node.file_slots.new(output.name)
                        tree.links.new(output, secondary_output_node.inputs[-1])
            
            # Connect main passes to main output node
            # If secondary output is disabled, include secondary passes here too
            outputs_for_main = main_outputs.copy()
            if not use_secondary:
                outputs_for_main.extend(secondary_outputs)
                
            # Now connect all the outputs for the main node
            first_connection = True
            for output in outputs_for_main:
                if first_connection:
                    main_output_node.file_slots[0].path = output.name
                    tree.links.new(output, main_output_node.inputs[0])
                    first_connection = False
                else:
                    main_output_node.file_slots.new(output.name)
                    tree.links.new(output, main_output_node.inputs[-1])
        
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