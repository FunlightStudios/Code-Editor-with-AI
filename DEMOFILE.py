import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QFileDialog, QSplitter,
    QTreeView, QFileSystemModel, QTabWidget, QAction, QInputDialog, QMessageBox, QComboBox, QDialog, QSpinBox, QLabel, QPushButton, QTextEdit,
    QPlainTextEdit, QWidget, QDialogButtonBox, QCheckBox, QGroupBox, QHBoxLayout, QLineEdit, QListWidget
)
from PyQt5.QtGui import (
    QFont, QTextCharFormat, QSyntaxHighlighter, QColor, QPainter, QTextFormat,
    QTextDocument, QTextCursor
)
from PyQt5.QtCore import Qt, QRegExp, QRect, QSize, QTranslator, QLocale
from translations import TRANSLATIONS

# Übersetzer für verschiedene Sprachen


class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []

        # Keyword Format
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#ff6b9b"))
        keywords = [
            "and", "as", "assert", "break", "class", "continue", "def",
            "del", "elif", "else", "except", "False", "finally", "for",
            "from", "global", "if", "import", "in", "is", "lambda", "None",
            "nonlocal", "not", "or", "pass", "raise", "return", "True",
            "try", "while", "with", "yield"
        ]
        for word in keywords:
            pattern = QRegExp("\\b" + word + "\\b")
            rule = (pattern, keyword_format)
            self.highlighting_rules.append(rule)

        # Function Format
        function_format = QTextCharFormat()
        function_format.setForeground(QColor("#dcdcaa"))
        pattern = QRegExp("\\b[A-Za-z0-9_]+(?=\\()")
        rule = (pattern, function_format)
        self.highlighting_rules.append(rule)

        # String Format
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#ce9178"))
        pattern = QRegExp("\".*\"")
        pattern.setMinimal(True)
        rule = (pattern, string_format)
        self.highlighting_rules.append(rule)
        pattern = QRegExp("'.*'")
        pattern.setMinimal(True)
        rule = (pattern, string_format)
        self.highlighting_rules.append(rule)

        # Comment Format
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6a9955"))
        pattern = QRegExp("#[^\n]*")
        rule = (pattern, comment_format)
        self.highlighting_rules.append(rule)

        # Numbers Format
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#b5cea8"))
        pattern = QRegExp("\\b[0-9]+\\b")
        rule = (pattern, number_format)
        self.highlighting_rules.append(rule)

        # Class Format
        class_format = QTextCharFormat()
        class_format.setForeground(QColor("#4ec9b0"))
        pattern = QRegExp("\\bclass\\b\\s*(\\w+)")
        rule = (pattern, class_format)
        self.highlighting_rules.append(rule)

    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            expression = QRegExp(pattern)
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)


class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.getLineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self.editor.lineNumberAreaPaintEvent(event)


