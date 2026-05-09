"""
Visualizer Module
Generates two architecture diagrams:
  1. project_architecture.png  — Project-level layered flow diagram
  2. method_diagram.png        — UML-style class/method diagram
"""

import os
import sys
import math
import textwrap
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib.patheffects as pe

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from parser.java_parser import JavaFileParser
from parser.java_crawler import get_java_files

# ── Design Tokens ─────────────────────────────────────────────────────────────
BG       = "#0d1117"
SURFACE  = "#161b22"
BORDER   = "#30363d"

LAYERS = [
    {"key": "controller", "label": "Controller",  "match": ["REST API", "MVC Controller"],
     "bg": "#0d2137", "border": "#1f6feb", "node": "#1f6feb", "text": "#cae8ff", "icon": "HTTP"},
    {"key": "service",    "label": "Service",      "match": ["Business logic"],
     "bg": "#0d2b00", "border": "#3fb950", "node": "#238636", "text": "#aff5b4", "icon": "SVC"},
    {"key": "repository", "label": "Repository",   "match": ["Data access"],
     "bg": "#2b1700", "border": "#d29922", "node": "#9e6a03", "text": "#f8e3a1", "icon": "REPO"},
    {"key": "entity",     "label": "Entity/Model", "match": ["JPA database"],
     "bg": "#290d17", "border": "#f85149", "node": "#b91c1c", "text": "#ffa8a8", "icon": "DB"},
    {"key": "component",  "label": "Component",    "match": ["Generic Spring", "DB transaction", "Utility", "Helper"],
     "bg": "#1b1040", "border": "#8957e5", "node": "#6e40c9", "text": "#d2a8ff", "icon": "UTIL"},
]

def _get_layer(layer_str):
    for l in LAYERS:
        if any(m.lower() in layer_str.lower() for m in l["match"]):
            return l
    return LAYERS[-1]

def _load_classes():
    all_classes = {}
    for f in get_java_files():
        try:
            parser = JavaFileParser(f)
            for cls in parser.get_classes():
                all_classes[cls['name']] = cls
        except Exception:
            continue
    return all_classes


# ══════════════════════════════════════════════════════════════════════════════
#  DIAGRAM 1 — Project-Level Architecture
# ══════════════════════════════════════════════════════════════════════════════

