# graph_viewer.py
import networkx as nx

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QGraphicsScene, QGraphicsView,
    QPushButton, QFileDialog
)
from PySide6.QtGui import (
    QPen, QBrush, QColor, QFont, QPainter, QImage,
    QPainterPath, QFontMetricsF
)
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtWidgets import QGraphicsItem, QGraphicsPathItem


class GraphView(QGraphicsView):
    """
    Custom QGraphicsView to handle zoom with CTRL+scroll.
    """
    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            zoom_in = 1.25
            zoom_out = 0.8

            if event.angleDelta().y() > 0:
                self.scale(zoom_in, zoom_in)
            else:
                self.scale(zoom_out, zoom_out)
        else:
            super().wheelEvent(event)


class OutlineTextItem(QGraphicsItem):
    """
    Text with outline: style B (white fill with black outline).
    """
    def __init__(self, text, font, fill_color=Qt.white,
                 outline_color=Qt.black, outline_width=2, parent=None):
        super().__init__(parent)
        self.text = text
        self.font = font
        self.fill_color = QColor(fill_color)
        self.outline_color = QColor(outline_color)
        self.outline_width = outline_width

        fm = QFontMetricsF(self.font)
        self._rect = fm.boundingRect(self.text).adjusted(-4, -4, 4, 4)

    def boundingRect(self) -> QRectF:
        return self._rect

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setFont(self.font)

        path = QPainterPath()
        path.addText(0, 0, self.font, self.text)

        bounds = path.boundingRect()
        dx = -bounds.left()
        dy = -bounds.top()
        painter.translate(dx, dy)

        # Outline
        pen = QPen(self.outline_color, self.outline_width,
                   Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)

        # Fill
        painter.setPen(Qt.NoPen)
        painter.setBrush(self.fill_color)
        painter.drawPath(path)


class NodeItem(QGraphicsItem):
    """
    Node item: circle + label in one object.
    Movable, clickable, notifies viewer when moved.
    """
    def __init__(self, node_id, viewer, center: QPointF, radius: float,
                 fill_color: QColor, label: str, font: QFont):
        super().__init__()
        self.node_id = node_id
        self.viewer = viewer
        self.radius = radius
        self.fill_color = fill_color
        self.label = label
        self.font = font

        self.setFlags(
            QGraphicsItem.ItemIsMovable |
            QGraphicsItem.ItemIsSelectable |
            QGraphicsItem.ItemSendsGeometryChanges
        )

        self._rect = QRectF(-radius, -radius, radius * 2, radius * 2)

        # Label child
        self.label_item = OutlineTextItem(
            self.label,
            self.font,
            fill_color=Qt.white,
            outline_color=Qt.black,
            outline_width=2,
            parent=self
        )
        lb = self.label_item.boundingRect()
        self.label_item.setPos(-lb.width() / 2, -lb.height() / 2)

        self.setPos(center)

    def boundingRect(self) -> QRectF:
        # include ellipse + label
        return self._rect.united(
            self.label_item.mapToParent(
                self.label_item.boundingRect()
            ).boundingRect()
        )

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(Qt.black, 2))
        painter.setBrush(QBrush(self.fill_color))
        painter.drawEllipse(self._rect)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            if self.viewer is not None:
                self.viewer.on_node_moved(self.node_id)
        return super().itemChange(change, value)

    def mousePressEvent(self, event):
        if self.viewer is not None:
            self.viewer.on_node_clicked(self.node_id)
        super().mousePressEvent(event)

    def center(self) -> QPointF:
        return self.scenePos()


