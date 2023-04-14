# Basic recursive implementation of Dijkstra for 2D surfaces.
# ____________________________________________________________________________________________________

# Note that an iterative version of the algorithm is necessary for dealing with large, high resolution
# surfaces since the Python's recursion limit will be easily reached and upping the limit simply breaks
# something else.

# Not sure how the ESRI tools work under-the-hood, but the idea here is that once the cost calculation on
# the surface is completed, generating cost path geometry and converting back over to vector is relatively 
# straightforward. Most of this stuff is not ESRI specific, so could be used with other stacks as well, 
# just need to find the right libraries for dealing with rasters & vectors.


# Create the adjacency list for determining the cost path
def construct_adjacency_list(input_graph: np.darray):
    # Length of the rows and columsn in the graph
    maximum_y = len(input_graph)
    maximum_x = len(input_graph[0])
    list_position = 0
    adjacency_list = np.empty((maximum_y * maximum_x, 9, 4), dtype=object)
    # Loop through every node in the graph object.  Graph is assumed to be a 2D data structure in this case
    for y in range(maximum_y):
        for x in range(maximum_x):
            center = np.array([list_position, y, x, input_graph[y][x]])
            # Define the X and Y coordinates of the 4 cardinal neighbors
            n_y, e_y, s_y, w_y = y - 1, y, y + 1, y
            n_x, e_x, s_x, w_x = x, x + 1, x, x - 1
            # Test whether or not the node/cell is an edge case.  One of the dependencies commonly used with
            # this tool sets the raster origin point at the top left, so y==0 at the northern edge rather than
            # southern edge
            northern_edge = y == 0
            eastern_edge = x == maximum_x - 1
            southern_edge = y == maximum_y - 1
            western_edge = x == 0
            # Set special values for edge cases
            if northern_edge:
                n, ne, nw = (np.array([-5] * 4) for i in range(3))
            if eastern_edge:
                e, se, ne = (np.array([-5] * 4) for i in range(3))
            if southern_edge:
                s, se, sw = (np.array([-5] * 4) for i in range(3))
            if western_edge:
                w, sw, nw = (np.array([-5] * 4) for i in range(3))
            # Characterize the neighbors of the central node
            if not northern_edge:
                neighbor_node_id = n_y * maximum_x + n_x
                n = np.array([neighbor_node_id, n_y, n_x, input_graph[n_y][n_x]])
            if not northern_edge and not eastern_edge:
                neighbor_node_id = n_y * maximum_x + e_x
                ne = np.array([neighbor_node_id, n_y, e_x, input_graph[n_y][e_x]])
            if not eastern_edge:
                neighbor_node_id = e_y * maximum_x + e_x
                e = np.array([neighbor_node_id, e_y, e_x, input_graph[e_y][e_x]])
            if not southern_edge and not eastern_edge:
                neighbor_node_id = s_y * maximum_x + e_x
                se = np.array([neighbor_node_id, s_y, e_x, input_graph[s_y][e_x]])
            if not southern_edge:
                neighbor_node_id = s_y * maximum_x + s_x
                s = np.array([neighbor_node_id, s_y, s_x, input_graph[s_y][s_x]])
            if not southern_edge and not western_edge:
                neighbor_node_id = s_y * maximum_x + w_x
                sw = np.array([neighbor_node_id, s_y, w_x, input_graph[s_y][w_x]])
            if not western_edge:
                neighbor_node_id = w_y * maximum_x + w_x
                w = np.array([neighbor_node_id, w_y, w_x, input_graph[w_y][w_x]])
            if not northern_edge and not western_edge:
                neighbor_node_id = n_y * maximum_x + w_x
                nw = np.array([neighbor_node_id, n_y, w_x, input_graph[n_y][w_x]])

            neighbor_node = np.array([center, n, ne, e, se, s, sw, w, nw], dtype=object)

            adjacency_list[list_position] = neighbor_node
            list_position += 1
    return adjacency_list


# Create the ancillary lists we need:
def create_ancillary_lists(starting_position: int, adjacency_list: np.darray):
    adjacency_list_length = len(adjacency_list)
    # Create arrays to keep track of nodes we have visited and those we haven't
    visited_list = np.array([-1] * adjacency_list_length)
    not_visited_list = np.arange(adjacency_list_length)
    # Create the cost table as a float becasue the inifity capability is useful
    cost_list = np.zeros((adjacency_list_length, 3), dtype="float32")
    # Populate the cost table with default values
    for j in range(0, adjacency_list_length):
        cost_list[i][0] = j
        # When initializing the cost list, the cost to reach the starting position
        # should be zero since we're already there, otherwise, set it to infinity
        # to bullet proof the cost computation
        if j == starting_position:
            cost_list[i][1] = 0
        else:
            cost_list[i][1] = np.inf
    return visited_list, not_visited_list, cost_list


# Create the cost surface using starting & destination positions along with the adjacency list created prior
def analyze_cost_for_surface(
    visited_list: np.darray,
    not_visited_list: np.darray,
    cost_list: np.darray,
    goal_destination: int,
    adjacency_list: np.darray,
):
    # Initialize minimum cost as infinity, ensuring anything less than infinity will get a visit.  Set the
    # least cost node ID to a number that doesn't actually exist to avoid confusion
    least_cost = np.inf
    least_cost_node_id = -1
    # Find the ID and cost of the item in the cost list with the lowest cost
    least_cost_node = min(
        ((i, c) for i, c in enumerate(cost_list) if visited_list[i] == -1),
        key=lambda x: x[1][1],
    )
    least_cost_node_id, least_cost = least_cost_node
    # Now that we've found the node with the minimum cost in our cost list, loop through its neighbor nodes and
    # determine the cost to get to them
    for neighbor_node in adjacency_list[least_cost_node_id]:
        neighbor_node_id = neighbor_node[0]
        if neighbor_node_id != -5:  # Literal edge case
            cost_to_node = least_cost + neighbor_node[3]
            if cost_to_node < cost_list[neighbor_node_id][1]:
                cost_list[neighbor_node_id][1] = cost_to_node
                cost_list[neighbor_node_id][2] = least_cost_node_id
    # Update the visited/not visited lists
    visited_list[least_cost_node_id] = least_cost_node_id
    not_visited_list[least_cost_node_id] = -1

    # Run the process recursively until we visit the goal position
    if not_visited_list[goal_destination] != -1:
        (
            visited_list,
            not_visited_list,
            cost_list,
            goal_destination,
        ) = analyze_cost_for_surface(
            visited_list, not_visited_list, cost_list, goal_destination, adjacency_list
        )

    return visited_list, not_visited_list, cost_list, goal_destination


# Construct the least cost path node by node by working backwards from the goal position
def trace_minimum_cost_path(
    current_node: int,
    cost_list: np.darray,
    starting_node: int,
    goal_destination: int,
    min_cost_nodes_list: list[int],
):
    # If we haven't visited any nodes yet, start at the goal destination and work backwards from there
    if current_node == -1:
        current_node = goal_destination
    else:
        current_node = int(cost_list[current_node][2])
    min_cost_nodes_list.append(current_node)
    # Run the process recursively until we arrive at the start position
    if current_node != starting_node:
        current_node, min_cost_nodes_list = trace_minimum_cost_path(
            current_node,
            cost_list,
            starting_node,
            goal_destination,
            min_cost_nodes_list,
        )
    else:
        min_cost_nodes_list.append(starting_node)

    return current_node, min_cost_nodes_list