class CodeEditor(QPlainTextEdit):
    """Ein einfacher Code-Editor mit Syntax-Hervorhebung."""
    def __init__(self):
        super().__init__()
        self.current_theme = "dark"  # Default theme
        self.matching_tag_selections = []
        self.current_line_selection = []
        self._auto_indent = True
        
        # Font setup - using system default monospace font as fallback
        font = QFont()
        font.setFamily("Consolas, Courier New, monospace")
        font.setFixedPitch(True)
        font.setPointSize(10)
        self.setFont(font)
        
        # Setup line numbers
        self.line_number_area = LineNumberArea(self)
        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)
        self.cursorPositionChanged.connect(self.highlightMatchingTags)
        
        # Initial updates
        self.updateLineNumberAreaWidth(0)
        self.highlightCurrentLine()
        
        # Setup editor properties
        self.setTabStopWidth(self.fontMetrics().width(' ') * 4)
        self.document().setDocumentMargin(10)
        
        # Setup syntax highlighter
        self.highlighter = None
        
    def getLineNumberAreaWidth(self):
        """Berechnet die Breite des Zeilennummernbereichs."""
        digits = 1
        max_num = max(1, self.blockCount())
        while max_num >= 10:
            max_num //= 10
            digits += 1
        space = 3 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def updateLineNumberAreaWidth(self, _):
        """Update the width of the line number area."""
        width = self.getLineNumberAreaWidth()
        self.setViewportMargins(width, 0, 0, 0)

    def updateLineNumberArea(self, rect, dy):
        """Update the line number area."""
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)

    def resizeEvent(self, event):
        """Handle resize events."""
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.getLineNumberAreaWidth(), cr.height()))

    def lineNumberAreaPaintEvent(self, event):
        """Paint the line number area."""
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor("#2b2b2b") if self.current_theme == "dark" else QColor("#f0f0f0"))
        
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        offset = self.contentOffset()
        top = round(self.blockBoundingGeometry(block).translated(offset).top())
        bottom = round(top + self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor("#808080") if self.current_theme == "dark" else QColor("#404040"))
                rect = QRect(0, top, self.line_number_area.width() - 2, self.fontMetrics().height())
                painter.drawText(rect, Qt.AlignRight, number)
            
            block = block.next()
            top = bottom
            bottom = round(top + self.blockBoundingRect(block).height())
            block_number += 1

    def highlightCurrentLine(self):  
        """Highlight the current line."""
        if not hasattr(self, 'current_line_selection'):
            self.current_line_selection = []
        if not hasattr(self, 'matching_tag_selections'):
            self.matching_tag_selections = []
            
        extra_selections = []
        
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color = QColor("#2d2d2d") if self.current_theme == "dark" else QColor("#f0f0f0")
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
        
        self.current_line_selection = extra_selections
        self.setExtraSelections(self.current_line_selection + self.matching_tag_selections)
        
        # Nach dem Hervorheben der aktuellen Zeile, prüfen wir auf Tags/Klammern
        self.highlightMatchingTags()

    def highlightMatchingTags(self):  
        """Hebt zusammengehörige Tags und Klammern hervor."""
        # Alte Hervorhebungen entfernen
        self.matching_tag_selections = []
        
        cursor = self.textCursor()
        document = self.document()
        current_pos = cursor.position()
        
        # Text des gesamten Dokuments
        text = document.toPlainText()
        
        # Position in der aktuellen Zeile finden
        block_pos = cursor.block().position()
        pos_in_block = current_pos - block_pos
        line_text = cursor.block().text()
        
        # Dateiendung bestimmen
        current_file = self.parent().current_file if hasattr(self.parent(), 'current_file') else ""
        file_ext = os.path.splitext(current_file)[1].lower() if current_file else ""
        
        # Klammerpaare für verschiedene Sprachen
        brackets = {
            'common': [('(', ')'), ('[', ']'), ('{', '}')],
            '.py': [('(', ')'), ('[', ']'), ('{', '}'), ('"""', '"""'), ("'''", "'''")],
            '.js': [('(', ')'), ('[', ']'), ('{', '}'), ('`', '`')],
            '.java': [('(', ')'), ('[', ']'), ('{', '}'), ('/**', '*/')],
            '.cpp': [('(', ')'), ('[', ']'), ('{', '}'), ('/*', '*/')],
            '.html': [('<', '>')],
            '.xml': [('<', '>')],
            '.php': [('(', ')'), ('[', ']'), ('{', '}'), ('<?php', '?>'), ('<!--', '-->')],
        }
        
        # Aktuelle Sprache bestimmen
        current_brackets = brackets.get(file_ext, brackets['common'])
        if file_ext in ['.html', '.xml']:
            self.highlight_xml_tags()
            return
            
        # Position des Cursors prüfen
        if pos_in_block >= len(line_text):
            return
            
        char = line_text[pos_in_block] if pos_in_block < len(line_text) else ''
        prev_char = line_text[pos_in_block - 1] if pos_in_block > 0 else ''
        
        # Prüfen auf Multi-Char-Brackets (z.B. """)
        for start, end in current_brackets:
            if len(start) > 1 or len(end) > 1:
                # Vorwärts prüfen
                if pos_in_block + len(start) <= len(line_text):
                    forward_text = line_text[pos_in_block:pos_in_block + len(start)]
                    if forward_text == start or forward_text == end:
                        self.find_and_highlight_multichar(forward_text, start, end, block_pos + pos_in_block)
                        return
                
                # Rückwärts prüfen
                if pos_in_block >= len(start):
                    backward_text = line_text[pos_in_block - len(start):pos_in_block]
                    if backward_text == start or backward_text == end:
                        self.find_and_highlight_multichar(backward_text, start, end, block_pos + pos_in_block - len(start))
                        return
        
        # Single-Char-Brackets prüfen
        for start, end in current_brackets:
            if len(start) == 1 and len(end) == 1:
                if char in (start, end):
                    self.find_and_highlight_bracket(char, start, end, block_pos + pos_in_block)
                    return
                elif prev_char in (start, end):
                    self.find_and_highlight_bracket(prev_char, start, end, block_pos + pos_in_block - 1)
                    return
    
    def find_and_highlight_bracket(self, char, start, end, pos):
        """Findet und hebt passende Einzelzeichen-Klammern hervor."""
        format = QTextCharFormat()
        format.setBackground(QColor("#4d4d4d") if self.current_theme == "dark" else QColor("#e6e6e6"))
        format.setForeground(QColor("#ffffff") if self.current_theme == "dark" else QColor("#000000"))
        
        # Erste Klammer hervorheben
        selection = QTextEdit.ExtraSelection()
        selection.format = format
        cursor = QTextCursor(self.document())
        cursor.setPosition(pos)
        cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor)
        selection.cursor = cursor
        self.matching_tag_selections.append(selection)
        
        # Richtung und Zielzeichen bestimmen
        is_opening = char == start
        target = end if is_opening else start
        count = 1
        
        # Suche nach passender Klammer
        cursor = QTextCursor(self.document())
        cursor.setPosition(pos)
        
        if is_opening:
            while not cursor.atEnd():
                cursor.movePosition(QTextCursor.Right)
                current_char = cursor.document().characterAt(cursor.position())
                if current_char == start:
                    count += 1
                elif current_char == end:
                    count -= 1
                    if count == 0:
                        selection = QTextEdit.ExtraSelection()
                        selection.format = format
                        cursor2 = QTextCursor(cursor)
                        cursor2.movePosition(QTextCursor.Left, QTextCursor.KeepAnchor)
                        selection.cursor = cursor2
                        self.matching_tag_selections.append(selection)
                        break
        else:
            while not cursor.atStart():
                cursor.movePosition(QTextCursor.Left)
                current_char = cursor.document().characterAt(cursor.position())
                if current_char == end:
                    count += 1
                elif current_char == start:
                    count -= 1
                    if count == 0:
                        selection = QTextEdit.ExtraSelection()
                        selection.format = format
                        selection.cursor = cursor
                        self.matching_tag_selections.append(selection)
                        break
        
        self.setExtraSelections(self.current_line_selection + self.matching_tag_selections)
    
    def find_and_highlight_multichar(self, text, start, end, pos):
        """Findet und hebt Multi-Zeichen-Klammern hervor (z.B. ''')."""
        format = QTextCharFormat()
        format.setBackground(QColor("#4d4d4d") if self.current_theme == "dark" else QColor("#e6e6e6"))
        format.setForeground(QColor("#ffffff") if self.current_theme == "dark" else QColor("#000000"))
        
        # Erstes Multi-Char hervorheben
        selection = QTextEdit.ExtraSelection()
        selection.format = format
        cursor = QTextCursor(self.document())
        cursor.setPosition(pos)
        cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, len(text))
        selection.cursor = cursor
        self.matching_tag_selections.append(selection)
        
        # Suche nach dem passenden Multi-Char
        is_start = text == start
        target = end if is_start else start
        doc_text = self.document().toPlainText()
        
        if is_start:
            next_pos = doc_text.find(target, pos + len(start))
            if next_pos != -1:
                selection = QTextEdit.ExtraSelection()
                selection.format = format
                cursor = QTextCursor(self.document())
                cursor.setPosition(next_pos)
                cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, len(target))
                selection.cursor = cursor
                self.matching_tag_selections.append(selection)
        else:
            prev_pos = doc_text.rfind(target, 0, pos)
            if prev_pos != -1:
                selection = QTextEdit.ExtraSelection()
                selection.format = format
                cursor = QTextCursor(self.document())
                cursor.setPosition(prev_pos)
                cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, len(target))
                selection.cursor = cursor
                self.matching_tag_selections.append(selection)
        
        self.setExtraSelections(self.current_line_selection + self.matching_tag_selections)
    
    def highlight_xml_tags(self):
        """Spezielle Behandlung für XML/HTML Tags."""
        cursor = self.textCursor()
        document = self.document()
        current_pos = cursor.position()
        
        # Text des gesamten Dokuments
        text = document.toPlainText()
        
        # Position in der aktuellen Zeile finden
        block_pos = cursor.block().position()
        pos_in_block = current_pos - block_pos
        line_text = cursor.block().text()
        
        # Prüfen, ob wir uns in einem Tag befinden
        tag_start = -1
        tag_end = -1
        is_closing_tag = False
        
        # Rückwärts suchen nach '<'
        for i in range(pos_in_block - 1, -1, -1):
            if line_text[i] == '<':
                tag_start = block_pos + i
                if i + 1 < len(line_text) and line_text[i + 1] == '/':
                    is_closing_tag = True
                break
            elif line_text[i] == '>':
                break
        
        # Vorwärts suchen nach '>'
        if tag_start != -1:
            for i in range(pos_in_block, len(line_text)):
                if line_text[i] == '>':
                    tag_end = block_pos + i
                    break
        
        if tag_start != -1 and tag_end != -1:
            # Tag-Name extrahieren
            tag_text = text[tag_start:tag_end + 1]
            if is_closing_tag:
                tag_name = tag_text[2:-1].split()[0]
                search_pattern = f"<{tag_name}[^>]*>"
            else:
                tag_name = tag_text[1:-1].split()[0]
                search_pattern = f"</{tag_name}>"
            
            # Hervorhebungsformat
            format = QTextCharFormat()
            format.setBackground(QColor("#4d4d4d") if self.current_theme == "dark" else QColor("#e6e6e6"))
            format.setForeground(QColor("#ffffff") if self.current_theme == "dark" else QColor("#000000"))
            
            # Aktuelles Tag hervorheben
            selection = QTextEdit.ExtraSelection()
            selection.format = format
            cursor = QTextCursor(document)
            cursor.setPosition(tag_start)
            cursor.setPosition(tag_end + 1, QTextCursor.KeepAnchor)
            selection.cursor = cursor
            self.matching_tag_selections.append(selection)
            
            # Nach dem passenden Tag suchen
            cursor = QTextCursor(document)
            regex = QRegExp(search_pattern)
            
            if is_closing_tag:
                # Rückwärts suchen für schließendes Tag
                cursor.setPosition(tag_start)
                cursor = document.find(regex, cursor, QTextDocument.FindBackward)
            else:
                # Vorwärts suchen für öffnendes Tag
                cursor.setPosition(tag_end)
                cursor = document.find(regex, cursor)
            
            if not cursor.isNull():
                selection = QTextEdit.ExtraSelection()
                selection.format = format
                selection.cursor = cursor
                self.matching_tag_selections.append(selection)
        
        # Hervorhebungen anwenden
        self.setExtraSelections(self.current_line_selection + self.matching_tag_selections)

    def update_theme(self, theme):
        """Aktualisiert das Theme des Editors."""
        if theme == "dark":
            # Dunkles Theme
            self.setStyleSheet("""
                QPlainTextEdit {
                    background-color: #1e1e1e;
                    color: #d4d4d4;
                    border: none;
                }
            """)
            # Syntax-Highlighter für Python
            self.highlighter = PythonHighlighter(self.document())
        else:
            # Helles Theme
            self.setStyleSheet("""
                QPlainTextEdit {
                    background-color: white;
                    color: black;
                    border: none;
                }
            """)
            if self.highlighter:
                self.highlighter.setDocument(None)
                self.highlighter = None

    def update_font(self):
        """Aktualisiert die Schriftgröße."""
        font = QFont("Consolas", self.font_size)
        font.setFixedPitch(True)
        self.setFont(font)

    def update_status_bar(self):
        """Aktualisiert die Statusleiste."""
        text = self.toPlainText()
        total_lines = text.count('\n') + 1
        
        # Zähle tatsächliche Code-Zeilen (keine leeren Zeilen oder Kommentare)
        code_lines = 0
        for line in text.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                code_lines += 1
        
        # Status-Text aktualisieren
        status_text = f"Lines: {total_lines} | Code Lines: {code_lines}"
        # print(status_text)  # Debugging

    def keyPressEvent(self, event):
        """Handle key press events for auto-indentation."""
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.handleNewLine()
        else:
            super().keyPressEvent(event)
            
    def handleNewLine(self):
        """Handle new line with auto-indentation."""
        cursor = self.textCursor()
        block = cursor.block()
        text = block.text()
        indent = self.getIndentation(text)
        
        # Check for special cases that need extra indentation
        if text.rstrip().endswith((':','{','[','(')):
            indent += '    '
            
        cursor.insertText('\n' + indent)
        
    def getIndentation(self, text):
        """Get the indentation of the current line."""
        return text[:len(text) - len(text.lstrip())]
        
    def setAutoIndentation(self, enabled):
        """Enable or disable auto-indentation."""
        self._auto_indent = enabled

