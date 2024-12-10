"""Code-Editor-Komponente für den Windsurf Code Editor."""
import sys
import os

# Füge das Hauptverzeichnis zum Python-Pfad hinzu
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from PySide6.QtWidgets import (
    QPlainTextEdit, QWidget, QHBoxLayout, QFrame,
    QTextEdit
)
from PySide6.QtCore import Qt, QRect, QSize, Signal, QTimer
from PySide6.QtGui import (
    QPainter, QColor, QTextFormat, QFont,
    QFontMetrics, QFontMetricsF, QTextCursor, QTextOption, QPalette
)

# Import aus dem themes-Package
from themes import WindsurfTheme
from syntax.python_highlighter import PythonHighlighter
from utils.line_numbers import LineNumberArea
from gui.minimap import MiniMap
from utils.autocomplete import AutoCompleter

class EditorContainer(QFrame):
    """Container für Editor und Mini-Map."""
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Layout erstellen
        self.layout = QHBoxLayout(self)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Editor erstellen
        self.editor = CodeEditor(self)
        self.layout.addWidget(self.editor)
        
        # Mini-Map erstellen
        self.minimap = MiniMap(self.editor, self)
        self.layout.addWidget(self.minimap)
        
        # Verbindungen herstellen
        self.editor.verticalScrollBar().valueChanged.connect(self.minimap.update_viewport_rect)
        
