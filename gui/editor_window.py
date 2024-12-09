from PySide6.QtWidgets import (
    QMainWindow, QVBoxLayout, QWidget, QFileDialog, QSplitter,
    QTreeView, QFileSystemModel, QTabWidget, QLabel, QMenuBar,
    QMenu, QStatusBar, QDialog, QMessageBox, QInputDialog,
    QStackedWidget, QTreeWidget, QHBoxLayout, QFrame, QTabBar
)
from PySide6.QtCore import Qt, QDir, QEvent
from PySide6.QtGui import QPalette, QColor, QAction, QKeySequence
from .code_editor import CodeEditor, EditorContainer
from .dialogs.search_dialog import SearchDialog
from .dialogs.settings_dialog import SettingsDialog
from .minimap import MiniMap
from .sidebar import SearchWidget
from translations import TRANSLATIONS
import os
import sys

class EditorWindow(QMainWindow):
    """Hauptfenster des Editors."""
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Grundeinstellungen
        self.current_theme = "dark"
        self.current_language = "Deutsch"  # Standardmäßig Deutsch
        self.translations = TRANSLATIONS
        
        self.setWindowTitle(self.tr("Code Editor"))
        
        # Layout erstellen
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Container für das Layout
        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)
        
        # Stack-Widget für Dateibaum und Suche
        self.stack_widget = QStackedWidget()
        self.stack_widget.setMinimumWidth(150)
        self.stack_widget.setMaximumWidth(400)
        
        # Dateibaum
        self.file_tree = QTreeView()
        self.file_model = QFileSystemModel()
        self.file_model.setRootPath("")
        self.file_model.setNameFilters(["*.txt", "*.py", "*.json", "*.md", "*.html", "*.css", "*.js"])
        self.file_model.setNameFilterDisables(False)
        self.file_tree.setModel(self.file_model)
        self.file_tree.setRootIndex(self.file_model.index(""))
        self.file_tree.hideColumn(1)
        self.file_tree.hideColumn(2)
        self.file_tree.hideColumn(3)
        self.file_tree.setHeaderHidden(True)
        self.file_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_tree.customContextMenuRequested.connect(self.show_explorer_context_menu)
        self.file_tree.doubleClicked.connect(self.handle_file_double_click)
        
        self.search_widget = SearchWidget()
        
        self.stack_widget.addWidget(self.file_tree)
        self.stack_widget.addWidget(self.search_widget)
        
        # Haupt-Splitter zwischen Stack-Widget und Editor-Bereich
        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_splitter.setChildrenCollapsible(False)
        self.main_splitter.setHandleWidth(1)
        self.main_splitter.addWidget(self.stack_widget)
        
        # Editor-Bereich mit horizontalem Splitter
        self.editor_splitter = QSplitter(Qt.Horizontal)
        self.editor_splitter.setChildrenCollapsible(False)
        self.editor_splitter.setHandleWidth(1)
        self.main_splitter.addWidget(self.editor_splitter)
        
        # Haupt-Tab-Widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.setMinimumWidth(200)
        self.tab_widget.setAcceptDrops(True)
        self.tab_widget.tabBar().setAcceptDrops(True)
        self.tab_widget.tabBar().installEventFilter(self)
        
        # Tab-Widget dem Editor-Splitter hinzufügen
        self.editor_splitter.addWidget(self.tab_widget)
        
        # Splitter zum Layout hinzufügen
        self.layout.addWidget(self.main_splitter)
        
        # Standard-Größen einstellen
        total_width = self.width() if self.width() > 0 else 1000
        self.main_splitter.setSizes([150, total_width - 150])
        
        # Splitter-Style
        splitter_style = """
            QSplitter::handle {
                background: #3C3C3C;
            }
            QSplitter::handle:horizontal {
                width: 1px;
            }
        """
        self.main_splitter.setStyleSheet(splitter_style)
        self.editor_splitter.setStyleSheet(splitter_style)
        
        # Event-Handler für Tab-Drag
        self.tab_widget.tabBar().installEventFilter(self)
        
        # Offene Dateien und aktiver Tab
        self.open_files = {}
        self.current_file = None
        
        # UI-Einrichtung
        self.setup_status_bar()
        self.apply_theme()
        self.retranslateUi()
        
        # Fenster maximieren
        self.showMaximized()

    def setup_ui(self):
        pass

    def show_explorer_context_menu(self, position):
        """Zeigt das Kontextmenü für den Explorer an."""
        menu = QMenu()
        
        # Aktionen erstellen
        new_file_action = menu.addAction("Neue Datei")
        new_folder_action = menu.addAction("Neuer Ordner")
        menu.addSeparator()
        rename_action = menu.addAction("Umbenennen")
        delete_action = menu.addAction("Löschen")
        
        # Aktuelle Auswahl ermitteln
        index = self.file_tree.indexAt(position)
        if index.isValid():
            file_path = self.file_model.filePath(index)
            
            # Aktion ausführen
            action = menu.exec_(self.file_tree.viewport().mapToGlobal(position))
            if action == new_file_action:
                self.create_new_file(file_path)
            elif action == new_folder_action:
                self.create_new_folder(file_path)
            elif action == rename_action:
                self.rename_file(file_path)
            elif action == delete_action:
                self.delete_file(file_path)
                
    def handle_file_double_click(self, index):
        """Behandelt Doppelklicks auf Dateien im Explorer."""
        file_path = self.file_model.filePath(index)
        if os.path.isfile(file_path):
            self.load_file(file_path)
            
    def create_new_file(self, parent_path):
        """Erstellt eine neue Datei."""
        if os.path.isfile(parent_path):
            parent_path = os.path.dirname(parent_path)
            
        name, ok = QInputDialog.getText(self, "Neue Datei", "Dateiname:")
        if ok and name:
            file_path = os.path.join(parent_path, name)
            try:
                with open(file_path, 'w') as f:
                    f.write("")
                self.load_file(file_path)
            except Exception as e:
                QMessageBox.warning(self, "Fehler", f"Fehler beim Erstellen der Datei: {str(e)}")
                
    def create_new_folder(self, parent_path):
        """Erstellt einen neuen Ordner."""
        if os.path.isfile(parent_path):
            parent_path = os.path.dirname(parent_path)
            
        name, ok = QInputDialog.getText(self, "Neuer Ordner", "Ordnername:")
        if ok and name:
            folder_path = os.path.join(parent_path, name)
            try:
                os.makedirs(folder_path)
            except Exception as e:
                QMessageBox.warning(self, "Fehler", f"Fehler beim Erstellen des Ordners: {str(e)}")
                
    def rename_file(self, file_path):
        """Benennt eine Datei oder einen Ordner um."""
        old_name = os.path.basename(file_path)
        new_name, ok = QInputDialog.getText(self, "Umbenennen", "Neuer Name:", text=old_name)
        
        if ok and new_name and new_name != old_name:
            new_path = os.path.join(os.path.dirname(file_path), new_name)
            try:
                os.rename(file_path, new_path)
            except Exception as e:
                QMessageBox.warning(self, "Fehler", f"Fehler beim Umbenennen: {str(e)}")
                
    def delete_file(self, file_path):
        """Löscht eine Datei oder einen Ordner."""
        msg = "Möchten Sie diese Datei wirklich löschen?" if os.path.isfile(file_path) else "Möchten Sie diesen Ordner wirklich löschen?"
        reply = QMessageBox.question(self, "Löschen bestätigen", msg, 
                                   QMessageBox.Yes | QMessageBox.No)
                                   
        if reply == QMessageBox.Yes:
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                else:
                    import shutil
                    shutil.rmtree(file_path)
            except Exception as e:
                QMessageBox.warning(self, "Fehler", f"Fehler beim Löschen: {str(e)}")

    def setup_status_bar(self):
        """Richtet die Statusleiste ein."""
        self.status_bar = QStatusBar()
        self.status_bar.setContentsMargins(0, 0, 0, 0)  # Keine Ränder
        self.setStatusBar(self.status_bar)
        
        # Label für die Statusanzeige
        self.status_label = QLabel()
        self.status_label.setContentsMargins(5, 0, 0, 0)  # Nur kleiner Abstand links
        self.status_bar.addWidget(self.status_label, 1)  # Stretch 1 damit es sich dehnt
        
        # Linke Seite: Zeilen-Zähler
        self.line_count_label = QLabel()
        self.status_bar.addWidget(self.line_count_label)
        
        # Cursor-Position
        self.cursor_position_label = QLabel()
        self.status_bar.addPermanentWidget(self.cursor_position_label)
        
        # Copyright
        copyright_label = QLabel(" 2025 Funlight Studios")
        copyright_label.setStyleSheet("padding-right: 5px;")
        self.status_bar.addPermanentWidget(copyright_label)
        
        self.update_status_bar()

    def update_status_bar(self):
        """Aktualisiert die Statusleiste."""
        current_editor = self.get_current_editor()
        if current_editor:
            # Zeilen zählen
            text = current_editor.toPlainText()
            total_lines = text.count('\n') + 1
            code_lines = sum(1 for line in text.split('\n') if line.strip() and not line.strip().startswith('#'))
            
            # Cursor-Position
            cursor = current_editor.textCursor()
            line = cursor.blockNumber() + 1
            col = cursor.columnNumber() + 1
            
            # Status-Text aktualisieren
            self.line_count_label.setText(
                f"{self.tr('Lines')}: {total_lines} | {self.tr('Code Lines')}: {code_lines}"
            )
            self.cursor_position_label.setText(
                f"{self.tr('Line')}: {line}, {self.tr('Column')}: {col}"
            )
        else:
            self.line_count_label.setText(f"{self.tr('Lines')}: 0 | {self.tr('Code Lines')}: 0")
            self.cursor_position_label.setText("")

    def create_menu(self):
        """Erstellt die Menüleiste."""
        menubar = self.menuBar()
        
        # Datei-Menü
        file_menu = menubar.addMenu(self.tr("Datei"))
        
        new_action = QAction(self.tr("Neu"), self)
        new_action.setShortcut(QKeySequence.New)
        new_action.triggered.connect(self.new_file)
        file_menu.addAction(new_action)
        
        open_action = QAction(self.tr("Öffnen"), self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        open_folder_action = QAction(self.tr("Ordner öffnen"), self)
        open_folder_action.triggered.connect(self.open_folder)
        file_menu.addAction(open_folder_action)
        
        file_menu.addSeparator()
        
        save_action = QAction(self.tr("Speichern"), self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)
        
        save_as_action = QAction(self.tr("Speichern unter"), self)
        save_as_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        save_as_action.triggered.connect(self.save_file_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction(self.tr("Beenden"), self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Bearbeiten-Menü
        edit_menu = menubar.addMenu(self.tr("Bearbeiten"))
        
        undo_action = QAction(self.tr("Rückgängig"), self)
        undo_action.setShortcut(QKeySequence.Undo)
        undo_action.triggered.connect(self.undo)
        edit_menu.addAction(undo_action)
        
        redo_action = QAction(self.tr("Wiederholen"), self)
        redo_action.setShortcut(QKeySequence.Redo)
        redo_action.triggered.connect(self.redo)
        edit_menu.addAction(redo_action)
        
        edit_menu.addSeparator()
        
        cut_action = QAction(self.tr("Ausschneiden"), self)
        cut_action.setShortcut(QKeySequence.Cut)
        cut_action.triggered.connect(self.cut)
        edit_menu.addAction(cut_action)
        
        copy_action = QAction(self.tr("Kopieren"), self)
        copy_action.setShortcut(QKeySequence.Copy)
        copy_action.triggered.connect(self.copy)
        edit_menu.addAction(copy_action)
        
        paste_action = QAction(self.tr("Einfügen"), self)
        paste_action.setShortcut(QKeySequence.Paste)
        paste_action.triggered.connect(self.paste)
        edit_menu.addAction(paste_action)
        
        edit_menu.addSeparator()
        
        find_action = QAction(self.tr("Suchen"), self)
        find_action.setShortcut(QKeySequence.Find)
        find_action.triggered.connect(self.show_search_dialog)
        edit_menu.addAction(find_action)
        
        replace_action = QAction(self.tr("Ersetzen"), self)
        replace_action.setShortcut(QKeySequence.Replace)
        replace_action.triggered.connect(self.show_replace_dialog)
        edit_menu.addAction(replace_action)

    def create_editor(self):
        """Erstellt einen neuen Code-Editor."""
        # Container erstellen
        container = EditorContainer(self)
        
        # Tab mit Container erstellen
        index = self.tab_widget.addTab(container, "Untitled")
        self.tab_widget.setCurrentIndex(index)
        
        # Editor aus Container zurückgeben
        return container.editor

    def new_file(self):
        editor = self.create_editor()
        editor.update_theme(self.current_theme)
        editor.setProperty("file_path", "")
        self.update_status_bar()

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, self.tr("Open File"))
        if file_path:
            self.load_file(file_path)

    def open_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, self.tr("Open Folder"))
        if folder_path:
            self.file_model.setRootPath(folder_path)
            self.file_tree.setRootIndex(self.file_model.index(folder_path))

    def load_file(self, file_path):
        """Lädt eine Datei in einen neuen Tab."""
        try:
            # Prüfen ob die Datei bereits geöffnet ist
            for i in range(self.tab_widget.count()):
                editor = self.get_editor_at(i)
                if editor and editor.property("file_path") == file_path:
                    self.tab_widget.setCurrentIndex(i)
                    return

            # Datei einlesen
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()

            # Container und Editor erstellen
            container = EditorContainer(self)
            editor = container.editor
            
            # Editor konfigurieren
            editor.setPlainText(text)
            editor.setProperty("file_path", file_path)
            
            # Tab erstellen und konfigurieren
            index = self.tab_widget.addTab(container, os.path.basename(file_path))
            self.tab_widget.setCurrentIndex(index)
            
            # Theme aktualisieren
            editor.update_theme(self.current_theme == "dark")
            self.update_status_bar()
                
        except Exception as e:
            error_msg = f"Fehler beim Öffnen der Datei: {str(e)}"
            self.status_bar.showMessage(error_msg, 3000)
            print(f"Error loading file: {str(e)}")  # Für Debug-Zwecke

    def save_file(self):
        current_editor = self.get_current_editor()
        if not current_editor:
            return

        path = current_editor.property("file_path")
        if not path:
            self.save_file_as()
            return

        with open(path, "w", encoding="utf-8") as file:
            file.write(current_editor.toPlainText())

    def save_file_as(self):
        current_editor = self.get_current_editor()
        if not current_editor:
            return

        path, _ = QFileDialog.getSaveFileName(
            self, self.tr("Save As"), "",
            self.tr("All Files (*.*)")
        )
        if path:
            with open(path, "w", encoding="utf-8") as file:
                file.write(current_editor.toPlainText())
            current_editor.setProperty("file_path", path)
            self.tab_widget.setTabText(
                self.tab_widget.currentIndex(),
                os.path.basename(path)
            )

    def close_tab(self, index):
        """Schließt den Tab mit dem angegebenen Index."""
        # Bestimme das aktuelle Tab-Widget
        sender = self.sender()
        if not isinstance(sender, QTabWidget):
            return
            
        # Tab schließen
        widget = sender.widget(index)
        if widget:
            sender.removeTab(index)
            
        # Wenn das Tab-Widget leer ist und es nicht das letzte ist, entfernen
        if sender.count() == 0 and self.editor_splitter.count() > 1:
            sender.setParent(None)
            sender.deleteLater()

    def apply_theme(self):
        """Wendet das ausgewählte Theme an."""
        if self.current_theme == "dark":
            # Dark Theme Farben
            status_bg = "#1e1e1e"
            status_fg = "#d4d4d4"
            border_color = "#2d2d2d"
            
            # Dark Theme Palette
            palette = QPalette()
            palette.setColor(QPalette.Window, QColor(53, 53, 53))
            palette.setColor(QPalette.WindowText, Qt.white)
            palette.setColor(QPalette.Base, QColor(35, 35, 35))
            palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
            palette.setColor(QPalette.ToolTipBase, QColor(25, 25, 25))
            palette.setColor(QPalette.ToolTipText, Qt.white)
            palette.setColor(QPalette.Text, Qt.white)
            palette.setColor(QPalette.Button, QColor(53, 53, 53))
            palette.setColor(QPalette.ButtonText, Qt.white)
            palette.setColor(QPalette.BrightText, Qt.red)
            palette.setColor(QPalette.Link, QColor(42, 130, 218))
            palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
            palette.setColor(QPalette.HighlightedText, Qt.black)
            
            # Theme auf Anwendung anwenden
            self.setPalette(palette)
            
            # Rest des Dark Theme Codes...
            self.setStyleSheet("""
                QMainWindow, QDialog {
                    background-color: #1e1e1e;
                    color: #d4d4d4;
                }
                QTreeView {
                    background-color: #1e1e1e;
                    color: #d4d4d4;
                    border: none;
                }
                QTreeView::item:selected {
                    background-color: #264f78;
                }
                QTreeView::item:hover {
                    background-color: #2a2d2e;
                }
                QTreeView::branch {
                    background-color: #1e1e1e;
                }
                QTreeView::branch:has-siblings:!adjoins-item {
                    border-image: url(vline.png) 0;
                }
                QTreeView::branch:has-siblings:adjoins-item {
                    border-image: url(branch-more.png) 0;
                }
                QTreeView::branch:!has-children:!has-siblings:adjoins-item {
                    border-image: url(branch-end.png) 0;
                }
                QTreeView::branch:has-children:!has-siblings:closed,
                QTreeView::branch:closed:has-children:has-siblings {
                    border-image: none;
                    image: url(branch-closed.png);
                }
                QTreeView::branch:open:has-children:!has-siblings,
                QTreeView::branch:open:has-children:has-siblings {
                    border-image: none;
                    image: url(branch-open.png);
                }
                QTreeView QHeaderView::section {
                    background-color: #252526;
                    color: #d4d4d4;
                    border: none;
                    padding: 4px;
                }
                QTabWidget::pane {
                    border: none;
                    background-color: #1e1e1e;
                }
                QTabBar::tab {
                    background-color: #2d2d2d;
                    color: #d4d4d4;
                    padding: 8px 12px;
                    border: none;
                    border-top-left-radius: 4px;
                    border-top-right-radius: 4px;
                    margin-right: 2px;
                }
                QTabBar::tab:selected {
                    background-color: #1e1e1e;
                }
                QTabBar::tab:hover:!selected {
                    background-color: #404040;
                }
                QStatusBar {
                    background-color: #1e1e1e;
                    color: #d4d4d4;
                    border-top: 2px solid #2d2d2d;
                }
                QStatusBar QLabel {
                    color: #d4d4d4;
                    background: transparent;
                    padding: 3px;
                }
                QStatusBar::item {
                    border: none;
                }
                QLabel {
                    color: #d4d4d4;
                    background: transparent;
                }
                QMenuBar {
                    background-color: #1e1e1e;
                    color: #d4d4d4;
                    border: none;
                }
                QMenuBar::item {
                    background-color: transparent;
                    padding: 4px 8px;
                }
                QMenuBar::item:selected {
                    background-color: #2d2d2d;
                }
                QMenu {
                    background-color: #1e1e1e;
                    color: #d4d4d4;
                    border: 1px solid #2d2d2d;
                }
                QMenu::item {
                    padding: 4px 20px;
                }
                QMenu::item:selected {
                    background-color: #264f78;
                }
                QMenu::separator {
                    height: 1px;
                    background-color: #2d2d2d;
                    margin: 4px 0;
                }
                QLineEdit, QSpinBox, QComboBox {
                    background-color: #3c3c3c;
                    color: #d4d4d4;
                    border: 1px solid #2d2d2d;
                    padding: 4px;
                    border-radius: 2px;
                }
                QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
                    border: 1px solid #007acc;
                }
                QComboBox::drop-down {
                    border: none;
                    width: 20px;
                }
                QComboBox::down-arrow {
                    image: url(down-arrow.png);
                }
                QCheckBox {
                    color: #d4d4d4;
                }
                QCheckBox::indicator {
                    width: 13px;
                    height: 13px;
                }
                QCheckBox::indicator:unchecked {
                    border: 1px solid #d4d4d4;
                    background-color: #1e1e1e;
                }
                QCheckBox::indicator:checked {
                    border: 1px solid #007acc;
                    background-color: #007acc;
                }
                QPushButton {
                    background-color: #0e639c;
                    color: white;
                    border: none;
                    padding: 6px 12px;
                    border-radius: 2px;
                }
                QPushButton:hover {
                    background-color: #1177bb;
                }
                QPushButton:pressed {
                    background-color: #094771;
                }
                QScrollBar:vertical {
                    border: none;
                    background-color: #1e1e1e;
                    width: 14px;
                    margin: 0;
                }
                QScrollBar::handle:vertical {
                    background-color: #424242;
                    min-height: 20px;
                }
                QScrollBar::handle:vertical:hover {
                    background-color: #686868;
                }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                    border: none;
                    background: none;
                }
                QScrollBar:horizontal {
                    border: none;
                    background-color: #1e1e1e;
                    height: 14px;
                    margin: 0;
                }
                QScrollBar::handle:horizontal {
                    background-color: #424242;
                    min-width: 20px;
                }
                QScrollBar::handle:horizontal:hover {
                    background-color: #686868;
                }
                QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                    border: none;
                    background: none;
                }
                QGroupBox {
                    border: 1px solid #2d2d2d;
                    border-radius: 4px;
                    margin-top: 8px;
                    padding-top: 8px;
                    color: #d4d4d4;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    subcontrol-position: top left;
                    left: 8px;
                    padding: 0 3px;
                }
            """)
        else:
            # Light Theme
            self.setPalette(self.style().standardPalette())
            self.setStyleSheet("""
                QStatusBar {
                    background-color: #f0f0f0;
                    color: #000000;
                    border-top: 2px solid #d0d0d0;
                }
                QStatusBar QLabel {
                    color: #000000;
                    background: transparent;
                    padding: 3px;
                }
                QStatusBar::item {
                    border: none;
                }
            """)

        # Theme auf alle offenen Editoren anwenden
        self.update_editor_themes()

    def undo(self):
        if editor := self.get_current_editor():
            editor.undo()

    def redo(self):
        if editor := self.get_current_editor():
            editor.redo()

    def cut(self):
        if editor := self.get_current_editor():
            editor.cut()

    def copy(self):
        if editor := self.get_current_editor():
            editor.copy()

    def paste(self):
        if editor := self.get_current_editor():
            editor.paste()

    def show_search_dialog(self):
        """Zeigt den Suchdialog."""
        current_editor = self.get_current_editor()
        if current_editor:
            dialog = SearchDialog(self)
            dialog.search_requested.connect(current_editor.find_text)
            dialog.exec()

    def show_replace_dialog(self):
        """Zeigt den Ersetzen-Dialog."""
        current_editor = self.get_current_editor()
        if current_editor:
            dialog = SearchDialog(self, replace_mode=True)
            dialog.search_requested.connect(current_editor.find_text)
            dialog.replace_requested.connect(current_editor.replace_text)
            dialog.replace_all_requested.connect(current_editor.replace_all_text)
            dialog.exec()

    def find_text(self, text, case_sensitive=False, whole_words=False, search_forward=True):
        """Sucht Text im aktuellen Editor."""
        current_editor = self.get_current_editor()
        if current_editor:
            current_editor.find_text(text, case_sensitive, whole_words, search_forward)

    def replace_text(self, find_text, replace_text, case_sensitive=False, whole_words=False):
        """Ersetzt Text im aktuellen Editor."""
        current_editor = self.get_current_editor()
        if current_editor:
            current_editor.replace_text(find_text, replace_text, case_sensitive, whole_words)

    def replace_all_text(self, find_text, replace_text, case_sensitive=False, whole_words=False):
        """Ersetzt allen Text im aktuellen Editor."""
        current_editor = self.get_current_editor()
        if current_editor:
            current_editor.replace_all_text(find_text, replace_text, case_sensitive, whole_words)

    def retranslateUi(self):
        """Aktualisiert alle übersetzbaren Texte."""
        # Fenster-Titel
        self.setWindowTitle(self.tr("Code Editor"))
        
        # Menü-Titel aktualisieren
        menubar = self.menuBar()
        for action in menubar.actions():
            menu = action.menu()
            if menu:
                # Hauptmenü-Titel übersetzen
                action.setText(self.tr(action.text()))
                
                # Untermenü-Einträge übersetzen
                for subaction in menu.actions():
                    if not subaction.isSeparator():
                        subaction.setText(self.tr(subaction.text()))
        
        # Tab-Titel aktualisieren
        for i in range(self.tab_widget.count()):
            self.tab_widget.setTabText(i, self.tr(self.tab_widget.tabText(i)))
            
        # Status-Bar aktualisieren
        if hasattr(self, 'statusBar'):
            for widget in self.statusBar().findChildren(QLabel):
                if widget.objectName():  # Nur benannte Widgets übersetzen
                    widget.setText(self.tr(widget.text()))

    def tr(self, text):
        """Übersetzt einen Text in die aktuelle Sprache."""
        if self.current_language in self.translations:
            translated = self.translations[self.current_language].get(text)
            if translated is not None:
                return translated
            print(f"Warning: No translation found for '{text}' in language '{self.current_language}'")
        return text

    def get_current_editor(self):
        """Gibt den aktuellen Editor zurück."""
        current_tab = self.tab_widget.currentWidget()
        if current_tab and hasattr(current_tab, 'editor'):
            return current_tab.editor
        return None

    def get_editor_at(self, index):
        """Gibt den Editor am angegebenen Tab-Index zurück."""
        widget = self.tab_widget.widget(index)
        if isinstance(widget, EditorContainer):
            return widget.editor
        return None

    def update_editor_themes(self):
        """Aktualisiert das Theme für alle Editor-Instanzen."""
        for i in range(self.tab_widget.count()):
            editor = self.get_editor_at(i)
            if editor:
                editor.update_theme(self.current_theme == "dark")

    def show_file_tree(self):
        """Zeigt den Dateibaum an."""
        self.stack_widget.setCurrentWidget(self.file_tree)
    
    def show_search(self):
        """Zeigt die Suche an und setzt den Fokus."""
        self.stack_widget.setCurrentWidget(self.search_widget)
        # Aktuellen Editor an die Suche übergeben
        current_editor = self.get_current_editor()
        if current_editor:
            self.search_widget.set_editor(current_editor)
        self.search_widget.search_input.setFocus()

    def get_current_editor(self):
        """Gibt den aktuellen Editor zurück."""
        current_tab = self.tab_widget.currentWidget()
        if current_tab and hasattr(current_tab, 'editor'):
            return current_tab.editor
        return None

    def show_settings_dialog(self):
        """Zeigt den Einstellungen-Dialog an."""
        dialog = SettingsDialog(self)
        if dialog.exec() == QDialog.Accepted:  
            settings = dialog.get_settings()
            
            # Sprache ändern, ohne das Theme zu beeinflussen
            if settings["language"] != self.current_language:
                self.current_language = settings["language"]
                self.retranslateUi()
            
            # Theme nur ändern, wenn es explizit im Dialog geändert wurde
            theme_changed = False
            if settings["theme"] == "dark" and self.current_theme != "dark":
                self.current_theme = "dark"
                theme_changed = True
            elif settings["theme"] == "light" and self.current_theme != "light":
                self.current_theme = "light"
                theme_changed = True
            
            if theme_changed:
                self.apply_theme()
            
            # Editor-Einstellungen anwenden
            for i in range(self.tab_widget.count()):
                editor = self.get_editor_at(i)
                if editor:
                    font = editor.font()
                    font.setPointSize(settings["font_size"])
                    editor.setFont(font)
                    editor.setTabStopDistance(settings["tab_size"] * editor.fontMetrics().horizontalAdvance(' '))
                    if hasattr(editor, "auto_indent"):
                        editor.auto_indent = settings["auto_indent"]

    def eventFilter(self, obj, event):
        """Event-Filter für Tab-Drag-Operationen."""
        # Prüfen ob das Event von einer TabBar kommt
        if isinstance(obj, QTabBar):
            tab_widget = obj.parent()
            
            if event.type() == QEvent.Type.MouseMove and event.buttons() == Qt.LeftButton:
                # Position des Mauszeigers relativ zum Tab-Widget
                pos = event.pos()
                widget_width = tab_widget.width()
                
                # Wenn wir im ersten Tab-Widget sind
                if tab_widget == self.tab_widget:
                    # Nur splitten, wenn der Mauszeiger in der rechten Hälfte ist
                    if pos.x() > widget_width * 0.75:  # Erst ab 75% der Breite
                        if self.editor_splitter.count() == 1:
                            # Visuellen Indikator für Split-Möglichkeit anzeigen
                            tab_widget.setStyleSheet("""
                                QTabWidget::pane {
                                    border-right: 2px solid #007ACC;
                                }
                            """)
                            
                            # Neues Tab-Widget erstellen
                            new_tab_widget = QTabWidget()
                            new_tab_widget.setTabsClosable(True)
                            new_tab_widget.setMovable(True)
                            new_tab_widget.setDocumentMode(True)
                            new_tab_widget.setMinimumWidth(200)
                            new_tab_widget.setAcceptDrops(True)
                            new_tab_widget.tabBar().setAcceptDrops(True)
                            new_tab_widget.tabCloseRequested.connect(self.close_tab)
                            new_tab_widget.tabBar().installEventFilter(self)
                            
                            # Dem Splitter hinzufügen
                            self.editor_splitter.addWidget(new_tab_widget)
                            
                            # Größen gleichmäßig verteilen
                            width = self.editor_splitter.width()
                            self.editor_splitter.setSizes([width//2, width//2])
                            
                            # Tab verschieben
                            current_index = tab_widget.currentIndex()
                            if current_index >= 0:
                                tab = tab_widget.widget(current_index)
                                text = tab_widget.tabText(current_index)
                                tab_widget.removeTab(current_index)
                                new_tab_widget.addTab(tab, text)
                                new_tab_widget.setCurrentWidget(tab)
                    else:
                        # Visuellen Indikator entfernen
                        tab_widget.setStyleSheet("")
                # Wenn wir im zweiten Tab-Widget sind
                else:
                    # Wenn der Mauszeiger in der linken Hälfte ist
                    if pos.x() < widget_width * 0.25:  # Erste 25% der Breite
                        # Visuellen Indikator für Merge-Möglichkeit anzeigen
                        self.tab_widget.setStyleSheet("""
                            QTabWidget::pane {
                                border-left: 2px solid #007ACC;
                            }
                        """)
                        
                        # Tab verschieben und Widgets zusammenführen
                        current_index = tab_widget.currentIndex()
                        if current_index >= 0:
                            tab = tab_widget.widget(current_index)
                            text = tab_widget.tabText(current_index)
                            tab_widget.removeTab(current_index)
                            self.tab_widget.addTab(tab, text)
                            
                            # Wenn das zweite Tab-Widget leer ist, entfernen
                            if tab_widget.count() == 0:
                                tab_widget.setParent(None)
                                tab_widget.deleteLater()
                    else:
                        # Visuellen Indikator entfernen
                        self.tab_widget.setStyleSheet("")
                        
            elif event.type() == QEvent.Type.MouseButtonRelease:
                # Alle visuellen Indikatoren beim Loslassen entfernen
                self.tab_widget.setStyleSheet("")
                if self.editor_splitter.count() > 1:
                    self.editor_splitter.widget(1).setStyleSheet("")
        
        return super().eventFilter(obj, event)
