from gdpc import Editor, Block
from gdpc.vector_tools import Rect
import numpy as np
import random
import os
import sys
import math
import json
from house_blueprints import HouseBlueprintFactory, MAX_STILT_HEIGHT

# Create a directory for house coordinates
coords_dir = "stilt_house_coordinates"
os.makedirs(coords_dir, exist_ok=True)

def fast_tree_clearing(editor, x, z, width, length, floor_y, buffer=3):
    """
    Optimized tree clearing algorithm that is much faster while still being effective.
    
    Parameters:
    editor: The Minecraft world editor
    x, z: Starting coordinates
    width, length: The size of the area to clear
    floor_y: The floor level of the house
    buffer: Additional blocks to clear around the perimeter (default: 3)
    
    Returns:
    int: Number of tree blocks cleared
    """
    import time
    
    tree_blocks = 0
    start_time = time.time()
    
    # Expand clearing area with buffer
    clear_x = x - buffer
    clear_z = z - buffer
    clear_width = width + buffer * 2
    clear_length = length + buffer * 2
    
    print(f"Fast clearing trees in area ({clear_x}, {clear_z}) to ({clear_x + clear_width}, {clear_z + clear_length})...")
    
    # Tree block types to identify - simplified list for faster string matching
    tree_block_types = ["log", "leaves", "stem", "trunk"]
    
    # Define clearing area more efficiently - focus mainly on where the house will be
    # Core area (house footprint) - check every block
    core_x1, core_z1 = x, z
    core_x2, core_z2 = x + width - 1, z + length - 1
    
    # Buffer area - check with lower density
    buffer_x1, buffer_z1 = clear_x, clear_z
    buffer_x2, buffer_z2 = clear_x + clear_width - 1, clear_z + clear_length - 1
    
    # Use different sampling densities based on area
    core_xstep = core_zstep = 1  # Check every block in core area
    buffer_xstep = buffer_zstep = 2  # Check every other block in buffer area
    
    # Use a lower vertical range for faster scanning - most trees are under 20 blocks
    vertical_range = 20  # Maximum typical tree height
    vertical_step = 2  # Check every other vertical block
    
    # Skip ground level detection - clear from a fixed range instead
    # This saves an entire pass through the area
    min_y = floor_y - 3  # Slightly below floor
    max_y = floor_y + vertical_range  # Well above floor
    
    # Tree removal approach: clear from top to bottom to handle falling blocks
    # This is more efficient than clearing bottom-up
    
    # Track a minimal set of positions for efficiency
    cleared_count = 0
    batch_size = 10  # Process in small batches to maintain responsiveness
    positions_to_clear = []
    
    # First check and mark tree blocks in the core area (house footprint) - thorough check
    print("Scanning house footprint area...")
    for curr_y in range(max_y, min_y, -vertical_step):
        for curr_x in range(core_x1, core_x2 + 1, core_xstep):
            for curr_z in range(core_z1, core_z2 + 1, core_zstep):
                try:
                    block = editor.getBlock((curr_x, curr_y, curr_z))
                    if block:
                        block_id = block.id.lower()
                        if any(tree_type in block_id for tree_type in tree_block_types):
                            positions_to_clear.append((curr_x, curr_y, curr_z))
                            
                            # Process in batches
                            if len(positions_to_clear) >= batch_size:
                                for pos in positions_to_clear:
                                    editor.placeBlock(pos, Block("air"))
                                cleared_count += len(positions_to_clear)
                                positions_to_clear = []
                                
                except Exception:
                    continue  # Skip any errors and continue
    
    # Then check the buffer area with reduced sampling density
    print("Scanning buffer area...")
    for curr_y in range(max_y, min_y, -vertical_step):
        for curr_x in range(buffer_x1, buffer_x2 + 1, buffer_xstep):
            for curr_z in range(buffer_z1, buffer_z2 + 1, buffer_zstep):
                # Skip if already in core area
                if (core_x1 <= curr_x <= core_x2 and core_z1 <= curr_z <= core_z2):
                    continue
                    
                try:
                    block = editor.getBlock((curr_x, curr_y, curr_z))
                    if block:
                        block_id = block.id.lower()
                        if any(tree_type in block_id for tree_type in tree_block_types):
                            positions_to_clear.append((curr_x, curr_y, curr_z))
                            
                            # Process in batches
                            if len(positions_to_clear) >= batch_size:
                                for pos in positions_to_clear:
                                    editor.placeBlock(pos, Block("air"))
                                cleared_count += len(positions_to_clear)
                                positions_to_clear = []
                except Exception:
                    continue  # Skip any errors and continue
    
    # Clear any remaining positions
    if positions_to_clear:
        for pos in positions_to_clear:
            try:
                editor.placeBlock(pos, Block("air"))
                cleared_count += 1
            except Exception:
                continue
    
    # Report time taken
    elapsed_time = time.time() - start_time
    print(f"Tree clearing completed in {elapsed_time:.2f} seconds")
    print(f"Cleared approximately {cleared_count} tree blocks")
    
    return cleared_count

