import bpy
import math

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
    nodes = tree.nodes
    
    if organize_type == 'GRID':
        # Simple grid arrangement
        grid_size = math.ceil(math.sqrt(len(nodes)))
        for i, node in enumerate(nodes):
            row = i // grid_size
            col = i % grid_size
            node.location = (col * 300, -row * 300)
    
    elif organize_type == 'FLOW':
        # Arrange nodes in a left-to-right flow
        # First, find all render layer nodes (starting points)
        render_layer_nodes = [n for n in nodes if n.type == 'R_LAYERS']
        
        # Position render layer nodes vertically
        for i, node in enumerate(render_layer_nodes):
            node.location = (0, -i * 300)
        
        # TODO: Implement a more sophisticated flow layout algorithm
        # This would need to follow the connections between nodes
    
    elif organize_type == 'HIERARCHY':
        # Group nodes by their connections
        # For each render layer node and its output node
        viewlayer_nodes = []
        for n in nodes:
            if n.type == 'R_LAYERS':
                # Find connected output nodes
                output_nodes = [link.to_node for out in n.outputs for link in out.links if link.to_node.type == 'OUTPUT_FILE']
                viewlayer_nodes.append((n, output_nodes))
        
        for i, (rl_node, output_nodes) in enumerate(viewlayer_nodes):
            # Spread output nodes horizontally
            x_spacing = 300
            start_x = 0
            
            # Position render layer node
            rl_node.location = (start_x, -i * 300)
            
            # Position output nodes
            for j, output_node in enumerate(output_nodes):
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