from gdpc import Editor
from gdpc.vector_tools import Rect
import numpy as np
from scipy import ndimage
import random
import os
import math

# Output directory for visualization plots
OUTPUT_DIR = "terrain_analysis"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Maximum stilt height for any terrain
MAX_STILT_HEIGHT = 5

def map_random_area(size=100):
    """
    Maps a random 100x100 area in the Minecraft world.
    
    Parameters:
    size (int): Size of the square area to map (default 100)
    
    Returns:
    dict: Contains information about the mapped area
    """
    # Create editor instance with buffering disabled to avoid issues
    editor = Editor(buffering=False)
    
    # Get build area set in Minecraft
    buildarea = editor.getBuildArea()
    
    # Extract coordinates
    x, y, z = buildarea.begin
    dx, dy, dz = buildarea.size
    
    # Determine a random position within the build area
    # Make sure we have at least 100x100 space
    if dx < size or dz < size:
        print(f"Warning: Build area is smaller than {size}x{size}")
        max_x = max(0, dx - size)
        max_z = max(0, dz - size)
    else:
        max_x = dx - size
        max_z = dz - size
    
    # Choose random starting position within bounds
    start_x = x + random.randint(0, max_x)
    start_z = z + random.randint(0, max_z)
    
    print(f"Mapping area from ({start_x}, {start_z}) to ({start_x + size}, {start_z + size})")
    
    # Load the world slice for this area
    rect = Rect((start_x, start_z), (size, size))
    worldslice = editor.loadWorldSlice(rect)
    
    # Create directory for visualizations
    output_dir = "terrain_mapping"
    os.makedirs(output_dir, exist_ok=True)
    
    # Get heightmaps
    terrain_heightmap = worldslice.heightmaps["MOTION_BLOCKING"]
    ocean_floor = worldslice.heightmaps["OCEAN_FLOOR"]
    
    # Visualize the heightmap
    try:
        import matplotlib.pyplot as plt
        
        plt.figure(figsize=(10, 8))
        plt.imshow(terrain_heightmap, cmap='terrain')
        plt.colorbar(label='Terrain Height')
        plt.title('Terrain Heightmap')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "terrain_heightmap.png"), dpi=300)
        plt.close()
        
        # Visualize water areas
        water_depth = terrain_heightmap - ocean_floor
        water_mask = water_depth > 0
        
        plt.figure(figsize=(10, 8))
        plt.imshow(water_mask, cmap='Blues')
        plt.colorbar(label='Water Present')
        plt.title('Water Map')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "water_map.png"), dpi=300)
        plt.close()
        
        # Calculate slopes
        # Calculate gradients
        gradient_x = ndimage.sobel(terrain_heightmap, axis=1) / 8.0
        gradient_y = ndimage.sobel(terrain_heightmap, axis=0) / 8.0
        slope = np.sqrt(gradient_x**2 + gradient_y**2)
        
        plt.figure(figsize=(10, 8))
        plt.imshow(slope, cmap='hot_r')
        plt.colorbar(label='Slope')
        plt.title('Terrain Slope Map')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "slope_map.png"), dpi=300)
        plt.close()
    
    except Exception as e:
        print(f"Warning: Could not generate visualizations: {e}")
    
    # Place markers at the corners of the area
    try:
        from gdpc import Block
        editor.placeBlock((start_x, terrain_heightmap[0, 0], start_z), Block("gold_block"))
        editor.placeBlock((start_x + size - 1, terrain_heightmap[0, size - 1], start_z), Block("gold_block"))
        editor.placeBlock((start_x, terrain_heightmap[size - 1, 0], start_z + size - 1), Block("gold_block"))
        editor.placeBlock((start_x + size - 1, terrain_heightmap[size - 1, size - 1], start_z + size - 1), Block("gold_block"))
    except Exception as e:
        print(f"Warning: Could not place marker blocks: {e}")
    
    # Return information about the mapped area
    return {
        'x_start': start_x,
        'z_start': start_z,
        'size': size,
        'heightmap': terrain_heightmap,
        'ocean_floor': ocean_floor,
        'worldslice': worldslice
    }