def determine_stilt_height_for_location(editor, x, y, z, terrain_type, width, length):
    """
    Determine appropriate stilt height based on terrain type and actual ground level.
    Scans the area to find the best stilt height that adapts to terrain.
    """
    actual_y = y  # Default ground level
    
    # Sample points across the house footprint
    sample_coords = [
        (x, z),                   # Front-left
        (x + width - 1, z),       # Front-right
        (x, z + length - 1),      # Back-left
        (x + width - 1, z + length - 1),  # Back-right
        (x + width//2, z + length//2)     # Center
    ]
    
    # Find the highest and lowest ground points
    max_height = 0
    min_height = 256
    water_depth = 0
    water_points = 0
    
    for sample_x, sample_z in sample_coords:
        # Scan downward to find ground level
        for check_y in range(y + 30, y - 30, -1):
            block = editor.getBlock((sample_x, check_y, sample_z))
            
            if block:
                block_id = block.id
                
                # Check if it's water
                if "water" in block_id:
                    water_depth += 1
                    water_points += 1
                    continue
                
                # Found solid ground
                if block_id != "minecraft:air" and "leaves" not in block_id:
                    max_height = max(max_height, check_y)
                    min_height = min(min_height, check_y)
                    actual_y = min_height  # Use the lowest point as the base
                    break
    
    # Calculate height difference (for slopes)
    height_diff = max_height - min_height
    
    # Determine stilt height based on terrain type
    if terrain_type == 2:  # Water
        # Water - stilts should clear the water
        if water_points > 0:
            avg_water_depth = water_depth / water_points
            stilt_height = min(MAX_STILT_HEIGHT, max(5, int(avg_water_depth) + 1))
        else:
            stilt_height = 8  # Default if we didn't detect water properly
    elif terrain_type == 1:  # Hill/slope
        # Hill - stilts should compensate for the slope
        if height_diff > 3:
            # Significant slope - use taller stilts
            stilt_height = min(MAX_STILT_HEIGHT, max(4, height_diff))
        else:
            # Gentle slope - use moderate stilts
            stilt_height = min(MAX_STILT_HEIGHT, max(3, height_diff + 1))
    else:  # Flat
        # Flat ground - use modest stilts
        stilt_height = random.randint(2, 3)
    
    return actual_y, stilt_height

def build_stilt_house(editor, x, y, z, terrain_type, blueprint=None, clear_trees=True):
    """
    Build a stilt house adapted to the terrain type (flat, hill, or water).
    Uses a blueprint for house design and clears trees before building.
    """
    # Ensure coordinates are integers
    x, y, z = int(x), int(y), int(z)
    
    # Create a blueprint if none provided
    if blueprint is None:
        blueprint = HouseBlueprintFactory.create_house("stilt")
    
    # Extract dimensions from blueprint
    width, height, length = blueprint.width, blueprint.height, blueprint.length
    
    # Determine actual ground level and appropriate stilt height
    ground_y, stilt_height = determine_stilt_height_for_location(
        editor, x, y, z, terrain_type, width, length
    )
    
    # Update y to the actual ground level
    y = ground_y
    floor_y = y + stilt_height
    
    # Update blueprint with terrain information
    blueprint.stilt_height = stilt_height
    blueprint.adapt_to_terrain(terrain_type, stilt_height)
    
    # Extract materials
    planks, logs, fence, stairs, door, trapdoor = blueprint.materials
    secondary_material = blueprint.secondary_material
    
    print(f"Building {blueprint.style} {blueprint.size} stilt house at ({x}, {y}, {z}) with stilt height: {stilt_height}")
    print(f"Terrain type: {'Water' if terrain_type == 2 else 'Hill' if terrain_type == 1 else 'Flat'}")
    print(f"Materials: {blueprint.wood_type} wood with {secondary_material} accents")
    
    # ALWAYS clear trees in the area before construction using fast tree clearing
    if clear_trees:
        print("Clearing trees before construction using optimized algorithm...")
        trees_cleared = fast_tree_clearing(editor, x, z, width, length, floor_y, buffer=3)
        if trees_cleared > 0:
            print(f"Cleared {trees_cleared} tree blocks to make space for the house")
    
    # 1. Build stilts (pillars)
    for stilt_dx, stilt_dz in blueprint.stilt_positions:
        stilt_x, stilt_z = x + stilt_dx, z + stilt_dz
        
        # Find actual ground level for this stilt
        actual_stilt_y = y
        for check_y in range(y + 20, y - 20, -1):
            block = editor.getBlock((stilt_x, check_y, stilt_z))
            if block and block.id != "minecraft:air" and "water" not in block.id and "leaves" not in block.id:
                actual_stilt_y = check_y
                break
        
        # Build stilt from ground up to floor level
        for h in range(floor_y - actual_stilt_y + 1):
            # For Nordic style, use thicker stilts (2x2) for main corner stilts
            if blueprint.style == "nordic" and stilt_dx in [0, width-1] and stilt_dz in [0, length-1]:
                # Build 2x2 thick stilt pillar
                editor.placeBlock((stilt_x, actual_stilt_y + h, stilt_z), Block(logs, {"axis": "y"}))
                if stilt_dx < width - 1:  # Can add second column in X direction
                    editor.placeBlock((stilt_x + 1, actual_stilt_y + h, stilt_z), Block(logs, {"axis": "y"}))
                if stilt_dz < length - 1:  # Can add second column in Z direction
                    editor.placeBlock((stilt_x, actual_stilt_y + h, stilt_z + 1), Block(logs, {"axis": "y"}))
                if stilt_dx < width - 1 and stilt_dz < length - 1:  # Can add diagonal column
                    editor.placeBlock((stilt_x + 1, actual_stilt_y + h, stilt_z + 1), Block(logs, {"axis": "y"}))
            else:
                # Standard stilt pillar
                editor.placeBlock((stilt_x, actual_stilt_y + h, stilt_z), Block(logs, {"axis": "y"}))
    
    # 2. Build cross-braces between stilts for stability
    for brace_x, brace_z, brace_type in blueprint.cross_braces:
        # Position braces differently based on style
        if blueprint.style == "asian":
            # Add multiple braces at different heights for more ornate appearance
            for h_offset in range(1, stilt_height - 1, 2):
                brace_y = y + h_offset
                
                if brace_type == "horizontal_z":
                    editor.placeBlock((x + brace_x, brace_y, z + brace_z), Block(logs, {"axis": "z"}))
                elif brace_type == "horizontal_x":
                    editor.placeBlock((x + brace_x, brace_y, z + brace_z), Block(logs, {"axis": "x"}))
                else:  # diagonal
                    editor.placeBlock((x + brace_x, brace_y, z + brace_z), Block(fence))
        else:
            # Standard brace height at 1/2 stilt height
            brace_y = y + stilt_height // 2
            
            if brace_type == "horizontal_z":
                editor.placeBlock((x + brace_x, brace_y, z + brace_z), Block(logs, {"axis": "z"}))
            elif brace_type == "horizontal_x":
                editor.placeBlock((x + brace_x, brace_y, z + brace_z), Block(logs, {"axis": "x"}))
            else:  # diagonal
                editor.placeBlock((x + brace_x, brace_y, z + brace_z), Block(fence))
    
    # 3. Build the main platform/floor
    for dx in range(width):
        for dz in range(length):
            # Skip cut-out areas for L-shaped buildings
            if hasattr(blueprint, 'shape_variation') and blueprint.shape_variation == "l_shape":
                if hasattr(blueprint, 'corner_cutout') and hasattr(blueprint, 'cutout_size'):
                    cutout = blueprint.corner_cutout
                    size = blueprint.cutout_size
                    if (cutout == "NE" and dx >= width - size and dz < size) or \
                       (cutout == "NW" and dx < size and dz < size) or \
                       (cutout == "SE" and dx >= width - size and dz >= length - size) or \
                       (cutout == "SW" and dx < size and dz >= length - size):
                        continue
            
            # Main floor
            floor_material = planks
            if blueprint.style == "modern" and random.random() < 0.3:
                floor_material = secondary_material  # Mix in some secondary material for modern floor
                
            editor.placeBlock((x + dx, floor_y, z + dz), Block(floor_material))
            
            # Add structural support beams under the floor
            if (dx == 0 or dx == width - 1 or dx % 2 == 0) and (dz == 0 or dz == length - 1 or dz % 2 == 0):
                editor.placeBlock((x + dx, floor_y - 1, z + dz), Block(planks))
    
    # 4. Build walls
    # Get door position and direction
    door_x, door_z, door_direction = blueprint.door_position
    door_x += x  # Convert to absolute coordinates
    door_z += z
    
    # For hill terrain, adjust door to be on the downhill side
    if terrain_type == 1:
        # Check ground height around the house to find the downhill side
        edge_heights = {
            "north": 999, "south": 999, "east": 999, "west": 999
        }
        
        # Check north edge (z=0)
        for check_x in range(x + 1, x + width - 1):
            for check_y in range(y + 20, y - 20, -1):
                block = editor.getBlock((check_x, check_y, z))
                if block and block.id != "minecraft:air" and "water" not in block.id:
                    edge_heights["north"] = min(edge_heights["north"], check_y)
                    break
        
        # Check south edge (z=length-1)
        for check_x in range(x + 1, x + width - 1):
            for check_y in range(y + 20, y - 20, -1):
                block = editor.getBlock((check_x, check_y, z + length - 1))
                if block and block.id != "minecraft:air" and "water" not in block.id:
                    edge_heights["south"] = min(edge_heights["south"], check_y)
                    break
        
        # Check east edge (x=width-1)
        for check_z in range(z + 1, z + length - 1):
            for check_y in range(y + 20, y - 20, -1):
                block = editor.getBlock((x + width - 1, check_y, check_z))
                if block and block.id != "minecraft:air" and "water" not in block.id:
                    edge_heights["east"] = min(edge_heights["east"], check_y)
                    break
        
        # Check west edge (x=0)
        for check_z in range(z + 1, z + length - 1):
            for check_y in range(y + 20, y - 20, -1):
                block = editor.getBlock((x, check_y, check_z))
                if block and block.id != "minecraft:air" and "water" not in block.id:
                    edge_heights["west"] = min(edge_heights["west"], check_y)
                    break
        
        # Find the lowest edge
        lowest_edge = min(edge_heights.items(), key=lambda x: x[1])
        lowest_direction = lowest_edge[0]
        
        # Place door on the downhill side
        if lowest_direction == "north":
            door_x, door_z = x + width // 2, z
            door_direction = "south"
        elif lowest_direction == "south":
            door_x, door_z = x + width // 2, z + length - 1
            door_direction = "north"
        elif lowest_direction == "east":
            door_x, door_z = x + width - 1, z + length // 2
            door_direction = "west"
        else:  # west
            door_x, door_z = x, z + length // 2
            door_direction = "east"
    
    # Build walls with windows
    for h in range(height):
        floor_level = floor_y + 1 + h
        
        for dx in range(width):
            for dz in range(length):
                # Skip if not on perimeter
                if dx > 0 and dx < width - 1 and dz > 0 and dz < length - 1:
                    continue
                
                # Skip cut-out areas for L-shaped buildings
                if hasattr(blueprint, 'shape_variation') and blueprint.shape_variation == "l_shape":
                    if hasattr(blueprint, 'corner_cutout') and hasattr(blueprint, 'cutout_size'):
                        cutout = blueprint.corner_cutout
                        size = blueprint.cutout_size
                        if (cutout == "NE" and dx >= width - size and dz < size) or \
                           (cutout == "NW" and dx < size and dz < size) or \
                           (cutout == "SE" and dx >= width - size and dz >= length - size) or \
                           (cutout == "SW" and dx < size and dz >= length - size):
                            continue
                
                curr_x, curr_z = x + dx, z + dz
                
                # Skip if it's a door position
                is_door = (curr_x == door_x and curr_z == door_z and h == 0)
                
                # Determine if this should be a window
                is_window = False
                for window_x, window_z, window_h in blueprint.windows:
                    if dx == window_x and dz == window_z and h == window_h:
                        is_window = True
                        break
                
                # Place appropriate block based on style
                if is_door:
                    # Door will be placed later
                    pass
                elif is_window:
                    if blueprint.style_features["window_style"] == "large" and h == 1:
                        # Large glass panes for modern style
                        editor.placeBlock((curr_x, floor_level, curr_z), Block("glass"))
                    elif blueprint.style_features["window_style"] == "lattice":
                        # Lattice style for Asian
                        if random.random() < 0.3:
                            editor.placeBlock((curr_x, floor_level, curr_z), Block(fence))
                        else:
                            editor.placeBlock((curr_x, floor_level, curr_z), Block("glass_pane"))
                    else:
                        # Standard windows
                        editor.placeBlock((curr_x, floor_level, curr_z), Block("glass_pane"))
                else:
                    # Wall material based on style
                    if blueprint.style == "modern":
                        # Modern uses mix of materials
                        if (dx == 0 or dx == width - 1) and (dz == 0 or dz == length - 1):
                            # Corners
                            editor.placeBlock((curr_x, floor_level, curr_z), Block(secondary_material))
                        elif random.random() < 0.3:
                            # Mix in some secondary material
                            editor.placeBlock((curr_x, floor_level, curr_z), Block(secondary_material))
                        else:
                            editor.placeBlock((curr_x, floor_level, curr_z), Block(planks))
                    elif blueprint.style == "asian" or blueprint.style == "nordic":
                        # Use logs for structural framing with planks between
                        if (dx == 0 or dx == width - 1) and (dz == 0 or dz == length - 1):
                            # Corners
                            editor.placeBlock((curr_x, floor_level, curr_z), Block(logs, {"axis": "y"}))
                        elif h == 0 and (dx == 0 or dx == width - 1 or dz == 0 or dz == length - 1):
                            # Base frame
                            if dx == 0 or dx == width - 1:
                                editor.placeBlock((curr_x, floor_level, curr_z), Block(logs, {"axis": "z"}))
                            else:
                                editor.placeBlock((curr_x, floor_level, curr_z), Block(logs, {"axis": "x"}))
                        elif h == height - 1 and (dx == 0 or dx == width - 1 or dz == 0 or dz == length - 1):
                            # Top frame
                            if dx == 0 or dx == width - 1:
                                editor.placeBlock((curr_x, floor_level, curr_z), Block(logs, {"axis": "z"}))
                            else:
                                editor.placeBlock((curr_x, floor_level, curr_z), Block(logs, {"axis": "x"}))
                        elif dx % 3 == 0 or dz % 3 == 0:
                            # Vertical supports every 3 blocks
                            editor.placeBlock((curr_x, floor_level, curr_z), Block(logs, {"axis": "y"}))
                        else:
                            # Fill with planks
                            editor.placeBlock((curr_x, floor_level, curr_z), Block(planks))
                    elif blueprint.style == "tropical":
                        # Tropical uses more open design with decorative elements
                        if (dx == 0 or dx == width - 1) and (dz == 0 or dz == length - 1):
                            # Corners
                            editor.placeBlock((curr_x, floor_level, curr_z), Block(logs, {"axis": "y"}))
                        elif dx % 2 == 0 or dz % 2 == 0:
                            # Support beams
                            editor.placeBlock((curr_x, floor_level, curr_z), Block(logs, {"axis": "y"}))
                        else:
                            # Fill with planks or leaves for tropical feel
                            if random.random() < 0.2 and h == height - 1:
                                editor.placeBlock((curr_x, floor_level, curr_z), Block("jungle_leaves"))
                            else:
                                editor.placeBlock((curr_x, floor_level, curr_z), Block(planks))
                    else:
                        # Traditional style - use logs for corners and planks for walls
                        if (dx == 0 or dx == width - 1) and (dz == 0 or dz == length - 1):
                            editor.placeBlock((curr_x, floor_level, curr_z), Block(logs, {"axis": "y"}))
                        else:
                            editor.placeBlock((curr_x, floor_level, curr_z), Block(planks))
    
    # Place the door
    editor.placeBlock((door_x, floor_y + 1, door_z), Block(door, {"facing": door_direction, "half": "lower"}))
    editor.placeBlock((door_x, floor_y + 2, door_z), Block(door, {"facing": door_direction, "half": "upper"}))
    
    # 5. Build the roof according to style
    roof_y = floor_y + height + 1
    
    if blueprint.roof_details["type"] == "a_frame":
        # A-frame roof
        for dx in range(width):
            for h in range((width // 2) + 1):
                # Calculate roof height at this position
                if dx <= width // 2:
                    roof_h = h
                else:
                    roof_h = width - dx - 1
                
                if roof_h <= 0:
                    continue
                
                # Build roof along the length
                for dz in range(-1, length + 1):  # Extend 1 block for overhang
                    if 0 <= dz < length or blueprint.roof_details["overhang"] > 0:
                        curr_x, curr_y, curr_z = x + dx, roof_y + roof_h, z + dz
                        editor.placeBlock((curr_x, curr_y, curr_z), Block(blueprint.roof_details["material"]))
    
    elif blueprint.roof_details["type"] == "steep_a_frame":
        # Steeper A-frame for Nordic
        for dx in range(-1, width + 1):  # Extend 1 block for overhang
            # Calculate how far this is from the center
            center_dist = abs(dx - width / 2)
            max_height = width // 2 + 2  # Higher peak
            
            for h in range(max_height + 1):
                # Steeper slope
                if center_dist <= max_height - h:
                    # Build roof along the length
                    for dz in range(-1, length + 1):  # Extend 1 block for overhang
                        if 0 <= dz < length or blueprint.roof_details["overhang"] > 0:
                            curr_x, curr_y, curr_z = x + dx, roof_y + h, z + dz
                            
                            # For snow-covered roof
                            if blueprint.roof_details.get("snow_covered", False) and h == max_height - int(center_dist):
                                editor.placeBlock((curr_x, curr_y, curr_z), Block("snow_block"))
                            else:
                                editor.placeBlock((curr_x, curr_y, curr_z), Block(blueprint.roof_details["material"]))
    
    elif blueprint.roof_details["type"] == "pagoda":
        # Pagoda-style stepped roof for Asian
        overhang = blueprint.roof_details["overhang"]
        
        for level in range(2):  # Two levels for the pagoda roof
            level_y = roof_y + level * 2
            
            # Each level has a different size
            level_overhang = overhang - level
            
            for dx in range(-level_overhang, width + level_overhang):
                for dz in range(-level_overhang, length + level_overhang):
                    # Only build on the perimeter for the upper level
                    is_perimeter = dx == -level_overhang or dx == width + level_overhang - 1 or dz == -level_overhang or dz == length + level_overhang - 1
                    
                    if level == 0 or is_perimeter:
                        # Upturned edges for corners
                        is_corner = (dx == -level_overhang or dx == width + level_overhang - 1) and (dz == -level_overhang or dz == length + level_overhang - 1)
                        
                        curr_x, curr_y, curr_z = x + dx, level_y, z + dz
                        
                        if is_corner and blueprint.roof_details.get("upturned_edges", False):
                            # Upturned corner with stair block
                            if dx == -level_overhang and dz == -level_overhang:
                                editor.placeBlock((curr_x, curr_y + 1, curr_z), Block(stairs, {"facing": "southeast", "half": "bottom"}))
                            elif dx == width + level_overhang - 1 and dz == -level_overhang:
                                editor.placeBlock((curr_x, curr_y + 1, curr_z), Block(stairs, {"facing": "southwest", "half": "bottom"}))
                            elif dx == -level_overhang and dz == length + level_overhang - 1:
                                editor.placeBlock((curr_x, curr_y + 1, curr_z), Block(stairs, {"facing": "northeast", "half": "bottom"}))
                            elif dx == width + level_overhang - 1 and dz == length + level_overhang - 1:
                                editor.placeBlock((curr_x, curr_y + 1, curr_z), Block(stairs, {"facing": "northwest", "half": "bottom"}))
                            
                            # Base block for the upturned corner
                            editor.placeBlock((curr_x, curr_y, curr_z), Block(blueprint.roof_details["material"]))
                        elif is_perimeter:
                            # Edges with stairs for a sloped effect
                            if dx == -level_overhang:
                                editor.placeBlock((curr_x, curr_y, curr_z), Block(stairs, {"facing": "east", "half": "bottom"}))
                            elif dx == width + level_overhang - 1:
                                editor.placeBlock((curr_x, curr_y, curr_z), Block(stairs, {"facing": "west", "half": "bottom"}))
                            elif dz == -level_overhang:
                                editor.placeBlock((curr_x, curr_y, curr_z), Block(stairs, {"facing": "south", "half": "bottom"}))
                            elif dz == length + level_overhang - 1:
                                editor.placeBlock((curr_x, curr_y, curr_z), Block(stairs, {"facing": "north", "half": "bottom"}))
                        else:
                            # Interior roof as full blocks
                            editor.placeBlock((curr_x, curr_y, curr_z), Block(blueprint.roof_details["material"]))
    
    elif blueprint.roof_details["type"] == "thatched":
        # Thatched roof for tropical
        overhang = blueprint.roof_details["overhang"]
        
        for dx in range(-overhang, width + overhang):
            # Simple peaked roof
            center_dist = abs(dx - (width - 1) / 2)
            roof_h = max(0, (width // 2) - center_dist)
            
            for h in range(int(roof_h) + 1):
                for dz in range(-overhang, length + overhang):
                    curr_x, curr_y, curr_z = x + dx, roof_y + h, z + dz
                    
                    # Use leaves or other material for thatched look
                    if 0 <= dx < width and 0 <= dz < length or overhang > 0:
                        if random.random() < 0.2 and h == roof_h:
                            # Add some textural variation
                            editor.placeBlock((curr_x, curr_y, curr_z), Block("jungle_leaves"))
                        else:
                            editor.placeBlock((curr_x, curr_y, curr_z), Block(blueprint.roof_details["material"]))
    
    else:  # flat roof (modern)
        # Flat roof with potential for small walls/railing
        for dx in range(width):
            for dz in range(length):
                # Roof surface
                editor.placeBlock((x + dx, roof_y, z + dz), Block(blueprint.roof_details["material"]))
                
                # Add railing if specified
                if blueprint.roof_details.get("has_railing", False) and (dx == 0 or dx == width - 1 or dz == 0 or dz == length - 1):
                    if blueprint.style == "modern":
                        # Glass pane railings for modern
                        editor.placeBlock((x + dx, roof_y + 1, z + dz), Block("glass_pane"))
                    else:
                        # Standard fence railing
                        editor.placeBlock((x + dx, roof_y + 1, z + dz), Block(fence))
    
    # 6. Build access to the house (stairs or ladder)
    if door_direction == "north":
        access_z = door_z + 1
        access_x = door_x
    elif door_direction == "south":
        access_z = door_z - 1
        access_x = door_x
    elif door_direction == "east":
        access_z = door_z
        access_x = door_x + 1
    else:  # west
        access_z = door_z
        access_x = door_x - 1
    
    # Find ground level at access point
    access_y = y
    for check_y in range(y + 20, y - 20, -1):
        block = editor.getBlock((access_x, check_y, access_z))
        if block and block.id != "minecraft:air" and "water" not in block.id:
            access_y = check_y
            break
    
    # Calculate height difference
    height_diff = floor_y - access_y
    
    # Asian style may have a raised entry platform
    if blueprint.style == "asian" and hasattr(blueprint, 'has_raised_entry') and blueprint.has_raised_entry:
        # Build a small platform in front of the door
        platform_y = floor_y - 1
        
        # Determine platform size based on direction
        if door_direction == "north":
            for dx in range(-1, 2):
                for dz in range(1, 3):
                    platform_x = door_x + dx
                    platform_z = door_z + dz
                    editor.placeBlock((platform_x, platform_y, platform_z), Block(planks))
            
            # Add railings
            for dx in range(-1, 2):
                editor.placeBlock((door_x + dx, platform_y + 1, door_z + 2), Block(fence))
            
            # Add stairs down from this platform
            stairs_z = door_z + 3
            for i in range(platform_y - access_y):
                editor.placeBlock((door_x, platform_y - i, stairs_z + i), Block(stairs, {"facing": "north", "half": "bottom"}))
                
                # Add support under stairs
                for j in range(platform_y - access_y):
                    if access_y + j <= platform_y - i:
                        editor.placeBlock((door_x, access_y + j, stairs_z + i), Block(logs, {"axis": "y"}))
        
        # Similar approaches for other directions
        elif door_direction == "south":
            for dx in range(-1, 2):
                for dz in range(-2, 0):
                    platform_x = door_x + dx
                    platform_z = door_z + dz
                    editor.placeBlock((platform_x, platform_y, platform_z), Block(planks))
            
            # Add railings
            for dx in range(-1, 2):
                editor.placeBlock((door_x + dx, platform_y + 1, door_z - 2), Block(fence))
            
            # Add stairs down from this platform
            stairs_z = door_z - 3
            for i in range(platform_y - access_y):
                editor.placeBlock((door_x, platform_y - i, stairs_z - i), Block(stairs, {"facing": "south", "half": "bottom"}))
                
                # Add support under stairs
                for j in range(platform_y - access_y):
                    if access_y + j <= platform_y - i:
                        editor.placeBlock((door_x, access_y + j, stairs_z - i), Block(logs, {"axis": "y"}))
    
    elif height_diff <= 3:
        # Build stairs for low stilts
        for i in range(height_diff):
            if door_direction == "north":
                step_z = door_z + i + 1
                step_x = door_x
                facing = "north"
            elif door_direction == "south":
                step_z = door_z - (i + 1)
                step_x = door_x
                facing = "south"
            elif door_direction == "east":
                step_z = door_z
                step_x = door_x + i + 1
                facing = "east"
            else:  # west
                step_z = door_z
                step_x = door_x - (i + 1)
                facing = "west"
                
            editor.placeBlock((step_x, floor_y - i - 1, step_z), 
                            Block(stairs, {"facing": facing, "half": "bottom"}))
            
            # Add support under stairs
            for j in range(floor_y - access_y):
                if access_y + j <= floor_y - i - 1:
                    editor.placeBlock((step_x, access_y + j, step_z), Block(logs, {"axis": "y"}))
    else:
        # For taller stilt houses (especially tropical and modern)
        if blueprint.style == "tropical" or blueprint.style == "modern":
            # Build a spiral staircase
            stair_radius = 2
            center_x = access_x
            center_z = access_z
            
            # Build a spiral staircase from ground to floor
            for i in range(height_diff + 1):
                # Calculate position along spiral
                angle = (i / height_diff) * 2 * math.pi
                offset_x = int(math.cos(angle) * stair_radius)
                offset_z = int(math.sin(angle) * stair_radius)
                
                stair_x = center_x + offset_x
                stair_z = center_z + offset_z
                stair_y = access_y + i
                
                # Determine stair orientation based on position in spiral
                if offset_x > 0 and offset_z >= 0:
                    facing = "west"
                elif offset_x <= 0 and offset_z > 0:
                    facing = "north"
                elif offset_x < 0 and offset_z <= 0:
                    facing = "east"
                else:
                    facing = "south"
                
                # Place stair and support pillar
                editor.placeBlock((stair_x, stair_y, stair_z), Block(stairs, {"facing": facing, "half": "bottom"}))
                
                # Add support pillar under the stairs
                for j in range(stair_y - access_y):
                    editor.placeBlock((stair_x, access_y + j, stair_z), Block(logs, {"axis": "y"}))
                
                # Add a center post
                editor.placeBlock((center_x, access_y + i, center_z), Block(logs, {"axis": "y"}))
        else:
            # Standard ladder for other styles with tall stilts
            for h in range(height_diff + 1):
                editor.placeBlock((access_x, access_y + h, access_z), 
                                Block("ladder", {"facing": door_direction}))
    
    # 7. Add interior furniture
    for furniture_item in blueprint.furniture:
        furniture_type, rel_x, rel_z, orientation = furniture_item
        
        # Skip if outside house bounds (for irregular shapes)
        if hasattr(blueprint, 'shape_variation') and blueprint.shape_variation == "l_shape":
            if hasattr(blueprint, 'corner_cutout') and hasattr(blueprint, 'cutout_size'):
                cutout = blueprint.corner_cutout
                size = blueprint.cutout_size
                if (cutout == "NE" and rel_x >= width - size and rel_z < size) or \
                   (cutout == "NW" and rel_x < size and rel_z < size) or \
                   (cutout == "SE" and rel_x >= width - size and rel_z >= length - size) or \
                   (cutout == "SW" and rel_x < size and rel_z >= length - size):
                    continue
        
        abs_x = x + rel_x
        abs_z = z + rel_z
        
        if furniture_type == "bed" or furniture_type.endswith("_bed"):
            # Place a bed (requires two blocks)
            bed_type = furniture_type if furniture_type.endswith("_bed") else "white_bed"
            
            if orientation == "north":
                editor.placeBlock((abs_x, floor_y + 1, abs_z), 
                                Block(bed_type, {"part": "foot", "facing": "north"}))
                editor.placeBlock((abs_x, floor_y + 1, abs_z + 1), 
                                Block(bed_type, {"part": "head", "facing": "north"}))
            elif orientation == "south":
                editor.placeBlock((abs_x, floor_y + 1, abs_z), 
                                Block(bed_type, {"part": "foot", "facing": "south"}))
                editor.placeBlock((abs_x, floor_y + 1, abs_z - 1), 
                                Block(bed_type, {"part": "head", "facing": "south"}))
            elif orientation == "east":
                editor.placeBlock((abs_x, floor_y + 1, abs_z), 
                                Block(bed_type, {"part": "foot", "facing": "east"}))
                editor.placeBlock((abs_x - 1, floor_y + 1, abs_z), 
                                Block(bed_type, {"part": "head", "facing": "east"}))
            else:  # west
                editor.placeBlock((abs_x, floor_y + 1, abs_z), 
                                Block(bed_type, {"part": "foot", "facing": "west"}))
                editor.placeBlock((abs_x + 1, floor_y + 1, abs_z), 
                                Block(bed_type, {"part": "head", "facing": "west"}))
        elif furniture_type == "chest":
            # Place a chest with orientation
            if orientation:
                editor.placeBlock((abs_x, floor_y + 1, abs_z), Block("chest", {"facing": orientation}))
            else:
                editor.placeBlock((abs_x, floor_y + 1, abs_z), Block("chest"))
        elif furniture_type == "furnace" or furniture_type == "smoker":
            # Place a furnace with orientation
            if orientation:
                editor.placeBlock((abs_x, floor_y + 1, abs_z), Block(furniture_type, {"facing": orientation}))
            else:
                editor.placeBlock((abs_x, floor_y + 1, abs_z), Block(furniture_type))
        else:
            # Place other blocks without orientation
            editor.placeBlock((abs_x, floor_y + 1, abs_z), Block(furniture_type))
    
    # 8. Add decorative elements
    for dec_item in blueprint.decorative_elements:
        dec_type, rel_x, rel_z, placement = dec_item
        
        # Skip if outside house bounds (for irregular shapes)
        if hasattr(blueprint, 'shape_variation') and blueprint.shape_variation == "l_shape":
            if hasattr(blueprint, 'corner_cutout') and hasattr(blueprint, 'cutout_size'):
                cutout = blueprint.corner_cutout
                size = blueprint.cutout_size
                if (cutout == "NE" and rel_x >= width - size and rel_z < size) or \
                   (cutout == "NW" and rel_x < size and rel_z < size) or \
                   (cutout == "SE" and rel_x >= width - size and rel_z >= length - size) or \
                   (cutout == "SW" and rel_x < size and rel_z >= length - size):
                    continue
        
        abs_x = x + rel_x
        abs_z = z + rel_z
        
        if placement == "ceiling":
            # Ceiling-mounted decorations
            editor.placeBlock((abs_x, floor_y + height, abs_z), Block(dec_type))
        elif placement == "hanging":
            # Hanging decorations
            editor.placeBlock((abs_x, floor_y + height - 1, abs_z), Block(dec_type, {"hanging": "true"}))
        elif placement == "wall":
            # Wall-mounted decorations on nearest wall
            if rel_x == 0:  # West wall
                editor.placeBlock((abs_x, floor_y + 2, abs_z), Block(dec_type, {"facing": "east"}))
            elif rel_x == width - 1:  # East wall
                editor.placeBlock((abs_x, floor_y + 2, abs_z), Block(dec_type, {"facing": "west"}))
            elif rel_z == 0:  # North wall
                editor.placeBlock((abs_x, floor_y + 2, abs_z), Block(dec_type, {"facing": "south"}))
            elif rel_z == length - 1:  # South wall
                editor.placeBlock((abs_x, floor_y + 2, abs_z), Block(dec_type, {"facing": "north"}))
        elif placement == "window":
            # Window box decorations
            if rel_z == 0:  # North window
                editor.placeBlock((abs_x, floor_y, abs_z - 1), Block(dec_type))
            elif rel_z == length - 1:  # South window
                editor.placeBlock((abs_x, floor_y, abs_z + 1), Block(dec_type))
            elif rel_x == 0:  # West window
                editor.placeBlock((abs_x - 1, floor_y, abs_z), Block(dec_type))
            elif rel_x == width - 1:  # East window
                editor.placeBlock((abs_x + 1, floor_y, abs_z), Block(dec_type))
        elif placement == "railing":
            # Roof railing
            editor.placeBlock((abs_x, roof_y + 1, abs_z), Block(dec_type))
        else:  # floor or default
            # Floor decorations
            editor.placeBlock((abs_x, floor_y + 1, abs_z), Block(dec_type))
    
    # Return information about the house
    return {
        "position": (x, y, z),
        "dimensions": (width, height, length),
        "floor_level": floor_y,
        "entrance": (door_x, floor_y, door_z),
        "stilt_height": stilt_height,
        "terrain_type": terrain_type,
        "style": blueprint.style,
        "size": blueprint.size,
        "wood_type": blueprint.wood_type
    }

def find_house_locations(terrain_data, min_houses=10, max_houses=25, min_distance=20):
    """
    Find suitable locations for stilt houses with specific prioritization:
    1. Shoreline (partially in water) - with better detection for partial submersion
    2. Hills without trees
    3. Flat areas without trees
    4. Last resort: areas with trees
    
    Parameters:
    terrain_data: Dictionary containing terrain analysis data
    min_houses: Minimum number of houses to place (default: 10)
    max_houses: Maximum number of houses to place (default: 25)
    min_distance: Minimum distance between houses
    
    Returns:
    List of dictionaries with house locations and terrain types
    """
    # Ensure max_houses doesn't exceed 25
    max_houses = min(25, max_houses)
    
    # Enforce a stronger minimum distance to avoid stacking
    min_distance = max(20, min_distance)  # At least 20 blocks between houses
    
    # Initialize data from terrain analysis
    suitability_map = terrain_data['suitability_map']
    terrain_type_map = terrain_data['terrain_type_map']
    tree_map = terrain_data.get('tree_map', np.zeros_like(suitability_map))  # Default to zeros if not present
    water_map = terrain_data.get('water_map', np.zeros_like(suitability_map, dtype=bool))  # Water locations
    heightmap = terrain_data.get('heightmap', None)
    ocean_floor = terrain_data.get('ocean_floor', None)
    shape = terrain_data['shape']
    x_start = terrain_data['x_start']
    z_start = terrain_data['z_start']
    
    # Get shoreline map if it's available in terrain_data, otherwise use simple detection
    shoreline_map = terrain_data.get('shoreline_map', None)
    if shoreline_map is None:
        print("Using simpler shoreline detection method...")
        shoreline_map = np.zeros_like(suitability_map)
        
        # Kernel size for shoreline detection
        kernel_size = 5
        
        for z_rel in range(kernel_size//2, shape[0] - kernel_size//2):
            for x_rel in range(kernel_size//2, shape[1] - kernel_size//2):
                # Extract the neighborhood
                z_start_idx = max(0, z_rel - kernel_size//2)
                z_end_idx = min(shape[0], z_rel + kernel_size//2 + 1)
                x_start_idx = max(0, x_rel - kernel_size//2)
                x_end_idx = min(shape[1], x_rel + kernel_size//2 + 1)
                
                neighborhood = water_map[z_start_idx:z_end_idx, x_start_idx:x_end_idx]
                
                # Check if this is a shoreline (has both water and land)
                has_water = np.any(neighborhood)
                has_land = np.any(~neighborhood)
                
                if has_water and has_land:
                    # Calculate how much is water vs land
                    water_percent = np.mean(neighborhood) * 100
                    
                    # Ideal shoreline has 30-50% water
                    if 30 <= water_percent <= 50:
                        shoreline_map[z_rel, x_rel] = 1.0
                    elif 20 <= water_percent < 30 or 50 < water_percent <= 60:
                        shoreline_map[z_rel, x_rel] = 0.7
    
    # Generate visualization for shoreline map
    try:
        import matplotlib.pyplot as plt
        
        # Create directory for visualizations if it doesn't exist
        output_dir = "stilt_house_analysis"
        os.makedirs(output_dir, exist_ok=True)
        
        plt.figure(figsize=(12, 10))
        plt.imshow(shoreline_map, cmap='Blues', interpolation='nearest')
        plt.colorbar(label='Shoreline Quality for Partial Submersion')
        plt.title('Optimal Shoreline Areas for Partially Submerged Stilt Houses')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "optimal_shoreline_map.png"), dpi=300)
        plt.close()
    except Exception as e:
        print(f"Warning: Could not generate shoreline map visualization: {e}")
    
    # Initialize priority categories
    shoreline_locations = []  # Priority 1: Shoreline with partial submersion
    hill_clear_locations = []  # Priority 2: Hills without trees
    flat_clear_locations = []  # Priority 3: Flat areas without trees
    tree_locations = []  # Priority 4: Areas with trees (last resort)
    
    print("Categorizing locations by priority...")
    
    # Categorize all valid locations with more emphasis on optimal shoreline areas
    for z_rel in range(5, shape[0] - 5):
        for x_rel in range(5, shape[1] - 5):
            # Get basic parameters
            shoreline_score = shoreline_map[z_rel, x_rel]
            is_optimal_shoreline = shoreline_score > 0.7  # High-quality shoreline for partial submersion
            terrain_type = terrain_type_map[z_rel, x_rel]  # 0=flat, 1=hill, 2=water
            tree_density = tree_map[z_rel, x_rel]
            base_score = suitability_map[z_rel, x_rel]
            
            # Skip clearly unsuitable locations
            if base_score < 0.3:
                continue
                
            # Convert to world coordinates
            x = x_start + x_rel
            z = z_start + z_rel
            y = 62  # Default y level, refined later
            
            # Create location data
            location_data = {
                "position": (int(x), int(y), int(z)),
                "score": float(base_score),
                "original_score": float(base_score),
                "tree_density": float(tree_density),
                "terrain_type": int(terrain_type),
                "is_shoreline": bool(is_optimal_shoreline),
                "shoreline_quality": float(shoreline_score)
            }
            
            # Categorize by priority with boosted scores for optimal shoreline locations
            if is_optimal_shoreline:
                # Boost score based on shoreline quality
                location_data["score"] = base_score * (1.0 + shoreline_score * 2)  # Double boost
                shoreline_locations.append(location_data)
            elif terrain_type == 1 and tree_density < 0.1:
                # Hills without trees
                hill_clear_locations.append(location_data)
            elif terrain_type == 0 and tree_density < 0.1:
                # Flat areas without trees
                flat_clear_locations.append(location_data)
            elif tree_density < 0.25:  # Slightly more tolerance for trees
                # Areas with tolerable tree density
                tree_locations.append(location_data)
    
    # Sort each category by relevant scores
    shoreline_locations.sort(key=lambda loc: (-loc["shoreline_quality"], loc["tree_density"], -loc["score"]))
    hill_clear_locations.sort(key=lambda loc: (loc["tree_density"], -loc["score"]))
    flat_clear_locations.sort(key=lambda loc: (loc["tree_density"], -loc["score"]))
    tree_locations.sort(key=lambda loc: (loc["tree_density"], -loc["score"]))
    
    # Print stats about available locations
    print(f"Available locations by priority:")
    print(f"  1. Optimal shoreline areas (partially in water): {len(shoreline_locations)}")
    print(f"  2. Hills without trees: {len(hill_clear_locations)}")
    print(f"  3. Flat areas without trees: {len(flat_clear_locations)}")
    print(f"  4. Areas with trees (last resort): {len(tree_locations)}")
    
    # Combine all locations in priority order
    all_locations = shoreline_locations + hill_clear_locations + flat_clear_locations + tree_locations
    
    # Select houses with sufficient spacing following priority order
    selected_houses = []
    
    # Track how many houses were selected from each category
    shoreline_count = 0
    hill_clear_count = 0
    flat_clear_count = 0
    tree_count = 0
    
    # Process all locations in priority order
    for location in all_locations:
        # Skip if we already have enough houses
        if len(selected_houses) >= max_houses:
            break
            
        # Check distance to already selected houses
        too_close = False
        for house in selected_houses:
            dist = math.sqrt(
                (location["position"][0] - house["position"][0])**2 +
                (location["position"][2] - house["position"][2])**2
            )
            # Enforce minimum distance strictly
            if dist < min_distance:
                too_close = True
                break
        
        # Add this location if it's not too close to existing houses
        if not too_close:
            selected_houses.append(location)
            
            # Count by priority category for reporting
            if location.get("is_shoreline", False):
                shoreline_count += 1
            elif location["terrain_type"] == 1 and location["tree_density"] < 0.1:
                hill_clear_count += 1
            elif location["terrain_type"] == 0 and location["tree_density"] < 0.1:
                flat_clear_count += 1
            else:
                tree_count += 1
    
    # If we still don't have enough houses, try with a smaller minimum distance
    if len(selected_houses) < min_houses:
        # Reduce minimum distance for a second pass
        reduced_distance = min_distance * 0.7  # 70% of original distance
        print(f"Not enough locations found. Reducing minimum distance to {reduced_distance:.1f} blocks...")
        
        for location in all_locations:
            # Skip locations already selected
            if any(loc["position"] == location["position"] for loc in selected_houses):
                continue
                
            # Skip if we already have enough houses
            if len(selected_houses) >= min_houses:
                break
                
            # Check distance with reduced minimum
            too_close = False
            for house in selected_houses:
                dist = math.sqrt(
                    (location["position"][0] - house["position"][0])**2 +
                    (location["position"][2] - house["position"][2])**2
                )
                if dist < reduced_distance:
                    too_close = True
                    break
            
            # Add this location if it's not too close
            if not too_close:
                selected_houses.append(location)
                
                # Count by priority category for reporting
                if location.get("is_shoreline", False):
                    shoreline_count += 1
                elif location["terrain_type"] == 1 and location["tree_density"] < 0.1:
                    hill_clear_count += 1
                elif location["terrain_type"] == 0 and location["tree_density"] < 0.1:
                    flat_clear_count += 1
                else:
                    tree_count += 1
    
    print(f"Found {len(selected_houses)} suitable locations for stilt houses.")
    
    # Print priority distribution
    print(f"\nHouses by priority category:")
    print(f"  1. Optimal shoreline (partially in water): {shoreline_count} houses")
    print(f"  2. Hills without trees: {hill_clear_count} houses")
    print(f"  3. Flat areas without trees: {flat_clear_count} houses") 
    print(f"  4. Areas with trees (last resort): {tree_count} houses")
    
    # Calculate average shoreline quality and tree density
    if selected_houses:
        shoreline_houses = [h for h in selected_houses if h.get("is_shoreline", False)]
        if shoreline_houses:
            avg_shoreline = sum(h.get("shoreline_quality", 0) for h in shoreline_houses) / len(shoreline_houses)
            print(f"Average shoreline quality of selected shoreline locations: {avg_shoreline:.3f}")
        
        avg_tree_density = sum(h.get("tree_density", 0) for h in selected_houses) / len(selected_houses)
        print(f"Average tree density of selected locations: {avg_tree_density:.3f}")
    
    return selected_houses

def main():
    """Main function to create stilt houses on various terrain types."""
    # Create editor instance with buffering disabled to avoid issues
    editor = Editor(buffering=False)
    
    try:
        # Analyze terrain for stilt house placement
        print("Analyzing terrain for versatile stilt house placement...")
        
        # Import the terrain analyzer
        from terrain_mapper import analyze_terrain
        terrain_data = analyze_terrain(editor)
        
        # Find suitable house locations
        house_locations = find_house_locations(terrain_data, min_distance=20)
        
        if not house_locations:
            print("Error: No suitable locations found for stilt houses.")
            return
        
        # Save house coordinates to a file
        coords_file = os.path.join(coords_dir, "house_coordinates.txt")
        
        with open(coords_file, "w") as f:
            f.write("Stilt House Network Coordinates\n")
            f.write("===============================\n\n")
        
        # Build houses and save information
        house_info = []
        
        for i, loc in enumerate(house_locations):
            position = loc["position"]
            x, y, z = position
            terrain_type = loc["terrain_type"]
            
            # Create a random blueprint
            blueprint = HouseBlueprintFactory.create_house(
                "stilt", 
                style=random.choice(["traditional", "modern", "asian"]),
                size=random.choice(["small", "medium", "large"])
            )
            
            # Build the house adapted to terrain type with tree clearing
            house_data = build_stilt_house(
                editor, x, y, z, 
                terrain_type=terrain_type,
                blueprint=blueprint,
                clear_trees=True
            )
            
            if house_data:
                house_info.append(house_data)
                
                # Print and save coordinates
                terrain_name = ["Flat", "Hill", "Water"][terrain_type]
                print(f"House {len(house_info)} built at {position} on {terrain_name} terrain")
                print(f"  Stilt height: {house_data['stilt_height']} blocks")
                print(f"  Floor level: {house_data['floor_level']}")
                print(f"  Teleport command: /tp @p {x} {house_data['floor_level']} {z}")
                
                with open(coords_file, "a") as f:
                    f.write(f"House {len(house_info)} ({house_data['size']} {house_data['style']} on {terrain_name}):\n")
                    f.write(f"  Position: {position}\n")
                    f.write(f"  Wood type: {blueprint.wood_type}\n")
                    f.write(f"  Dimensions: {house_data['dimensions']}\n")
                    f.write(f"  Stilt height: {house_data['stilt_height']} blocks\n")
                    f.write(f"  Floor level: {house_data['floor_level']}\n")
                    f.write(f"  Teleport: /tp @p {x} {house_data['floor_level']} {z}\n\n")
        
        if not house_info:
            print("Failed to build any houses. Could not find suitable locations.")
            return
            
        print(f"\nSuccessfully built {len(house_info)} stilt houses.")
        print(f"House coordinates saved to: {coords_file}")
        
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()