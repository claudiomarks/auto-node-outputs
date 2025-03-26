import bpy
import math
import re

def create_node_group(tree, nodes, name):
    """Create a group node containing the specified nodes"""
    # Create a new node group
    group = bpy.data.node_groups.new(name, 'CompositorNodeTree')
    
    # Create input/output interfaces
    group_inputs = group.nodes.new('NodeGroupInput')
    group_inputs.location = (-200, 0)
    group_outputs = group.nodes.new('NodeGroupOutput')
    group_outputs.location = (400, 0)
    
    # Track external connections and node mapping
    external_inputs = {}  # {(to_node, to_socket_name): (from_node, from_socket)}
    external_outputs = {}  # {(from_node, from_socket_name): [(to_node, to_socket)]}
    old_to_new_nodes = {}  # Map original nodes to their copies in the group
    
    # First pass: identify all external connections
    for node in nodes:
        for input_idx, input_socket in enumerate(node.inputs):
            for link in input_socket.links:
                if link.from_node not in nodes:  # External input
                    key = (node, input_socket.name)
                    external_inputs[key] = (link.from_node, link.from_socket)
        
        for output_idx, output_socket in enumerate(node.outputs):
            for link in output_socket.links:
                if link.to_node not in nodes:  # External output
                    key = (node, output_socket.name)
                    if key not in external_outputs:
                        external_outputs[key] = []
                    external_outputs[key].append((link.to_node, link.to_socket))
    
    # Second pass: copy nodes to the group
    for node in nodes:
        # Create a new node in the group
        new_node = group.nodes.new(node.bl_idname)
        old_to_new_nodes[node] = new_node
        
        # Copy basic properties
        new_node.name = node.name
        new_node.label = node.label
        new_node.location = node.location
        
        # Copy specific properties based on node type
        if node.type == 'R_LAYERS':
            new_node.layer = node.layer
        elif node.type == 'OUTPUT_FILE':
            new_node.base_path = node.base_path
            new_node.format.file_format = node.format.file_format
            # Copy file slots
            while len(new_node.file_slots) > 0:
                new_node.file_slots.remove(new_node.file_slots[0])
            for slot in node.file_slots:
                new_slot = new_node.file_slots.new(slot.path)
    
    # Third pass: create interface sockets and internal connections
    input_map = {}  # Map (node, socket_name) to group input index
    output_map = {}  # Map (node, socket_name) to group output index
    
    # Create group input sockets
    for (node, socket_name), (from_node, from_socket) in external_inputs.items():
        new_socket = group.inputs.new(from_socket.bl_idname, socket_name)
        input_map[(node, socket_name)] = len(group.inputs) - 1
    
    # Create group output sockets
    for (node, socket_name), to_links in external_outputs.items():
        for to_node, to_socket in to_links:
            new_socket = group.outputs.new(to_socket.bl_idname, socket_name)
            output_map[(node, socket_name)] = len(group.outputs) - 1
    
    # Create internal links
    for link in tree.links:
        if link.from_node in nodes and link.to_node in nodes:
            from_node = old_to_new_nodes[link.from_node]
            to_node = old_to_new_nodes[link.to_node]
            # Find the matching sockets by name
            from_socket = None
            to_socket = None
            for s in from_node.outputs:
                if s.name == link.from_socket.name:
                    from_socket = s
                    break
            for s in to_node.inputs:
                if s.name == link.to_socket.name:
                    to_socket = s
                    break
            if from_socket and to_socket:
                group.links.new(from_socket, to_socket)
    
    # Connect group inputs to node inputs
    for (node, socket_name), idx in input_map.items():
        new_node = old_to_new_nodes[node]
        for socket in new_node.inputs:
            if socket.name == socket_name:
                group.links.new(group_inputs.outputs[idx], socket)
                break
    
    # Connect node outputs to group outputs
    for (node, socket_name), idx in output_map.items():
        new_node = old_to_new_nodes[node]
        for socket in new_node.outputs:
            if socket.name == socket_name:
                group.links.new(socket, group_outputs.inputs[idx])
                break
    
    # Create the group node in the original tree
    group_node = tree.nodes.new('CompositorNodeGroup')
    group_node.node_tree = group
    group_node.name = name
    group_node.label = name
    group_node.location = (nodes[0].location.x + 100, nodes[0].location.y)
    
    # Connect external inputs to the group node
    for (node, socket_name), (from_node, from_socket) in external_inputs.items():
        idx = input_map[(node, socket_name)]
        tree.links.new(from_socket, group_node.inputs[idx])
    
    # Connect the group node to external outputs
    for (node, socket_name), to_links in external_outputs.items():
        idx = output_map[(node, socket_name)]
        for to_node, to_socket in to_links:
            tree.links.new(group_node.outputs[idx], to_socket)
    
    # Remove original nodes
    for node in nodes:
        tree.nodes.remove(node)
    
    return group_node