def improved_shoreline_detection(water_map, shape, terrain_type_map, heightmap, ocean_floor):
    """
    Improved shoreline detection that identifies areas where a house would have
    some stilts in water and some on land - perfect for partially submerged houses.
    
    Parameters:
    water_map: 2D array indicating water locations (True/False)
    shape: Tuple with dimensions (z, x)
    terrain_type_map: Map of terrain types (0=flat, 1=hill, 2=water)
    heightmap: Terrain heightmap
    ocean_floor: Ocean floor heightmap
    
    Returns:
    numpy.ndarray: A shoreline suitability map
    """
    import numpy as np
    from scipy import ndimage
    
    shoreline_map = np.zeros(shape)
    
    # Larger neighborhood for better context
    kernel_size = 11
    
    # Simulate typical stilt patterns for different house sizes
    small_house_stilts = [(0, 0), (0, 5), (5, 0), (5, 5)]  # 6x6 house
    med_house_stilts = [(0, 0), (0, 7), (7, 0), (7, 7), (3, 0), (0, 3), (7, 3), (3, 7)]  # 8x8 house
    large_house_stilts = [(0, 0), (0, 9), (9, 0), (9, 9), (4, 0), (0, 4), (9, 4), (4, 9)]  # 10x10 house
    
    stilt_patterns = [small_house_stilts, med_house_stilts, large_house_stilts]
    
    print("Analyzing potential stilt positions for partial water submersion...")
    
    for z_rel in range(kernel_size//2, shape[0] - kernel_size//2):
        for x_rel in range(kernel_size//2, shape[1] - kernel_size//2):
            # Extract the neighborhood for analysis
            z_start_idx = max(0, z_rel - kernel_size//2)
            z_end_idx = min(shape[0], z_rel + kernel_size//2 + 1)
            x_start_idx = max(0, x_rel - kernel_size//2)
            x_end_idx = min(shape[1], x_rel + kernel_size//2 + 1)
            
            neighborhood = water_map[z_start_idx:z_end_idx, x_start_idx:x_end_idx]
            
            # Skip if no mix of water and land
            has_water = np.any(neighborhood)
            has_land = np.any(~neighborhood)
            
            if not (has_water and has_land):
                continue
            
            # Calculate overall water percentage
            water_percent = np.mean(neighborhood) * 100
            
            # Only consider true shoreline areas with appropriate water coverage
            if water_percent < 10 or water_percent > 70:
                continue
            
            # Check water depth at this location
            if z_rel < heightmap.shape[0] and x_rel < heightmap.shape[1]:
                water_depth = heightmap[z_rel, x_rel] - ocean_floor[z_rel, x_rel] if water_map[z_rel, x_rel] else 0
                
                # Skip if water is too deep
                if water_depth > 3:
                    continue
            
            # Check each stilt pattern to find ideal partial submersion
            pattern_scores = []
            
            for stilts in stilt_patterns:
                # Count how many stilts would be in water vs. land
                water_stilts = 0
                land_stilts = 0
                valid_pattern = True
                
                for stilt_dz, stilt_dx in stilts:
                    # Calculate absolute position for this stilt
                    check_z = z_rel + stilt_dz - kernel_size//4
                    check_x = x_rel + stilt_dx - kernel_size//4
                    
                    if 0 <= check_z < shape[0] and 0 <= check_x < shape[1]:
                        if water_map[check_z, check_x]:
                            water_stilts += 1
                        else:
                            land_stilts += 1
                    else:
                        valid_pattern = False
                        break
                
                if not valid_pattern:
                    continue
                    
                total_stilts = water_stilts + land_stilts
                
                if total_stilts > 0:
                    # Calculate water-to-land ratio - we want 30-50% stilts in water
                    water_ratio = water_stilts / total_stilts
                    
                    # Score based on ideal partial submersion
                    if 0.3 <= water_ratio <= 0.5:
                        pattern_scores.append(1.0)  # Ideal mix - some stilts in water, most on land
                    elif 0.2 <= water_ratio < 0.3 or 0.5 < water_ratio <= 0.6:
                        pattern_scores.append(0.8)  # Good but not ideal
                    elif 0.1 <= water_ratio < 0.2 or 0.6 < water_ratio <= 0.7:
                        pattern_scores.append(0.5)  # Acceptable
                    else:
                        pattern_scores.append(0.2)  # Poor distribution
            
            # Use best pattern score
            if pattern_scores:
                shoreline_map[z_rel, x_rel] = max(pattern_scores)
    
    # Smooth the map for more natural transitions
    shoreline_map = ndimage.gaussian_filter(shoreline_map, sigma=1.0)
    
    print(f"Found {np.sum(shoreline_map > 0.7)} high-quality shoreline locations for partially submerged stilt houses")
    
    return shoreline_map

def analyze_terrain(editor):
    """
    Analyze terrain for stilt house placement on various terrain types:
    - Flat ground
    - Hills/slopes
    - Water areas
    
    Returns a dictionary with terrain data.
    """
    # Get the build area
    buildarea = editor.getBuildArea()
    print(f"Build area: {buildarea}")
    
    # Extract coordinates
    x, y, z = buildarea.begin
    dx, dy, dz = buildarea.size
    
    print(f"Analyzing area from ({x}, {z}) to ({x + dx}, {z + dz})")
    
    # Load the world slice
    rect = Rect((x, z), (dx, dz))
    worldslice = editor.loadWorldSlice(rect)
    
    # Initialize maps
    suitability_map = np.zeros((dz, dx))
    terrain_type_map = np.zeros((dz, dx), dtype=int)  # 0=flat, 1=hill, 2=water
    water_map = np.zeros((dz, dx), dtype=bool)
    slope_map = np.zeros((dz, dx))
    
    # Get heightmaps
    print("Loading heightmaps...")
    terrain_heightmap = worldslice.heightmaps["MOTION_BLOCKING"]
    ocean_floor = worldslice.heightmaps["OCEAN_FLOOR"]
    
    # Calculate water areas and slopes
    print("Analyzing terrain characteristics...")
    for z_rel in range(dz):
        for x_rel in range(dx):
            # Get heights
            top_height = terrain_heightmap[z_rel, x_rel]
            floor_height = ocean_floor[z_rel, x_rel]
            
            # Check for water (difference between terrain and ocean floor)
            water_depth = top_height - floor_height
            if water_depth > 0:
                water_map[z_rel, x_rel] = True
                terrain_type_map[z_rel, x_rel] = 2  # Water
            
            # Calculate local slope by checking height differences with neighbors
            heights = []
            for dz_off in range(-1, 2):
                for dx_off in range(-1, 2):
                    if 0 <= z_rel + dz_off < dz and 0 <= x_rel + dx_off < dx:
                        heights.append(terrain_heightmap[z_rel + dz_off, x_rel + dx_off])
            
            if len(heights) > 0:
                height_variance = np.std(heights)
                slope_map[z_rel, x_rel] = height_variance
                
                # Classify as hill if significant slope detected
                if height_variance > 1.5 and not water_map[z_rel, x_rel]:
                    terrain_type_map[z_rel, x_rel] = 1  # Hill
    
    # Calculate suitability scores for each terrain type
    # 1. Score for flat areas - moderate preference
    flat_mask = (terrain_type_map == 0)
    suitability_map[flat_mask] = 0.6  # Base score for flat terrain
    
    # 2. Score for hills - high preference for stilt houses
    hill_mask = (terrain_type_map == 1)
    # Hills with moderate slope are ideal (not too steep, not too flat)
    for z_rel in range(dz):
        for x_rel in range(dx):
            if hill_mask[z_rel, x_rel]:
                slope = slope_map[z_rel, x_rel]
                if 1.5 < slope < 3.0:
                    suitability_map[z_rel, x_rel] = 0.9  # Ideal hillside
                elif slope <= 1.5:
                    suitability_map[z_rel, x_rel] = 0.7  # Gentle slope
                else:
                    suitability_map[z_rel, x_rel] = 0.5  # Too steep
    
    # 3. Score for water - also good for stilt houses but with depth limits
    water_mask = (terrain_type_map == 2)
    for z_rel in range(dz):
        for x_rel in range(dx):
            if water_mask[z_rel, x_rel]:
                water_depth = terrain_heightmap[z_rel, x_rel] - ocean_floor[z_rel, x_rel]
                if water_depth <= MAX_STILT_HEIGHT:
                    suitability_map[z_rel, x_rel] = 0.8  # Suitable water depth
                else:
                    suitability_map[z_rel, x_rel] = 0.3  # Too deep
    
    # Apply Gaussian smoothing for more continuous suitable areas
    suitability_map = ndimage.gaussian_filter(suitability_map, sigma=1.0)
    
    # Normalize scores
    if np.max(suitability_map) > 0:
        suitability_map = suitability_map / np.max(suitability_map)
    
    # Generate visualization plots
    try:
        generate_visualizations(
            suitability_map, 
            terrain_type_map, 
            slope_map, 
            OUTPUT_DIR
        )
    except Exception as e:
        print(f"Warning: Could not generate visualizations: {e}")
    
    # Detect trees in the area
    print("Detecting trees...")
    tree_map = detect_trees(editor, x, z, dx, dz, terrain_heightmap)
    
    # Apply strong penalty to suitability for areas with trees
    print("Applying tree density penalties to suitability map...")
    for z_rel in range(dz):
        for x_rel in range(dx):
            tree_density = tree_map[z_rel, x_rel]
            
            # Apply progressively stronger penalties based on tree density
            if tree_density > 0.7:  # Very dense forest
                suitability_map[z_rel, x_rel] *= 0.1  # 90% penalty
            elif tree_density > 0.4:  # Moderate forest
                suitability_map[z_rel, x_rel] *= 0.3  # 70% penalty
            elif tree_density > 0.2:  # Light forest
                suitability_map[z_rel, x_rel] *= 0.6  # 40% penalty
    
    # Re-normalize after tree penalty
    if np.max(suitability_map) > 0:
        suitability_map = suitability_map / np.max(suitability_map)
    
    # Generate combined visualization showing suitability with tree penalties
    try:
        import matplotlib.pyplot as plt
        from matplotlib.colors import LinearSegmentedColormap
        
        plt.figure(figsize=(12, 10))
        colors = ['#000033', '#0066CC', '#66CCFF', '#66FFCC', '#FFFF99']
        cmap = LinearSegmentedColormap.from_list("suitability_with_trees", colors, N=100)
        plt.imshow(suitability_map, cmap=cmap, interpolation='nearest')
        plt.colorbar(label='Adjusted Suitability Score')
        plt.title('Stilt House Placement Suitability (With Tree Penalties)')
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, "suitability_with_trees.png"), dpi=300)
        plt.close()
    except Exception as e:
        print(f"Warning: Could not generate tree-adjusted suitability visualization: {e}")
    
    # Calculate improved shoreline detection map for optimal partial submersion
    print("Running improved shoreline detection for partial submersion...")
    shoreline_map = improved_shoreline_detection(water_map, (dz, dx), terrain_type_map, terrain_heightmap, ocean_floor)
    
    # Generate visualization for optimal shoreline areas
    try:
        import matplotlib.pyplot as plt
        
        plt.figure(figsize=(12, 10))
        plt.imshow(shoreline_map, cmap='Blues', interpolation='nearest')
        plt.colorbar(label='Shoreline Quality for Partial Submersion')
        plt.title('Optimal Shoreline Areas for Partially Submerged Stilt Houses')
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, "optimal_shoreline_map.png"), dpi=300)
        plt.close()
        
        # Create a combined visualization showing terrain types and optimal shoreline
        plt.figure(figsize=(12, 10))
        # Use a custom colormap for terrain types
        terrain_rgb = np.zeros((dz, dx, 3))
        terrain_rgb[terrain_type_map == 0] = [0.4, 0.8, 0.4]  # Green for flat
        terrain_rgb[terrain_type_map == 1] = [0.8, 0.7, 0.4]  # Brown for hills
        terrain_rgb[terrain_type_map == 2] = [0.2, 0.4, 0.8]  # Blue for water
        
        # Overlay shoreline quality
        shoreline_overlay = np.zeros((dz, dx, 4))
        shoreline_overlay[..., 0] = 1.0  # Red
        shoreline_overlay[..., 1] = 0.6  # Some green
        shoreline_overlay[..., 2] = 0.0  # No blue
        shoreline_overlay[..., 3] = shoreline_map * 0.7  # Alpha based on shoreline quality
        
        plt.imshow(terrain_rgb)
        plt.imshow(shoreline_overlay)
        plt.colorbar(label='Shoreline Quality Overlay')
        plt.title('Terrain with Optimal Shoreline Areas Highlighted')
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, "terrain_with_shoreline.png"), dpi=300)
        plt.close()
    except Exception as e:
        print(f"Warning: Could not generate shoreline visualization: {e}")
    
    # Return all analyzed data including the improved shoreline map
    return {
        'suitability_map': suitability_map,
        'terrain_type_map': terrain_type_map,
        'water_map': water_map,
        'slope_map': slope_map,
        'heightmap': terrain_heightmap,
        'ocean_floor': ocean_floor,
        'tree_map': tree_map,
        'shoreline_map': shoreline_map,
        'shape': (dz, dx),
        'x_start': x,
        'z_start': z
    }

