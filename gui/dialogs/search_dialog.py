from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QCheckBox
)
from PySide6.QtCore import Signal

class SearchDialog(QDialog):
    """Dialog für Suchen und Ersetzen."""
    
    # Signale für Suchanfragen
    search_requested = Signal(str, bool, bool, bool)  # text, case_sensitive, whole_words, search_forward
    replace_requested = Signal(str, str, bool, bool)  # find_text, replace_text, case_sensitive, whole_words
    replace_all_requested = Signal(str, str, bool, bool)  # find_text, replace_text, case_sensitive, whole_words

    def __init__(self, parent=None, replace_mode=False):
        super().__init__(parent)
        self.replace_mode = replace_mode
        self.setup_ui()
        self.setWindowTitle(self.tr("Find and Replace") if replace_mode else self.tr("Find"))

    def setup_ui(self):
        """Erstellt die UI-Elemente."""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Sucheingabe
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel(self.tr("Search for:")))
        self.search_input = QLineEdit()
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # Ersetzen-Eingabe (nur im Ersetzen-Modus)
        if self.replace_mode:
            replace_layout = QHBoxLayout()
            replace_layout.addWidget(QLabel(self.tr("Replace with:")))
            self.replace_input = QLineEdit()
            replace_layout.addWidget(self.replace_input)
            layout.addLayout(replace_layout)

        # Optionen
        options_layout = QHBoxLayout()
        self.case_sensitive = QCheckBox(self.tr("Match Case"))
        self.whole_words = QCheckBox(self.tr("Whole Word"))
        options_layout.addWidget(self.case_sensitive)
        options_layout.addWidget(self.whole_words)
        layout.addLayout(options_layout)

        # Buttons
        button_layout = QHBoxLayout()
        
        # Suchen-Buttons
        find_next = QPushButton(self.tr("Find Next"))
        find_next.clicked.connect(self.find_next)
        button_layout.addWidget(find_next)

        find_prev = QPushButton(self.tr("Find Previous"))
        find_prev.clicked.connect(self.find_previous)
        button_layout.addWidget(find_prev)

        # Ersetzen-Buttons (nur im Ersetzen-Modus)
        if self.replace_mode:
            replace_button = QPushButton(self.tr("Replace"))
            replace_button.clicked.connect(self.replace)
            button_layout.addWidget(replace_button)

            replace_all = QPushButton(self.tr("Replace All"))
            replace_all.clicked.connect(self.replace_all)
            button_layout.addWidget(replace_all)

        # Schließen-Button
        close_button = QPushButton(self.tr("Close"))
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)

        layout.addLayout(button_layout)

    def find_next(self):
        """Sucht den nächsten Treffer."""
        self.search_requested.emit(
            self.search_input.text(),
            self.case_sensitive.isChecked(),
            self.whole_words.isChecked(),
            True  # search_forward
        )

    def find_previous(self):
        """Sucht den vorherigen Treffer."""
        self.search_requested.emit(
            self.search_input.text(),
            self.case_sensitive.isChecked(),
            self.whole_words.isChecked(),
            False  # search_forward
        )

    def replace(self):
        """Ersetzt den aktuellen Treffer."""
        if self.replace_mode:
            self.replace_requested.emit(
                self.search_input.text(),
                self.replace_input.text(),
                self.case_sensitive.isChecked(),
                self.whole_words.isChecked()
            )

    def replace_all(self):
        """Ersetzt alle Treffer."""
        if self.replace_mode:
            self.replace_all_requested.emit(
                self.search_input.text(),
                self.replace_input.text(),
                self.case_sensitive.isChecked(),
                self.whole_words.isChecked()
            )
