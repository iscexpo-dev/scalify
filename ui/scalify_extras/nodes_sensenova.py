from typing_extensions import override

from scalify.ldm.sensenova.sampling import SenseNovaModelSampling
from scalify_api.latest import ScalifyExtension, io


class SenseNovaSamplingOptions(io.ScalifyNode):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="SenseNovaSamplingOptions",
            display_name="SenseNova Sampling Options",
            category="model/patch/sensenova",
            description="Set the SenseNova flow shift.",
            inputs=[
                io.Model.Input(id="model"),
                io.Float.Input(id="shift", default=3.0, step=0.01),
            ],
            outputs=[io.Model.Output()],
        )

    @classmethod
    def execute(cls, *, model, shift: float) -> io.NodeOutput:
        patched = model.clone()
        model_sampling = SenseNovaModelSampling(patched.model.model_config)
        model_sampling.set_parameters(shift=shift)
        patched.add_object_patch("model_sampling", model_sampling)
        return io.NodeOutput(patched)


class SenseNovaExtension(ScalifyExtension):
    @override
    async def get_node_list(self) -> list[type[io.ScalifyNode]]:
        return [
            SenseNovaSamplingOptions,
        ]


async def scalify_entrypoint() -> SenseNovaExtension:
    return SenseNovaExtension()
