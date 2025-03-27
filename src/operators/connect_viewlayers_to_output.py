import bpy
import os
import re
from bpy.types import Operator

def clean_viewlayer_name(name):
    """
    Clean the viewlayer name:
    1. Replace dots with underscores
    2. Remove the final .vl suffix if present
    3. Add a trailing underscore
    """
    # Remove .vl suffix if present
    if name.endswith(".vl"):
        name = name[:-3]
    
    # Replace dots with underscores
    cleaned_name = name.replace('.', '_')
    
    # Add trailing underscore if not already present
    if not cleaned_name.endswith('_'):
        cleaned_name += '_'
    
    return cleaned_name

def clean_gp_layer_name(name):
    """
    Clean the grease pencil layer name:
    1. Remove the .gp suffix
    2. Replace dots with underscores
    """
    # Remove .gp suffix if present
    if name.endswith(".gp"):
        name = name[:-3]
    
    # Replace dots with underscores
    cleaned_name = name.replace('.', '_')
    
    return cleaned_name

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
        
        # Get the selected output formats and settings from user preferences
        main_format = settings.main_output_format
        use_secondary = settings.use_secondary_output
        secondary_format = settings.secondary_output_format
        
        # Get compression codec settings
        main_compression = settings.main_exr_codec
        secondary_compression = settings.secondary_exr_codec
        
        # Get bit depth settings
        main_bitdepth = settings.main_exr_bitdepth
        secondary_bitdepth = settings.secondary_exr_bitdepth
        
        # Define the specific passes that should go to secondary output
        # These passes will ONLY go to the secondary output node if it's enabled
        secondary_passes = ['Depth', 'Position', 'Normal', 'Vector']
        
        # Track progress for UI feedback
        wm = context.window_manager
        wm.progress_begin(0, len(viewlayers))
        
        # Separate grease pencil layers and regular layers
        gp_layers = []
        regular_layers = []
        
        for viewlayer in viewlayers:
            if viewlayer.name.endswith(".gp"):
                gp_layers.append(viewlayer)
            else:
                regular_layers.append(viewlayer)
        
        # Create a single output node for all grease pencil layers if any exist
        gp_output_node = None
        if gp_layers:
            # Determine bit depth suffix for the GP output
            main_bit_depth_suffix = "EXR16" if main_bitdepth == '16' else "EXR32"
            
            gp_output_node = tree.nodes.new('CompositorNodeOutputFile')
            gp_output_node.name = f"{base_filename}_GP_{main_bit_depth_suffix}_"
            gp_output_node.label = f"{base_filename}_GP_{main_bit_depth_suffix}_"
            gp_output_node.location = (start_x + 400, start_y)
            
            # Use the custom output path from settings
            output_path = settings.custom_output_path
            if not output_path.endswith(os.sep):
                output_path += os.sep
                
            # Create file path for grease pencil output
            gp_output_node.base_path = output_path + f"GP/{base_filename}_GP_{main_bit_depth_suffix}_"
            
            # Set file format based on user selection
            gp_output_node.format.file_format = main_format
            
            # Apply compression codec and bit depth settings for EXR formats
            if main_format in ['OPEN_EXR', 'OPEN_EXR_MULTILAYER']:
                gp_output_node.format.exr_codec = main_compression
                gp_output_node.format.color_depth = main_bitdepth
            
            # Clear existing inputs for GP output
            while len(gp_output_node.inputs) > 1:
                gp_output_node.inputs.remove(gp_output_node.inputs[-1])
        
        # Process grease pencil layers first
        for idx, viewlayer in enumerate(gp_layers):
            wm.progress_update(idx)
            
            # Get the original viewlayer name
            original_viewlayer_name = viewlayer.name
            
            # Clean the viewlayer name for use as the connection name (without .gp suffix)
            cleaned_gp_name = clean_gp_layer_name(original_viewlayer_name)
            
            rl_node = tree.nodes.new('CompositorNodeRLayers')
            rl_node.name = f"ViewLayer_{original_viewlayer_name}"  # Use original for internal reference
            rl_node.label = original_viewlayer_name  # Keep original name in UI
            rl_node.layer = original_viewlayer_name  # Must be original to match actual viewlayer
            rl_node.location = (start_x, start_y + (idx * spacing_y))
            
            # Connect all available outputs to the shared GP output node
            for output_idx, output in enumerate(rl_node.outputs):
                if not output.enabled:
                    continue
                
                # Create a new connection with the cleaned GP name as the connection name
                if output_idx == 0:
                    gp_output_node.file_slots[0].path = cleaned_gp_name
                    tree.links.new(output, gp_output_node.inputs[0])
                else:
                    gp_output_node.file_slots.new(cleaned_gp_name)
                    tree.links.new(output, gp_output_node.inputs[-1])
        
        # Process regular layers (non-GP layers)
        offset = len(gp_layers)
        for idx, viewlayer in enumerate(regular_layers):
            adjusted_idx = idx + offset
            wm.progress_update(adjusted_idx)
            
            # Get the original viewlayer name
            original_viewlayer_name = viewlayer.name
            
            # Clean the viewlayer name for use in file paths and node labels
            cleaned_viewlayer_name = clean_viewlayer_name(original_viewlayer_name)
            
            rl_node = tree.nodes.new('CompositorNodeRLayers')
            rl_node.name = f"ViewLayer_{original_viewlayer_name}"  # Use original for internal reference
            rl_node.label = original_viewlayer_name  # Keep original name in UI
            rl_node.layer = original_viewlayer_name  # Must be original to match actual viewlayer
            rl_node.location = (start_x, start_y + (adjusted_idx * spacing_y))
            
            # Create lists to track what outputs go to which node
            main_outputs = []
            secondary_outputs = []
            
            # Gather all available outputs and sort them
            for output in rl_node.outputs:
                if not output.enabled:
                    continue
                    
                # Check if this is a pass for secondary output
                if output.name in secondary_passes or output.name.startswith('Crypto'):
                    secondary_outputs.append(output)
                else:
                    main_outputs.append(output)
            
            # Determine bit depth suffix for the main output
            main_bit_depth_suffix = "EXR16" if main_bitdepth == '16' else "EXR32"
            
            # Main output node with user-selected format
            main_output_node = tree.nodes.new('CompositorNodeOutputFile')
            main_output_node.name = f"{base_filename}_{cleaned_viewlayer_name}{main_bit_depth_suffix}_"
            main_output_node.label = f"{base_filename}_{cleaned_viewlayer_name}{main_bit_depth_suffix}_"
            main_output_node.location = (rl_node.location.x + 400, rl_node.location.y)
            
            # Use the custom output path from settings
            output_path = settings.custom_output_path
            if not output_path.endswith(os.sep):
                output_path += os.sep
                
            # Create file path in the new format
            main_output_node.base_path = output_path + f"{cleaned_viewlayer_name}/{base_filename}_{cleaned_viewlayer_name}{main_bit_depth_suffix}_"
            
            # Set file format based on user selection
            main_output_node.format.file_format = main_format
            
            # Apply compression codec and bit depth settings for EXR formats
            if main_format in ['OPEN_EXR', 'OPEN_EXR_MULTILAYER']:
                main_output_node.format.exr_codec = main_compression
                main_output_node.format.color_depth = main_bitdepth
            
            # Clear existing inputs for main output
            while len(main_output_node.inputs) > 1:
                main_output_node.inputs.remove(main_output_node.inputs[-1])
            
            # Create a secondary output node if enabled
            secondary_output_node = None
            if use_secondary:
                # Determine bit depth suffix for the secondary output
                secondary_bit_depth_suffix = "EXR16" if secondary_bitdepth == '16' else "EXR32"
                
                secondary_output_node = tree.nodes.new('CompositorNodeOutputFile')
                secondary_output_node.name = f"{base_filename}_{cleaned_viewlayer_name}{secondary_bit_depth_suffix}_"
                secondary_output_node.label = f"{base_filename}_{cleaned_viewlayer_name}{secondary_bit_depth_suffix}_"
                secondary_output_node.location = (rl_node.location.x + 800, rl_node.location.y)
                
                # Set user-selected format for the secondary output
                secondary_output_node.format.file_format = secondary_format
                
                # Apply compression codec and bit depth settings for EXR formats
                if secondary_format in ['OPEN_EXR', 'OPEN_EXR_MULTILAYER']:
                    secondary_output_node.format.exr_codec = secondary_compression
                    secondary_output_node.format.color_depth = secondary_bitdepth
                
                secondary_output_node.base_path = output_path + f"{cleaned_viewlayer_name}/{base_filename}_{cleaned_viewlayer_name}{secondary_bit_depth_suffix}_"
                
                # Clear existing inputs for secondary output
                while len(secondary_output_node.inputs) == 1:
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
        
        # Use frame-based grouping if enabled
        if settings.auto_frame_by_prefix:
            from ..utils.node_utils import group_nodes_by_prefix_in_frames
            group_nodes_by_prefix_in_frames(tree)
        # Or organize the nodes if that option is enabled
        elif settings.auto_organize:
            from ..utils.node_utils import arrange_nodes
            arrange_nodes(tree, 'HIERARCHY')
            
        return {'FINISHED'}