def detect_trees(editor, x_start, z_start, width, length, heightmap):
    """
    Detect trees in the area and create a tree density map.
    Uses sparse sampling to be more efficient while still finding tree clusters.
    
    Parameters:
    editor: The Minecraft world editor
    x_start, z_start: Starting coordinates
    width, length: Dimensions of the area
    heightmap: Terrain heightmap for ground level reference
    
    Returns:
    numpy.ndarray: A 2D array where values represent tree density (0.0-1.0)
    """
    print("Scanning for trees in the area (using sparse sampling)...")
    
    # Initialize tree map
    tree_map = np.zeros((length, width))
    
    # Sample step - check fewer points for better performance
    # This means checking approximately 4% of all possible points
    sample_step_x = 5  # Check every 5 blocks in x direction
    sample_step_z = 5  # Check every 5 blocks in z direction
    sample_step_y = 5  # Check every 5 blocks in y direction
    
    # Make the grid offset slightly to catch more varied terrain
    offset_x = random.randint(0, 4)
    offset_z = random.randint(0, 4)
    
    # Detection height range
    max_height = 25  # Maximum height to check above ground
    
    # List of sample positions to check
    positions_to_check = []
    
    # First, build a list of all positions to check
    for z_rel in range(offset_z, length, sample_step_z):
        for x_rel in range(offset_x, width, sample_step_x):
            if z_rel >= length or x_rel >= width:
                continue
                
            # Get ground level at this position
            if z_rel < length and x_rel < width:
                ground_y = heightmap[z_rel, x_rel]
                
                # Add vertical sample points at this position
                for y_offset in range(0, max_height, sample_step_y):
                    y = int(ground_y + y_offset)
                    positions_to_check.append((x_start + x_rel, y, z_start + z_rel, x_rel, z_rel))
            
    # Shuffle positions for better distribution of requests
    random.shuffle(positions_to_check)
    
    # Now check a subset of the positions (further optimization)
    max_positions = min(len(positions_to_check), 500)  # Cap at 500 sample points
    sample_positions = positions_to_check[:max_positions]
    
    print(f"Checking {len(sample_positions)} sample points for trees...")
    
    # Dictionary to track tree blocks per grid cell
    tree_counts = {}
    
    # Tree block types to look for
    tree_block_types = [
        "log", "leaves", "trunk", "stem", "mushroom_stem", 
        "warped_stem", "crimson_stem", "mangrove"
    ]
    
    # Check all sample positions 
    for (x, y, z, x_rel, z_rel) in sample_positions:
        # Add delay to prevent overwhelming the HTTP interface
        import time
        time.sleep(0.01)  # 10ms delay
        
        try:
            block = editor.getBlock((x, y, z))
            
            if block:
                block_id = block.id.lower()
                # Check if it's a tree-related block
                is_tree = any(tree_type in block_id for tree_type in tree_block_types)
                
                if is_tree:
                    # Calculate grid cell for this position
                    grid_x = x_rel // sample_step_x
                    grid_z = z_rel // sample_step_z
                    
                    # Increment tree count for this grid cell
                    key = (grid_x, grid_z)
                    tree_counts[key] = tree_counts.get(key, 0) + 1
        except Exception as e:
            # Just skip any blocks we can't check
            continue
    
    # Now map the tree counts to the tree density map
    max_tree_count = 5  # Threshold for maximum tree density
    
    for (grid_x, grid_z), count in tree_counts.items():
        # Normalize count to density
        density = min(1.0, count / max_tree_count)
        
        # Fill the corresponding area in the tree map
        start_x = grid_x * sample_step_x
        start_z = grid_z * sample_step_z
        
        # Fill a block of the tree map
        for dz in range(sample_step_z):
            for dx in range(sample_step_x):
                if start_z + dz < length and start_x + dx < width:
                    tree_map[start_z + dz, start_x + dx] = density
    
    # Apply Gaussian smoothing for a more continuous tree map
    try:
        from scipy import ndimage
        tree_map = ndimage.gaussian_filter(tree_map, sigma=2.0)
    except Exception as e:
        print(f"Warning: Could not apply smoothing to tree map: {e}")
    
    # Generate visualization for tree map
    try:
        import matplotlib.pyplot as plt
        plt.figure(figsize=(10, 8))
        plt.imshow(tree_map, cmap='Greens', interpolation='nearest')
        plt.colorbar(label='Tree Density')
        plt.title('Tree Density Map (Sparse Sampling)')
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, "tree_map.png"), dpi=300)
        plt.close()
    except Exception as e:
        print(f"Warning: Could not generate tree map visualization: {e}")
    
    print("Tree detection complete.")
    return tree_map

