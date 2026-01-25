#!/usr/bin/env python
"""Offline pruning: merge a redundant expert into another and remap addresses."""

from __future__ import annotations

import argparse
import os
import sys

import torch


def _infer_num_experts(state: dict) -> int:
    max_idx = -1
    prefix = "head.experts."
    for key in state.keys():
        if key.startswith(prefix):
            try:
                idx = int(key[len(prefix):].split(".", 1)[0])
            except ValueError:
                continue
            max_idx = max(max_idx, idx)
    return max_idx + 1


def _expert_keys(state: dict, expert_id: int) -> list[str]:
    prefix = f"head.experts.{expert_id}."
    return [key for key in state.keys() if key.startswith(prefix)]


def _drop_optimizer_entries(optim: dict | None, param_names: list[str] | None, drop_names: set[str]):
    if not optim or not param_names or not drop_names:
        return optim, param_names
    param_groups = optim.get("param_groups", [])
    if not param_groups:
        return optim, param_names

    params_list = list(param_groups[0].get("params", []))
    name_to_pid = {name: pid for name, pid in zip(param_names, params_list)}
    drop_pids = {name_to_pid[name] for name in drop_names if name in name_to_pid}
    if not drop_pids:
        return optim, param_names

    for group in param_groups:
        group_params = [pid for pid in group.get("params", []) if pid not in drop_pids]
        group["params"] = group_params
    state = optim.get("state", {})
    for pid in drop_pids:
        state.pop(pid, None)
    optim["state"] = state
    optim["param_groups"] = param_groups
    param_names = [name for name in param_names if name not in drop_names]
    return optim, param_names


def main() -> int:
    parser = argparse.ArgumentParser(description="VRAXION prune: merge redundant experts offline.")
    parser.add_argument("--checkpoint", required=True, help="Input checkpoint (.pt)")
    parser.add_argument("--output", required=True, help="Output checkpoint (.pt)")
    parser.add_argument("--merge-from", type=int, required=True, help="Expert id to remove")
    parser.add_argument("--merge-into", type=int, required=True, help="Expert id to keep")
    args = parser.parse_args()

    ckpt_path = os.path.abspath(args.checkpoint)
    out_path = os.path.abspath(args.output)
    merge_from = int(args.merge_from)
    merge_into = int(args.merge_into)

    ckpt = torch.load(ckpt_path, map_location="cpu")
    if "model" not in ckpt:
        raise KeyError("Checkpoint missing 'model' state dict")
    state = ckpt["model"]

    num_experts = ckpt.get("num_experts")
    if num_experts is None:
        num_experts = _infer_num_experts(state)
    num_experts = int(num_experts)
    if num_experts <= 1:
        raise ValueError("Cannot prune with <= 1 expert")
    if merge_from != num_experts - 1:
        raise ValueError(
            f"merge-from {merge_from} must be the highest expert id ({num_experts - 1})"
        )
    if merge_from == merge_into:
        raise ValueError("merge-from and merge-into must be different")

    # Update router map to reroute merge_from -> merge_into.
    if "router_map" not in state:
        raise KeyError("Checkpoint missing router_map; cannot prune")
    router_map = state["router_map"].clone()
    router_map[router_map == merge_from] = merge_into
    state["router_map"] = router_map

    # Drop expert parameters for merge_from.
    drop_keys = set(_expert_keys(state, merge_from))
    if not drop_keys:
        raise ValueError(f"No parameters found for expert {merge_from}")
    for key in drop_keys:
        state.pop(key, None)

    ckpt["model"] = state
    ckpt["num_experts"] = num_experts - 1
    ckpt["prune"] = {
        "merge_from": merge_from,
        "merge_into": merge_into,
        "router_remap": f"{merge_from}->{merge_into}",
    }

    # Trim optimizer state for removed params (keeps momentum for remaining).
    optim = ckpt.get("optim")
    param_names = ckpt.get("param_names")
    optim, param_names = _drop_optimizer_entries(optim, param_names, drop_keys)
    if optim is not None:
        ckpt["optim"] = optim
    if param_names is not None:
        ckpt["param_names"] = param_names

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    torch.save(ckpt, out_path)
    print(
        f"[prune] merged expert {merge_from} -> {merge_into}, "
        f"removed {len(drop_keys)} tensors, new experts={ckpt['num_experts']}, "
        f"saved {out_path}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