class EditorWindow(QMainWindow):
    """Hauptfenster des Editors."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("General Editor")
        self.setGeometry(100, 100, 1280, 800)  # Default-Größe, falls nicht maximiert
        self.showMaximized()  # Fenster maximiert starten
        self.current_theme = "dark"
        self.current_language = "Deutsch"  # Standardsprache
        self.translations = TRANSLATIONS

        # Hauptlayout
        main_layout = QVBoxLayout()
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Splitter für Dateibaum und Tabs
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # Dateibaum
        self.file_tree = QTreeView()
        self.file_model = QFileSystemModel()
        self.file_tree.setModel(self.file_model)
        self.file_tree.hideColumn(3)  # Versteckt die "Date Modified" Spalte
        self.file_tree.clicked.connect(self.open_file)
        splitter.addWidget(self.file_tree)

        # Tabs für Dateien
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.update_status_bar)  # Update bei Tab-Wechsel
        splitter.addWidget(self.tabs)

        # Splitter-Größen setzen (20% für Dateibaum, 80% für Tabs)
        splitter.setSizes([200, 800])

        # Status Bar
        self.status_bar = self.statusBar()
        
        # Linke Seite: Zeilen-Zähler
        self.line_count_label = QLabel()
        self.status_bar.addWidget(self.line_count_label)
        self.line_count_label.setText("Zeilen: 0 | Code-Zeilen: 0")  # Initial anzeigen
        
        # Rechte Seite: Copyright
        copyright_label = QLabel("Copyright 2025 Funlight Studios")
        copyright_label.setStyleSheet("padding-right: 5px;")  # Padding rechts hinzufügen
        self.status_bar.addPermanentWidget(copyright_label)

        # Menü
        self.create_menu()
        
        # Initial theme anwenden
        self.apply_theme()

    def update_status_bar(self):
        """Aktualisiert die Statusleiste mit Informationen zum aktuellen Dokument."""
        current_editor = self.tabs.currentWidget()
        if isinstance(current_editor, CodeEditor):
            text = current_editor.toPlainText()
            total_lines = text.count('\n') + 1
            
            # Zähle tatsächliche Code-Zeilen (keine leeren Zeilen oder Kommentare)
            code_lines = 0
            for line in text.split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):
                    code_lines += 1
        else:
            total_lines = 0
            code_lines = 0
            
        # Status-Text aktualisieren mit Übersetzung
        status_text = f"{self.tr('Lines')}: {total_lines} | {self.tr('Code Lines')}: {code_lines}"
        self.line_count_label.setText(status_text)

    def tr(self, text):
        """Übersetzt einen Text in die aktuelle Sprache."""
        return self.translations[self.current_language].get(text, text)

    def load_file(self, path):
        """Lädt eine Datei in einen neuen Tab."""
        with open(path, "r", encoding="utf-8") as file:
            content = file.read()

        editor = CodeEditor()
        editor.setPlainText(content)
        editor.update_theme(self.current_theme)
        
        # Verbinde das textChanged-Signal mit update_status_bar
        editor.textChanged.connect(self.update_status_bar)

        tab_index = self.tabs.addTab(editor, os.path.basename(path))
        self.tabs.setCurrentIndex(tab_index)
        editor.setProperty("file_path", path)
        
        # Status Bar initial aktualisieren
        self.update_status_bar()

    def apply_theme(self):
        """Wendet das aktuelle Theme auf alle Komponenten an."""
        if self.current_theme == "dark":
            # Dunkles Theme
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #1e1e1e;
                    color: #d4d4d4;
                }
                QMenuBar {
                    background-color: #1e1e1e;
                    color: #d4d4d4;
                }
                QMenuBar::item:selected {
                    background-color: #2d2d2d;
                }
                QMenu {
                    background-color: #1e1e1e;
                    color: #d4d4d4;
                    border: 1px solid #2d2d2d;
                }
                QMenu::item:selected {
                    background-color: #2d2d2d;
                }
                QTabWidget::pane {
                    border: 1px solid #2d2d2d;
                }
                QTabBar::tab {
                    background-color: #2d2d2d;
                    color: #d4d4d4;
                    padding: 5px;
                    border: 1px solid #1e1e1e;
                }
                QTabBar::tab:selected {
                    background-color: #1e1e1e;
                    border-bottom: none;
                }
                QTreeView {
                    background-color: #1e1e1e;
                    color: #d4d4d4;
                    border: none;
                }
                QTreeView::item:hover {
                    background-color: #2d2d2d;
                }
                QTreeView::item:selected {
                    background-color: #264f78;
                }
                QTreeView::branch {
                    background-color: #1e1e1e;
                }
                QHeaderView::section {
                    background-color: #2d2d2d;
                    color: #d4d4d4;
                    padding: 5px;
                    border: none;
                }
                QStatusBar {
                    background-color: #2d2d2d;
                    color: #d4d4d4;
                    border-top: 1px solid #1e1e1e;
                }
                QSplitter::handle {
                    background-color: #2d2d2d;
                }
                QDialog {
                    background-color: #1e1e1e;
                    color: #d4d4d4;
                }
                QLabel {
                    color: #d4d4d4;
                }
                QPushButton {
                    background-color: #0e639c;
                    color: white;
                    border: none;
                    padding: 5px 10px;
                }
                QPushButton:hover {
                    background-color: #1177bb;
                }
                QPushButton:pressed {
                    background-color: #094771;
                }
                QLineEdit {
                    background-color: #3c3c3c;
                    color: #d4d4d4;
                    border: 1px solid #2d2d2d;
                    padding: 3px;
                }
                QSpinBox {
                    background-color: #3c3c3c;
                    color: #d4d4d4;
                    border: 1px solid #2d2d2d;
                }
                QComboBox {
                    background-color: #3c3c3c;
                    color: #d4d4d4;
                    border: 1px solid #2d2d2d;
                    padding: 3px;
                }
                QComboBox::drop-down {
                    border: none;
                }
                QComboBox::down-arrow {
                    image: none;
                    border-left: 3px solid none;
                    border-right: 3px solid none;
                    border-top: 6px solid #d4d4d4;
                    width: 0;
                    height: 0;
                }
                QComboBox QAbstractItemView {
                    background-color: #1e1e1e;
                    color: #d4d4d4;
                    selection-background-color: #264f78;
                }
                QGroupBox {
                    color: #d4d4d4;
                    border: 1px solid #2d2d2d;
                    margin-top: 5px;
                }
                QGroupBox::title {
                    color: #d4d4d4;
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
                }
                QCheckBox::indicator:checked {
                    background-color: #007acc;
                    border: 1px solid #007acc;
                }
                QListWidget {
                    background-color: #1e1e1e;
                    color: #d4d4d4;
                    border: 1px solid #2d2d2d;
                }
                QListWidget::item:hover {
                    background-color: #2d2d2d;
                }
                QListWidget::item:selected {
                    background-color: #264f78;
                }
            """)
            
            # Syntax-Highlighting für dunkles Theme
            for i in range(self.tabs.count()):
                editor = self.tabs.widget(i)
                if isinstance(editor, CodeEditor):
                    editor.update_theme("dark")
        else:
            # Helles Theme
            self.setStyleSheet("""
                QMainWindow {
                    background-color: white;
                    color: black;
                }
                QMenuBar {
                    background-color: white;
                    color: black;
                }
                QMenuBar::item:selected {
                    background-color: #e5e5e5;
                }
                QMenu {
                    background-color: white;
                    color: black;
                    border: 1px solid #c0c0c0;
                }
                QMenu::item:selected {
                    background-color: #e5e5e5;
                }
                QTabWidget::pane {
                    border: 1px solid #c0c0c0;
                }
                QTabBar::tab {
                    background-color: #f0f0f0;
                    color: black;
                    padding: 5px;
                    border: 1px solid #c0c0c0;
                }
                QTabBar::tab:selected {
                    background-color: white;
                    border-bottom: none;
                }
                QTreeView {
                    background-color: white;
                    color: black;
                    border: none;
                }
                QTreeView::item:hover {
                    background-color: #e5e5e5;
                }
                QTreeView::item:selected {
                    background-color: #cce8ff;
                }
                QTreeView::branch {
                    background-color: white;
                }
                QHeaderView::section {
                    background-color: #f0f0f0;
                    color: black;
                    padding: 5px;
                    border: none;
                }
                QStatusBar {
                    background-color: #f0f0f0;
                    color: black;
                    border-top: 1px solid #c0c0c0;
                }
                QSplitter::handle {
                    background-color: #e5e5e5;
                }
                QDialog {
                    background-color: white;
                    color: black;
                }
                QLabel {
                    color: black;
                }
                QPushButton {
                    background-color: #0078d7;
                    color: white;
                    border: none;
                    padding: 5px 10px;
                }
                QPushButton:hover {
                    background-color: #1084d7;
                }
                QPushButton:pressed {
                    background-color: #006cc1;
                }
                QLineEdit {
                    background-color: white;
                    color: black;
                    border: 1px solid #c0c0c0;
                    padding: 3px;
                }
                QSpinBox {
                    background-color: white;
                    color: black;
                    border: 1px solid #c0c0c0;
                }
                QComboBox {
                    background-color: white;
                    color: black;
                    border: 1px solid #c0c0c0;
                    padding: 3px;
                }
                QComboBox::drop-down {
                    border: none;
                }
                QComboBox::down-arrow {
                    image: none;
                    border-left: 3px solid none;
                    border-right: 3px solid none;
                    border-top: 6px solid black;
                    width: 0;
                    height: 0;
                }
                QComboBox QAbstractItemView {
                    background-color: white;
                    color: black;
                    selection-background-color: #cce8ff;
                }
                QGroupBox {
                    color: black;
                    border: 1px solid #c0c0c0;
                    margin-top: 5px;
                }
                QGroupBox::title {
                    color: black;
                }
                QCheckBox {
                    color: black;
                }
                QCheckBox::indicator {
                    width: 13px;
                    height: 13px;
                }
                QCheckBox::indicator:unchecked {
                    border: 1px solid black;
                }
                QCheckBox::indicator:checked {
                    background-color: #0078d7;
                    border: 1px solid #0078d7;
                }
                QListWidget {
                    background-color: white;
                    color: black;
                    border: 1px solid #c0c0c0;
                }
                QListWidget::item:hover {
                    background-color: #e5e5e5;
                }
                QListWidget::item:selected {
                    background-color: #cce8ff;
                }
            """)
            
            # Syntax-Highlighting für helles Theme
            for i in range(self.tabs.count()):
                editor = self.tabs.widget(i)
                if isinstance(editor, CodeEditor):
                    editor.update_theme("light")

    def create_menu(self):
        """Erstellt die Menüleiste."""
        menubar = self.menuBar()

        # Datei-Menü
        file_menu = menubar.addMenu(self.tr('File'))
        
        new_file_action = QAction(self.tr('New File'), self)
        new_file_action.setShortcut('Ctrl+N')
        new_file_action.triggered.connect(self.new_file)
        file_menu.addAction(new_file_action)

        open_file_action = QAction(self.tr('Open File'), self)
        open_file_action.setShortcut('Ctrl+O')
        open_file_action.triggered.connect(self.open_file_dialog)
        file_menu.addAction(open_file_action)

        open_folder_action = QAction(self.tr('Open Folder'), self)
        open_folder_action.setShortcut('Ctrl+K')
        open_folder_action.triggered.connect(self.open_folder_dialog)
        file_menu.addAction(open_folder_action)

        save_file_action = QAction(self.tr('Save'), self)
        save_file_action.setShortcut('Ctrl+S')
        save_file_action.triggered.connect(self.save_file)
        file_menu.addAction(save_file_action)

        save_as_action = QAction(self.tr('Save As'), self)
        save_as_action.setShortcut('Ctrl+Shift+S')
        save_as_action.triggered.connect(self.save_file_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        exit_action = QAction(self.tr('Exit'), self)
        exit_action.setShortcut('Alt+F4')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Bearbeiten-Menü
        edit_menu = menubar.addMenu(self.tr('Edit'))
        
        undo_action = QAction(self.tr('Undo'), self)
        undo_action.setShortcut('Ctrl+Z')
        undo_action.triggered.connect(lambda: self.tabs.currentWidget().undo() if self.tabs.currentWidget() else None)
        edit_menu.addAction(undo_action)

        redo_action = QAction(self.tr('Redo'), self)
        redo_action.setShortcut('Ctrl+Y')
        redo_action.triggered.connect(lambda: self.tabs.currentWidget().redo() if self.tabs.currentWidget() else None)
        edit_menu.addAction(redo_action)

        edit_menu.addSeparator()

        cut_action = QAction(self.tr('Cut'), self)
        cut_action.setShortcut('Ctrl+X')
        cut_action.triggered.connect(lambda: self.tabs.currentWidget().cut() if self.tabs.currentWidget() else None)
        edit_menu.addAction(cut_action)

        copy_action = QAction(self.tr('Copy'), self)
        copy_action.setShortcut('Ctrl+C')
        copy_action.triggered.connect(lambda: self.tabs.currentWidget().copy() if self.tabs.currentWidget() else None)
        edit_menu.addAction(copy_action)

        paste_action = QAction(self.tr('Paste'), self)
        paste_action.setShortcut('Ctrl+V')
        paste_action.triggered.connect(lambda: self.tabs.currentWidget().paste() if self.tabs.currentWidget() else None)
        edit_menu.addAction(paste_action)

        edit_menu.addSeparator()

        find_action = QAction(self.tr("Find"), self)
        find_action.triggered.connect(self.show_find_dialog)
        edit_menu.addAction(find_action)

        find_replace_action = QAction(self.tr("Find and Replace"), self)
        find_replace_action.triggered.connect(self.show_find_replace_dialog)
        edit_menu.addAction(find_replace_action)

        find_in_files_action = QAction(self.tr("Find in Files"), self)
        find_in_files_action.triggered.connect(self.show_find_in_files_dialog)
        edit_menu.addAction(find_in_files_action)
        
        # Ansicht-Menü
        view_menu = menubar.addMenu(self.tr("View"))
        
        settings_action = QAction(self.tr("Settings"), self)
        settings_action.triggered.connect(self.show_settings_dialog)
        view_menu.addAction(settings_action)

    def show_find_dialog(self):
        dialog = SearchDialog(self)
        dialog.exec_()

    def show_find_replace_dialog(self):
        dialog = SearchDialog(self, replace=True)
        dialog.exec_()

    def show_find_in_files_dialog(self):
        dialog = SearchDialog(self, in_files=True)
        dialog.exec_()

    def find_text(self, text, match_case=False, whole_word=False, forward=True):
        if not text or not self.tabs.currentWidget():
            return

        editor = self.tabs.currentWidget()
        flags = QTextDocument.FindFlags()

        if match_case:
            flags |= QTextDocument.FindCaseSensitively
        if whole_word:
            flags |= QTextDocument.FindWholeWords
        if not forward:
            flags |= QTextDocument.FindBackward

        cursor = editor.textCursor()
        if not forward:
            cursor.movePosition(QTextCursor.Start)

        cursor = editor.document().find(text, cursor, flags)
        if not cursor.isNull():
            editor.setTextCursor(cursor)
        else:
            # Wenn nicht gefunden, von vorne/hinten beginnen
            cursor = editor.textCursor()
            cursor.movePosition(QTextCursor.Start if forward else QTextCursor.End)
            cursor = editor.document().find(text, cursor, flags)
            if not cursor.isNull():
                editor.setTextCursor(cursor)

    def replace_text(self, find_text, replace_text, match_case=False, whole_word=False):
        if not find_text or not self.tabs.currentWidget():
            return

        editor = self.tabs.currentWidget()
        cursor = editor.textCursor()
        if cursor.hasSelection() and cursor.selectedText() == find_text:
            cursor.insertText(replace_text)
            editor.setTextCursor(cursor)
        self.find_text(find_text, match_case, whole_word, True)

    def replace_all_text(self, find_text, replace_text, match_case=False, whole_word=False):
        if not find_text or not self.tabs.currentWidget():
            return

        editor = self.tabs.currentWidget()
        cursor = editor.textCursor()
        cursor.beginEditBlock()
        cursor.movePosition(QTextCursor.Start)
        editor.setTextCursor(cursor)

        count = 0
        while True:
            self.find_text(find_text, match_case, whole_word, True)
            cursor = editor.textCursor()
            if not cursor.hasSelection():
                break
            cursor.insertText(replace_text)
            count += 1

        cursor.endEditBlock()
        QMessageBox.information(self, self.tr("Replace All"), 
                              f"{count} " + self.tr("occurrences replaced"))

    def get_open_folders(self):
        folders = set()
        root = self.file_model.rootPath()
        if root:
            folders.add(root)
        return list(folders)

    def show_settings_dialog(self):
        """Zeigt den Einstellungen-Dialog an."""
        dialog = SettingsDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            settings = dialog.get_settings()
            
            # Sprache ändern (ohne Theme zu beeinflussen)
            if settings["language"] != self.current_language:
                self.current_language = settings["language"]
                self.retranslateUi()
            
            # Theme separat behandeln
            if settings["theme"] != self.current_theme:
                self.current_theme = settings["theme"]
                self.apply_theme()
            
            # Schriftgröße ändern
            for i in range(self.tabs.count()):
                editor = self.tabs.widget(i)
                if isinstance(editor, CodeEditor):
                    font = editor.font()
                    font.setPointSize(settings["font_size"])
                    editor.setFont(font)
            
            # Editor-Einstellungen anwenden
            for i in range(self.tabs.count()):
                editor = self.tabs.widget(i)
                if isinstance(editor, CodeEditor):
                    # Hier könnten weitere Editor-Einstellungen angewendet werden
                    pass

    def new_file(self):
        """Erstellt eine neue leere Datei in einem neuen Tab."""
        editor = CodeEditor()
        editor.update_theme(self.current_theme)
        tab_index = self.tabs.addTab(editor, self.tr("New File"))
        self.tabs.setCurrentIndex(tab_index)
        editor.setProperty("file_path", "")
        self.update_status_bar()

    def open_file_dialog(self):
        """Öffnet eine Datei über einen Dialog."""
        path, _ = QFileDialog.getOpenFileName(self, self.tr("Open File"), os.getcwd(), self.tr("All Files (*.*)"))
        if path:
            self.load_file(path)

    def open_file(self, index):
        """Öffnet eine Datei aus dem Dateibaum."""
        path = self.file_model.filePath(index)
        if os.path.isfile(path):
            self.load_file(path)

    def save_file(self):
        """Speichert die aktuelle Datei."""
        current_widget = self.tabs.currentWidget()
        if isinstance(current_widget, CodeEditor):
            path = current_widget.property("file_path")
            if path:
                with open(path, "w", encoding="utf-8") as file:
                    file.write(current_widget.toPlainText())

    def save_file_as(self):
        """Speichert die aktuelle Datei unter einem neuen Namen."""
        current_widget = self.tabs.currentWidget()
        if isinstance(current_widget, CodeEditor):
            path, _ = QFileDialog.getSaveFileName(self, self.tr("Save As"), os.getcwd(), self.tr("All Files (*.*)"))
            if path:
                with open(path, "w", encoding="utf-8") as file:
                    file.write(current_widget.toPlainText())
                current_widget.setProperty("file_path", path)
                self.tabs.setTabText(self.tabs.currentIndex(), os.path.basename(path))

    def close_tab(self, index):
        """Schließt einen Tab."""
        self.tabs.removeTab(index)

    def open_folder_dialog(self):
        """Öffnet einen Ordner über einen Dialog."""
        folder_path = QFileDialog.getExistingDirectory(self, self.tr("Open Folder"))
        if folder_path:
            self.file_model.setRootPath(folder_path)
            self.file_tree.setRootIndex(self.file_model.index(folder_path))

class SearchDialog(QDialog):
    def __init__(self, parent=None, replace=False, in_files=False):
        super().__init__(parent)
        self.parent = parent
        self.replace = replace
        self.in_files = in_files
        self.setWindowTitle(self.parent.tr("Find and Replace") if replace else self.parent.tr("Find"))
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Search input
        search_group = QGroupBox(self.parent.tr("Search for"))
        search_layout = QVBoxLayout()
        self.search_input = QLineEdit()
        search_layout.addWidget(self.search_input)
        search_group.setLayout(search_layout)
        layout.addWidget(search_group)

        # Replace input (if replace mode)
        if self.replace:
            replace_group = QGroupBox(self.parent.tr("Replace with"))
            replace_layout = QVBoxLayout()
            self.replace_input = QLineEdit()
            replace_layout.addWidget(self.replace_input)
            replace_group.setLayout(replace_layout)
            layout.addWidget(replace_group)

        # Options
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout()
        
        self.match_case = QCheckBox(self.parent.tr("Match Case"))
        self.whole_word = QCheckBox(self.parent.tr("Whole Word"))
        
        options_layout.addWidget(self.match_case)
        options_layout.addWidget(self.whole_word)
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        # Search location (if searching in files)
        if self.in_files:
            location_group = QGroupBox(self.parent.tr("Search in"))
            location_layout = QVBoxLayout()
            self.location_list = QListWidget()
            self.location_list.addItems(self.parent.get_open_folders())
            location_layout.addWidget(self.location_list)
            location_group.setLayout(location_layout)
            layout.addWidget(location_group)

            # Results list
            results_group = QGroupBox(self.parent.tr("Search Results"))
            results_layout = QVBoxLayout()
            self.results_list = QListWidget()
            self.results_list.itemDoubleClicked.connect(self.open_result)
            results_layout.addWidget(self.results_list)
            results_group.setLayout(results_layout)
            layout.addWidget(results_group)

        # Buttons
        button_layout = QHBoxLayout()
        
        if not self.in_files:
            self.find_prev_btn = QPushButton(self.parent.tr("Find Previous"))
            self.find_prev_btn.clicked.connect(self.find_previous)
            button_layout.addWidget(self.find_prev_btn)

        self.find_next_btn = QPushButton(self.parent.tr("Find Next"))
        self.find_next_btn.clicked.connect(self.find_next)
        button_layout.addWidget(self.find_next_btn)

        if self.replace:
            self.replace_btn = QPushButton(self.parent.tr("Replace"))
            self.replace_btn.clicked.connect(self.replace_current)
            button_layout.addWidget(self.replace_btn)

            self.replace_all_btn = QPushButton(self.parent.tr("Replace All"))
            self.replace_all_btn.clicked.connect(self.replace_all)
            button_layout.addWidget(self.replace_all_btn)

        layout.addLayout(button_layout)

    def find_next(self):
        if self.in_files:
            self.search_in_files()
        else:
            self.parent.find_text(
                self.search_input.text(),
                match_case=self.match_case.isChecked(),
                whole_word=self.whole_word.isChecked(),
                forward=True
            )

    def find_previous(self):
        self.parent.find_text(
            self.search_input.text(),
            match_case=self.match_case.isChecked(),
            whole_word=self.whole_word.isChecked(),
            forward=False
        )

    def replace_current(self):
        self.parent.replace_text(
            self.search_input.text(),
            self.replace_input.text(),
            match_case=self.match_case.isChecked(),
            whole_word=self.whole_word.isChecked()
        )

    def replace_all(self):
        self.parent.replace_all_text(
            self.search_input.text(),
            self.replace_input.text(),
            match_case=self.match_case.isChecked(),
            whole_word=self.whole_word.isChecked()
        )

    def search_in_files(self):
        search_text = self.search_input.text()
        if not search_text:
            return

        self.results_list.clear()
        selected_folders = [item.text() for item in self.location_list.selectedItems()]
        if not selected_folders:
            # Wenn keine Ordner ausgewählt sind, alle verwenden
            selected_folders = [self.location_list.item(i).text() for i in range(self.location_list.count())]

        for folder in selected_folders:
            for root, _, files in os.walk(folder):
                for file in files:
                    if file.endswith(('.py', '.txt', '.md', '.json', '.xml', '.html', '.css', '.js')):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                for i, line in enumerate(f, 1):
                                    if search_text in line:
                                        self.results_list.addItem(f"{file_path}:{i}: {line.strip()}")
                        except:
                            continue

    def open_result(self, item):
        # Format ist "Pfad:Zeile: Inhalt"
        text = item.text()
        # Finde die Position des ersten ":"
        first_colon = text.find(":")
        if first_colon == -1:
            return
            
        # Extrahiere den Pfad (alles vor dem ersten ":")
        file_path = text[:first_colon]
        
        # Finde die Position des zweiten ":"
        second_colon = text.find(":", first_colon + 1)
        if second_colon == -1:
            return
            
        # Extrahiere die Zeilennummer (zwischen erstem und zweitem ":")
        try:
            line_num = int(text[first_colon + 1:second_colon])
        except ValueError:
            return

        # Öffne die Datei und springe zur Zeile
        self.parent.load_file(file_path)
        current_editor = self.parent.tabs.currentWidget()
        if current_editor:
            cursor = current_editor.textCursor()
            block = current_editor.document().findBlockByLineNumber(line_num - 1)
            cursor.setPosition(block.position())
            current_editor.setTextCursor(cursor)
            current_editor.centerCursor()

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle(self.parent.tr("Settings"))
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        # Layout
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Tabs für Kategorien
        tabs = QTabWidget()
        layout.addWidget(tabs)

        # Erscheinungsbild Tab
        appearance_tab = QWidget()
        appearance_layout = QVBoxLayout()
        appearance_tab.setLayout(appearance_layout)
        
        # Theme Gruppe
        theme_group = QGroupBox(self.parent.tr("Theme"))
        theme_layout = QVBoxLayout()
        self.theme_combo = QComboBox()
        self.theme_combo.addItems([self.parent.tr("Dark Theme"), self.parent.tr("Light Theme")])
        self.theme_combo.setCurrentText(self.parent.tr("Dark Theme") if self.parent.current_theme == "dark" else self.parent.tr("Light Theme"))
        theme_layout.addWidget(self.theme_combo)
        theme_group.setLayout(theme_layout)
        appearance_layout.addWidget(theme_group)
        
        # Schrift Gruppe
        font_group = QGroupBox(self.parent.tr("Font"))
        font_layout = QVBoxLayout()
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 72)
        self.font_size_spin.setValue(self.parent.tabs.currentWidget().font().pointSize() if self.parent.tabs.count() > 0 else 11)
        font_layout.addWidget(QLabel(self.parent.tr("Font Size") + ":"))
        font_layout.addWidget(self.font_size_spin)
        font_group.setLayout(font_layout)
        appearance_layout.addWidget(font_group)
        
        appearance_layout.addStretch()
        tabs.addTab(appearance_tab, self.parent.tr("Appearance"))

        # Sprache Tab
        language_tab = QWidget()
        language_layout = QVBoxLayout()
        language_tab.setLayout(language_layout)
        
        # Sprache Gruppe
        language_group = QGroupBox(self.parent.tr("Language"))
        language_layout_inner = QVBoxLayout()
        self.language_combo = QComboBox()
        self.language_combo.addItems(["English", "Deutsch", "Français", "Español", "中文", "日本語", "Italiano", "हिंदी"])
        self.language_combo.setCurrentText(self.parent.current_language)
        language_layout_inner.addWidget(self.language_combo)
        language_group.setLayout(language_layout_inner)
        language_layout.addWidget(language_group)
        language_layout.addStretch()
        tabs.addTab(language_tab, self.parent.tr("Language"))

        # Editor Tab
        editor_tab = QWidget()
        editor_layout = QVBoxLayout()
        editor_tab.setLayout(editor_layout)
        
        # Editor Einstellungen Gruppe
        editor_group = QGroupBox(self.parent.tr("Editor Settings"))
        editor_layout_inner = QVBoxLayout()
        
        # Tab Größe
        tab_size_layout = QHBoxLayout()
        tab_size_layout.addWidget(QLabel(self.parent.tr("Tab Size") + ":"))
        self.tab_size_spin = QSpinBox()
        self.tab_size_spin.setRange(2, 8)
        self.tab_size_spin.setValue(4)  # Standard Tab-Größe
        tab_size_layout.addWidget(self.tab_size_spin)
        tab_size_layout.addStretch()
        editor_layout_inner.addLayout(tab_size_layout)
        
        # Auto-Einrückung
        self.auto_indent = QCheckBox(self.parent.tr("Auto Indent"))
        self.auto_indent.setChecked(True)
        editor_layout_inner.addWidget(self.auto_indent)
        
        # Zeilennummern anzeigen
        self.show_line_numbers = QCheckBox(self.parent.tr("Show Line Numbers"))
        self.show_line_numbers.setChecked(True)
        editor_layout_inner.addWidget(self.show_line_numbers)
        
        editor_group.setLayout(editor_layout_inner)
        editor_layout.addWidget(editor_group)
        editor_layout.addStretch()
        tabs.addTab(editor_tab, self.parent.tr("Editor Settings"))

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.button(QDialogButtonBox.Ok).setText(self.parent.tr("OK"))
        button_box.button(QDialogButtonBox.Cancel).setText(self.parent.tr("Cancel"))
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_settings(self):
        return {
            "theme": "dark" if self.theme_combo.currentText() == self.parent.tr("Dark Theme") else "light",
            "language": self.language_combo.currentText(),
            "font_size": self.font_size_spin.value(),
            "tab_size": self.tab_size_spin.value(),
            "auto_indent": self.auto_indent.isChecked(),
            "show_line_numbers": self.show_line_numbers.isChecked()
        }

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = EditorWindow()
    window.show()
    sys.exit(app.exec_())