def arrange_nodes(tree, organize_type='GRID'):
    """Arrange nodes in the compositor tree"""
    # Get all nodes
    nodes = list(tree.nodes)
    
    # If no nodes, return immediately
    if not nodes:
        return {'FINISHED'}
    
    if organize_type == 'GRID':
        # Simple grid arrangement
        grid_size = max(1, math.ceil(math.sqrt(len(nodes))))
        for i, node in enumerate(nodes):
            row = i // grid_size
            col = i % grid_size
            node.location = (col * 300, -row * 300)
    
    elif organize_type == 'FLOW':
        # Arrange nodes in a left-to-right flow
        render_layer_nodes = [n for n in nodes if n.type == 'R_LAYERS']
        
        if not render_layer_nodes:
            # Fallback to grid if no render layer nodes
            grid_size = max(1, math.ceil(math.sqrt(len(nodes))))
            for i, node in enumerate(nodes):
                row = i // grid_size
                col = i % grid_size
                node.location = (col * 300, -row * 300)
        else:
            # Position render layer nodes vertically
            for i, node in enumerate(render_layer_nodes):
                node.location = (0, -i * 300)
    
    elif organize_type == 'HIERARCHY':
        # Find render layer and output nodes
        rl_nodes = [n for n in nodes if n.type == 'R_LAYERS']
        output_nodes = [n for n in nodes if n.type == 'OUTPUT_FILE']
        
        # If no render layer or output nodes, fallback to grid
        if not rl_nodes or not output_nodes:
            grid_size = max(1, math.ceil(math.sqrt(len(nodes))))
            for i, node in enumerate(nodes):
                row = i // grid_size
                col = i % grid_size
                node.location = (col * 300, -row * 300)
        else:
            # Attempt to match render layer nodes with output nodes
            for i, rl_node in enumerate(rl_nodes):
                # Find matching output nodes connected to this render layer
                # Fixed: Check link validity properly without accessing is_valid on sockets
                connected_outputs = []
                for out_node in output_nodes:
                    for link in tree.links:
                        # Check if this link connects the render layer node to this output node
                        if link.from_node == rl_node and link.to_node == out_node:
                            if out_node not in connected_outputs:
                                connected_outputs.append(out_node)
                                break
                
                # Position render layer node
                start_x = 0
                rl_node.location = (start_x, -i * 300)
                
                # Position output nodes
                x_spacing = 300
                for j, output_node in enumerate(connected_outputs):
                    output_node.location = (start_x + (j + 1) * x_spacing, -i * 300)
    
    return {'FINISHED'}

def get_connected_output(tree, node):
    """Find the output node connected to the given node"""
    for output in node.outputs:
        for link in output.links:
            if link.to_node.type == 'OUTPUT_FILE':
                return link.to_node
    return None

def sort_viewlayers(scene, sort_type='ALPHABETICAL'):
    """Sort viewlayers by the specified method"""
    viewlayers = list(scene.view_layers)
    
    if sort_type == 'ALPHABETICAL':
        # Sort alphabetically
        viewlayers.sort(key=lambda vl: vl.name.lower())
    elif sort_type == 'CUSTOM':
        # Sort by custom property (would need to be added to viewlayers)
        pass
    
    # Return the sorted list
    return viewlayers

