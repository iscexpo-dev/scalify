from kornia.filters import canny
from typing_extensions import override

import scalify.model_management
from scalify_api.latest import ScalifyExtension, io
import torch


class Canny(io.ScalifyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="Canny",
            display_name="Detect Edges (Canny)",
            search_aliases=["edge detection", "outline", "contour detection", "line art"],
            category="image/filters",
            essentials_category="Image Tools",
            inputs=[
                io.Image.Input("image"),
                io.Float.Input("low_threshold", default=0.4, min=0.01, max=0.99, step=0.01),
                io.Float.Input("high_threshold", default=0.8, min=0.01, max=0.99, step=0.01),
            ],
            outputs=[io.Image.Output()],
        )

    @classmethod
    def detect_edge(cls, image, low_threshold, high_threshold):
        # Deprecated: use the V3 schema's `execute` method instead of this.
        return cls.execute(image, low_threshold, high_threshold)

    @classmethod
    def execute(cls, image, low_threshold, high_threshold) -> io.NodeOutput:
        output = canny(image[..., :3].to(device=scalify.model_management.get_torch_device(), dtype=torch.float32).movedim(-1, 1), low_threshold, high_threshold)
        img_out = output[1].to(device=scalify.model_management.intermediate_device(), dtype=scalify.model_management.intermediate_dtype()).repeat(1, 3, 1, 1).movedim(1, -1)
        return io.NodeOutput(img_out)


class CannyExtension(ScalifyExtension):
    @override
    async def get_node_list(self) -> list[type[io.ScalifyNode]]:
        return [Canny]


async def scalify_entrypoint() -> CannyExtension:
    return CannyExtension()
