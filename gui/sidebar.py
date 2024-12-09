from PySide6.QtWidgets import (QWidget, QVBoxLayout, QToolButton, 
                                 QStackedWidget, QLineEdit, QTreeWidget,
                                 QHBoxLayout, QPushButton, QLabel, QTreeWidgetItem,
                                 QTextEdit, QFrame)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QFont, QTextCursor, QTextFormat, QColor

class SidebarIcons(QWidget):
    """Vertikale Leiste mit Icons für Dateibaum und Suche."""
    page_changed = Signal(int)
    settings_clicked = Signal()  # Neues Signal für Einstellungen
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(40)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Icons für die Seitenleiste
        self.file_tree_button = QToolButton(self)
        self.file_tree_button.setIcon(QIcon.fromTheme("folder", QIcon("🗀")))
        self.file_tree_button.setToolTip("Dateibaum")
        self.file_tree_button.setCheckable(True)
        self.file_tree_button.setChecked(True)  # Standardmäßig aktiv
        self.file_tree_button.clicked.connect(lambda: self.handle_button_click(0))
        
        self.search_button = QToolButton(self)
        self.search_button.setIcon(QIcon.fromTheme("edit-find", QIcon("🔍")))
        self.search_button.setToolTip("Suchen")
        self.search_button.setCheckable(True)
        self.search_button.clicked.connect(lambda: self.handle_button_click(1))
        
        # Einstellungs-Button
        self.settings_button = QToolButton(self)
        self.settings_button.setIcon(QIcon("resources/icons/settings.png"))
        self.settings_button.setToolTip("Einstellungen")
        self.settings_button.clicked.connect(lambda: self.settings_clicked.emit())
        
        # Buttons zur Layout hinzufügen
        self.layout.addWidget(self.file_tree_button)
        self.layout.addWidget(self.search_button)
        self.layout.addStretch()  # Schiebt den Settings-Button nach unten
        self.layout.addWidget(self.settings_button)
        
        # Liste aller umschaltbaren Buttons
        self.buttons = [self.file_tree_button, self.search_button]
        
        # Styling
        self.setStyleSheet("""
            QToolButton {
                border: none;
                padding: 10px;
                margin: 0;
            }
            QToolButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            QToolButton:checked {
                background-color: rgba(255, 255, 255, 0.2);
            }
        """)
        
    def handle_button_click(self, index):
        """Behandelt Klicks auf die Buttons und aktualisiert den aktiven Zustand."""
        # Alle Buttons deaktivieren
        for button in self.buttons:
            button.setChecked(False)
            
        # Angeklickten Button aktivieren
        self.buttons[index].setChecked(True)
        
        # Style aktualisieren
        self.style().unpolish(self)
        self.style().polish(self)
        
        # Signal senden
        self.page_changed.emit(index)

    def set_active_button(self, index):
        """Setzt den aktiven Button von außen."""
        self.handle_button_click(index)