def clear_all_viewlayer_nodes(tree):
    """Remove all viewlayer and output nodes"""
    nodes_to_remove = []
    
    for node in tree.nodes:
        if node.type == 'R_LAYERS' or node.type == 'OUTPUT_FILE':
            nodes_to_remove.append(node)
    
    # Remove the nodes
    for node in nodes_to_remove:
        tree.nodes.remove(node)
    
    return len(nodes_to_remove)

def group_viewlayer_nodes(tree):
    """Group each viewlayer node with its corresponding output nodes"""
    viewlayer_nodes = [n for n in tree.nodes if n.type == 'R_LAYERS']
    groups_created = 0
    
    for vl_node in viewlayer_nodes:
        # Find all connected output nodes
        output_nodes = [link.to_node for out in vl_node.outputs for link in out.links if link.to_node.type == 'OUTPUT_FILE']
        
        if output_nodes:
            group_name = f"ViewLayer_{vl_node.name}_Group"
            create_node_group(tree, [vl_node] + output_nodes, group_name)
            groups_created += 1
    
    return groups_created

# New functions for prefix-based grouping

def extract_prefix(name):
    """Extract prefix from a name based on common separators"""
    # Common separators: underscore, dot, dash, or space
    separators = ['_', '.', '-', ' ']
    
    for sep in separators:
        if sep in name:
            # Get the prefix part (before the first separator)
            return name.split(sep)[0]
    
    # If no separator is found, use the first 3 characters or the whole name if shorter
    return name[:min(3, len(name))]

def group_nodes_by_prefix_in_frames(tree):
    """Group nodes by their prefix and place them in frames"""
    viewlayer_nodes = [n for n in tree.nodes if n.type == 'R_LAYERS']
    
    # Dictionary to group nodes by their prefix
    prefix_groups = {}
    
    # First, categorize all viewlayer nodes by their prefix
    for vl_node in viewlayer_nodes:
        layer_name = vl_node.layer  # Get the original layer name
        prefix = extract_prefix(layer_name)
        
        if prefix not in prefix_groups:
            prefix_groups[prefix] = []
            
        # Find connected output nodes
        output_nodes = []
        for out in vl_node.outputs:
            for link in out.links:
                if link.to_node.type == 'OUTPUT_FILE' and link.to_node not in output_nodes:
                    output_nodes.append(link.to_node)
        
        # Add the viewlayer node and its outputs to the prefix group
        prefix_groups[prefix].append((vl_node, output_nodes))
    
    # Create frames for each prefix group
    frames_created = 0
    vertical_offset = 0
    frame_spacing = 500  # Space between frames vertically
    
    for prefix, node_groups in prefix_groups.items():
        if not node_groups:  # Skip empty groups
            continue
            
        # Create a frame
        frame_node = tree.nodes.new('NodeFrame')
        frame_node.name = f"Frame_{prefix}"
        frame_node.label = f"Prefix: {prefix}"
        frame_node.use_custom_color = True
        
        # Generate a unique color based on the prefix
        # This creates a pseudo-random but consistent color for each prefix
        color_seed = sum(ord(c) for c in prefix)
        frame_node.color = (
            (color_seed * 13 % 100) / 100,  # R component
            (color_seed * 23 % 100) / 100,  # G component
            (color_seed * 37 % 100) / 100   # B component
        )
        
        # Arrange nodes within the frame
        horizontal_spacing = 400
        
        for i, (vl_node, connected_outputs) in enumerate(node_groups):
            # Position the viewlayer node and assign it to the frame
            vl_node.location = (0, -i * 300)
            vl_node.parent = frame_node
            
            # Position and parent the connected output nodes
            for j, output_node in enumerate(connected_outputs):
                output_node.location = ((j + 1) * horizontal_spacing, -i * 300)
                output_node.parent = frame_node
        
        # Adjust the frame position
        frame_node.location = (0, vertical_offset)
        vertical_offset -= frame_spacing + len(node_groups) * 300
        
        frames_created += 1
    
    return frames_created