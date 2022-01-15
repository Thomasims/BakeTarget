
# Bake to Target

This Blender Addon adds a new shader node type capable of reducing the texture-bake step to a single button press.

Please note that this is *not* a polished addon, it is designed to work around one problem and not much else.

## Usage
The node is found under `Add > Bake > Bake to Target`
It has only one input, `Color`, and the following parameters:
- Mode:
	The bake type, Image or Vertex Colors
- Image: (*Image Mode*)
	The image to bake to.
- Output: (*Image Mode, optional*)
	The file path to write the result to.
- Append Object: (*Image Mode, optional*)
	Whether to append the name of the baked object to the output file path or not.
- Object: (*Vertex Colors Mode*)
	The object to use for baking.
- Vertex Colors: (*Vertex Colors Mode*)
	The Vertex Colors layer to use for baking.

This node also has a `Bake` button, pressing this button will setup a bake operation using the target parameters of the node.