def generate_visualizations(suitability_map, terrain_type_map, slope_map, output_dir):
    """Generate visualization plots for terrain analysis."""
    print("Generating visualization plots...")
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap
    
    # Plot suitability map
    plt.figure(figsize=(10, 8))
    colors = ['#000033', '#0066CC', '#66CCFF', '#66FFCC', '#FFFF99']
    cmap = LinearSegmentedColormap.from_list("stilt_suitability", colors, N=100)
    plt.imshow(suitability_map, cmap=cmap, interpolation='nearest')
    plt.colorbar(label='Suitability Score')
    plt.title('Stilt House Placement Suitability')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "stilt_suitability.png"), dpi=300)
    plt.close()
    
    # Plot terrain type map
    plt.figure(figsize=(10, 8))
    terrain_cmap = plt.cm.get_cmap('viridis', 3)
    plt.imshow(terrain_type_map, cmap=terrain_cmap, interpolation='nearest')
    plt.colorbar(ticks=[0, 1, 2], label='Terrain Type')
    plt.title('Terrain Classification (0=Flat, 1=Hill, 2=Water)')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "terrain_types.png"), dpi=300)
    plt.close()
    
    # Plot slope map
    plt.figure(figsize=(10, 8))
    plt.imshow(slope_map, cmap='hot_r', interpolation='nearest')
    plt.colorbar(label='Terrain Slope (Height Variance)')
    plt.title('Terrain Slope Map')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "slope_map.png"), dpi=300)
    plt.close()

# Run standalone terrain mapping if executed directly
if __name__ == "__main__":
    import sys
    
    # Parse command line arguments
    x, z = None, None
    size = 100
    
    if len(sys.argv) >= 3:
        try:
            x = int(sys.argv[1])
            z = int(sys.argv[2])
            if len(sys.argv) >= 4:
                size = int(sys.argv[3])
        except ValueError:
            print("Invalid arguments. Using random position.")
            x, z = None, None
    
    # Map the area
    editor = Editor(buffering=False)
    
    if x is not None and z is not None:
        print(f"Mapping fixed area at ({x}, {z}) with size {size}x{size}")
        # TODO: Implement fixed position mapping
    else:
        area_data = map_random_area(size)
        print(f"Mapped random area at ({area_data['x_start']}, {area_data['z_start']}) with size {size}x{size}")
    
    # Run terrain analysis
    print("\nAnalyzing terrain for stilt house placement...")
    terrain_data = analyze_terrain(editor)
    print("Terrain analysis complete! Visualizations saved to the terrain_analysis directory.")