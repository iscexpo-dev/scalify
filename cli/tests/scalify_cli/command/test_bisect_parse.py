from scalify_cli.command.custom_nodes.bisect_custom_nodes import parse_cm_output

CM_OUTPUT_REAL = """\
FETCH ScalifyRegistry Data: 5/85
FETCH ScalifyRegistry Data: 10/85
FETCH ScalifyRegistry Data: 15/85
FETCH ScalifyRegistry Data: 20/85
FETCH ScalifyRegistry Data: 25/85
FETCH ScalifyRegistry Data: 30/85
FETCH ScalifyRegistry Data: 35/85
FETCH ScalifyRegistry Data: 40/85
FETCH ScalifyRegistry Data: 45/85
FETCH ScalifyRegistry Data: 50/85
FETCH ScalifyRegistry Data: 55/85
FETCH ScalifyRegistry Data: 60/85
FETCH ScalifyRegistry Data: 65/85
FETCH ScalifyRegistry Data: 70/85
FETCH ScalifyRegistry Data: 75/85
FETCH ScalifyRegistry Data: 80/85
FETCH ScalifyRegistry Data: 85/85
FETCH ScalifyRegistry Data [DONE]
FETCH DATA from: https://raw.githubusercontent.com/ltdrdata/ScalifyUI-Manager/main/custom-node-list.json [DONE]
FETCH DATA from: https://raw.githubusercontent.com/ltdrdata/ScalifyUI-Manager/main/custom-node-list.json [DONE]
A3D ScalifyUI Integration@1.0.2
ScalifyUI_ACE-Step@1.1.2
Bjornulf_custom_nodes@1.1.1
cg-use-everywhere@6.1.0
ScalifyUI-0246@1.1.3
ScalifyUI ArtVenture@nightly
scalifyui-auto-nodes-layout@0.0.1
ScalifyUI-ConDelta@nightly
ScalifyUI-Custom-Scripts@nightly
ScalifyUI-DiaTTS@0.3.0
ScalifyUI-Easy-Use@1.3.0
ScalifyUI F5-TTS@nightly
ScalifyUI-Florence2@1.0.3
ScalifyUI@nightly
ScalifyUI-GGUF@nightly
ScalifyUI-Image-Filters@nightly
ScalifyUI-KJNodes@nightly
scalifyui-lmstudio-image-to-text-node@1.1.14
ScalifyUI-LogicUtils@1.7.2
ScalifyUI-LTXVideo@nightly
ScalifyUI-Manager@nightly
ScalifyUI-MMAudio@1.0.2
ScalifyUI-mxToolkit@0.9.92
ScalifyUI-VideoHelperSuite@1.6.1
ScalifyUI Web Viewer@1.0.32
scalifyui_controlnet_aux@1.0.7
ScalifyUI_IPAdapter_plus@2.0.0
Prompt Stash@1.2.0
efficiency-nodes-scalifyui@1.0.6
gguf@2.1.0
scalifyui_HiDream-Sampler@1.0.0
LF Nodes@0.7.0
lora-info@1.0.2
Masquerade Nodes@nightly
rgthree-scalify@nightly
ScalifyUI-TeaCache@1.5.1
WAS Node Suite@1.0.2
ScalifyUI-ultimate-openpose-editor@nightly
ScalifyUI-Dia@unknown
ScalifyUI-Orpheus@unknown
"""

EXPECTED_NODES = [
    "A3D ScalifyUI Integration@1.0.2",
    "ScalifyUI_ACE-Step@1.1.2",
    "Bjornulf_custom_nodes@1.1.1",
    "cg-use-everywhere@6.1.0",
    "ScalifyUI-0246@1.1.3",
    "ScalifyUI ArtVenture@nightly",
    "scalifyui-auto-nodes-layout@0.0.1",
    "ScalifyUI-ConDelta@nightly",
    "ScalifyUI-Custom-Scripts@nightly",
    "ScalifyUI-DiaTTS@0.3.0",
    "ScalifyUI-Easy-Use@1.3.0",
    "ScalifyUI F5-TTS@nightly",
    "ScalifyUI-Florence2@1.0.3",
    "ScalifyUI@nightly",
    "ScalifyUI-GGUF@nightly",
    "ScalifyUI-Image-Filters@nightly",
    "ScalifyUI-KJNodes@nightly",
    "scalifyui-lmstudio-image-to-text-node@1.1.14",
    "ScalifyUI-LogicUtils@1.7.2",
    "ScalifyUI-LTXVideo@nightly",
    "ScalifyUI-Manager@nightly",
    "ScalifyUI-MMAudio@1.0.2",
    "ScalifyUI-mxToolkit@0.9.92",
    "ScalifyUI-VideoHelperSuite@1.6.1",
    "ScalifyUI Web Viewer@1.0.32",
    "scalifyui_controlnet_aux@1.0.7",
    "ScalifyUI_IPAdapter_plus@2.0.0",
    "Prompt Stash@1.2.0",
    "efficiency-nodes-scalifyui@1.0.6",
    "gguf@2.1.0",
    "scalifyui_HiDream-Sampler@1.0.0",
    "LF Nodes@0.7.0",
    "lora-info@1.0.2",
    "Masquerade Nodes@nightly",
    "rgthree-scalify@nightly",
    "ScalifyUI-TeaCache@1.5.1",
    "WAS Node Suite@1.0.2",
    "ScalifyUI-ultimate-openpose-editor@nightly",
    "ScalifyUI-Dia@unknown",
    "ScalifyUI-Orpheus@unknown",
]


class TestParseCmOutput:
    def test_real_output_filters_fetch_lines(self):
        result = parse_cm_output(CM_OUTPUT_REAL)
        assert result == EXPECTED_NODES
        assert len(result) == 40

    def test_no_fetch_lines_in_result(self):
        result = parse_cm_output(CM_OUTPUT_REAL)
        for node in result:
            assert not node.startswith("FETCH"), f"FETCH line leaked: {node}"

    def test_pinned_nodes_excluded(self):
        pinned = {"ScalifyUI-Manager@nightly", "ScalifyUI@nightly"}
        result = parse_cm_output(CM_OUTPUT_REAL, pinned)
        assert "ScalifyUI-Manager@nightly" not in result
        assert "ScalifyUI@nightly" not in result
        assert len(result) == 38

    def test_empty_output(self):
        assert parse_cm_output("") == []
        assert parse_cm_output("   \n  \n  ") == []

    def test_only_fetch_lines(self):
        output = "FETCH ScalifyRegistry Data: 5/85\nFETCH DATA from: foo [DONE]\n"
        assert parse_cm_output(output) == []

    def test_no_fetch_lines(self):
        output = "NodeA@1.0\nNodeB@nightly\n"
        assert parse_cm_output(output) == ["NodeA@1.0", "NodeB@nightly"]

    def test_arbitrary_status_lines_filtered(self):
        output = "some random status line\nINFO: loading\nNodeA@1.0\nDone.\n"
        assert parse_cm_output(output) == ["NodeA@1.0"]