class CodeEditor(QPlainTextEdit):
    """Haupteditor-Komponente mit Syntax-Highlighting und erweiterter Funktionalität."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.container = parent  # Referenz auf den Container
        
        # Theme-System
        self.theme_styles = WindsurfTheme.get_editor_styles(is_dark=True)
        
        # Minimap Einstellungen
        self._minimap_enabled = True
        self._minimap = None
        
        # Update Timer für Performance-Optimierung
        self._update_timer = QTimer()
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self._delayed_update)
        
        # Zeilennummern
        self._line_numbers_enabled = True
        self.line_number_area = QWidget(self)
        self.line_number_area.paintEvent = self._paint_line_numbers
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self._update_line_number_area)
        self.update_line_number_area_width(0)
        
        # Performance-Optimierungen
        self.setLineWrapMode(QPlainTextEdit.NoWrap)  # Deaktiviert Zeilenumbruch für bessere Performance
        self.setCenterOnScroll(False)  # Verhindert unnötiges Neuzeichnen
        self.setMaximumBlockCount(0)  # Kein Limit für Blöcke
        
        # Viewport-Optimierungen
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.viewport().setCursor(Qt.IBeamCursor)
        
        # Document-Cache
        self._document_cache = {}
        self._last_visible_block = None
        
        # Grundlegende Editor-Einstellungen
        self.setFont(QFont("Consolas", 10))
        self.setTabStopDistance(QFontMetrics(self.font()).horizontalAdvance(' ') * 4)
        
        # Selektionen initialisieren
        self.matching_tag_selections = []
        self.current_line_selection = []
        
        # Aktuelle Zeile hervorheben
        self.cursorPositionChanged.connect(self._highlight_current_line)
        
        # Syntax-Highlighter
        self.highlighter = PythonHighlighter(self.document())
        
        # Autovervollständigung initialisieren
        self.auto_completer = AutoCompleter(self)
        
        # Initial UI aktualisieren
        self._highlight_current_line()
        
    def get_widget(self):
        """Gibt den Container zurück."""
        return self.container
        
    def get_minimap(self):
        """Gibt die Minimap des Containers zurück."""
        if self.container and hasattr(self.container, 'minimap'):
            return self.container.minimap
        return None
        
    def update_theme(self, is_dark=True):
        """Aktualisiert das Theme des Editors."""
        self.theme_styles = WindsurfTheme.get_editor_styles(is_dark)
        
        # Editor-Farben aktualisieren
        self.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: {self.theme_styles['background']};
                color: {self.theme_styles['foreground']};
                selection-background-color: {self.theme_styles['selection_background']};
                selection-color: {self.theme_styles['foreground']};
            }}
        """)
        
        # Syntax-Highlighter aktualisieren
        if hasattr(self, 'highlighter'):
            self.highlighter.update_theme(self.theme_styles)
        
    def setup_ui(self):
        """Initialisiert die UI-Komponenten."""
        # Font optimieren
        font = QFont("Consolas", 10)
        font.setStyleHint(QFont.Monospace)
        font.setFixedPitch(True)
        self.setFont(font)
        
        # Tab-Einstellungen
        self.setTabStopDistance(
            QFontMetricsF(self.font()).horizontalAdvance(' ') * 4
        )
        
        # Zeilennummern
        self.line_number_area = QWidget(self)
        
        # Verbindungen für Updates
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self._update_line_number_area)
        self.cursorPositionChanged.connect(self._highlight_current_line)
        
        # Initial width setzen
        self.update_line_number_area_width(0)
        
    def _delayed_update(self):
        """Verzögerte Aktualisierung des Editors."""
        if hasattr(self.highlighter, 'rehighlight_visible'):
            self.highlighter.rehighlight_visible()
        else:
            self.highlighter.rehighlight()  # Fallback auf normale Hervorhebung
            
        if self._minimap_enabled:
            self.update_minimap()
            
    def paintEvent(self, event):
        """Zeichnet den Editor-Inhalt."""
        super().paintEvent(event)
        
    def _paint_line_numbers(self, event):
        """Zeichnet die Zeilennummern im line_number_area Widget."""
        if not self._line_numbers_enabled:
            return
            
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor(self.theme_styles['line_numbers_bg']))
        
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()
        
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor(self.theme_styles['line_numbers_fg']))
                painter.drawText(
                    0, int(top),
                    self.line_number_area.width() - 2, self.fontMetrics().height(),
                    Qt.AlignRight, number
                )
            
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1

    def keyPressEvent(self, event):
        """Optimierte Tastenverarbeitung."""
        # Auto-Vervollständigung
        if event.key() == Qt.Key_Space and event.modifiers() == Qt.ControlModifier:
            self.auto_completer.show_completions()
            return
            
        # Einrückung
        if event.key() == Qt.Key_Tab:
            if event.modifiers() == Qt.NoModifier:
                if self.textCursor().hasSelection():
                    self.indent_selection()
                else:
                    self.insertPlainText("    ")
                return
                
        # Ausrückung
        if event.key() == Qt.Key_Backtab:
            self.unindent_selection()
            return
            
        # Enter mit Auto-Einrückung
        if event.key() == Qt.Key_Return and self._auto_indent:
            self.handle_new_line()
            return
            
        super().keyPressEvent(event)
        
        # Verzögertes Update
        self._update_timer.start(500)
        
    def resizeEvent(self, event):
        """Behandelt Größenänderungen des Editors."""
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(cr.left(), cr.top(), self.get_line_number_area_width(), cr.height())
        
    def wheelEvent(self, event):
        """Optimiertes Scroll-Event mit Minimap-Update."""
        if event.modifiers() & Qt.ControlModifier:
            # Zoom mit Strg + Mausrad
            if event.angleDelta().y() > 0:
                self.zoomIn(1)
            else:
                self.zoomOut(1)
            event.accept()
        else:
            # Normales Scrollen
            super().wheelEvent(event)
            
            # Minimap-Update nur wenn aktiviert
            if self._minimap_enabled and self._minimap:
                self._minimap.update_viewport()
                
    def toggle_feature(self, feature_name: str, enabled: bool):
        """Aktiviert/Deaktiviert Features für bessere Performance."""
        if feature_name == "syntax_highlight":
            self._syntax_highlight_enabled = enabled
        elif feature_name == "line_numbers":
            self._line_numbers_enabled = enabled
            self.line_number_area.setVisible(enabled)
        elif feature_name == "minimap":
            self._minimap_enabled = enabled
            
        self._delayed_update()
        
    def optimize_for_large_file(self):
        """Optimiert den Editor für große Dateien."""
        self.toggle_feature("syntax_highlight", False)
        self.toggle_feature("minimap", False)
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.setCenterOnScroll(False)
        self._document_cache.clear()
        
    def _highlight_current_line(self):
        """Hebt die aktuelle Zeile hervor."""
        extra_selections = []

        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color = QColor(self.theme_styles['current_line'])
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)

        self.current_line_selection = extra_selections
        self.setExtraSelections(self.current_line_selection + self.matching_tag_selections)

    def get_line_number_area_width(self):
        """Berechnet die benötigte Breite für den Zeilennummern-Bereich."""
        digits = 1
        max_num = max(1, self.blockCount())
        while max_num >= 10:
            max_num //= 10
            digits += 1
        space = 3 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def update_line_number_area_width(self, _):
        """Aktualisiert die Breite des Zeilennummern-Bereichs."""
        width = self.get_line_number_area_width() if self._line_numbers_enabled else 0
        self.setViewportMargins(width, 0, 0, 0)
        self.line_number_area.setFixedWidth(width)

    def _update_line_number_area(self, rect, dy):
        """Aktualisiert den Zeilennummern-Bereich bei Scroll-Events."""
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def find_text(self, text, case_sensitive=False, whole_words=False, search_forward=True):
        """Sucht nach Text im Editor."""
        if not text:
            return False

        # Aktuelle Cursor-Position
        cursor = self.textCursor()
        document = self.document()

        # Suchoptionen
        find_flags = QTextDocument.FindFlags()
        if case_sensitive:
            find_flags |= QTextDocument.FindCaseSensitively
        if whole_words:
            find_flags |= QTextDocument.FindWholeWords
        if not search_forward:
            find_flags |= QTextDocument.FindBackward

        # Suche durchführen
        found_cursor = document.find(text, cursor, find_flags)
        if found_cursor.isNull():
            # Wenn nichts gefunden wurde, von Anfang/Ende neu suchen
            cursor = QTextCursor(document)
            if not search_forward:
                cursor.movePosition(QTextCursor.End)
            found_cursor = document.find(text, cursor, find_flags)
            if found_cursor.isNull():
                return False

        # Gefundenen Text markieren
        self.setTextCursor(found_cursor)
        return True

    def replace_text(self, find_text, replace_text, case_sensitive=False, whole_words=False):
        """Ersetzt den aktuell markierten Text, wenn er mit dem Suchtext übereinstimmt."""
        cursor = self.textCursor()
        if cursor.hasSelection():
            selected_text = cursor.selectedText()
            if (selected_text == find_text or 
                (not case_sensitive and selected_text.lower() == find_text.lower())):
                cursor.insertText(replace_text)
                return True
        return self.find_text(find_text, case_sensitive, whole_words, True)

    def replace_all_text(self, find_text, replace_text, case_sensitive=False, whole_words=False):
        """Ersetzt alle Vorkommen des Suchtexts."""
        count = 0
        cursor = self.textCursor()
        cursor.beginEditBlock()
        
        # Cursor an den Anfang setzen
        cursor.movePosition(QTextCursor.Start)
        self.setTextCursor(cursor)
        
        # Alle Vorkommen ersetzen
        while self.find_text(find_text, case_sensitive, whole_words, True):
            cursor = self.textCursor()
            if cursor.hasSelection():
                cursor.insertText(replace_text)
                count += 1
        
        cursor.endEditBlock()
        return count

    def highlightMatchingTags(self):
        """Hebt die passenden Tags hervor."""
        extraSelections = []

        if not self.isReadOnly():
            cursor = self.textCursor()
            block = cursor.block()
            text = block.text()
            pos = cursor.positionInBlock()
            char = text[pos]

            if char in ('(', ')', '[', ']', '{', '}'):
                matching_char = {'(': ')', ')': '(', '[': ']', ']': '[', '{': '}', '}': '{'}[char]
                matching_pos = text.find(matching_char, pos + 1)

                if matching_pos != -1:
                    selection = QTextEdit.ExtraSelection()
                    selection.format.setForeground(QColor(Qt.blue))
                    selection.cursor = QTextCursor(block)
                    selection.cursor.setPosition(pos)
                    selection.cursor.setPosition(matching_pos + 1, QTextCursor.KeepAnchor)
                    extraSelections.append(selection)

        self.matching_tag_selections = extraSelections
        self.setExtraSelections(self.matching_tag_selections + self.current_line_selection)

    def set_line_numbers_visible(self, visible):
        """Zeigt oder versteckt die Zeilennummern."""
        self._line_numbers_enabled = visible
        self.line_number_area.setVisible(visible)
        self.update_line_number_area_width(0)
        
    def set_auto_indent(self, enabled):
        """Aktiviert oder deaktiviert die automatische Einrückung."""
        self._auto_indent = enabled
        
    def update_minimap(self):
        """Aktualisiert die Mini-Map mit Performance-Optimierungen."""
        if not hasattr(self, 'container') or not hasattr(self.container, 'minimap') or not self._minimap_enabled:
            return
            
        minimap = self.container.minimap
        if minimap:
            minimap.mark_cache_dirty()
            minimap.update()
            
    def _update_minimap_content(self, minimap):
        """Aktualisiert den Inhalt der Minimap."""
        if minimap:
            minimap.mark_cache_dirty()
            minimap.update()

    def handle_new_line(self):
        """Behandelt Zeilenumbrüche mit automatischer Einrückung."""
        cursor = self.textCursor()
        current_line = cursor.block().text()
        
        # Aktuelle Einrückung ermitteln
        indent = ""
        for char in current_line:
            if char in (" ", "\t"):
                indent += char
            else:
                break
        
        # Zusätzliche Einrückung nach bestimmten Zeichen
        if current_line.strip().endswith(":"):
            indent += "    "
            
        # Neue Zeile mit Einrückung einfügen
        cursor.insertText("\n" + indent)
        
    def indent_selection(self):
        """Rückt ausgewählte Zeilen ein."""
        cursor = self.textCursor()
        if not cursor.hasSelection():
            return
            
        # Sicherstellen, dass wir ganze Zeilen auswählen
        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        cursor.setPosition(start)
        cursor.movePosition(cursor.StartOfBlock)
        cursor.setPosition(end, cursor.KeepAnchor)
        cursor.movePosition(cursor.EndOfBlock, cursor.KeepAnchor)
        
        # Text in Zeilen aufteilen und einrücken
        selected_text = cursor.selectedText()
        lines = selected_text.split("\u2029")  # Unicode-Zeilenumbruch in Qt
        indented_lines = ["    " + line for line in lines]
        
        # Eingerückten Text einfügen
        cursor.insertText("\n".join(indented_lines))
        
    def unindent_selection(self):
        """Rückt ausgewählte Zeilen aus."""
        cursor = self.textCursor()
        if not cursor.hasSelection():
            return
            
        # Sicherstellen, dass wir ganze Zeilen auswählen
        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        cursor.setPosition(start)
        cursor.movePosition(cursor.StartOfBlock)
        cursor.setPosition(end, cursor.KeepAnchor)
        cursor.movePosition(cursor.EndOfBlock, cursor.KeepAnchor)
        
        # Text in Zeilen aufteilen und ausrücken
        selected_text = cursor.selectedText()
        lines = selected_text.split("\u2029")
        unindented_lines = []
        
        for line in lines:
            if line.startswith("    "):
                unindented_lines.append(line[4:])
            elif line.startswith("\t"):
                unindented_lines.append(line[1:])
            else:
                unindented_lines.append(line)
                
        # Ausgerückten Text einfügen
        cursor.insertText("\n".join(unindented_lines))