class ProjectArchitectureDiagram:
    """
    Renders a top-to-bottom layered flow diagram:
      [Client/HTTP]
           |
      [Controllers]  ← blue column
           |
      [Services]     ← green column
           |
      [Repositories] ← amber column
           |
      [Entities/DB]  ← red column
    Each column contains rounded-rect class cards.
    Cross-layer arrows show dependency flow.
    """

    def _draw_client_box(self, ax, x, y, w=2.5, h=0.7):
        box = FancyBboxPatch((x - w/2, y - h/2), w, h,
                             boxstyle="round,pad=0.08",
                             facecolor="#21262d", edgecolor="#58a6ff",
                             linewidth=2, zorder=4)
        ax.add_patch(box)
        ax.text(x, y, "Client / HTTP Request", ha="center", va="center",
                fontsize=9, fontweight="bold", color="#58a6ff", zorder=5)

    def _draw_db_box(self, ax, x, y, w=2.5, h=0.7):
        box = FancyBboxPatch((x - w/2, y - h/2), w, h,
                             boxstyle="round,pad=0.08",
                             facecolor="#21262d", edgecolor="#f85149",
                             linewidth=2, zorder=4)
        ax.add_patch(box)
        ax.text(x, y, "Database", ha="center", va="center",
                fontsize=9, fontweight="bold", color="#f85149", zorder=5)

    def _draw_layer_column(self, ax, layer, names, cx, y_start, row_h=1.0):
        """Draw a column of class cards for a given layer."""
        card_w, card_h = 3.2, 0.65
        positions = []
        for i, name in enumerate(names):
            cy = y_start - i * row_h
            # card
            card = FancyBboxPatch((cx - card_w/2, cy - card_h/2), card_w, card_h,
                                  boxstyle="round,pad=0.07",
                                  facecolor=layer["bg"], edgecolor=layer["border"],
                                  linewidth=1.5, zorder=4)
            ax.add_patch(card)
            # label badge
            badge_w = 0.55
            badge = FancyBboxPatch((cx - card_w/2 + 0.06, cy - 0.15), badge_w, 0.3,
                                   boxstyle="round,pad=0.04",
                                   facecolor=layer["node"], edgecolor="none", zorder=5)
            ax.add_patch(badge)
            ax.text(cx - card_w/2 + 0.06 + badge_w/2, cy,
                    layer["icon"], ha="center", va="center",
                    fontsize=5.5, fontweight="bold", color="white", zorder=6)
            # class name
            short = name if len(name) <= 22 else name[:20] + ".."
            ax.text(cx - card_w/2 + badge_w + 0.2, cy, short,
                    ha="left", va="center",
                    fontsize=7.5, fontweight="bold", color="white", zorder=5,
                    fontfamily="monospace")
            positions.append((cx, cy))
        return positions

    def _draw_flow_arrow(self, ax, x, y_from, y_to, color):
        mid_y = (y_from + y_to) / 2
        ax.annotate("", xy=(x, y_to + 0.35), xytext=(x, y_from - 0.35),
                    arrowprops=dict(arrowstyle="-|>",
                                   color=color,
                                   lw=2,
                                   connectionstyle="arc3,rad=0"))

    def _draw_dep_arrow(self, ax, p1, p2, color):
        ax.annotate("", xy=p2, xytext=p1,
                    arrowprops=dict(arrowstyle="-|>",
                                   color=color, lw=1.2, alpha=0.6,
                                   connectionstyle="arc3,rad=0.25"))

    def generate(self, all_classes, output_path):
        # bucket classes
        buckets = {l["key"]: [] for l in LAYERS}
        for name, cls in all_classes.items():
            layer = _get_layer(cls["layer"])
            buckets[layer["key"]].append(name)

        active = [l for l in LAYERS if buckets[l["key"]]]
        if not active:
            return

        # Layout: each active layer is a column, left→right
        n_cols   = len(active)
        COL_SEP  = 4.8
        ROW_H    = 1.0
        max_rows = max(len(buckets[l["key"]]) for l in active)

        fig_w = max(14, n_cols * COL_SEP + 2)
        fig_h = max(10, max_rows * ROW_H + 6)

        fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=150)
        ax.set_facecolor(BG)
        fig.patch.set_facecolor(BG)
        ax.set_xlim(-1, n_cols * COL_SEP)
        ax.set_ylim(-max_rows * ROW_H - 3, 4)
        ax.axis("off")

        Y_CLIENT = 2.8
        Y_START  = 1.6
        Y_DB     = -max_rows * ROW_H - 1.5

        col_xs = [i * COL_SEP + COL_SEP/2 for i in range(n_cols)]
        center_x = (col_xs[0] + col_xs[-1]) / 2

        # Client box at top
        self._draw_client_box(ax, center_x, Y_CLIENT)

        # Section background panels
        for i, layer in enumerate(active):
            cx     = col_xs[i]
            names  = buckets[layer["key"]]
            n      = len(names)
            pw     = 3.8
            ph     = n * ROW_H + 0.8
            py     = Y_START - (n - 1) * ROW_H - 0.4

            panel = FancyBboxPatch((cx - pw/2, py), pw, ph,
                                   boxstyle="round,pad=0.1",
                                   facecolor=layer["bg"], edgecolor=layer["border"],
                                   linewidth=1.5, zorder=1, alpha=0.5)
            ax.add_patch(panel)

            # Layer header
            ax.text(cx, Y_START + 0.65, layer["label"],
                    ha="center", va="center", fontsize=9, fontweight="bold",
                    color=layer["text"], zorder=3,
                    bbox=dict(boxstyle="round,pad=0.3", facecolor=layer["bg"],
                              edgecolor=layer["border"], linewidth=1))

            positions = self._draw_layer_column(ax, layer, names, cx, Y_START, ROW_H)

            # Arrow from client to first column
            ax.annotate("", xy=(cx, Y_START + 0.35), xytext=(center_x, Y_CLIENT - 0.36),
                        arrowprops=dict(arrowstyle="-|>", color=layer["border"],
                                        lw=1.5, alpha=0.7,
                                        connectionstyle="arc3,rad=0"))

        # DB box at bottom
        self._draw_db_box(ax, center_x, Y_DB)

        # Cross-layer dependency arrows
        dep_colors = {
            ("controller", "service"):    "#1f6feb",
            ("service",    "repository"): "#3fb950",
            ("repository", "entity"):     "#d29922",
        }
        layer_keys = [l["key"] for l in active]
        for (src_key, dst_key), color in dep_colors.items():
            if src_key in layer_keys and dst_key in layer_keys:
                si = layer_keys.index(src_key)
                di = layer_keys.index(dst_key)
                if si != di:
                    sx, dx = col_xs[si], col_xs[di]
                    ax.annotate("", xy=(dx, Y_START), xytext=(sx, Y_START),
                                arrowprops=dict(arrowstyle="-|>",
                                                color=color, lw=2,
                                                connectionstyle="arc3,rad=-0.3"))

        # Title
        total = len(all_classes)
        ax.set_title(
            f"Project Architecture  |  {total} classes across {len(active)} layers",
            fontsize=13, fontweight="bold", color="white", pad=14)

        # Legend
        patches = [mpatches.Patch(facecolor=l["node"], edgecolor=l["border"],
                                  label=l["label"]) for l in active]
        ax.legend(handles=patches, loc="lower center",
                  bbox_to_anchor=(0.5, -0.04), ncol=len(active),
                  fontsize=8, facecolor=SURFACE, labelcolor="white",
                  edgecolor=BORDER, framealpha=0.95)

        plt.tight_layout(pad=1.5)
        plt.savefig(output_path, dpi=150, bbox_inches="tight",
                    facecolor=BG, edgecolor="none")
        plt.close(fig)
        print(f"[Visualizer] Project diagram saved -> {output_path}")


