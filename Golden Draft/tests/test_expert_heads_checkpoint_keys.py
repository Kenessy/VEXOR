"""Behavior locks for EXPERT_HEADS-driven checkpoint layouts."""

from __future__ import annotations

import unittest

import conftest  # noqa: F401  (import side-effect: sys.path bootstrap)


class ExpertHeadsCheckpointKeyTests(unittest.TestCase):
    def test_state_dict_uses_expert_heads_layout_when_enabled(self) -> None:
        with conftest.temporary_env(
            VRX_EXPERT_HEADS="2",
            VRX_RING_LEN="8",
            VRX_SLOT_DIM="16",
            VRX_SENSORY_RING="0",
            VRX_VAULT="0",
            VRX_THINK_RING="0",
            VRX_NAN_GUARD=None,
        ):
            from vraxion.instnct import seed as seed_mod

            seed_mod.EXPERT_HEADS = 2

            from tools import instnct_runner

            ctx = instnct_runner.default_context()
            model = ctx.model_ctor(
                input_dim=1,
                num_classes=2,
                ring_len=ctx.ring_len,
                slot_dim=ctx.slot_dim,
            ).cpu()

            keys = list(model.state_dict().keys())

            self.assertTrue(any(key.startswith("head.experts.0.") for key in keys), "missing head.experts.0.* keys")
            self.assertTrue(any(key.startswith("head.experts.1.") for key in keys), "missing head.experts.1.* keys")
            self.assertFalse(any(key.startswith("head.single.") for key in keys), "unexpected head.single.* keys present")


if __name__ == "__main__":
    unittest.main()