class SearchWidget(QWidget):
    """Widget für die Suche und Ersetzen-Funktionalität."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 0)
        self.layout.setSpacing(2)
        
        # Suchfeld mit Clear-Button
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("Suchen...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self.handle_search)
        
        # Ersetzen-Container
        replace_container = QWidget()
        replace_layout = QHBoxLayout(replace_container)
        replace_layout.setContentsMargins(0, 0, 0, 0)
        replace_layout.setSpacing(2)
        
        # Ersetzen-Feld mit Clear-Button
        self.replace_input = QLineEdit(self)
        self.replace_input.setPlaceholderText("Ersetzen mit...")
        self.replace_input.setClearButtonEnabled(True)
        self.replace_input.textChanged.connect(self.update_replace_preview)
        
        # Ersetzen-Button
        self.replace_button = QPushButton("Ersetzen", self)
        self.replace_button.setFixedWidth(70)
        self.replace_button.clicked.connect(self.replace_current)
        
        # Ersetzen-Alles-Button
        self.replace_all_button = QPushButton("Alle", self)
        self.replace_all_button.setFixedWidth(50)
        self.replace_all_button.clicked.connect(self.replace_all)
        
        # Extra-Selections für Hervorhebungen
        self.search_selections = []
        self.replace_selections = []
        
        # Buttons zum Replace-Layout hinzufügen
        replace_layout.addWidget(self.replace_input)
        replace_layout.addWidget(self.replace_button)
        replace_layout.addWidget(self.replace_all_button)
        
        # Ergebnisliste
        self.results_tree = QTreeWidget(self)
        self.results_tree.setHeaderHidden(True)
        self.results_tree.itemClicked.connect(self.handle_result_click)
        
        # Widgets zum Layout hinzufügen
        self.layout.addWidget(self.search_input)
        self.layout.addWidget(replace_container)
        self.layout.addWidget(self.results_tree)
        
        # Status-Label für Anzahl der Treffer
        self.status_label = QLabel("", self)
        self.status_label.setStyleSheet("color: #888;")
        self.layout.addWidget(self.status_label)
        
        self.setStyleSheet("""
            QLineEdit {
                padding: 5px;
                border: 1px solid #3C3C3C;
                background: #252526;
                color: #D4D4D4;
            }
            QLineEdit:focus {
                border: 1px solid #007ACC;
            }
            QPushButton {
                background: #0E639C;
                border: none;
                padding: 4px 8px;
                color: white;
            }
            QPushButton:hover {
                background: #1177BB;
            }
            QPushButton:pressed {
                background: #094771;
            }
            QTreeWidget {
                background: #252526;
                border: none;
                color: #D4D4D4;
            }
            QTreeWidget::item:hover {
                background: rgba(255, 255, 255, 0.1);
            }
            QTreeWidget::item:selected {
                background: #094771;
            }
        """)
        
        self.editor = None
        self.current_results = []
    
    def set_editor(self, editor):
        """Setzt den aktuellen Editor für die Suche."""
        self.editor = editor
        if self.search_input.text():
            self.handle_search(self.search_input.text())
    
    def handle_search(self, text):
        """Führt die Suche durch und aktualisiert die Ergebnisliste."""
        # Alles zurücksetzen
        self.results_tree.clear()
        self.current_results.clear()
        self.search_selections.clear()
        self.replace_selections.clear()
        self.editor.setExtraSelections([])
        self.status_label.setText("")
        
        if not self.editor or not text:
            return
        
        # Suche im aktuellen Dokument
        document = self.editor.document()
        cursor = QTextCursor(document)
        
        # Suche durchführen
        while True:
            cursor = document.find(text, cursor)
            if cursor.isNull():
                break
                
            # Position speichern
            block_number = cursor.blockNumber()
            block = document.findBlockByNumber(block_number)
            line_text = block.text()
            
            # Ergebnis zur Liste hinzufügen
            result_item = QTreeWidgetItem(self.results_tree)
            result_item.setText(0, f"Zeile {block_number + 1}: {line_text}")
            result_item.setData(0, Qt.UserRole, {
                'block': block_number,
                'column': cursor.positionInBlock() - len(text),
                'length': len(text)
            })
            
            # Suchvorkommen grün hervorheben
            selection = QTextEdit.ExtraSelection()
            selection.format.setBackground(QColor(0, 255, 0, 30))  # Leicht grün
            selection.cursor = QTextCursor(cursor)
            self.search_selections.append(selection)
            
            # Position für spätere Verwendung speichern
            self.current_results.append(cursor.position())
        
        # Status aktualisieren
        count = len(self.current_results)
        self.status_label.setText(f"{count} {'Treffer' if count != 1 else 'Treffer'}")
        
        # Hervorhebungen aktualisieren
        if self.search_selections:
            self.editor.setExtraSelections(self.search_selections)
            
        # Wenn Ersetzungstext vorhanden, auch die Vorschau aktualisieren
        if self.replace_input.text():
            self.update_replace_preview()

    def update_replace_preview(self):
        """Aktualisiert die Vorschau für das Ersetzen."""
        if not self.editor or not self.search_input.text() or not self.replace_input.text():
            # Wenn kein Ersetzungstext, behalte die normalen Suchmarkierungen
            if self.search_selections:
                self.editor.setExtraSelections(self.search_selections)
            return
            
        search_text = self.search_input.text()
        replace_text = self.replace_input.text()
        document = self.editor.document()
        
        # Die vorhandenen grünen Suchmarkierungen kopieren und Tooltip hinzufügen
        all_selections = []
        for selection in self.search_selections:
            new_selection = QTextEdit.ExtraSelection()
            new_selection.format = selection.format  # Grüne Markierung übernehmen
            new_selection.cursor = QTextCursor(selection.cursor)
            new_selection.format.setToolTip(f"→ {replace_text}")
            all_selections.append(new_selection)
        
        # Alle Markierungen auf einmal setzen
        self.editor.setExtraSelections(all_selections)

    def handle_result_click(self, item):
        """Springt zum ausgewählten Suchergebnis."""
        if not self.editor:
            return
            
        data = item.data(0, Qt.UserRole)
        if data:
            cursor = self.editor.textCursor()
            block = self.editor.document().findBlockByNumber(data['block'])
            pos = block.position() + data['column']
            cursor.setPosition(pos)
            cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, data['length'])
            self.editor.setTextCursor(cursor)
            self.editor.setFocus()
    
    def replace_current(self):
        """Ersetzt das aktuelle Vorkommen."""
        if not self.editor or not self.current_results:
            return
            
        cursor = self.editor.textCursor()
        if cursor.hasSelection():
            cursor.insertText(self.replace_input.text())
            self.handle_search(self.search_input.text())  # Liste und Highlights aktualisieren
    
    def replace_all(self):
        """Ersetzt alle Vorkommen."""
        if not self.editor or not self.current_results:
            return
            
        # Alle Vorkommen ersetzen
        cursor = self.editor.textCursor()
        cursor.beginEditBlock()
        
        for _ in range(len(self.current_results)):
            cursor = self.editor.document().find(self.search_input.text(), cursor)
            if cursor.isNull():
                break
            cursor.insertText(self.replace_input.text())
        
        cursor.endEditBlock()
        self.handle_search(self.search_input.text())  # Liste und Highlights aktualisieren

class Sidebar(QWidget):
    """Hauptwidget für die Seitenleiste mit Icons und Stack-Widget."""
    search_triggered = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(300)  # Gesamtbreite der Sidebar
        
        # Hauptlayout
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Icons
        self.icons = SidebarIcons(self)
        self.layout.addWidget(self.icons)
        
        # Vertikaler Trennstrich nach den Icons
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Plain)
        separator.setStyleSheet("QFrame { color: #3C3C3C; }")
        self.layout.addWidget(separator)
        
        # Stack-Widget für Dateibaum und Suche
        self.stack = QStackedWidget(self)
        self.file_tree = QTreeWidget(self)
        self.file_tree.setHeaderHidden(True)
        self.search_widget = SearchWidget(self)
        
        self.stack.addWidget(self.file_tree)
        self.stack.addWidget(self.search_widget)
        
        self.layout.addWidget(self.stack)
        
        # Verbindungen
        self.icons.page_changed.connect(self.show_page)
        self.icons.settings_clicked.connect(self.show_settings)
        
        # Styling
        self.setStyleSheet("""
            Sidebar {
                background: #252526;
            }
            QTreeWidget {
                background: #252526;
                border: none;
                color: #D4D4D4;
            }
            QTreeWidget::item {
                padding: 2px;
            }
            QTreeWidget::item:hover {
                background: rgba(255, 255, 255, 0.1);
            }
            QTreeWidget::item:selected {
                background: #094771;
            }
        """)
    
    def show_page(self, index):
        """Wechselt zur Seite mit dem angegebenen Index."""
        self.stack.setCurrentIndex(index)
        if index == 1:
            self.search_widget.search_input.setFocus()

    def show_settings(self):
        """Öffnet die Einstellungen."""
        print("Einstellungen geöffnet")