class CurvedEdgeItem(QGraphicsPathItem):
    """
    Curved edge with outline-text label.
    """
    def __init__(self, src_item: NodeItem, dst_item: NodeItem,
                 label: str, font: QFont):
        super().__init__()
        self.src_item = src_item
        self.dst_item = dst_item
        self.label_text = label
        self.font = font

        self.setPen(QPen(QColor("#AAAAAA"), 2))
        self.setCacheMode(QGraphicsItem.NoCache)  # moving path = no cache

        self.label_item = OutlineTextItem(
            self.label_text,
            self.font,
            fill_color=QColor(255, 80, 80),
            outline_color=Qt.black,
            outline_width=2
        )

    def boundingRect(self) -> QRectF:
        # Expand boundingRect so Qt fully clears antialiased curve
        rect = super().boundingRect()
        margin = 12.0
        return rect.adjusted(-margin, -margin, margin, margin)

    def update_path(self):
        # Let Qt know geometry changed so it repaints correctly
        self.prepareGeometryChange()

        p1 = self.src_item.center()
        p2 = self.dst_item.center()

        # Quadratic bezier curve
        mid = (p1 + p2) / 2
        vec = p2 - p1
        perp = QPointF(-vec.y(), vec.x())
        if perp.manhattanLength() > 0:
            perp /= perp.manhattanLength()

        curvature = 40.0
        ctrl = mid + perp * curvature

        path = QPainterPath()
        path.moveTo(p1)
        path.quadTo(ctrl, p2)
        self.setPath(path)

        # Place label at curve midpoint
        t = 0.5
        mid_x = (1 - t) ** 2 * p1.x() + 2 * (1 - t) * t * ctrl.x() + t ** 2 * p2.x()
        mid_y = (1 - t) ** 2 * p1.y() + 2 * (1 - t) * t * ctrl.y() + t ** 2 * p2.y()
        lb = self.label_item.boundingRect()
        self.label_item.setPos(mid_x - lb.width() / 2, mid_y - lb.height() / 2)

        self.update()
        self.label_item.update()


