from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, QPushButton,
    QHBoxLayout, QLabel, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QTextCursor, QPalette, QColor, QKeyEvent

class AIAssistant(QFrame):
    code_edit_requested = Signal(str)  # Signal für Code-Änderungen

    def __init__(self, chatgpt_api, parent=None):
        super().__init__(parent)
        self.chatgpt_api = chatgpt_api
        self.current_code = ""
        self.current_file = None
        self.setup_ui()
        self.apply_theme(True)  # Standard: Dark Theme

    def setup_ui(self):
        """Erstellt das UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Chat-Ausgabefeld
        self.output_field = QTextEdit()
        self.output_field.setReadOnly(True)
        self.output_field.setStyleSheet("QTextEdit { padding: 10px; }")
        layout.addWidget(self.output_field)

        # Willkommensnachricht
        welcome_message = (
            "👋 Willkommen! Ich bin Funlight AI, Ihr intelligenter Coding-Assistent.\n\n"
            "Ich kann Ihnen helfen mit:\n"
            "💻 Code-Analyse und Verbesserungen\n"
            "🔧 Direkten Code-Änderungen\n"
            "❓ Programmier-Fragen\n"
            "💬 Allgemeinen Gesprächen\n\n"
            "Schreiben Sie einfach Ihre Frage oder Anweisung - ich bin hier, um zu helfen!\n"
        )
        self.output_field.append(welcome_message)

        # Eingabebereich
        input_container = QFrame()
        input_container.setStyleSheet("QFrame { background: rgba(40, 40, 40, 0.6); border-radius: 5px; }")
        input_layout = QVBoxLayout(input_container)
        input_layout.setContentsMargins(15, 15, 15, 15)
        input_layout.setSpacing(10)

        # Buttons in einer horizontalen Leiste
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # Button-Stile
        button_style = """
            QPushButton {
                background: #3c3c3c;
                border: none;
                padding: 5px 15px;
                border-radius: 3px;
                color: #ffffff;
            }
            QPushButton:hover {
                background: #4c4c4c;
            }
            QPushButton:pressed {
                background: #2c2c2c;
            }
        """
        
        self.analyze_button = QPushButton("Analysieren")
        self.suggest_button = QPushButton("Vorschläge")
        self.edit_button = QPushButton("Bearbeiten")
        
        for button in [self.analyze_button, self.suggest_button, self.edit_button]:
            button.setStyleSheet(button_style)
            button.clicked.connect(self.get_suggestions)
            button_layout.addWidget(button)
            
        input_layout.addLayout(button_layout)

        # Eingabefeld
        self.input_field = QTextEdit()
        self.input_field.setPlaceholderText("Stelle eine Frage oder gib eine Anweisung...")
        self.input_field.setMinimumHeight(40)
        self.input_field.setMaximumHeight(80)
        self.input_field.setStyleSheet("""
            QTextEdit {
                background: #2d2d2d;
                border: 1px solid #3c3c3c;
                border-radius: 3px;
                padding: 5px;
                color: #ffffff;
            }
        """)
        self.input_field.installEventFilter(self)
        input_layout.addWidget(self.input_field)

        layout.addWidget(input_container)
        layout.setStretchFactor(self.output_field, 1)
        layout.setStretchFactor(input_container, 0)

    def eventFilter(self, obj, event):
        if obj == self.input_field and isinstance(event, QKeyEvent):
            if event.key() == Qt.Key_Return and not event.modifiers() & Qt.ShiftModifier:
                # Enter ohne Shift startet die Analyse
                self.get_suggestions()
                return True
            elif event.key() == Qt.Key_Return and event.modifiers() & Qt.ShiftModifier:
                # Shift+Enter für neue Zeile
                cursor = self.input_field.textCursor()
                cursor.insertText("\\n")
                return True
        return super().eventFilter(obj, event)

    def apply_theme(self, is_dark=True):
        if is_dark:
            # Dark Theme (Windsurf Style)
            bg_color = "#1e1e1e"
            text_color = "#d4d4d4"
            input_bg = "#2d2d2d"
            button_bg = "#3c3c3c"
            button_hover = "#4a4a4a"
            border_color = "#3c3c3c"
        else:
            # Light Theme
            bg_color = "#ffffff"
            text_color = "#000000"
            input_bg = "#f5f5f5"
            button_bg = "#e0e0e0"
            button_hover = "#d0d0d0"
            border_color = "#cccccc"

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                color: {text_color};
                border: none;
            }}
            QTextEdit {{
                background-color: {input_bg};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 3px;
                padding: 5px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 12px;
            }}
            QPushButton {{
                background-color: {button_bg};
                color: {text_color};
                border: none;
                padding: 5px 15px;
                border-radius: 3px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {button_hover};
            }}
        """)

    def set_editor_content(self, content):
        """Aktualisiert den gespeicherten Code."""
        self.current_code = content

    def set_current_file(self, file_path, code):
        """Setzt die aktuelle Datei und den Code."""
        self.current_file = file_path
        self.current_code = code

    def analyze_current_code(self):
        """Analysiert den aktuellen Code."""
        if not self.current_code or self.current_code.strip() == "":
            self.output_field.append("🤖 Funlight AI: Es ist aktuell keine Datei geöffnet. "
                                   "Wie kann ich Ihnen anderweitig helfen?\n")
            return
            
        self.output_field.append("🔍 Code-Analyse angefordert...")
        analysis = self.chatgpt_api.analyze_code(self.current_code)
        self.output_field.append(f"🤖 Funlight AI: {analysis}\n")

    def get_suggestions(self):
        """Verarbeitet die Benutzereingabe."""
        query = self.input_field.toPlainText().strip()
        if not query:
            self.output_field.append("🤖 Funlight AI: Bitte geben Sie eine Frage oder Anweisung ein.\n")
            return
        
        self.output_field.append(f"💬 Sie: {query}")
        
        # Hole den aktuellen Code-Kontext, falls vorhanden
        code_context = None
        if self.current_code.strip():
            code_context = f"Datei: {self.current_file}\n\nCode:\n{self.current_code}"
        
        # Hole Antwort von der AI
        response = self.chatgpt_api.chat(query, code_context)
        self.output_field.append(f"🤖 Funlight AI: {response}\n")
        self.input_field.clear()

    def apply_code_edit(self, edit_suggestion):
        """Wendet die Code-Änderung direkt an."""
        if not self.current_file:
            self.output_field.append("🤖 Funlight AI: Keine Datei zum Bearbeiten ausgewählt.\n")
            return False
            
        try:
            with open(self.current_file, 'w', encoding='utf-8') as f:
                f.write(edit_suggestion)
            self.output_field.append("✅ Code wurde erfolgreich aktualisiert!\n")
            return True
        except Exception as e:
            self.output_field.append(f"⚠️ Fehler beim Speichern: {str(e)}\n")
            return False

    def request_code_edit(self):
        """Fordert eine Code-Änderung an."""
        if not self.current_code or self.current_code.strip() == "":
            self.output_field.append("🤖 Funlight AI: Es ist aktuell keine Datei geöffnet. "
                                   "Öffnen Sie zuerst eine Datei, die Sie bearbeiten möchten.\n")
            return
            
        instruction = self.input_field.toPlainText().strip()
        if not instruction:
            self.output_field.append("🤖 Funlight AI: Bitte geben Sie eine Anweisung für die Code-Änderung ein.\n")
            return
        
        self.output_field.append(f"✏️ Code-Änderung angefordert: {instruction}")
        edit_suggestion = self.chatgpt_api.get_code_edit_suggestion(self.current_code, instruction)
        
        # Zeige Vorschau der Änderungen
        self.output_field.append("\n📝 Vorgeschlagene Änderungen:")
        self.output_field.append(f"```python\n{edit_suggestion}\n```\n")
        
        # Frage nach Bestätigung
        self.output_field.append("Möchten Sie diese Änderungen anwenden? Antworten Sie mit 'ja' oder 'nein'.")
        self.waiting_for_confirmation = True
        self.pending_edit = edit_suggestion
        self.input_field.clear()

    def keyPressEvent(self, event: QKeyEvent):
        """Behandelt Tastatureingaben."""
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            if event.modifiers() == Qt.ShiftModifier:
                # Shift+Enter fügt neue Zeile ein
                cursor = self.input_field.textCursor()
                cursor.insertText('\n')
            else:
                # Enter verarbeitet Eingabe
                if hasattr(self, 'waiting_for_confirmation') and self.waiting_for_confirmation:
                    answer = self.input_field.toPlainText().strip().lower()
                    if answer == 'ja':
                        if self.apply_code_edit(self.pending_edit):
                            self.output_field.append("✅ Änderungen wurden erfolgreich angewendet!")
                        self.code_edit_requested.emit(self.pending_edit)
                    else:
                        self.output_field.append("❌ Änderungen wurden verworfen.")
                    self.waiting_for_confirmation = False
                    self.pending_edit = None
                else:
                    self.get_suggestions()
                self.input_field.clear()
        else:
            super().keyPressEvent(event)
