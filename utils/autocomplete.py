"""Autovervollständigungs-System für den Windsurf Code Editor."""
import jedi
from concurrent.futures import ThreadPoolExecutor
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QFrame
from PySide6.QtCore import Qt, Signal, QPoint, QTimer
from PySide6.QtGui import QFontMetrics, QColor

class CompletionList(QListWidget):
    """Liste der Autovervollständigungs-Vorschläge."""
    completion_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setFrameStyle(QFrame.Box | QFrame.Plain)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setMaximumHeight(200)  # Begrenzt die Höhe für bessere Performance
        
        # Performance-Optimierungen
        self.setUniformItemSizes(True)  # Gleiche Größe für alle Items
        self.setLayoutMode(QListWidget.Batched)  # Batch-Layout-Updates
        
        # Styling
        self.setStyleSheet("""
            QListWidget {
                border: 1px solid #666;
                background-color: #2d2d2d;
                color: #ffffff;
                selection-background-color: #404040;
            }
            QListWidget::item {
                padding: 4px;
                font-family: Consolas;
            }
            QListWidget::item:selected {
                background-color: #404040;
            }
        """)
        
    def select_next(self):
        """Wählt den nächsten Eintrag in der Liste."""
        current = self.currentRow()
        if current < self.count() - 1:
            self.setCurrentRow(current + 1)
            
    def select_previous(self):
        """Wählt den vorherigen Eintrag in der Liste."""
        current = self.currentRow()
        if current > 0:
            self.setCurrentRow(current - 1)
            
    def keyPressEvent(self, event):
        """Behandelt Tastatureingaben in der Liste."""
        if event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Tab):
            if self.currentItem():
                self.completion_selected.emit(self.currentItem().text())
                self.hide()
        elif event.key() == Qt.Key_Escape:
            self.hide()
        else:
            super().keyPressEvent(event)

class AutoCompleter:
    """Hauptklasse für die Autovervollständigung."""
    def __init__(self, editor):
        self.editor = editor
        self.completion_list = CompletionList()
        self.completion_list.completion_selected.connect(self.insert_completion)
        self.completion_prefix = ""
        
        # Thread-Pool für asynchrone Vervollständigung
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.current_future = None
        
        # Verzögerungstimer für Vervollständigungsanfragen
        self.delay_timer = QTimer()
        self.delay_timer.setSingleShot(True)
        self.delay_timer.timeout.connect(self.request_completions)
        
    def get_position(self):
        """Ermittelt die aktuelle Cursor-Position für die Vervollständigungsliste."""
        cursor = self.editor.textCursor()
        rect = self.editor.cursorRect(cursor)
        pos = self.editor.mapToGlobal(rect.bottomLeft())
        return QPoint(pos.x(), pos.y() + 5)
        
    def show_completions(self):
        """Startet den Vervollständigungsprozess."""
        self.delay_timer.start(100)  # 100ms Verzögerung
        
    def request_completions(self):
        """Fordert Vervollständigungen asynchron an."""
        try:
            # Aktuelle Position und Code ermitteln
            cursor = self.editor.textCursor()
            text = self.editor.toPlainText()
            line = cursor.blockNumber() + 1
            column = cursor.positionInBlock()
            
            # Vorherige Anfrage abbrechen
            if self.current_future and not self.current_future.done():
                self.current_future.cancel()
            
            # Neue asynchrone Anfrage starten
            self.current_future = self.executor.submit(
                self.get_completions,
                text, line, column
            )
            self.current_future.add_done_callback(self.handle_completions)
            
        except Exception as e:
            print(f"Fehler bei Vervollständigungsanfrage: {str(e)}")
            
    def get_completions(self, text, line, column):
        """Holt Vervollständigungen von Jedi (läuft im Thread)."""
        try:
            script = jedi.Script(text)
            return script.complete(line, column)
        except Exception as e:
            print(f"Jedi-Fehler: {str(e)}")
            return []
            
    def handle_completions(self, future):
        """Verarbeitet die Vervollständigungen aus dem Thread."""
        try:
            if future.cancelled():
                return
                
            completions = future.result()
            if not completions:
                return
                
            # Liste leeren und neue Vorschläge hinzufügen
            self.completion_list.clear()
            
            # Vorschläge zur Liste hinzufügen (maximal 100 für bessere Performance)
            for completion in completions[:100]:
                item = QListWidgetItem(completion.name)
                item.setToolTip(f"{completion.type}: {completion.description}")
                self.completion_list.addItem(item)
            
            # Position und Größe anpassen
            self.completion_list.setCurrentRow(0)
            self.completion_list.resize(300, min(200, 25 * len(completions)))
            
            # Liste anzeigen
            pos = self.get_position()
            self.completion_list.move(pos)
            self.completion_list.show()
            
        except Exception as e:
            print(f"Fehler beim Verarbeiten der Vervollständigungen: {str(e)}")
            
    def insert_completion(self, completion):
        """Fügt die ausgewählte Vervollständigung in den Editor ein."""
        cursor = self.editor.textCursor()
        
        # Aktuelles Wort ermitteln
        cursor.movePosition(cursor.StartOfWord, cursor.KeepAnchor)
        cursor.removeSelectedText()
        
        # Vervollständigung einfügen
        cursor.insertText(completion)
        self.editor.setTextCursor(cursor)
