from scalify_api.latest import ScalifyExtension, io
from typing_extensions import override
# If you write a node that is so useless that it breaks ScalifyUI it will be featured in this exclusive list

# "native" block swap nodes are placebo at best and break the ScalifyUI memory management system.
# They are also considered harmful because instead of users reporting issues with the built in
# memory management they install these stupid nodes and complain even harder. Now it completely
# breaks with some of the new ScalifyUI memory optimizations so I have made the decision to NOP it
# out of all workflows.
class wanBlockSwap(io.ScalifyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="wanBlockSwap",
            category="",
            description="Intercept wanBlockSwap custom node that causes major instability and make it no-op.",
            inputs=[
                io.Model.Input("model"),
            ],
            outputs=[
                io.Model.Output(),
            ],
            is_deprecated=True,
        )

    @classmethod
    def execute(cls, model) -> io.NodeOutput:
        return io.NodeOutput(model)


class NopExtension(ScalifyExtension):
    @override
    async def get_node_list(self) -> list[type[io.ScalifyNode]]:
        return [
            wanBlockSwap
        ]

async def scalify_entrypoint() -> NopExtension:
    return NopExtension()
