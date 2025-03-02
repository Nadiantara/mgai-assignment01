# Minecraft Procedural Stilt House Generator

A tool that procedurally generates stilt houses in a Minecraft world, adapting to various terrain types including flat land, hills, and water.

## Features

- **Terrain Analysis**: Automatically maps and analyzes terrain to find optimal building locations
- **Style Variety**: Generates houses in multiple architectural styles (traditional, modern, Asian, Nordic, tropical)
- **Adaptive Building**: Houses adapt to terrain with appropriate stilt heights and designs
- **Intelligent Placement**: Prioritizes shorelines, hills, and clear areas for house placement
- **Tree Detection**: Identifies and clears trees for building space

## Styles

- **Traditional**: Cozy wooden structures with A-frame roofs
- **Modern**: Clean lines with flat roofs and large windows
- **Asian**: Pagoda-style roofs with lattice windows and ornate details
- **Nordic**: Steep roofs with thick support structures for snowy climates
- **Tropical**: Open designs with thatched roofs for warm climates

## Usage

Run the main script with an optional parameter to specify the number of houses to generate:

```bash
python main.py [number_of_houses]
```

Default: 10 houses (maximum: 25)

## Requirements

- Python 3.6+
- GDPC (Generative Design Python Client)
- NumPy
- SciPy
- Matplotlib (for visualization)

## Output

The generator creates:
- Stilt houses adapted to the terrain
- Visualization maps for terrain analysis
- A coordinates file with teleport commands to visit each house

## License

MIT License