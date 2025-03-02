from gdpc import Editor
import os
import random
import sys
import time
# Import terrain analysis and mapping functions
from terrain_mapper import map_random_area, analyze_terrain
from house_blueprints import HouseBlueprintFactory
import stilt_house_builder as builder

def main():
    """
    Main function to procedurally generate stilt houses in a Minecraft world.
    Maps a random area, analyzes terrain, clears trees, and builds houses with proper stilts.
    """
    print("============================================")
    print("Minecraft Procedural Stilt House Generator")
    print("============================================")
    
    # Parse command line arguments
    num_houses = 10  # Default
    if len(sys.argv) > 1:
        try:
            num_houses = int(sys.argv[1])
            # Limit to maximum 25 houses
            num_houses = min(25, num_houses)
        except ValueError:
            print(f"Invalid argument: {sys.argv[1]}. Using default of 10 houses.")
    
    print(f"Will generate up to {num_houses} houses")
    
    # Create editor instance with buffering disabled to avoid issues
    editor = Editor(buffering=False)
    
    try:
        # Step 1: Map a random 100x100 area
        print("\n1. Mapping a random 100x100 area...")
        area_data = map_random_area(size=100)
        print(f"   Area mapped at coordinates ({area_data['x_start']}, {area_data['z_start']})")
        
        # Step 2: Analyze terrain for stilt house placement
        print("\n2. Analyzing terrain for stilt house placement...")
        start_time = time.time()
        terrain_data = analyze_terrain(editor)
        print(f"   Terrain analysis completed in {time.time() - start_time:.2f} seconds")
        
        print("\n3. Finding suitable house locations...")
        print("   Priority order: 1) Optimal shoreline 2) Hills without trees 3) Flat areas without trees 4) Areas with trees")
        house_locations = builder.find_house_locations(
            terrain_data,
            min_houses=20,  # Minimum of 10 houses
            max_houses=num_houses,
            min_distance=10  # 20 blocks minimum distance
        )
        
        if not house_locations:
            print("Error: No suitable locations found for stilt houses.")
            return
        
        print(f"   Found {len(house_locations)} suitable locations for houses")
        
        # Print information about tree density at these locations
        print("\n   Selected locations:")
        for i, loc in enumerate(house_locations):
            position = loc["position"]
            terrain_type = loc["terrain_type"]
            terrain_name = ["Flat", "Hill", "Water"][terrain_type]
            tree_density = loc.get("tree_density", 0)
            is_shoreline = loc.get("is_shoreline", False)
            shoreline_quality = loc.get("shoreline_quality", 0)
            
            tree_status = "Unknown"
            if tree_density < 0.1:
                tree_status = "LOW"
            elif tree_density < 0.3:
                tree_status = "MEDIUM"
            else:
                tree_status = "HIGH"
            
            location_type = f"Shoreline (quality: {shoreline_quality:.2f})" if is_shoreline else terrain_name
            print(f"   {i+1}. Position: {position}, Type: {location_type}, Tree density: {tree_status} ({tree_density:.2f})")

        
        # Create directory for house coordinates
        coords_dir = "stilt_house_coordinates"
        os.makedirs(coords_dir, exist_ok=True)
        
        # Save house coordinates to a file
        coords_file = os.path.join(coords_dir, "house_coordinates.txt")
        
        with open(coords_file, "w") as f:
            f.write("Stilt House Network Coordinates\n")
            f.write("===============================\n\n")
        
        # Step 4: Build houses and save information
        print("\n4. Building procedurally generated stilt houses...")
        house_info = []
        
        for i, loc in enumerate(house_locations):
            position = loc["position"]
            x, y, z = position
            terrain_type = loc["terrain_type"]
            
            # Create a random house blueprint
            style = random.choice(["traditional", "modern", "asian", "nordic", "tropical"])
            size = random.choice(["small", "medium", "large"])
            wood_type = random.choice([None, "oak", "spruce", "birch", "jungle", "acacia", "dark_oak"])
            
            blueprint = HouseBlueprintFactory.create_house("stilt", style, size, wood_type)
            
            print(f"\n   Building house {i+1}/{len(house_locations)}:")
            print(f"   - Style: {blueprint.style}")
            print(f"   - Size: {blueprint.size}")
            print(f"   - Wood: {blueprint.wood_type}")
            
            # Build the house adapted to terrain type with tree clearing using optimized function
            house_data = builder.build_stilt_house(
                editor, x, y, z, 
                terrain_type=terrain_type,
                blueprint=blueprint,
                clear_trees=True
            )
            
            if house_data:
                house_info.append(house_data)
                
                # Print and save coordinates
                terrain_name = ["Flat", "Hill", "Water"][terrain_type]
                print(f"   House {i+1} built at {position} on {terrain_name} terrain")
                print(f"   Stilt height: {house_data['stilt_height']} blocks")
                print(f"   Dimensions: {house_data['dimensions']}")
                print(f"   Teleport command: /tp @p {x} {house_data['floor_level']} {z}")
                
                with open(coords_file, "a") as f:
                    f.write(f"House {len(house_info)} ({house_data['size']} {house_data['style']} on {terrain_name}):\n")
                    f.write(f"  Position: {position}\n")
                    f.write(f"  Wood type: {blueprint.wood_type}\n")
                    f.write(f"  Dimensions: {house_data['dimensions']}\n")
                    f.write(f"  Stilt height: {house_data['stilt_height']} blocks\n")
                    f.write(f"  Floor level: {house_data['floor_level']}\n")
                    f.write(f"  Teleport: /tp @p {x} {house_data['floor_level']} {z}\n\n")
        
        if not house_info:
            print("\nFailed to build any houses. Could not find suitable locations.")
            return
            
        print(f"\nSuccessfully built {len(house_info)} stilt houses.")
        print(f"House coordinates saved to: {coords_file}")
        print("\nProcess completed successfully!")
        
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()