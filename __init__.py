import nodeitems_utils
import bpy

bl_info = {
    "name": "Bake Target",
    "description": "Adds a new shader node to streamline the texture-baking process to a single click",
    "blender": (2, 80, 0),
    "category": "Node",
}


def get_active_output(nodes):
    for node in nodes:
        if node.type == "OUTPUT_MATERIAL" and node.is_active_output:
            return node
        if node.type == "GROUP":
            rec = get_active_output(node.node_tree.nodes)
            if rec != None:
                return rec
    return None


def editfilepath(filepath, extra):
    lastslash = max(filepath.rfind("/"), filepath.rfind("\\"), 0)
    dot = filepath.find(".", lastslash)
    if dot == -1:
        return filepath + extra
    else:
        return filepath[:dot] + extra + filepath[dot:]


bakesettings = {
    "margin": 4,
    "use_pass_color": True,
    "use_pass_direct": False,
    "use_pass_indirect": False,
    "use_selected_to_active": False,
    "target": "IMAGE_TEXTURES"
}

cyclessettings = {
    "use_adaptive_sampling": False,
    "samples": 1,
    "time_limit": 1,
    "use_denoising": False,
    "bake_type": "DIFFUSE",
}


def setsettings(prev, target, settings):
    for key in settings:
        prev[key] = getattr(target, key)
        setattr(target, key, settings[key])


def resetsettings(prev, target, settings):
    for key in settings:
        setattr(target, key, prev[key])


def createnodes(from_socket, tree):
    shader_node = tree.nodes.new("ShaderNodeBsdfDiffuse")
    output_node = tree.nodes.new("ShaderNodeOutputMaterial")
    texture_node = tree.nodes.new("ShaderNodeTexImage")

    output_node.target = "CYCLES"

    tree.links.new(from_socket, shader_node.inputs["Color"])
    tree.links.new(shader_node.outputs["BSDF"], output_node.inputs["Surface"])

    return (texture_node, shader_node, output_node)


class node_bake_target(bpy.types.Operator):
    """Bake node color to its target"""

    bl_idname = "node.bake_target"
    bl_label = "Bake nodes to target"

    prop_material: bpy.props.StringProperty(name="Material")
    prop_node: bpy.props.StringProperty(name="Node")

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        tree = bpy.data.materials[self.prop_material].node_tree
        nodes = tree.nodes
        node = nodes[self.prop_node]
        prevobj = bpy.context.active_object
        if node.inputs[0].is_linked:
            from_socket = node.inputs[0].links[0].from_socket
            (texture_node, shader_node, output_node) = createnodes(from_socket, tree)

            previous_output = get_active_output(nodes)
            prev = dict()
            setsettings(prev, bpy.context.scene.render.bake, bakesettings)
            setsettings(prev, bpy.context.scene.cycles, cyclessettings)
            try:
                if previous_output:
                    previous_output.is_active_output = False
                    previous_output.mute = True
                output_node.is_active_output = True

                if node.prop_mode == "image" and node.prop_target_image:
                    img = node.prop_target_image
                    img.source = "GENERATED"
                    img.colorspace_settings.name = node.prop_target_image_colorspace
                    texture_node.image = img
                    texture_node.select = True
                    nodes.active = texture_node

                    prev["tile_size"] = bpy.context.scene.cycles.tile_size
                    bpy.context.scene.cycles.tile_size = img.size[0]
                    bpy.ops.object.bake(
                        type="DIFFUSE", target="IMAGE_TEXTURES")

                    if node.prop_target_file != "":
                        filepath = node.prop_target_file
                        if node.prop_target_file_object:
                            filepath = editfilepath(
                                filepath, "_" + bpy.path.clean_name(prevobj.name))
                        if filepath.startswith("//"):
                            filepath = bpy.path.abspath(filepath)
                        img.save_render(
                            filepath=bpy.path.ensure_ext(filepath, ".png"))

                elif node.prop_mode == "vertex" and node.prop_target_object in bpy.data.objects:
                    obj = bpy.data.objects[node.prop_target_object]
                    bpy.context.view_layer.objects.active = obj
                    if node.prop_target_vertex_color in obj.data.vertex_colors:
                        obj.data.vertex_colors[node.prop_target_vertex_color].active_render = True
                        bpy.ops.object.bake(type="DIFFUSE", target="VERTEX_COLORS")

            except RuntimeError as e:
                raise e
            finally:
                resetsettings(prev, bpy.context.scene.render.bake, bakesettings)
                resetsettings(prev, bpy.context.scene.cycles, cyclessettings)
                if "tile_size" in prev:
                    bpy.context.scene.cycles.tile_size = prev["tile_size"]
                nodes.remove(texture_node)
                nodes.remove(shader_node)
                nodes.remove(output_node)
                if previous_output:
                    previous_output.is_active_output = True
                    previous_output.mute = False
                bpy.context.view_layer.objects.active = prevobj

        return {"FINISHED"}