class GraphViewer(QWidget):
    """
    Interactive relationship map:
      - Rooted tree layout (from root_id)
      - Force layout alternative
      - Dynamic node sizes by degree
      - Curved edges
      - Click nodes -> callback
      - Drag nodes -> live edge redraw
      - Ctrl+scroll zoom
      - Fit to view
      - Export PNG
    """
    def __init__(self, G: nx.DiGraph, root_id=None,
                 parent=None, entry_callback=None):
        super().__init__(parent)
        self.setWindowTitle("Relationship Map")
        self.setMinimumSize(1000, 800)

        self.G = G
        self.root_id = root_id
        self.entry_callback = entry_callback

        self.scene = QGraphicsScene()
        self.view = GraphView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setDragMode(QGraphicsView.ScrollHandDrag)

        main_layout = QVBoxLayout(self)

        # Buttons
        btn_layout = QHBoxLayout()
        self.tree_btn = QPushButton("Tree Layout")
        self.force_btn = QPushButton("Force Layout")
        self.fit_btn = QPushButton("Fit to View")
        self.export_btn = QPushButton("Export PNG")

        self.tree_btn.clicked.connect(self.apply_tree_layout)
        self.force_btn.clicked.connect(self.apply_force_layout)
        self.fit_btn.clicked.connect(self.fit_to_view)
        self.export_btn.clicked.connect(self.export_png)

        btn_layout.addWidget(self.tree_btn)
        btn_layout.addWidget(self.force_btn)
        btn_layout.addWidget(self.fit_btn)
        btn_layout.addWidget(self.export_btn)
        btn_layout.addStretch()

        main_layout.addLayout(btn_layout)
        main_layout.addWidget(self.view)

        # State
        self.node_items: dict[int, NodeItem] = {}
        self.edge_items: list[CurvedEdgeItem] = []

        # Initial layout
        if self.root_id is not None and self.root_id in self.G.nodes:
            self.current_layout = "tree"
            self.positions = self.compute_tree_layout(self.root_id)
        else:
            self.current_layout = "force"
            self.positions = self.compute_force_layout()

        self.draw_graph()
        self.fit_to_view()

    # ---------------- Layouts ----------------
    def compute_tree_layout(self, root_id):
        UG = self.G.to_undirected()
        layers = {}
        visited = set()
        queue = [(root_id, 0)]
        visited.add(root_id)

        while queue:
            node, depth = queue.pop(0)
            layers.setdefault(depth, []).append(node)
            for neighbor in UG.neighbors(node):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, depth + 1))

        max_depth = max(layers.keys()) if layers else 0
        for node in self.G.nodes:
            if node not in visited:
                max_depth += 1
                layers.setdefault(max_depth, []).append(node)

        for depth in layers:
            layers[depth].sort(key=lambda n: UG.degree(n), reverse=True)

        pos = {}
        vertical_gap = 170
        horizontal_gap = 150

        for depth, nodes in layers.items():
            count = len(nodes)
            total_width = (count - 1) * horizontal_gap
            start_x = -total_width / 2.0
            for i, node in enumerate(nodes):
                x = start_x + i * horizontal_gap
                y = depth * vertical_gap
                pos[node] = (x, y)

        return pos

    def compute_force_layout(self):
        raw_pos = nx.spring_layout(self.G, k=1.2, iterations=70)
        scale = 320.0
        return {n: (x * scale, y * scale) for n, (x, y) in raw_pos.items()}

    # ---------------- Drawing ----------------
    def draw_graph(self):
        self.scene.clear()
        self.node_items.clear()
        self.edge_items.clear()

        base_radius = 22.0
        mult = 4.0
        node_font = QFont("Arial", 11)
        centers: dict[int, QPointF] = {}

        for node in self.G.nodes:
            x, y = self.positions.get(node, (0.0, 0.0))
            centers[node] = QPointF(x, y)

        # Nodes
        for node, data in self.G.nodes(data=True):
            degree = self.G.degree(node)
            radius = base_radius + mult * min(degree, 8)

            label = data.get("label", str(node))
            category = data.get("category", "default")

            color_map = {
                "Character": "#66AAFF",
                "Location": "#88CC66",
                "Item": "#FFCC66",
                "Event": "#CC66FF",
                "default": "#AAAAAA",
            }
            fill_color = QColor(color_map.get(category, "#AAAAAA"))
            center = centers.get(node, QPointF(0, 0))

            node_item = NodeItem(node, self, center, radius,
                                 fill_color, label, node_font)
            node_item.setZValue(2)
            node_item.label_item.setZValue(3)

            self.scene.addItem(node_item)
            self.node_items[node] = node_item

        # Edges
        edge_font = QFont("Arial", 9)
        seen_pairs = set()

        for src, dst, data in self.G.edges(data=True):
            key = tuple(sorted((src, dst)))
            if key in seen_pairs:
                continue
            seen_pairs.add(key)

            if src not in self.node_items or dst not in self.node_items:
                continue

            label = data.get("label", "")
            src_item = self.node_items[src]
            dst_item = self.node_items[dst]

            edge_item = CurvedEdgeItem(src_item, dst_item, label, edge_font)
            edge_item.setZValue(0)
            edge_item.label_item.setZValue(1)

            self.scene.addItem(edge_item)
            self.scene.addItem(edge_item.label_item)
            edge_item.update_path()

            self.edge_items.append(edge_item)

    # ---------------- Layout buttons ----------------
    def apply_tree_layout(self):
        if self.root_id is not None and self.root_id in self.G.nodes:
            self.current_layout = "tree"
            self.positions = self.compute_tree_layout(self.root_id)
            self.apply_positions()
            self.fit_to_view()

    def apply_force_layout(self):
        self.current_layout = "force"
        self.positions = self.compute_force_layout()
        self.apply_positions()
        self.fit_to_view()

    def apply_positions(self):
        for node, pos in self.positions.items():
            if node in self.node_items:
                self.node_items[node].setPos(QPointF(pos[0], pos[1]))
        self.update_all_edges()

    # ---------------- Edge updating ----------------
    def on_node_moved(self, node_id):
        self.update_all_edges()

    def update_all_edges(self):
        for edge in self.edge_items:
            edge.update_path()

    # ---------------- Node click ----------------
    def on_node_clicked(self, node_id):
        self.highlight_neighbors(node_id)
        if self.entry_callback:
            self.entry_callback(node_id)

    def highlight_neighbors(self, node_id):
        succ = set(self.G.successors(node_id))
        pred = set(self.G.predecessors(node_id))
        neighbors = succ | pred
        neighbors.add(node_id)

        for n, node_item in self.node_items.items():
            node_item.setOpacity(1.0 if n in neighbors else 0.25)

        for edge in self.edge_items:
            src = edge.src_item.node_id
            dst = edge.dst_item.node_id
            highlight = (src in neighbors and dst in neighbors)
            edge.setOpacity(1.0 if highlight else 0.2)
            edge.label_item.setOpacity(1.0 if highlight else 0.2)

    # ---------------- View helpers ----------------
    def fit_to_view(self):
        rect = self.scene.itemsBoundingRect()
        if rect.isNull():
            return
        self.view.fitInView(rect, Qt.KeepAspectRatio)

    def export_png(self):
        rect = self.scene.itemsBoundingRect()
        if rect.isNull():
            return

        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Export Graph as PNG",
            "relationship_graph.png",
            "PNG Files (*.png)"
        )
        if not file_name:
            return

        img = QImage(int(rect.width()) * 2, int(rect.height()) * 2,
                     QImage.Format_ARGB32)
        img.fill(Qt.transparent)

        painter = QPainter(img)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.translate(-rect.topLeft())
        painter.scale(2.0, 2.0)
        self.scene.render(painter)
        painter.end()

        img.save(file_name)
