import random
import math

# Materials for different house styles
WOOD_TYPES = ["oak", "spruce", "birch", "jungle", "acacia", "dark_oak"]
WOOD_PAIRS = {
    "oak": ("oak_planks", "oak_log", "oak_fence", "oak_stairs", "oak_door", "oak_trapdoor"),
    "spruce": ("spruce_planks", "spruce_log", "spruce_fence", "spruce_stairs", "spruce_door", "spruce_trapdoor"),
    "birch": ("birch_planks", "birch_log", "birch_fence", "birch_stairs", "birch_door", "birch_trapdoor"),
    "jungle": ("jungle_planks", "jungle_log", "jungle_fence", "jungle_stairs", "jungle_door", "jungle_trapdoor"),
    "acacia": ("acacia_planks", "acacia_log", "acacia_fence", "acacia_stairs", "acacia_door", "acacia_trapdoor"),
    "dark_oak": ("dark_oak_planks", "dark_oak_log", "dark_oak_fence", "dark_oak_stairs", "dark_oak_door", "dark_oak_trapdoor")
}

# Style-specific materials and features
STYLE_FEATURES = {
    "traditional": {
        "secondary_materials": ["cobblestone", "stone_bricks", "mossy_cobblestone"],
        "decorative_blocks": ["lantern", "flower_pot", "bookshelf"],
        "window_style": "full", # Full windows
        "roof_overhang": 1,     # Roof extends 1 block beyond walls
        "stilt_pattern": "square", # Square arrangement of stilts
        "furniture_style": "rustic"
    },
    "modern": {
        "secondary_materials": ["smooth_stone", "white_concrete", "glass"],
        "decorative_blocks": ["sea_lantern", "end_rod", "glazed_terracotta"],
        "window_style": "large", # Large windows
        "roof_overhang": 0,     # Flat roof with no overhang
        "stilt_pattern": "minimal", # Minimal stilts for modern look
        "furniture_style": "minimalist"
    },
    "asian": {
        "secondary_materials": ["smooth_stone", "prismarine", "dark_prismarine"],
        "decorative_blocks": ["lantern", "bell", "bamboo"],
        "window_style": "lattice", # Lattice windows
        "roof_overhang": 2,     # Extended roof overhang
        "stilt_pattern": "complex", # Complex stilt arrangement
        "furniture_style": "traditional_asian"
    },
    "tropical": {
        "secondary_materials": ["sandstone", "smooth_sandstone", "prismarine"],
        "decorative_blocks": ["coral", "sea_pickle", "tropical_fish_bucket"],
        "window_style": "open", # Open windows
        "roof_overhang": 1,     # Moderate overhang
        "stilt_pattern": "tall", # Tall stilts
        "furniture_style": "beach"
    },
    "nordic": {
        "secondary_materials": ["spruce_planks", "cobblestone", "polished_andesite"],
        "decorative_blocks": ["lantern", "campfire", "smoker"],
        "window_style": "small", # Small windows
        "roof_overhang": 1,     # Moderate overhang
        "stilt_pattern": "thick", # Thick, sturdy stilts
        "furniture_style": "rustic_nordic"
    }
}

# Maximum stilt height for any terrain
MAX_STILT_HEIGHT = 15


