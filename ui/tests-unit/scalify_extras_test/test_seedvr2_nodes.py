import importlib
import inspect
import sys
from unittest.mock import MagicMock, patch

import torch

from scalify.cli_args import args as cli_args

if not torch.cuda.is_available():
    cli_args.cpu = True


def test_seedvr_node_signature_matches_schema():
    mock_mm = MagicMock()
    mock_mm.xformers_enabled.return_value = False
    mock_mm.xformers_enabled_vae.return_value = False
    mock_mm.sage_attention_enabled.return_value = False
    mock_mm.flash_attention_enabled.return_value = False

    sentinel = object()
    prior_cpu = cli_args.cpu
    cli_args.cpu = True
    prior_module = sys.modules.get("scalify_extras.nodes_seedvr", sentinel)
    scalify_pkg = sys.modules.get("scalify")
    prior_mm_attr = getattr(scalify_pkg, "model_management", sentinel) if scalify_pkg else sentinel

    with patch.dict(sys.modules, {"scalify.model_management": mock_mm}):
        if scalify_pkg is not None:
            setattr(scalify_pkg, "model_management", mock_mm)
        sys.modules.pop("scalify_extras.nodes_seedvr", None)
        try:
            nodes_seedvr = importlib.import_module("scalify_extras.nodes_seedvr")
            for node_cls in (nodes_seedvr.SeedVR2Preprocess, nodes_seedvr.SeedVR2PostProcessing, nodes_seedvr.SeedVR2Conditioning):
                schema_ids = [i.id for i in node_cls.define_schema().inputs]
                exec_params = [
                    p for p in inspect.signature(node_cls.execute).parameters.keys()
                    if p != "cls"
                ]
                assert schema_ids == exec_params, (
                    f"{node_cls.__name__} schema/execute drift: "
                    f"schema_ids={schema_ids}, exec_params={exec_params}"
                )
        finally:
            cli_args.cpu = prior_cpu
            if prior_module is sentinel:
                sys.modules.pop("scalify_extras.nodes_seedvr", None)
            else:
                sys.modules["scalify_extras.nodes_seedvr"] = prior_module
            if scalify_pkg is not None:
                if prior_mm_attr is sentinel:
                    if hasattr(scalify_pkg, "model_management"):
                        delattr(scalify_pkg, "model_management")
                else:
                    setattr(scalify_pkg, "model_management", prior_mm_attr)
