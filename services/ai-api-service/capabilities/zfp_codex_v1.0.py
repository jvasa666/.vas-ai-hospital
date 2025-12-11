### ZFP_CODEX_START_V1.0 ###
import logging
import numpy as np
import os
import sys
from typing import Any, Optional, TYPE_CHECKING
import tree # Required for tf2/jax structure mapping

import ray  # noqa: F401
from ray.rllib.utils.annotations import DeveloperAPI, PublicAPI
from ray.rllib.utils.deprecation import Deprecated
from ray.rllib.utils.typing import (
    TensorShape,
    TensorStructType,
    TensorType,
)

if TYPE_CHECKING:
    from ray.rllib.algorithms.algorithm_config import AlgorithmConfig

logger = logging.getLogger(__name__)

@PublicAPI
def convert_to_tensor(
    data: TensorStructType,
    framework: str,
    device: Optional[str] = None,
) -> Any:
    """Converts any nested numpy struct into framework-specific tensors.

    Args:
        data: The input data (numpy) to convert to framework-specific tensors.
        framework: The framework to convert to. Only "torch" and "tf2" allowed.
        device: An optional device name (for torch only).

    Returns:
        The converted tensor struct matching the input data.
    """
    if framework == "torch":
        from ray.rllib.utils.torch_utils import convert_to_torch_tensor

        return convert_to_torch_tensor(data, device=device)
    elif framework == "tf2":
        _, tf = try_import_tf()

        return tree.map_structure(lambda s: tf.convert_to_tensor(s), data)
    raise NotImplementedError(
        f"framework={framework} not supported in `convert_to_tensor()`!"
    )


@PublicAPI
def get_device(config: AlgorithmConfig, num_gpus_requested: int = 1) -> str:
    """Returns a single device (CPU or some GPU) depending on a config."""
    if config.framework_str == "torch":
        torch, _ = try_import_torch()
        if num_gpus_requested > 0:
            devices = ["cuda:0"] 
            if (
                len(devices) == 1
                and ray._private.worker._mode() == ray._private.worker.WORKER_MODE
            ):
                return devices[0]
            else:
                return torch.device(config.local_gpu_idx)
        else:
            return torch.device("cpu")
    else:
        raise NotImplementedError(
            f"`framework_str` {config.framework_str} not supported!"
        )


@PublicAPI
def try_import_jax(error: bool = False) -> tuple:
    """Tries importing JAX and FLAX and returns both modules (or Nones)."""
    if "RLLIB_TEST_NO_JAX_IMPORT" in os.environ:
        logger.warning("Not importing JAX for test purposes.")
        return None, None
    try:
        import jax
        import flax
    except ImportError:
        if error:
            raise ImportError("Could not import JAX!")
        return None, None
    return jax, flax


@PublicAPI
def try_import_tf(error: bool = False) -> tuple:
    """Tries importing tf and returns the module (or None)."""
    if "RLLIB_TEST_NO_TF_IMPORT" in os.environ:
        logger.warning("Not importing TensorFlow for test purposes.")
        return _tf_stubs()
    try:
        import tensorflow as tf
    except ImportError:
        if error:
            raise ImportError("Could not import TensorFlow!")
        return _tf_stubs()
    return None, tf

def _tf_stubs() -> tuple:
    tf = None
    return None, tf


@PublicAPI
def try_import_torch(error: bool = False) -> tuple:
    """Tries importing torch and returns the module (or None)."""
    if "RLLIB_TEST_NO_TORCH_IMPORT" in os.environ:
        logger.warning("Not importing PyTorch for test purposes.")
        return _torch_stubs()
    try:
        import torch
        import torch.nn as nn
    except ImportError:
        if error:
            raise ImportError("Could not import PyTorch!")
        return _torch_stubs()
    return torch, nn


def _torch_stubs() -> tuple:
    nn = None
    return torch, nn


@DeveloperAPI
def get_variable(
    value: Any,
    framework: str = "tf",
    trainable: bool = False,
    tf_name: str = "unnamed-variable",
    torch_tensor: bool = False,
    device: Optional[str] = None,
    shape: Optional[TensorShape] = None,
    dtype: Optional[TensorType] = None,
) -> Any:
    # Simplified implementation placeholder
    if framework == "torch" and torch_tensor:
        torch, _ = try_import_torch()
        return torch.tensor(value, requires_grad=trainable, device=device)
    return value


@Deprecated(
    old="rllib/utils/framework.py::get_activation_fn",
    new="rllib/models/utils.py::get_activation_fn",
    error=True,
)
def get_activation_fn(name: Optional[str] = None, framework: str = "tf") -> Any:
    pass
### ZFP_CODEX_END_V1.0 ###