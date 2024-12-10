import os
import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow, QApplication, QVBoxLayout, QHBoxLayout, 
    QWidget, QFrame, QMenuBar, QLabel, QPushButton, QMenu,
    QInputDialog, QMessageBox, QDockWidget, QLineEdit
)
from PySide6.QtGui import QFontMetricsF, QKeySequence, QAction
from gui.editor_window import EditorWindow
from gui.sidebar import SidebarIcons
from themes import WindsurfTheme
from chatgpt_api import ChatGPTAPI
from gui.ai_assistant import AIAssistant

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Übersetzungen laden
        from translations import TRANSLATIONS
        self.translations = TRANSLATIONS
        self.current_language = "Deutsch"  # Standardsprache
        
        self.setWindowTitle(self.tr("Funlight Editor"))
        
        # Fenster-Flags setzen für benutzerdefinierte Titelleiste
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        
        # Hauptfenster erstellen
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Benutzerdefinierte Titelleiste erstellen
        self.title_bar = QWidget()
        self.title_bar.setFixedHeight(30)
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(0)
        
        # Editor-Fenster erstellen
        self.editor_window = EditorWindow()
        
        # Menüleiste in die Titelleiste integrieren
        self.menubar = QMenuBar()
        self.menubar.setFixedHeight(30)
        self.menubar.setStyleSheet("""
            QMenuBar {
                background: transparent;
                color: #FFFFFF;
                border: none;
                padding: 0;
                spacing: 0;
            }
            QMenuBar::item {
                background: transparent;
                padding: 6px 10px;
                height: 30px;
                margin: 0;
            }
            QMenuBar::item:selected {
                background: rgba(255, 255, 255, 0.1);
            }
            QMenu {
                background: #2D2D2D;
                border: 1px solid #3C3C3C;
            }
            QMenu::item {
                padding: 4px 20px;
                color: #FFFFFF;
            }
            QMenu::item:selected {
                background: #094771;
            }
        """)
        
        self.create_menus()
        
        # Fenster-Titel (nach dem Menü)
        title_label = QLabel(self.tr("Funlight Editor"))
        title_label.setStyleSheet("color: #FFFFFF; padding: 0 10px;")
        
        # Fenstersteuerung
        window_controls = QWidget()
        window_controls.setFixedWidth(120)
        control_layout = QHBoxLayout(window_controls)
        control_layout.setContentsMargins(0, 0, 0, 0)
        control_layout.setSpacing(0)
        
        # Minimieren, Maximieren und Schließen Buttons
        for icon, slot in [("🗕", self.showMinimized), ("🗖", self.toggle_maximize), ("✕", self.close)]:
            btn = QPushButton(icon)
            btn.setFixedSize(40, 30)
            btn.clicked.connect(slot)
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                    color: #FFFFFF;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.1);
                }
                QPushButton:pressed {
                    background: rgba(255, 255, 255, 0.2);
                }
            """)
            control_layout.addWidget(btn)
        
        # Komponenten zur Titelleiste hinzufügen
        title_layout.addWidget(self.menubar)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(window_controls)
        
        # Titelleiste zum Hauptlayout hinzufügen
        self.main_layout.addWidget(self.title_bar)
        
        # Layout für den Hauptinhalt
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Icons für die Seitenleiste
        self.sidebar_icons = SidebarIcons(self)
        content_layout.addWidget(self.sidebar_icons)
        
        # Vertikaler Trennstrich zwischen Sidebar und Editor
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Plain)
        separator.setStyleSheet("QFrame { color: #3C3C3C; }")
        content_layout.addWidget(separator)
        
        # Editor-Fenster zum Layout hinzufügen
        content_layout.addWidget(self.editor_window)
        
        # Hauptinhalt zum Layout hinzufügen
        self.main_layout.addLayout(content_layout)
        
        # Verbindungen für die Icons
        self.sidebar_icons.page_changed.connect(self.handle_page_change)
        self.sidebar_icons.settings_clicked.connect(self.editor_window.show_settings_dialog)
        
        # Editor-Bereich maximieren
        content_layout.setStretch(2, 1)
        
        # Fenster maximieren
        self.showMaximized()
        
        # Mausverfolgungs-Variablen für Fensterbewegung
        self._drag_pos = None
        self.title_bar.mousePressEvent = self._title_bar_mouse_press
        self.title_bar.mouseMoveEvent = self._title_bar_mouse_move
        
        # ChatGPT API initialisieren
        self.init_chatgpt_api()
        
    def init_chatgpt_api(self):
        """Initialisiert die ChatGPT API."""
        self.chatgpt_api = ChatGPTAPI()
        self.setup_ai_assistant()

    def setup_ai_assistant(self):
        """Initialisiert und konfiguriert den AI Assistenten."""
        self.ai_assistant = AIAssistant(self.chatgpt_api)
        self.ai_assistant_dock = QDockWidget("AI Assistent", self)
        self.ai_assistant_dock.setWidget(self.ai_assistant)
        self.ai_assistant_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.RightDockWidgetArea, self.ai_assistant_dock)
        
        # Verbinde den AI Assistenten mit dem aktuellen Editor
        self.editor_window.tab_widget.currentChanged.connect(self._update_ai_assistant_content)
        self.ai_assistant.code_edit_requested.connect(self._handle_ai_code_edit)

    def _update_ai_assistant_content(self):
        """Aktualisiert den Code im AI Assistenten wenn sich der Editor ändert."""
        current_container = self.editor_window.get_current_editor()
        if current_container and hasattr(current_container, 'editor'):
            code = current_container.editor.toPlainText()
            self.ai_assistant.set_editor_content(code)
            # Aktualisiere auch das Theme
            is_dark = self.editor_window.current_theme == "dark"
            self.ai_assistant.apply_theme(is_dark)

    def _handle_ai_code_edit(self, new_code):
        """Verarbeitet Code-Änderungsvorschläge vom AI Assistenten."""
        current_container = self.editor_window.get_current_editor()
        if not current_container or not hasattr(current_container, 'editor'):
            return
            
        reply = QMessageBox.question(
            self,
            "Code-Änderung bestätigen",
            "Möchten Sie die vorgeschlagenen Code-Änderungen übernehmen?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            current_container.editor.setPlainText(new_code)

    def tr(self, text):
        """Übersetzt einen Text in die aktuelle Sprache."""
        if self.current_language in self.translations:
            translated = self.translations[self.current_language].get(text)
            if translated is not None:
                return translated
        return text

    def _title_bar_mouse_press(self, event):
        """Behandelt Mausklicks auf die Titelleiste."""
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def _title_bar_mouse_move(self, event):
        """Behandelt Mausbewegungen auf der Titelleiste."""
        if event.buttons() & Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            
    def toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
            
    def handle_page_change(self, index):
        """Behandelt den Wechsel zwischen Dateibaum und Suche."""
        if index == 0:
            self.editor_window.show_file_tree()
        else:
            self.editor_window.show_search()
            
    def create_menus(self):
        """Erstellt die Menüleiste mit allen Menüs."""
        # Datei-Menü
        file_menu = self.menubar.addMenu(self.tr("Datei"))
        new_action = QAction(self.tr("Neu"), self)
        new_action.setShortcut(QKeySequence.New)
        new_action.triggered.connect(self.editor_window.new_file)
        file_menu.addAction(new_action)
        
        open_action = QAction(self.tr("Öffnen"), self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self.editor_window.open_file)
        file_menu.addAction(open_action)
        
        open_folder_action = QAction(self.tr("Ordner öffnen"), self)
        open_folder_action.triggered.connect(self.editor_window.open_folder)
        file_menu.addAction(open_folder_action)
        
        file_menu.addSeparator()
        
        save_action = QAction(self.tr("Speichern"), self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.triggered.connect(self.editor_window.save_file)
        file_menu.addAction(save_action)
        
        save_as_action = QAction(self.tr("Speichern unter"), self)
        save_as_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        save_as_action.triggered.connect(self.editor_window.save_file_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction(self.tr("Beenden"), self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Bearbeiten-Menü
        edit_menu = self.menubar.addMenu(self.tr("Bearbeiten"))
        undo_action = QAction(self.tr("Rückgängig"), self)
        undo_action.setShortcut(QKeySequence.Undo)
        undo_action.triggered.connect(self.editor_window.undo)
        edit_menu.addAction(undo_action)
        
        redo_action = QAction(self.tr("Wiederholen"), self)
        redo_action.setShortcut(QKeySequence.Redo)
        redo_action.triggered.connect(self.editor_window.redo)
        edit_menu.addAction(redo_action)
        
        edit_menu.addSeparator()
        
        cut_action = QAction(self.tr("Ausschneiden"), self)
        cut_action.setShortcut(QKeySequence.Cut)
        cut_action.triggered.connect(self.editor_window.cut)
        edit_menu.addAction(cut_action)
        
        copy_action = QAction(self.tr("Kopieren"), self)
        copy_action.setShortcut(QKeySequence.Copy)
        copy_action.triggered.connect(self.editor_window.copy)
        edit_menu.addAction(copy_action)
        
        paste_action = QAction(self.tr("Einfügen"), self)
        paste_action.setShortcut(QKeySequence.Paste)
        paste_action.triggered.connect(self.editor_window.paste)
        edit_menu.addAction(paste_action)
        
        edit_menu.addSeparator()
        
        find_action = QAction(self.tr("Suchen"), self)
        find_action.setShortcut(QKeySequence.Find)
        find_action.triggered.connect(self.editor_window.show_search_dialog)
        edit_menu.addAction(find_action)
        
        replace_action = QAction(self.tr("Ersetzen"), self)
        replace_action.setShortcut(QKeySequence.Replace)
        replace_action.triggered.connect(self.editor_window.show_replace_dialog)
        edit_menu.addAction(replace_action)
        
        ai_help_action = QAction('AI Hilfe anfordern', self)
        ai_help_action.triggered.connect(self.show_ai_help_dialog)
        edit_menu.addAction(ai_help_action)

    def show_ai_help_dialog(self):
        text, ok = QInputDialog.getText(self, 'AI Hilfe anfordern', 'Gib deine Anfrage ein:')
        if ok and text:
            response = self.request_ai_help(text)
            QMessageBox.information(self, 'AI Antwort', response)

    def request_ai_help(self, prompt):
        response = self.chatgpt_api.get_response(prompt)
        if response:
            return response['choices'][0]['message']['content']
        else:
            return 'Fehler bei der Anfrage an die AI.'

    def update_current_file(self):
        """Aktualisiert die aktuelle Datei im AI Assistant."""
        editor = self.editor_window.get_current_editor()
        if editor:
            file_path = editor.file_path if hasattr(editor, 'file_path') else None
            if file_path:
                self.ai_assistant.set_current_file(file_path, editor.toPlainText())
            else:
                self.ai_assistant.set_current_file(None, editor.toPlainText())
        else:
            self.ai_assistant.set_current_file(None, "")

    def on_tab_changed(self, index):
        """Wird aufgerufen, wenn der aktive Tab sich ändert."""
        super().on_tab_changed(index)
        self.update_current_file()

    def on_file_saved(self):
        """Wird aufgerufen, wenn eine Datei gespeichert wird."""
        super().on_file_saved()
        self.update_current_file()

def main():
    app = QApplication([])
    window = MainWindow()
    window.show()
    return app.exec()

if __name__ == "__main__":
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_root)
    sys.exit(main())
