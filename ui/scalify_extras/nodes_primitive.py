import sys
from typing_extensions import override

from scalify_api.latest import ScalifyExtension, io


class String(io.ScalifyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="PrimitiveString",
            search_aliases=["text", "string", "text box", "prompt"],
            display_name="Text",
            category="utilities/primitive",
            inputs=[io.String.Input("value")],
            outputs=[io.String.Output()]
        )

    @classmethod
    def execute(cls, value: str) -> io.NodeOutput:
        return io.NodeOutput(value)


class StringMultiline(io.ScalifyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="PrimitiveStringMultiline",
            search_aliases=["text", "string", "text box", "prompt"],
            display_name="Text (Multiline)",
            category="utilities/primitive",
            essentials_category="Basics",
            inputs=[io.String.Input("value", multiline=True)],
            outputs=[io.String.Output()],
        )

    @classmethod
    def execute(cls, value: str) -> io.NodeOutput:
        return io.NodeOutput(value)


class Int(io.ScalifyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="PrimitiveInt",
            display_name="Int",
            category="utilities/primitive",
            inputs=[
                io.Int.Input("value", min=-sys.maxsize, max=sys.maxsize, control_after_generate=io.ControlAfterGenerate.fixed),
            ],
            outputs=[io.Int.Output()],
        )

    @classmethod
    def execute(cls, value: int) -> io.NodeOutput:
        return io.NodeOutput(value)


class Float(io.ScalifyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="PrimitiveFloat",
            display_name="Float",
            category="utilities/primitive",
            inputs=[
                io.Float.Input("value", min=-sys.maxsize, max=sys.maxsize, step=0.1),
            ],
            outputs=[io.Float.Output()],
        )

    @classmethod
    def execute(cls, value: float) -> io.NodeOutput:
        return io.NodeOutput(value)


class Boolean(io.ScalifyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="PrimitiveBoolean",
            display_name="Boolean",
            category="utilities/primitive",
            inputs=[
                io.Boolean.Input("value"),
            ],
            outputs=[io.Boolean.Output()],
        )

    @classmethod
    def execute(cls, value: bool) -> io.NodeOutput:
        return io.NodeOutput(value)


class PrimitivesExtension(ScalifyExtension):
    @override
    async def get_node_list(self) -> list[type[io.ScalifyNode]]:
        return [
            String,
            StringMultiline,
            Int,
            Float,
            Boolean,
        ]

async def scalify_entrypoint() -> PrimitivesExtension:
    return PrimitivesExtension()
