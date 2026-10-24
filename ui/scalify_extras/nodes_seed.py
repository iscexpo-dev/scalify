import sys
from typing_extensions import override

from scalify_api.latest import ScalifyExtension, io


class SeedNode(io.ScalifyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="SeedNode",
            display_name="Seed",
            search_aliases=["seed", "random"],
            category="utilities",
            inputs=[
                io.Int.Input("seed", min=0, max=sys.maxsize, control_after_generate=io.ControlAfterGenerate.fixed),
            ],
            outputs=[io.Int.Output(display_name="seed")],
        )

    @classmethod
    def execute(cls, seed: int) -> io.NodeOutput:
        return io.NodeOutput(seed)


class SeedExtension(ScalifyExtension):
    @override
    async def get_node_list(self) -> list[type[io.ScalifyNode]]:
        return [SeedNode]


async def scalify_entrypoint() -> SeedExtension:
    return SeedExtension()
