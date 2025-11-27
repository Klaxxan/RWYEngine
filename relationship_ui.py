# relationship_ui.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QLabel,
    QPushButton, QComboBox, QLineEdit
)
from PySide6.QtCore import Qt

from graph import build_graph
from graph_viewer import GraphViewer


class RelationshipEditorDialog(QDialog):
    def __init__(self, db, current_entry_id, parent=None):
        super().__init__(parent)
        self.db = db
        self.current_entry_id = current_entry_id

        entry = self.db.get_entry(self.current_entry_id)
        title = entry["title"] if entry else f"ID {self.current_entry_id}"

        self.setWindowTitle(f"Relationships for: {title}")
        self.setMinimumSize(700, 500)

        main_layout = QVBoxLayout(self)

        # Header
        self.entry_label = QLabel(f"Editing relationships for: <b>{title}</b>")
        main_layout.addWidget(self.entry_label)

        # Relationships list
        self.rel_list = QListWidget()
        main_layout.addWidget(self.rel_list)

        # Add relationship controls
        add_layout = QHBoxLayout()
        self.other_entry_combo = QComboBox()
        self.rel_type_field = QLineEdit()
        self.rel_type_field.setPlaceholderText(
            "Relationship type (e.g. Enemy, Ally, Mentor)"
        )
        self.add_btn = QPushButton("Add")

        add_layout.addWidget(self.other_entry_combo)
        add_layout.addWidget(self.rel_type_field)
        add_layout.addWidget(self.add_btn)
        main_layout.addLayout(add_layout)

        # Bottom buttons
        bottom_layout = QHBoxLayout()
        self.delete_btn = QPushButton("Delete Selected")
        self.map_btn = QPushButton("Open Relationship Map")
        self.close_btn = QPushButton("Close")

        bottom_layout.addWidget(self.delete_btn)
        bottom_layout.addWidget(self.map_btn)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.close_btn)
        main_layout.addLayout(bottom_layout)

        # Signals
        self.add_btn.clicked.connect(self.add_relationship)
        self.delete_btn.clicked.connect(self.delete_selected_relationship)
        self.map_btn.clicked.connect(self.open_map)
        self.close_btn.clicked.connect(self.accept)

        # Data
        self.populate_other_entries()
        self.load_relationships()

    # ------------------------------------------------------
    def populate_other_entries(self):
        self.other_entry_combo.clear()
        entries = self.db.get_all_entries()
        for e in entries:
            if e["id"] == self.current_entry_id:
                continue
            display = f"{e['title']} (ID {e['id']})"
            self.other_entry_combo.addItem(display, e["id"])

    def load_relationships(self):
        self.rel_list.clear()
        rels = self.db.get_relationships_for_entry(self.current_entry_id)

        for r in rels:
            a_id = r["entry_a"]
            b_id = r["entry_b"]
            rel_type = r["type"] or "relationship"

            a_entry = self.db.get_entry(a_id)
            b_entry = self.db.get_entry(b_id)
            a_name = a_entry["title"] if a_entry else f"ID {a_id}"
            b_name = b_entry["title"] if b_entry else f"ID {b_id}"

            # Always show current entry on the left
            if self.current_entry_id == a_id:
                left = a_name
                right = b_name
            else:
                left = b_name
                right = a_name

            text = f"{left} --[{rel_type}]--> {right}"

            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, r["id"])
            self.rel_list.addItem(item)

    # ------------------------------------------------------
    def add_relationship(self):
        other_id = self.other_entry_combo.currentData()
        if other_id is None:
            return

        rel_type = self.rel_type_field.text().strip()
        if not rel_type:
            rel_type = "relationship"

        self.db.add_relationship(self.current_entry_id, other_id, rel_type)
        self.load_relationships()
        self.rel_type_field.clear()

    def delete_selected_relationship(self):
        item = self.rel_list.currentItem()
        if not item:
            return
        rel_id = item.data(Qt.UserRole)
        self.db.delete_relationship(rel_id)
        self.load_relationships()

    # ------------------------------------------------------
    def open_map(self):
        entries = self.db.get_all_entries()
        relationships = self.db.get_all_relationships()
        G = build_graph(entries, relationships)

        self.map_window = GraphViewer(
            G,
            root_id=self.current_entry_id,
            parent=None,
            entry_callback=self.select_entry_in_main
        )
        self.map_window.show()
        self.map_window.activateWindow()
        self.map_window.raise_()

    def select_entry_in_main(self, entry_id):
        parent = self.parent()
        if parent and hasattr(parent, "select_entry_by_id"):
            parent.select_entry_by_id(entry_id)