# ══════════════════════════════════════════════════════════════════════════════
#  DIAGRAM 2 — Method-Level UML Class Diagram
# ══════════════════════════════════════════════════════════════════════════════

class MethodLevelDiagram:
    """
    Renders UML-style class boxes showing:
      ┌─────────────────────┐
      │ <<annotation>>      │  (header)
      │  ClassName          │
      ├─────────────────────┤
      │ - fieldName: Type   │  (fields)
      ├─────────────────────┤
      │ + method(): Return  │  (methods)
      └─────────────────────┘
    Arrows show @Autowired dependencies.
    """

    BOX_W      = 3.0
    HEADER_H   = 0.75
    LINE_H     = 0.28
    SECTION_PAD = 0.12
    COL_SEP    = 4.2
    ROW_SEP    = 0.5

    def _measure_box(self, cls):
        """Calculate total box height for a class."""
        n_fields  = len(cls.get("fields",  []))
        n_methods = len(cls.get("methods", []))
        h = self.HEADER_H
        h += self.SECTION_PAD
        h += max(n_fields,  1) * self.LINE_H + self.SECTION_PAD
        h += max(n_methods, 1) * self.LINE_H + self.SECTION_PAD
        return h

    def _draw_class_box(self, ax, cls, x, y, layer):
        bw = self.BOX_W
        bh = self._measure_box(cls)

        # Outer shadow
        shadow = FancyBboxPatch((x - bw/2 + 0.05, y - bh - 0.05), bw, bh,
                                boxstyle="round,pad=0.05",
                                facecolor="#000000", edgecolor="none",
                                linewidth=0, zorder=2, alpha=0.4)
        ax.add_patch(shadow)

        # Main box background
        box = FancyBboxPatch((x - bw/2, y - bh), bw, bh,
                             boxstyle="round,pad=0.05",
                             facecolor=layer["bg"], edgecolor=layer["border"],
                             linewidth=1.8, zorder=3)
        ax.add_patch(box)

        cy = y  # current y cursor (top)

        # ── Header ──────────────────────────────────────────────────────────
        hdr = FancyBboxPatch((x - bw/2, cy - self.HEADER_H), bw, self.HEADER_H,
                             boxstyle="round,pad=0.05",
                             facecolor=layer["node"], edgecolor="none",
                             linewidth=0, zorder=4)
        ax.add_patch(hdr)

        # Stereotype (first annotation if any)
        annos = cls.get("annotations", [])
        if annos:
            ax.text(x, cy - 0.18, f"<<{annos[0]}>>",
                    ha="center", va="center", fontsize=5.5,
                    color="white", alpha=0.85, zorder=5, style="italic")

        ax.text(x, cy - 0.50, cls["name"],
                ha="center", va="center", fontsize=7.5, fontweight="bold",
                color="white", zorder=5, fontfamily="monospace")

        cy -= self.HEADER_H

        # Divider
        ax.plot([x - bw/2 + 0.1, x + bw/2 - 0.1], [cy, cy],
                color=layer["border"], linewidth=0.8, zorder=5)
        cy -= self.SECTION_PAD

        # ── Fields ──────────────────────────────────────────────────────────
        fields = cls.get("fields", [])
        if fields:
            for field in fields[:6]:  # cap at 6
                anno_mark = "@" if field.get("annotations") else " "
                label = f"  {anno_mark} {field['name']}: {field['type']}"
                label = label if len(label) <= 32 else label[:30] + ".."
                ax.text(x - bw/2 + 0.15, cy - self.LINE_H/2, label,
                        ha="left", va="center", fontsize=5.8,
                        color=layer["text"], zorder=5, fontfamily="monospace")
                cy -= self.LINE_H
            if len(fields) > 6:
                ax.text(x - bw/2 + 0.15, cy - self.LINE_H/2,
                        f"  ... +{len(fields)-6} more",
                        ha="left", va="center", fontsize=5.5,
                        color=layer["text"], alpha=0.6, zorder=5)
                cy -= self.LINE_H
        else:
            ax.text(x - bw/2 + 0.15, cy - self.LINE_H/2, "  (no fields)",
                    ha="left", va="center", fontsize=5.5,
                    color=layer["text"], alpha=0.5, zorder=5)
            cy -= self.LINE_H

        cy -= self.SECTION_PAD
        # Divider
        ax.plot([x - bw/2 + 0.1, x + bw/2 - 0.1], [cy, cy],
                color=layer["border"], linewidth=0.8, alpha=0.6, zorder=5)
        cy -= self.SECTION_PAD

        # ── Methods ─────────────────────────────────────────────────────────
        methods = cls.get("methods", [])
        if methods:
            for m in methods[:6]:
                params = ", ".join(t for t, _ in m["parameters"][:2])
                if len(m["parameters"]) > 2:
                    params += ".."
                sig = f"  + {m['name']}({params}): {m['return_type']}"
                sig = sig if len(sig) <= 34 else sig[:32] + ".."
                ax.text(x - bw/2 + 0.15, cy - self.LINE_H/2, sig,
                        ha="left", va="center", fontsize=5.8,
                        color=layer["text"], zorder=5, fontfamily="monospace")
                cy -= self.LINE_H
            if len(methods) > 6:
                ax.text(x - bw/2 + 0.15, cy - self.LINE_H/2,
                        f"  ... +{len(methods)-6} more",
                        ha="left", va="center", fontsize=5.5,
                        color=layer["text"], alpha=0.6, zorder=5)
                cy -= self.LINE_H
        else:
            ax.text(x - bw/2 + 0.15, cy - self.LINE_H/2, "  (no methods)",
                    ha="left", va="center", fontsize=5.5,
                    color=layer["text"], alpha=0.5, zorder=5)

        # Return anchor points (right-center for outgoing, left-center for incoming)
        box_h = self._measure_box(cls)
        mid_y = y - box_h / 2
        return (x + bw/2, mid_y), (x - bw/2, mid_y)

    def generate(self, all_classes, output_path):
        if not all_classes:
            return

        # Group by layer
        buckets = {l["key"]: [] for l in LAYERS}
        for name, cls in all_classes.items():
            layer = _get_layer(cls["layer"])
            buckets[layer["key"]].append(name)

        active = [l for l in LAYERS if buckets[l["key"]]]
        n_cols = len(active)

        # Compute grid positions
        positions = {}   # name -> (cx, top_y)
        anchors   = {}   # name -> (right_pt, left_pt)

        col_xs = {l["key"]: i * self.COL_SEP + self.COL_SEP/2
                  for i, l in enumerate(active)}

        max_height = 0
        col_heights = {}
        for layer in active:
            names = buckets[layer["key"]]
            total_h = sum(self._measure_box(all_classes[n]) for n in names)
            total_h += (len(names) - 1) * self.ROW_SEP
            col_heights[layer["key"]] = total_h
            max_height = max(max_height, total_h)

        for layer in active:
            cx    = col_xs[layer["key"]]
            names = buckets[layer["key"]]
            cy    = max_height / 2  # start from top, center vertically
            for name in names:
                positions[name] = (cx, cy)
                cy -= self._measure_box(all_classes[name]) + self.ROW_SEP

        # Canvas
        fig_w = max(16, n_cols * self.COL_SEP + 2)
        fig_h = max(12, max_height + 5)

        fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=150)
        ax.set_facecolor(BG)
        fig.patch.set_facecolor(BG)
        ax.axis("off")

        # Column header banners
        for layer in active:
            cx = col_xs[layer["key"]]
            ax.text(cx, max_height/2 + 1.0, layer["label"],
                    ha="center", va="center", fontsize=10, fontweight="bold",
                    color=layer["text"], zorder=6,
                    bbox=dict(boxstyle="round,pad=0.4",
                              facecolor=layer["bg"], edgecolor=layer["border"],
                              linewidth=2))
            # Vertical guide line
            ax.axvline(cx, color=layer["border"], linewidth=0.4,
                       alpha=0.2, linestyle="--", zorder=0)

        # Draw class boxes
        for name, (cx, top_y) in positions.items():
            cls   = all_classes[name]
            layer = _get_layer(cls["layer"])
            r, l  = self._draw_class_box(ax, cls, cx, top_y, layer)
            anchors[name] = (r, l)

        # Draw dependency arrows
        for name, cls in all_classes.items():
            if name not in anchors:
                continue
            src_right, _ = anchors[name]
            for field in cls.get("fields", []):
                dep = field["type"]
                if dep in anchors and dep != name:
                    _, dst_left = anchors[dep]
                    # Arrow color based on source layer
                    layer = _get_layer(cls["layer"])
                    ax.annotate("",
                                xy=dst_left, xytext=src_right,
                                arrowprops=dict(
                                    arrowstyle="-|>",
                                    color=layer["border"],
                                    lw=1.3, alpha=0.75,
                                    connectionstyle="arc3,rad=0.2"
                                ), zorder=6)

        # Title
        ax.set_title(
            f"Method-Level Class Diagram  |  {len(all_classes)} classes",
            fontsize=13, fontweight="bold", color="white", pad=14)

        # Legend
        patches = [mpatches.Patch(facecolor=l["node"], edgecolor=l["border"],
                                  label=l["label"]) for l in active]
        ax.legend(handles=patches, loc="lower center",
                  bbox_to_anchor=(0.5, -0.03), ncol=len(active),
                  fontsize=8, facecolor=SURFACE, labelcolor="white",
                  edgecolor=BORDER, framealpha=0.95)

        plt.tight_layout(pad=1.5)
        plt.savefig(output_path, dpi=150, bbox_inches="tight",
                    facecolor=BG, edgecolor="none")
        plt.close(fig)
        print(f"[Visualizer] Method diagram saved -> {output_path}")


# ══════════════════════════════════════════════════════════════════════════════
#  Public entry point (backward compatible)
# ══════════════════════════════════════════════════════════════════════════════

class SpringLayerVisualizer:

    def generate_graph(self):
        """Legacy entry — generates both diagrams."""
        self.generate_all()

    def generate_all(self):
        all_classes = _load_classes()
        os.makedirs(config.DOCS_DIR, exist_ok=True)

        ProjectArchitectureDiagram().generate(
            all_classes,
            os.path.join(config.DOCS_DIR, "architecture_graph.png")
        )
        MethodLevelDiagram().generate(
            all_classes,
            os.path.join(config.DOCS_DIR, "method_diagram.png")
        )


if __name__ == "__main__":
    SpringLayerVisualizer().generate_all()
