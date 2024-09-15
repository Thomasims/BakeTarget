
# Bake to Target

This Blender Addon adds a new shader node type capable of reducing the texture-bake step to a single button press.

Please note that this is *not* a polished addon, it is designed to work around one problem and not much else.

![image](https://user-images.githubusercontent.com/3007463/149631301-e50e437b-67b7-4c82-95c3-3696ebad521c.png)

## Installation
- Download this repository as zip `Code > Download Zip`
- Blender: `Preferences > Add-Ons > Install` select the zip file
- Check the Add-On to enable it

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
