"""Pre-render all TDDB formula images using matplotlib (one last time run).
Output: ui/gen/formula_images/*.png — loaded at runtime, no matplotlib needed.
"""
import hashlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from io import BytesIO
from pathlib import Path

BASE = Path(__file__).resolve().parent
IMG_DIR = BASE / "formula_images"
IMG_DIR.mkdir(parents=True, exist_ok=True)

formulas = [
    (r"\eta = A \cdot e^{-\gamma \cdot E_{ox} + E_a/kT}", "life_e_model"),
    (r"\eta = \tau_0 \cdot e^{G/E_{ox} + E_a/kT}", "life_1e_model"),
    (r"\eta = A \cdot e^{-\beta_v \cdot V + E_a/kT}", "life_v_model"),
    (r"F(t) = 1 - e^{-(t/\eta)^\beta}", "fail_common"),
]

def render(latex, stem, fontsize=10, dpi=120):
    fig, ax = plt.subplots(figsize=(max(len(latex) * 0.08, 1.5), 0.6))
    ax.text(0.5, 0.5, f"${latex}$" if not latex.startswith("$") else latex,
            fontsize=fontsize, ha='center', va='center',
            transform=ax.transAxes)
    ax.axis('off')
    buf = BytesIO()
    fig.savefig(buf, dpi=dpi, bbox_inches='tight', pad_inches=0.1,
                format='png', transparent=True)
    plt.close(fig)
    buf.seek(0)
    out = IMG_DIR / f"{stem}.png"
    out.write_bytes(buf.getvalue())
    print(f"  ✓ {out.name}  ({len(buf.getvalue()) / 1024:.1f} KB)")

    # Also write to user cache so existing cached files are consistent
    cache_dir = Path.home() / ".cache" / "reliability-tool" / "tddb_formulas"
    cache_dir.mkdir(parents=True, exist_ok=True)
    ck = hashlib.md5(f"{latex}_{fontsize}_{dpi}".encode()).hexdigest()
    (cache_dir / f"{ck}.png").write_bytes(buf.getvalue())

print("Pre-rendering TDDB formula images...")
for latex, stem in formulas:
    render(latex, stem)
print(f"\nDone! {len(formulas)} images in {IMG_DIR}")
