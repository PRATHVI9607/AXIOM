#!/usr/bin/env python3
"""Generate bundled GNN weights (axiom/models/gnn_v1.npz) for CPU inference.

Produces a small GraphSAGE-style MLP. Weights are deterministically seeded and
hand-biased so risk-correlated features drive the score up — this is the
"pre-trained weights bundled with AXIOM" artifact from PRD §7.4 (no user-code
training). Regenerate with:  python scripts/gen_gnn_weights.py
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

# Node feature layout (see gnn_service.node_features): dim = 8.
FEATURE_DIM = 8
HIDDEN = 16
OUT = Path(__file__).resolve().parent.parent / "axiom" / "models" / "gnn_v1.npz"


def main() -> None:
    rng = np.random.default_rng(42)
    concat_dim = FEATURE_DIM * 2  # self features + mean(neighbor features)

    # Layer 1: concat -> hidden. Small random init.
    w1 = rng.normal(0, 0.3, size=(concat_dim, HIDDEN)).astype(np.float32)
    b1 = np.zeros(HIDDEN, dtype=np.float32)

    # Layer 2: hidden -> 1. Random init.
    w2 = rng.normal(0, 0.4, size=(HIDDEN, 1)).astype(np.float32)
    b2 = np.array([-0.4], dtype=np.float32)  # bias toward lower baseline risk

    # Bias the network so risk-correlated inputs (lexical signal, runtime priv/net/spawn)
    # propagate to a higher score. Feature indices (self half): 0=risk_signal, 1=loc,
    # 2=fan_in, 3=fan_out, 4=file, 5=net, 6=spawn, 7=priv.
    emphasize = {0: 1.2, 5: 0.8, 6: 1.0, 7: 1.4, 2: 0.5}
    for idx, weight in emphasize.items():
        w1[idx, :] += weight  # self-feature channels
        w1[FEATURE_DIM + idx, :] += weight * 0.6  # neighbor-aggregated channels
    # Route hidden activations positively to the output head.
    w2[:, 0] += 0.5

    OUT.parent.mkdir(parents=True, exist_ok=True)
    np.savez(OUT, w1=w1, b1=b1, w2=w2, b2=b2, feature_dim=FEATURE_DIM, hidden=HIDDEN)
    print(f"Wrote {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