class HouseBlueprint:
    """Base class for house blueprints"""
    def __init__(self, style="traditional", size="medium", wood_type=None):
        # Expand style options
        all_styles = list(STYLE_FEATURES.keys())
        self.style = style if style in all_styles else random.choice(all_styles)
        
        self.size = size
        self.wood_type = wood_type or random.choice(WOOD_TYPES)
        self.materials = WOOD_PAIRS[self.wood_type]
        
        # Get style-specific features
        self.style_features = STYLE_FEATURES[self.style]
        self.secondary_material = random.choice(self.style_features["secondary_materials"])
        
        # Set dimensions based on size
        if size == "small":
            self.width = random.randint(5, 6)
            self.length = random.randint(5, 6)
            self.height = random.randint(3, 4)
        elif size == "large":
            self.width = random.randint(8, 10)
            self.length = random.randint(8, 10)
            self.height = random.randint(4, 5)
        else:  # medium (default)
            self.width = random.randint(6, 8)
            self.length = random.randint(6, 8)
            self.height = random.randint(3, 4)
            
        # Randomly vary the shape slightly
        self.shape_variation = random.choice(["rectangle", "l_shape", "square", "irregular"])
        if self.shape_variation != "rectangle" and size != "small":
            # Apply shape variation
            if self.shape_variation == "l_shape":
                # Create an L-shaped building by removing one corner
                self.corner_cutout = random.choice(["NE", "NW", "SE", "SW"])
                self.cutout_size = random.randint(2, min(self.width, self.length) // 2)
            elif self.shape_variation == "irregular":
                # Create a slight irregularity - one wall is shorter or longer
                self.irregular_wall = random.choice(["N", "S", "E", "W"])
                self.wall_offset = random.randint(1, 2)
    
    def get_info(self):
        """Return information about the house blueprint"""
        return {
            "style": self.style,
            "size": self.size,
            "wood_type": self.wood_type,
            "materials": self.materials,
            "secondary_material": self.secondary_material,
            "dimensions": (self.width, self.height, self.length),
            "shape_variation": getattr(self, "shape_variation", "rectangle"),
            "style_features": self.style_features
        }
    
    def get_footprint(self):
        """Return the footprint of the house as (width, length)"""
        return (self.width, self.length)

class StiltHouseBlueprint(HouseBlueprint):
    """Blueprint for stilt houses that adapt to different terrain types"""
    def __init__(self, style="traditional", size="medium", wood_type=None):
        super().__init__(style, size, wood_type)
        self.stilt_height = 0  # Will be determined dynamically based on terrain
        self.stilt_positions = []
        self.cross_braces = []
        self.door_position = None
        self.windows = []
        self.furniture = []
        self.decorative_elements = []
        self.roof_details = {}
        
        # Generate style-specific architectural features
        self._generate_layout()
        self._generate_style_features()
    
    def _generate_layout(self):
        """Generate the house layout including stilt positions, door, windows, etc."""
        width, height, length = self.width, self.height, self.length
        
        # Generate stilt positions based on style pattern
        stilt_pattern = self.style_features["stilt_pattern"]
        
        if stilt_pattern == "square":
            # Traditional square arrangement
            self.stilt_positions = [
                (0, 0),                  # Front-left
                (width - 1, 0),          # Front-right
                (0, length - 1),         # Back-left
                (width - 1, length - 1)  # Back-right
            ]
            
            # Add middle stilts for larger houses
            if width > 6 or length > 6:
                self.stilt_positions.append((width // 2, 0))  # Front-middle
                self.stilt_positions.append((width // 2, length - 1))  # Back-middle
                self.stilt_positions.append((0, length // 2))  # Left-middle
                self.stilt_positions.append((width - 1, length // 2))  # Right-middle
                
                if width > 7 and length > 7:
                    self.stilt_positions.append((width // 2, length // 2))  # Center
        
        elif stilt_pattern == "minimal":
            # Modern with fewer stilts
            self.stilt_positions = [
                (0, 0),                  # Front-left
                (width - 1, 0),          # Front-right
                (0, length - 1),         # Back-left
                (width - 1, length - 1)  # Back-right
            ]
            
            # Add just one central stilt for larger houses
            if width > 7 and length > 7:
                self.stilt_positions.append((width // 2, length // 2))  # Center
        
        elif stilt_pattern == "complex":
            # Asian with more complex pattern
            self.stilt_positions = [
                (0, 0),                  # Front-left
                (width - 1, 0),          # Front-right
                (0, length - 1),         # Back-left
                (width - 1, length - 1),  # Back-right
                (width // 3, 0),         # Front third point
                (2 * width // 3, 0),     # Front two-thirds point
                (width // 3, length - 1), # Back third point
                (2 * width // 3, length - 1), # Back two-thirds point
                (0, length // 3),         # Left third point
                (0, 2 * length // 3),     # Left two-thirds point
                (width - 1, length // 3),  # Right third point
                (width - 1, 2 * length // 3) # Right two-thirds point
            ]
            
            # For larger houses, add interior stilts
            if width > 7 and length > 7:
                self.stilt_positions.append((width // 3, length // 3))
                self.stilt_positions.append((2 * width // 3, length // 3))
                self.stilt_positions.append((width // 3, 2 * length // 3))
                self.stilt_positions.append((2 * width // 3, 2 * length // 3))
        
        elif stilt_pattern == "tall":
            # Tropical with taller stilts (determined during building)
            self.stilt_positions = [
                (0, 0),                  # Front-left
                (width - 1, 0),          # Front-right
                (0, length - 1),         # Back-left
                (width - 1, length - 1)  # Back-right
            ]
            
            # Add some middle stilts but fewer than traditional
            if width > 6 or length > 6:
                self.stilt_positions.append((width // 2, 0))  # Front-middle
                self.stilt_positions.append((width // 2, length - 1))  # Back-middle
        
        elif stilt_pattern == "thick":
            # Nordic with thick stilts (implemented in the builder)
            # But fewer stilts overall for a more sturdy look
            self.stilt_positions = [
                (0, 0),                  # Front-left
                (width - 1, 0),          # Front-right
                (0, length - 1),         # Back-left
                (width - 1, length - 1)  # Back-right
            ]
            
            # Just add central support
            if width > 6 and length > 6:
                self.stilt_positions.append((width // 2, length // 2))  # Center
        
        # Generate the cross braces pattern
        self._generate_cross_braces()
        
        # Set door position based on style
        if self.style == "traditional":
            # Door in the middle of one wall
            self.door_position = (width // 2, length - 1, "north")
        elif self.style == "modern":
            # Door offset from center for asymmetrical look
            offset = random.choice([-1, 1])
            self.door_position = (max(1, min(width - 2, width // 2 + offset)), length - 1, "north")
        elif self.style == "asian":
            # Centered door with potential for raised entryway
            self.door_position = (width // 2, length - 1, "north")
            self.has_raised_entry = True
        elif self.style == "tropical":
            # Door could be on any wall
            wall = random.choice(["north", "south", "east", "west"])
            if wall == "north":
                self.door_position = (width // 2, 0, "south")
            elif wall == "south":
                self.door_position = (width // 2, length - 1, "north")
            elif wall == "east":
                self.door_position = (width - 1, length // 2, "west")
            else:  # west
                self.door_position = (0, length // 2, "east")
        elif self.style == "nordic":
            # Door typically on the shorter wall
            if width < length:
                side = random.choice(["east", "west"])
                if side == "east":
                    self.door_position = (width - 1, length // 2, "west")
                else:
                    self.door_position = (0, length // 2, "east")
            else:
                side = random.choice(["north", "south"])
                if side == "north":
                    self.door_position = (width // 2, 0, "south")
                else:
                    self.door_position = (width // 2, length - 1, "north")
        
        # Generate windows based on style
        self._generate_windows()
        
        # Generate furniture layout based on style
        self._generate_furniture()
    
    def _generate_style_features(self):
        """Generate style-specific architectural features"""
        # Roof details
        if self.style == "traditional":
            # A-frame roof
            self.roof_details = {
                "type": "a_frame",
                "material": self.materials[0],  # planks
                "overhang": 1
            }
        elif self.style == "modern":
            # Flat roof with potential for small overhang
            self.roof_details = {
                "type": "flat",
                "material": self.secondary_material,
                "overhang": 0,
                "has_railing": True
            }
        elif self.style == "asian":
            # Pagoda-style roof with upturned edges
            self.roof_details = {
                "type": "pagoda",
                "material": self.materials[3],  # stairs
                "overhang": 2,
                "upturned_edges": True
            }
        elif self.style == "tropical":
            # Thatched or sloped roof
            self.roof_details = {
                "type": "thatched",
                "material": "jungle_leaves" if self.wood_type != "jungle" else "oak_leaves",
                "overhang": 1
            }
        elif self.style == "nordic":
            # Steep A-frame roof
            self.roof_details = {
                "type": "steep_a_frame",
                "material": self.materials[0],  # planks
                "overhang": 1,
                "snow_covered": random.choice([True, False])
            }
        
        # Decorative elements
        self._generate_decorative_elements()
    
    def _generate_cross_braces(self):
        """Generate cross braces between stilts for stability"""
        self.cross_braces = []
        
        # Style-specific brace patterns
        if self.style == "modern":
            # Minimal cross-bracing for modern style
            # Just connect the corners diagonally
            corners = [(0, 0), (self.width - 1, 0), (0, self.length - 1), (self.width - 1, self.length - 1)]
            for i in range(len(corners)):
                for j in range(i + 1, len(corners)):
                    s1_x, s1_z = corners[i]
                    s2_x, s2_z = corners[j]
                    dist = math.sqrt((s1_x - s2_x)**2 + (s1_z - s2_z)**2)
                    
                    if dist <= 7:  # Only brace corners that are close enough
                        mid_x = (s1_x + s2_x) // 2
                        mid_z = (s1_z + s2_z) // 2
                        self.cross_braces.append((mid_x, mid_z, "diagonal"))
        
        elif self.style == "asian" or self.style == "tropical":
            # More complex cross-bracing with X patterns
            # For each pair of adjacent stilts
            for i, stilt1 in enumerate(self.stilt_positions):
                s1_x, s1_z = stilt1
                
                # Find closest neighbor stilts
                neighbors = []
                for j, stilt2 in enumerate(self.stilt_positions):
                    if i == j:
                        continue
                    
                    s2_x, s2_z = stilt2
                    dist = math.sqrt((s1_x - s2_x)**2 + (s1_z - s2_z)**2)
                    
                    if dist <= 7:  # Only consider close neighbors
                        neighbors.append((stilt2, dist))
                
                # Sort neighbors by distance
                neighbors.sort(key=lambda x: x[1])
                
                # Create braces to 2 closest neighbors (if available)
                for n in range(min(2, len(neighbors))):
                    stilt2, _ = neighbors[n]
                    s2_x, s2_z = stilt2
                    
                    # Compute brace positions
                    if s1_x == s2_x:  # Vertical alignment
                        mid_x = s1_x
                        mid_z = (s1_z + s2_z) // 2
                        self.cross_braces.append((mid_x, mid_z, "horizontal_z"))
                    elif s1_z == s2_z:  # Horizontal alignment
                        mid_x = (s1_x + s2_x) // 2
                        mid_z = s1_z
                        self.cross_braces.append((mid_x, mid_z, "horizontal_x"))
                    else:  # Diagonal
                        mid_x = (s1_x + s2_x) // 2
                        mid_z = (s1_z + s2_z) // 2
                        self.cross_braces.append((mid_x, mid_z, "diagonal"))
                        
                        # For Asian style, add X-bracing (additional cross piece)
                        if self.style == "asian" and random.random() > 0.5:
                            quarter_x = s1_x + (s2_x - s1_x) // 4
                            quarter_z = s1_z + (s2_z - s1_z) // 4
                            three_quarter_x = s1_x + 3 * (s2_x - s1_x) // 4
                            three_quarter_z = s1_z + 3 * (s2_z - s1_z) // 4
                            
                            self.cross_braces.append((quarter_x, quarter_z, "diagonal"))
                            self.cross_braces.append((three_quarter_x, three_quarter_z, "diagonal"))
        
        else:  # Default pattern for traditional and nordic
            # For each pair of stilts
            for i, stilt1 in enumerate(self.stilt_positions):
                for j, stilt2 in enumerate(self.stilt_positions[i+1:], i+1):
                    s1_x, s1_z = stilt1
                    s2_x, s2_z = stilt2
                    
                    # Only add braces between stilts that are close to each other
                    dist = math.sqrt((s1_x - s2_x)**2 + (s1_z - s2_z)**2)
                    
                    if dist <= 7:  # Only brace stilts within reasonable distance
                        # Check if horizontal or diagonal brace
                        if s1_x == s2_x or s1_z == s2_z:
                            # Horizontal brace (use logs)
                            mid_x = (s1_x + s2_x) // 2
                            mid_z = (s1_z + s2_z) // 2
                            
                            # Store brace position and type
                            if s1_x == s2_x:
                                self.cross_braces.append((mid_x, mid_z, "horizontal_z"))
                            else:
                                self.cross_braces.append((mid_x, mid_z, "horizontal_x"))
                        else:
                            # Diagonal brace (use fence)
                            mid_x = (s1_x + s2_x) // 2
                            mid_z = (s1_z + s2_z) // 2
                            self.cross_braces.append((mid_x, mid_z, "diagonal"))
            
            # For Nordic, add extra horizontal braces for a sturdier look
            if self.style == "nordic":
                for stilt_x, stilt_z in self.stilt_positions:
                    # Add horizontal braces at mid-height
                    if stilt_x == 0 or stilt_x == self.width - 1:
                        # For each stilt on the side, add braces along z-axis
                        for z_pos in range(1, self.length - 1, 2):
                            if z_pos != stilt_z:
                                self.cross_braces.append((stilt_x, z_pos, "horizontal_z"))
                    
                    if stilt_z == 0 or stilt_z == self.length - 1:
                        # For each stilt on the front/back, add braces along x-axis
                        for x_pos in range(1, self.width - 1, 2):
                            if x_pos != stilt_x:
                                self.cross_braces.append((x_pos, stilt_z, "horizontal_x"))
    
    def _generate_windows(self):
        """Generate windows based on style"""
        self.windows = []
        width, length = self.width, self.length
        window_style = self.style_features["window_style"]
        
        # Default positions for door to avoid placing windows there
        door_x, door_z, _ = self.door_position
        
        if window_style == "large":  # Modern style
            # Larger and fewer windows
            # North wall (z=0)
            if random.random() < 0.8:  # 80% chance of large window
                window_width = min(3, width - 2)
                start_x = (width - window_width) // 2
                for x in range(start_x, start_x + window_width):
                    self.windows.append((x, 0, 1))
            
            # South wall (z=length-1)
            if door_z != length - 1 and random.random() < 0.8:
                window_width = min(3, width - 2)
                start_x = (width - window_width) // 2
                for x in range(start_x, start_x + window_width):
                    self.windows.append((x, length-1, 1))
            
            # East wall (x=width-1)
            if random.random() < 0.8:
                window_length = min(3, length - 2)
                start_z = (length - window_length) // 2
                for z in range(start_z, start_z + window_length):
                    self.windows.append((width-1, z, 1))
            
            # West wall (x=0)
            if random.random() < 0.8:
                window_length = min(3, length - 2)
                start_z = (length - window_length) // 2
                for z in range(start_z, start_z + window_length):
                    self.windows.append((0, z, 1))
        
        elif window_style == "lattice":  # Asian style
            # Lattice windows - pairs of small windows
            # North wall (z=0)
            for x in range(1, width-1, 2):
                if random.random() < 0.7:
                    self.windows.append((x, 0, 1))
                    if x + 1 < width - 1:
                        self.windows.append((x+1, 0, 1))
            
            # South wall (z=length-1)
            for x in range(1, width-1, 2):
                if x != door_x and x+1 != door_x and random.random() < 0.7:
                    self.windows.append((x, length-1, 1))
                    if x + 1 < width - 1:
                        self.windows.append((x+1, length-1, 1))
            
            # East wall (x=width-1)
            for z in range(1, length-1, 2):
                if random.random() < 0.7:
                    self.windows.append((width-1, z, 1))
                    if z + 1 < length - 1:
                        self.windows.append((width-1, z+1, 1))
            
            # West wall (x=0)
            for z in range(1, length-1, 2):
                if random.random() < 0.7:
                    self.windows.append((0, z, 1))
                    if z + 1 < length - 1:
                        self.windows.append((0, z+1, 1))
        
        elif window_style == "open":  # Tropical style
            # More open windows, potentially some at higher levels
            # North wall (z=0)
            for x in range(1, width-1):
                if random.random() < 0.7:
                    self.windows.append((x, 0, 1))
                    # Some windows on second level
                    if self.height > 3 and random.random() < 0.4:
                        self.windows.append((x, 0, 2))
            
            # South wall (z=length-1)
            for x in range(1, width-1):
                if x != door_x and random.random() < 0.7:
                    self.windows.append((x, length-1, 1))
                    # Some windows on second level
                    if self.height > 3 and random.random() < 0.4:
                        self.windows.append((x, length-1, 2))
            
            # East wall (x=width-1)
            for z in range(1, length-1):
                if random.random() < 0.7:
                    self.windows.append((width-1, z, 1))
                    # Some windows on second level
                    if self.height > 3 and random.random() < 0.4:
                        self.windows.append((width-1, z, 2))
            
            # West wall (x=0)
            for z in range(1, length-1):
                if random.random() < 0.7:
                    self.windows.append((0, z, 1))
                    # Some windows on second level
                    if self.height > 3 and random.random() < 0.4:
                        self.windows.append((0, z, 2))
        
        elif window_style == "small":  # Nordic style
            # Fewer, smaller windows
            # North wall (z=0)
            for x in range(1, width-1, 2):
                if random.random() < 0.4:
                    self.windows.append((x, 0, 1))
            
            # South wall (z=length-1)
            for x in range(1, width-1, 2):
                if x != door_x and random.random() < 0.4:
                    self.windows.append((x, length-1, 1))
            
            # East wall (x=width-1)
            for z in range(1, length-1, 2):
                if random.random() < 0.4:
                    self.windows.append((width-1, z, 1))
            
            # West wall (x=0)
            for z in range(1, length-1, 2):
                if random.random() < 0.4:
                    self.windows.append((0, z, 1))
        
        else:  # Default / traditional pattern
            # North wall (z=0)
            for x in range(1, width-1):
                if random.random() < 0.5:
                    self.windows.append((x, 0, 1))
            
            # South wall (z=length-1)
            for x in range(1, width-1):
                if x != door_x and random.random() < 0.5:
                    self.windows.append((x, length-1, 1))
            
            # East wall (x=width-1)
            for z in range(1, length-1):
                if random.random() < 0.5:
                    self.windows.append((width-1, z, 1))
            
            # West wall (x=0)
            for z in range(1, length-1):
                if random.random() < 0.5:
                    self.windows.append((0, z, 1))
    
    def _generate_furniture(self):
        """Generate furniture layout based on style"""
        width, length = self.width, self.length
        self.furniture = []
        
        furniture_style = self.style_features["furniture_style"]
        
        if furniture_style == "minimalist":  # Modern style
            # Minimalist furniture with clean lines
            # Bed in corner
            bed_x = width // 4
            bed_z = length // 4
            self.furniture.append(("white_bed", bed_x, bed_z, "north"))
            
            # Storage
            chest_x = width - 2
            chest_z = 2
            self.furniture.append(("chest", chest_x, chest_z, "west"))
            
            # Table with quartz if large house
            if width >= 7 and length >= 7:
                self.furniture.append(("smooth_quartz", width // 2, length // 2, None))
                self.furniture.append(("smooth_quartz", width // 2 + 1, length // 2, None))
                
            # Some plants for decoration
            if self.size != "small":
                self.furniture.append(("potted_plant", 1, length - 2, None))
                self.furniture.append(("potted_plant", width - 2, length - 2, None))
        
        elif furniture_style == "traditional_asian":  # Asian style
            # Low table in center
            table_x = width // 2
            table_z = length // 2
            self.furniture.append(("smooth_stone_slab", table_x, table_z, None))
            self.furniture.append(("smooth_stone_slab", table_x + 1, table_z, None))
            
            # Floor cushions around table
            if width >= 6 and length >= 6:
                self.furniture.append(("red_carpet", table_x - 1, table_z, None))
                self.furniture.append(("red_carpet", table_x + 2, table_z, None))
                self.furniture.append(("red_carpet", table_x, table_z - 1, None))
                self.furniture.append(("red_carpet", table_x + 1, table_z - 1, None))
                self.furniture.append(("red_carpet", table_x, table_z + 1, None))
                self.furniture.append(("red_carpet", table_x + 1, table_z + 1, None))
            
            # Storage and decorations
            self.furniture.append(("chest", 1, 1, "south"))
            self.furniture.append(("chest", 2, 1, "south"))
            self.furniture.append(("lantern", width - 2, 1, None))
            self.furniture.append(("flower_pot", width - 3, 1, None))
            
            # Bed in back
            bed_x = width // 4
            bed_z = length - 2
            self.furniture.append(("white_bed", bed_x, bed_z, "north"))
            
            # Bookshelves
            if self.size == "large":
                self.furniture.append(("bookshelf", width - 2, length - 2, None))
                self.furniture.append(("bookshelf", width - 3, length - 2, None))
        
        elif furniture_style == "beach":  # Tropical style
            # Hammock-style bed
            bed_x = width // 4
            bed_z = length // 4
            self.furniture.append(("light_blue_bed", bed_x, bed_z, "east"))
            
            # Dining area
            if width >= 6 and length >= 6:
                table_x = width // 2
                table_z = length // 2
                self.furniture.append(("jungle_fence", table_x, table_z, None))
                self.furniture.append(("jungle_pressure_plate", table_x, table_z + 1, None))
                
                # Chairs
                self.furniture.append(("jungle_stairs", table_x - 1, table_z, "east"))
                self.furniture.append(("jungle_stairs", table_x + 1, table_z, "west"))
            
            # Storage
            self.furniture.append(("chest", width - 2, 2, "west"))
            self.furniture.append(("barrel", width - 2, 3, None))
            
            # Decorative elements
            self.furniture.append(("potted_fern", 1, length - 2, None))
            self.furniture.append(("potted_bamboo", width - 2, length - 2, None))
            
            if width >= 7 and length >= 7:
                self.furniture.append(("crafting_table", width - 3, 2, None))
        
        elif furniture_style == "rustic_nordic":  # Nordic style
            # Large bed
            bed_x = 1
            bed_z = length - 3
            self.furniture.append(("white_bed", bed_x, bed_z, "east"))
            self.furniture.append(("white_bed", bed_x, bed_z + 1, "east"))
            
            # Hearth / fireplace
            hearth_x = width // 2
            hearth_z = 1
            self.furniture.append(("cobblestone", hearth_x, hearth_z, None))
            self.furniture.append(("cobblestone", hearth_x + 1, hearth_z, None))
            self.furniture.append(("campfire", hearth_x, hearth_z + 1, None))
            
            # Table with chairs
            if width >= 6 and length >= 6:
                table_x = width // 2
                table_z = length // 2
                self.furniture.append(("spruce_fence", table_x, table_z, None))
                self.furniture.append(("spruce_pressure_plate", table_x + 1, table_z, None))
                
                # Chairs
                self.furniture.append(("spruce_stairs", table_x, table_z - 1, "south"))
                self.furniture.append(("spruce_stairs", table_x + 1, table_z - 1, "south"))
                self.furniture.append(("spruce_stairs", table_x, table_z + 1, "north"))
                self.furniture.append(("spruce_stairs", table_x + 1, table_z + 1, "north"))
            
            # Storage
            self.furniture.append(("chest", width - 2, length - 2, "west"))
            self.furniture.append(("barrel", width - 2, length - 3, None))
            
            # Work area
            self.furniture.append(("crafting_table", width - 2, 2, None))
            self.furniture.append(("smoker", width - 2, 3, "west"))
            
            # Decorative elements
            self.furniture.append(("lantern", 1, 1, None))
            
            if self.size == "large":
                self.furniture.append(("loom", width - 3, length - 2, "west"))
                self.furniture.append(("bookshelf", 1, length - 2, None))
        
        else:  # Default rustic style for traditional
            # Bed in corner
            bed_x = width // 4
            bed_z = length // 4
            self.furniture.append(("bed", bed_x, bed_z, "north"))
            
            # Add a crafting table
            craft_x = width - 2
            craft_z = 2
            self.furniture.append(("crafting_table", craft_x, craft_z, None))
            
            # Add a chest
            chest_x = width - 2
            chest_z = 3
            self.furniture.append(("chest", chest_x, chest_z, "west"))
            
            # Add a furnace if the house is big enough
            if width >= 7 and length >= 7:
                furnace_x = width - 2
                furnace_z = 4
                self.furniture.append(("furnace", furnace_x, furnace_z, "west"))
            
            # Add bookshelf if the house is large
            if self.size == "large":
                self.furniture.append(("bookshelf", 1, 1, None))
    
    def _generate_decorative_elements(self):
        """Generate style-specific decorative elements"""
        self.decorative_elements = []
        width, length = self.width, self.length
        
        if self.style == "traditional":
            # Flower boxes under windows
            for x, z, h in self.windows:
                if z == 0 or z == length - 1:  # Windows on north/south walls
                    self.decorative_elements.append(("flower_box", x, z, "window"))
            
            # Lanterns
            self.decorative_elements.append(("lantern", 0, 0, "hanging"))
            self.decorative_elements.append(("lantern", width - 1, 0, "hanging"))
            self.decorative_elements.append(("lantern", 0, length - 1, "hanging"))
            self.decorative_elements.append(("lantern", width - 1, length - 1, "hanging"))
        
        elif self.style == "modern":
            # Minimal decorations
            # Glass panels for railing
            for x in range(width):
                self.decorative_elements.append(("glass_pane", x, 0, "railing"))
                self.decorative_elements.append(("glass_pane", x, length - 1, "railing"))
            
            for z in range(1, length - 1):
                self.decorative_elements.append(("glass_pane", 0, z, "railing"))
                self.decorative_elements.append(("glass_pane", width - 1, z, "railing"))
            
            # End rods for modern lights
            self.decorative_elements.append(("end_rod", width // 3, length // 3, "ceiling"))
            self.decorative_elements.append(("end_rod", 2 * width // 3, length // 3, "ceiling"))
            self.decorative_elements.append(("end_rod", width // 3, 2 * length // 3, "ceiling"))
            self.decorative_elements.append(("end_rod", 2 * width // 3, 2 * length // 3, "ceiling"))
        
        elif self.style == "asian":
            # Lanterns hanging from roof corners
            self.decorative_elements.append(("lantern", 0, 0, "hanging"))
            self.decorative_elements.append(("lantern", width - 1, 0, "hanging"))
            self.decorative_elements.append(("lantern", 0, length - 1, "hanging"))
            self.decorative_elements.append(("lantern", width - 1, length - 1, "hanging"))
            
            # Banners or decorative blocks
            door_x, door_z, _ = self.door_position
            if door_z == length - 1:  # Door on south wall
                self.decorative_elements.append(("red_banner", door_x - 1, door_z, "wall"))
                self.decorative_elements.append(("red_banner", door_x + 1, door_z, "wall"))
            
            # Bonsai trees or potted plants
            self.decorative_elements.append(("potted_bamboo", 1, 1, "floor"))
            self.decorative_elements.append(("potted_bamboo", width - 2, 1, "floor"))
            
            # Paper lanterns in ceiling
            for x in range(2, width - 2, 2):
                for z in range(2, length - 2, 2):
                    self.decorative_elements.append(("lantern", x, z, "ceiling"))
        
        elif self.style == "tropical":
            # Coral decorations
            self.decorative_elements.append(("coral_fan", 1, 1, "floor"))
            self.decorative_elements.append(("coral_fan", width - 2, 1, "floor"))
            
            # Hanging plants
            for x in range(2, width - 2, 2):
                for z in range(2, length - 2, 2):
                    self.decorative_elements.append(("hanging_roots", x, z, "ceiling"))
            
            # Seashells or similar decorations
            self.decorative_elements.append(("turtle_egg", width // 2, 1, "floor"))
            
            # Bamboo or wooden decorative elements
            door_x, door_z, _ = self.door_position
            if door_z == length - 1:  # Door on south wall
                self.decorative_elements.append(("bamboo", door_x - 1, door_z, "wall"))
                self.decorative_elements.append(("bamboo", door_x + 1, door_z, "wall"))
        
        elif self.style == "nordic":
            # Hunting trophies or wall decorations
            self.decorative_elements.append(("item_frame", width // 2, 0, "wall"))
            
            # Hanging lanterns
            self.decorative_elements.append(("lantern", width // 3, length // 3, "hanging"))
            self.decorative_elements.append(("lantern", 2 * width // 3, 2 * length // 3, "hanging"))
            
            # Furs or carpets
            self.decorative_elements.append(("white_carpet", width // 2, length // 2, "floor"))
            self.decorative_elements.append(("white_carpet", width // 2 + 1, length // 2, "floor"))
            self.decorative_elements.append(("white_carpet", width // 2, length // 2 + 1, "floor"))
            self.decorative_elements.append(("white_carpet", width // 2 + 1, length // 2 + 1, "floor"))
            
            # Shield decorations
            self.decorative_elements.append(("shield", 1, length // 2, "wall"))
            self.decorative_elements.append(("shield", width - 2, length // 2, "wall"))
    
    def adapt_to_terrain(self, terrain_type, height_difference):
        """Adapt the blueprint to the specific terrain type"""
        # Adjust stilt height based on terrain
        if terrain_type == 2:  # Water
            # Water - stilts should clear the water
            self.stilt_height = min(MAX_STILT_HEIGHT, max(8, height_difference + 1))
            
            # For tropical style on water, increase stilt height for more dramatic effect
            if self.style == "tropical":
                self.stilt_height = min(MAX_STILT_HEIGHT, self.stilt_height + 1)
                
        elif terrain_type == 1:  # Hill/slope
            # Hill - stilts should compensate for the slope
            if height_difference > 3:
                # Significant slope - use taller stilts
                self.stilt_height = min(MAX_STILT_HEIGHT, max(6, height_difference))
            else:
                # Gentle slope - use moderate stilts
                self.stilt_height = min(MAX_STILT_HEIGHT, max(4, height_difference + 1))
                
            # Nordic style often has houses sitting closer to the ground
            if self.style == "nordic":
                self.stilt_height = max(2, self.stilt_height - 1)
                
        else:  # Flat
            # Flat ground - use modest stilts
            self.stilt_height = random.randint(3, 4)
            
            # Style-specific adaptations
            if self.style == "modern":
                # Modern houses often have higher stilts for aesthetic reasons
                self.stilt_height = random.randint(3, 4)
            elif self.style == "nordic":
                # Nordic houses often sit lower to the ground
                self.stilt_height = random.randint(1, 2)
            elif self.style == "asian":
                # Asian houses often have a consistent height off the ground
                self.stilt_height = 4
        
        # For hills, we may want to have the door facing the downhill side
        if terrain_type == 1:
            # This would be properly implemented in the builder where we have access
            # to actual terrain heights
            pass

class HouseBlueprintFactory:
    """Factory for creating different house blueprints"""
    @staticmethod
    def create_house(house_type="stilt", style=None, size=None, wood_type=None):
        """Create a house blueprint based on type and parameters"""
        # Randomize parameters if not specified
        available_styles = list(STYLE_FEATURES.keys())
        style = style or random.choice(available_styles)
        
        # Make sure the style is valid
        if style not in available_styles:
            style = random.choice(available_styles)
            
        size = size or random.choice(["small", "medium", "large"])
        
        if house_type.lower() == "stilt":
            return StiltHouseBlueprint(style, size, wood_type)
        else:
            # Default to basic house if type not recognized
            return HouseBlueprint(style, size, wood_type)

# Example usage
if __name__ == "__main__":
    # Create a stilt house blueprint
    blueprint = HouseBlueprintFactory.create_house("stilt")
    info = blueprint.get_info()
    
    print(f"Created {info['size']} {info['style']} stilt house blueprint")
    print(f"Wood type: {info['wood_type']}")
    print(f"Secondary material: {info['secondary_material']}")
    print(f"Dimensions: {info['dimensions']}")
    print(f"Number of stilts: {len(blueprint.stilt_positions)}")
    print(f"Number of windows: {len(blueprint.windows)}")
    print(f"Number of furniture pieces: {len(blueprint.furniture)}")
    print(f"Number of decorative elements: {len(blueprint.decorative_elements)}")
    print(f"Roof details: {blueprint.roof_details}")