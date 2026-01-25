"""Expert routing utilities for TP6.

The original kernel uses pointer bin addresses to choose between multiple output
heads (experts). This module contains the extracted router.
"""

from __future__ import annotations

import hashlib
import os
from typing import Dict, Optional

import torch
import torch.nn as nn


def _hash_state_dict(state: Optional[Dict[str, torch.Tensor]]) -> Optional[str]:
    if not state:
        return None
    hasher = hashlib.sha256()
    for key in sorted(state.keys()):
        tensor = state[key]
        hasher.update(key.encode("utf-8"))
        if torch.is_tensor(tensor):
            arr = tensor.contiguous().cpu().numpy()
            hasher.update(arr.tobytes())
        else:
            hasher.update(repr(tensor).encode("utf-8"))
    return hasher.hexdigest()


def _safe_torch_load(path: str):
    try:
        return torch.load(path, map_location="cpu", weights_only=True)
    except TypeError:
        return torch.load(path, map_location="cpu")


def _load_expert_snapshot(path: str):
    if not path or not os.path.exists(path):
        return None, None
    state = _safe_torch_load(path)
    return state, _hash_state_dict(state)


def _restore_expert_state(expert: nn.Module, state: Dict[str, torch.Tensor]) -> None:
    if not state:
        return
    with torch.no_grad():
        for name, param in expert.named_parameters():
            if name in state:
                param.copy_(state[name].to(device=param.device, dtype=param.dtype))
        for name, buf in expert.named_buffers():
            if name in state:
                buf.copy_(state[name].to(device=buf.device, dtype=buf.dtype))


class LocationExpertRouter(nn.Module):
    """Route each batch element to one of N output heads.

    Routing rule (behavior-preserving):
      - If `pointer_addresses` is None, all samples route to expert 0.
      - Else `expert_index = pointer_addresses % num_experts`.

    This matches `tournament_phase6.LocationExpertRouter`.
    """

    def __init__(self, d_model: int, vocab_size: int, num_experts: int = 1):
        super().__init__()
        self.num_experts = max(1, int(num_experts))
        self.in_features = int(d_model)
        self.out_features = int(vocab_size)
        if self.num_experts == 1:
            self.single = nn.Linear(d_model, vocab_size)
            self.experts = None
        else:
            self.single = None
            self.experts = nn.ModuleList([nn.Linear(d_model, vocab_size) for _ in range(self.num_experts)])

    def reset_parameters(self):
        def init_layer(layer):
            nn.init.xavier_uniform_(layer.weight)
            if layer.bias is not None:
                nn.init.zeros_(layer.bias)

        if self.single is not None:
            init_layer(self.single)
        else:
            for expert in self.experts:
                init_layer(expert)

    def forward(self, x: torch.Tensor, pointer_addresses: torch.Tensor | None = None) -> torch.Tensor:
        if self.single is not None:
            return self.single(x)

        if pointer_addresses is None:
            expert_indices = torch.zeros(x.shape[0], device=x.device, dtype=torch.long)
        else:
            expert_indices = pointer_addresses.to(torch.long, non_blocking=True) % self.num_experts

        hibernation_state = getattr(self, "hibernation_state", None)
        hibernation_enabled = getattr(self, "hibernation_enabled", False)

        out_dtype = self.experts[0].weight.dtype
        out = torch.zeros(x.shape[0], self.experts[0].out_features, device=x.device, dtype=out_dtype)
        for i, expert in enumerate(self.experts):
            if hibernation_state and hibernation_enabled:
                meta = hibernation_state.get(i)
                if meta and meta.get("offloaded"):
                    state, disk_hash = _load_expert_snapshot(meta.get("path"))
                    saved_hash = meta.get("hash")
                    if disk_hash is None:
                        self.hibernation_corrupt = getattr(self, "hibernation_corrupt", 0) + 1
                        meta["offloaded"] = False
                    else:
                        if saved_hash and disk_hash != saved_hash:
                            self.hibernation_corrupt = getattr(self, "hibernation_corrupt", 0) + 1
                        _restore_expert_state(expert, state)
                        meta["hash"] = disk_hash
                        meta["offloaded"] = False
                    self.hibernation_fetched = getattr(self, "hibernation_fetched", 0) + 1
            mask = expert_indices == i
            if mask.any():
                out[mask] = expert(x[mask]).to(out_dtype)
        return out
