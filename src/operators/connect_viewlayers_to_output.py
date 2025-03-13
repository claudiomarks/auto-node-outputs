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
        
        tree = context.scene.node_tree
        base_filename = os.path.splitext(bpy.path.basename(bpy.data.filepath))[0]
        if not base_filename:
            base_filename = "untitled"
        
        viewlayers = context.scene.view_layers
        if not viewlayers:
            self.report({'WARNING'}, "No ViewLayers found in the scene")
            return {'CANCELLED'}
        
        start_x = 0
        start_y = 0
        spacing_y = -300
        
        for idx, viewlayer in enumerate(viewlayers):
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
            output_node.base_path = f"//" + base_filename + "_" + viewlayer_name
            output_node.format.file_format = 'OPEN_EXR_MULTILAYER'
            
            while len(output_node.inputs) > 1:
                output_node.inputs.remove(output_node.inputs[-1])
            
            first_connection = True
            for output in rl_node.outputs:
                if output.enabled:
                    if first_connection:
                        output_node.file_slots[0].path = output.name
                        tree.links.new(output, output_node.inputs[0])
                        first_connection = False
                    else:
                        output_node.file_slots.new(output.name)
                        tree.links.new(output, output_node.inputs[-1])
        
        self.report({'INFO'}, f"Connected {len(viewlayers)} ViewLayers to File Output nodes")
        return {'FINISHED'}