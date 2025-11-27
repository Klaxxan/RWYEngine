# main.py
import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QListWidget, QListWidgetItem, QTextEdit,
    QPushButton, QLabel
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from database import Database
from search import fuzzy_search
from relationship_ui import RelationshipEditorDialog


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.db = Database()
        self.setWindowIcon(QIcon("RWYLogo.ico"))
        self.setWindowTitle("RWYEngine")
        self.setMinimumSize(900, 600)

        # Prevent autosave while loading fields
        self.loading_entry = False
        self.current_entry_id = None

        main_layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()

        # Search bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search...")
        self.search_bar.textChanged.connect(self.run_search)

        # Entry list
        self.entry_list = QListWidget()
        self.entry_list.itemClicked.connect(self.load_entry_details)

        # Buttons under list
        self.new_btn = QPushButton("New Entry")
        self.new_btn.clicked.connect(self.create_entry)

        self.delete_btn = QPushButton("Delete Entry")
        self.delete_btn.clicked.connect(self.delete_entry)

        list_button_row = QHBoxLayout()
        list_button_row.addWidget(self.new_btn)
        list_button_row.addWidget(self.delete_btn)

        # Entry detail fields
        self.title_field = QLineEdit()
        self.title_field.setPlaceholderText("Title")

        self.description_field = QTextEdit()

        self.category_field = QLineEdit()
        self.category_field.setPlaceholderText("Category (e.g. Character, Location, Item, Event)")

        self.tags_field = QLineEdit()
        self.tags_field.setPlaceholderText("Tags (comma separated)")

        self.synonyms_field = QLineEdit()
        self.synonyms_field.setPlaceholderText("Synonyms (comma separated)")

        # Bottom-right buttons
        self.save_btn = QPushButton("Save Changes")
        self.save_btn.clicked.connect(self.save_entry)

        self.relationships_btn = QPushButton("Relationships")
        self.relationships_btn.clicked.connect(self.open_relationship_editor)

        bottom_btn_row = QHBoxLayout()
        bottom_btn_row.addWidget(self.save_btn)
        bottom_btn_row.addWidget(self.relationships_btn)
        bottom_btn_row.addStretch()

        # Assemble left
        left_layout.addWidget(self.search_bar)
        left_layout.addWidget(self.entry_list)
        left_layout.addLayout(list_button_row)

        # Assemble right
        right_layout.addWidget(QLabel("Title:"))
        right_layout.addWidget(self.title_field)

        right_layout.addWidget(QLabel("Description:"))
        right_layout.addWidget(self.description_field)

        right_layout.addWidget(QLabel("Category:"))
        right_layout.addWidget(self.category_field)

        right_layout.addWidget(QLabel("Tags:"))
        right_layout.addWidget(self.tags_field)

        right_layout.addWidget(QLabel("Synonyms:"))
        right_layout.addWidget(self.synonyms_field)

        right_layout.addLayout(bottom_btn_row)

        main_layout.addLayout(left_layout, 30)
        main_layout.addLayout(right_layout, 70)
        self.setLayout(main_layout)

        self.load_all_entries()

    # ---------------------------------------------------
    # Utility: clear entry fields
    # ---------------------------------------------------
    def clear_entry_fields(self):
        self.title_field.clear()
        self.description_field.clear()
        self.category_field.clear()
        self.tags_field.clear()
        self.synonyms_field.clear()

    # ---------------------------------------------------
    # Autosave current entry
    # ---------------------------------------------------
    def autosave_current_entry(self):
        if self.loading_entry:
            return
        if self.current_entry_id is None:
            return

        title = self.title_field.text()
        description = self.description_field.toPlainText()
        category = self.category_field.text()
        tags = self.tags_field.text()
        synonyms = self.synonyms_field.text()

        # Skip empty entries
        if not (title or description or category or tags or synonyms):
            return

        self.db.update_entry(
            self.current_entry_id, title, description, category, tags, synonyms
        )

    # ---------------------------------------------------
    # Load all entries into the list
    # ---------------------------------------------------
    def load_all_entries(self):
        self.entry_list.clear()
        entries = self.db.get_all_entries()
        for e in entries:
            item = QListWidgetItem(e["title"])
            item.setData(Qt.UserRole, e["id"])
            self.entry_list.addItem(item)

    # ---------------------------------------------------
    # Handle selection
    # ---------------------------------------------------
    def load_entry_details(self, item):
        # Prevent autosave from triggering during loading
        self.loading_entry = True

        # Save old entry first
        self.autosave_current_entry()

        entry_id = item.data(Qt.UserRole)
        self.current_entry_id = entry_id
        data = self.db.get_entry(entry_id)

        # Load fields safely
        self.title_field.setText(data["title"])
        self.description_field.setPlainText(data["description"])
        self.category_field.setText(data["category"])
        self.tags_field.setText(data["tags"])
        self.synonyms_field.setText(data["synonyms"])

        self.loading_entry = False

    # ---------------------------------------------------
    # Helper: select entry by id (used by graph)
    # ---------------------------------------------------
    def select_entry_by_id(self, entry_id):
        # Prevent autosave during loading
        self.loading_entry = True

        self.autosave_current_entry()
        self.current_entry_id = entry_id

        # Highlight and load entry
        for i in range(self.entry_list.count()):
            item = self.entry_list.item(i)
            if item.data(Qt.UserRole) == entry_id:
                self.entry_list.setCurrentItem(item)

                data = self.db.get_entry(entry_id)
                self.title_field.setText(data["title"])
                self.description_field.setPlainText(data["description"])
                self.category_field.setText(data["category"])
                self.tags_field.setText(data["tags"])
                self.synonyms_field.setText(data["synonyms"])

                break

        self.loading_entry = False

    # ---------------------------------------------------
    # Create a new entry
    # ---------------------------------------------------
    def create_entry(self):
        self.autosave_current_entry()
        new_id = self.db.add_entry("New Entry")
        self.load_all_entries()

        for i in range(self.entry_list.count()):
            item = self.entry_list.item(i)
            if item.data(Qt.UserRole) == new_id:
                self.entry_list.setCurrentItem(item)
                self.load_entry_details(item)
                break

    # ---------------------------------------------------
    # Save entry manually
    # ---------------------------------------------------
    def save_entry(self):
        if self.current_entry_id is None:
            return

        title = self.title_field.text()
        description = self.description_field.toPlainText()
        category = self.category_field.text()
        tags = self.tags_field.text()
        synonyms = self.synonyms_field.text()

        self.db.update_entry(
            self.current_entry_id, title, description, category, tags, synonyms
        )
        self.load_all_entries()

    # ---------------------------------------------------
    # Delete entry
    # ---------------------------------------------------
    def delete_entry(self):
        if self.current_entry_id is None:
            return

        entry_id = self.current_entry_id
        self.db.delete_entry_and_relationships(entry_id)
        self.current_entry_id = None
        self.clear_entry_fields()
        self.load_all_entries()

    # ---------------------------------------------------
    # Search
    # ---------------------------------------------------
    def run_search(self):
        query = self.search_bar.text().strip()

        if not query:
            self.load_all_entries()
            return

        entries = self.db.get_all_entries()
        results = fuzzy_search(query, entries)

        self.entry_list.clear()
        for entry_id, score in results:
            entry = self.db.get_entry(entry_id)
            if entry:
                item = QListWidgetItem(f"{entry['title']}  ({score}%)")
                item.setData(Qt.UserRole, entry_id)
                self.entry_list.addItem(item)

    # ---------------------------------------------------
    # Relationships
    # ---------------------------------------------------
    def open_relationship_editor(self):
        if self.current_entry_id is None:
            return

        self.autosave_current_entry()
        self.rel_dialog = RelationshipEditorDialog(self.db, self.current_entry_id, parent=self)
        self.rel_dialog.show()

    # ---------------------------------------------------
    # Cleanup
    # ---------------------------------------------------
    def closeEvent(self, event):
        self.autosave_current_entry()
        self.db.close()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