class node_bake_all_target(bpy.types.Operator):
    """Bake all BakeTarget nodes to their target"""

    bl_idname = "node.bake_all_target"
    bl_label = "Bake all nodes to target"

    prop_material: bpy.props.StringProperty(name="Material")

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        tree = bpy.data.materials[self.prop_material].node_tree
        nodes = tree.nodes
        found_nodes = []
        for node in nodes:
            if node.bl_idname == "ShaderNodeBakeTarget":
                found_nodes.append(node)
        for node in found_nodes:
            bpy.ops.node.bake_target(prop_material=self.prop_material, prop_node=node.name)
        return {"FINISHED"}


class BakeTargetNode(bpy.types.ShaderNode):
    """ BakeTargetNode
    This node simplifies the texture baking process by abstracting it all behind
    a single fake-output shading node.
    """

    bl_idname = "ShaderNodeBakeTarget"
    bl_label = "Bake to Target"
    bl_icon = "RENDER_STILL"

    # Bake type
    prop_mode: bpy.props.EnumProperty(
        items=[
            ("image", "Image", "Output to an image"),
            ("vertex", "Vertex Color", "Output to vertex colors")
        ], name="Mode", default="image")

    # == Image mode properties ==
    # Target image block
    prop_target_image: bpy.props.PointerProperty(type=bpy.types.Image)
    # Target image colorspace
    prop_target_image_colorspace: bpy.props.EnumProperty(
        items=[
            ("Filmic Log", "Filmic Log", "Log based filmic shaper with 16.5 stops of latitude, and 25 stops of dynamic range."),
            ("Linear", "Linear", "Rec. 709 (Full Range), Blender native linear space."),
            ("Linear ACES", "Linear ACES", "ACES linear space."),
            ("Non-Color", "Non-Color", "Color space used for images which contains non-color data."),
            ("Raw", "Raw", "Raw."),
            ("sRGB", "sRGB", "Standard RGB Display Space."),
            ("XYZ", "XYZ", "XYZ."),
        ], name="Colorspace", default="sRGB")
    # Output file
    prop_target_file: bpy.props.StringProperty(
        name="Output", description="Write the resulting image to a file", subtype="FILE_PATH")
    # Append object to filename
    prop_target_file_object: bpy.props.BoolProperty(
        name="Append Object", description="Append the active Object name to the filename", default=True)

    # == Vertex mode properties ==
    # Target object
    prop_target_object: bpy.props.StringProperty(
        name="Object", description="Target Object, also used for the bake source")
    # Target vertex color layer
    prop_target_vertex_color: bpy.props.StringProperty(
        name="Vertex Colors", description="Vertex Colors Layer to bake to")

    def init(self, context):
        self.inputs.new("NodeSocketColor", "Color")

    def draw_buttons(self, context, layout):
        layout.prop(self, "prop_mode")
        if self.prop_mode == "image":
            layout.template_ID(self, "prop_target_image", new="image.new", open="image.open")
            layout.prop(self, "prop_target_image_colorspace")
            row = layout.row()
            row.prop(self, "prop_target_file")
            row.prop(self, "prop_target_file_object")
        elif self.prop_mode == "vertex":
            layout.prop_search(self, "prop_target_object", context.scene, "objects")
            if self.prop_target_object in context.scene.objects:
                obj = context.scene.objects[self.prop_target_object]
                if obj.type == "MESH":
                    layout.prop_search(self, "prop_target_vertex_color", obj.data, "vertex_colors")
        op = layout.operator("node.bake_target", text="Bake", icon="RENDER_STILL")
        op.prop_material = context.material.name
        op.prop_node = self.name

    def draw_label(self):
        if self.prop_mode == "image" and self.prop_target_image:
            return self.prop_target_image.name
        elif self.prop_mode == "vertex" and self.prop_target_vertex_color != "":
            return self.prop_target_vertex_color
        return "Bake Target"


class BakeTargetMenu(bpy.types.Panel):
    """ BakeTargetMenu
    Runs all the BakeTarget nodes in the active shader tree.
    """
    bl_idname = "UI_PT_bake_target"
    bl_label = "Bake to Target"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Tool"

    def draw(self, context):
        op = self.layout.operator("node.bake_all_target", text="Bake All", icon="RENDER_STILL")
        op.prop_material = context.material.name

    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == "ShaderNodeTree"


class ShaderNodeCategory(nodeitems_utils.NodeCategory):
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == "ShaderNodeTree"


node_categories = [
    ShaderNodeCategory("BAKETARGET", "Bake", items=[
        nodeitems_utils.NodeItem("ShaderNodeBakeTarget"),
    ]),
]

classes = (
    BakeTargetNode,
    BakeTargetMenu,
    node_bake_target,
    node_bake_all_target,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    nodeitems_utils.register_node_categories(
        "BAKE_SHADER_NODES", node_categories)


def unregister():
    nodeitems_utils.unregister_node_categories("BAKE_SHADER_NODES")

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
