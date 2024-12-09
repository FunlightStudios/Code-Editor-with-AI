"""Mini-Map Widget für Code-Übersicht im Windsurf-Stil."""
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QRect, QSize, QTimer, QPoint, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import (
    QPainter, QColor, QPainterPath, QLinearGradient,
    QPen, QBrush, QImage, QFontMetrics
)

class MiniMap(QWidget):
    def __init__(self, editor, parent=None):
        if parent is None:
            parent = editor
        super().__init__(parent)
        self.editor = editor
        self.setFixedWidth(80)
        
        # Basis-Setup
        self.cached_image = None
        self.cache_dirty = True
        self.hover_opacity = 0.0
        
        # Performance-Optimierung
        self.block_cache = {}  # Cache für Block-Rendering
        self.last_doc_size = None
        self.last_viewport_size = None
        self.font_metrics = None
        self.update_font_metrics()
        
        # Design-Konfiguration
        self.colors = {
            'background': QColor(30, 30, 30),
            'code': QColor(200, 200, 200, 200),
            'viewport': QColor(100, 100, 100, 20),
            'viewport_border': QColor(120, 120, 120, 40),
            'scroll_bar': QColor(82, 139, 255, 100)
        }
        
        # Performance-Optimierung
        self.update_timer = QTimer(self)
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self.delayed_update)
        
        # Event-Handler
        self.editor.document().contentsChanged.connect(self.mark_cache_dirty)
        self.editor.verticalScrollBar().valueChanged.connect(self.smooth_scroll_update)
        
        # Initialisierung
        self.viewport_rect = QRect()
        self.target_viewport_rect = QRect()
        self.update_viewport_rect()

    def cache_block(self, block, formats, text, x_start, max_width):
        """Cached Block-Rendering für bessere Performance."""
        key = (block.blockNumber(), text, x_start, max_width)
        if key in self.block_cache:
            return self.block_cache[key]

        # Rendere den Block einmal und cache das Ergebnis
        result = []
        if not formats:
            # Unformatierter Text
            clipped_text = self.font_metrics.elidedText(text, Qt.ElideRight, max_width - x_start)
            result.append((self.colors['code'], x_start, clipped_text))
        else:
            x_pos = x_start
            remaining_text = text
            
            for fmt in formats:
                if x_pos >= max_width:
                    break

                start = fmt.start
                length = fmt.length
                
                if start > 0:
                    pre_text = remaining_text[:start]
                    result.append((self.colors['code'], x_pos, pre_text))
                    x_pos += self.font_metrics.horizontalAdvance(pre_text)
                    remaining_text = remaining_text[start:]
                
                format_text = remaining_text[:length]
                color = fmt.format.foreground().color()
                if not color.isValid():
                    color = self.colors['code']
                else:
                    color = QColor(color)
                    color.setAlpha(200)
                
                if x_pos < max_width:
                    text_width = self.font_metrics.horizontalAdvance(format_text)
                    if x_pos + text_width > max_width:
                        format_text = self.font_metrics.elidedText(format_text, Qt.ElideRight, max_width - x_pos)
                    result.append((color, x_pos, format_text))
                    x_pos += self.font_metrics.horizontalAdvance(format_text)
                
                remaining_text = remaining_text[length:]

        self.block_cache[key] = result
        return result

    def update_font_metrics(self):
        """Aktualisiert Font-Metrics für schnellere Berechnungen."""
        mini_font = self.editor.font()
        mini_font.setPointSize(1)
        self.font_metrics = QFontMetrics(mini_font)

    def should_update_cache(self):
        """Prüft, ob Cache aktualisiert werden muss."""
        if not self.editor:
            return False
            
        doc = self.editor.document()
        current_doc_size = doc.size()
        current_viewport_size = self.editor.viewport().size()
        
        # Prüfe ob sich Größen geändert haben
        size_changed = (self.last_doc_size != current_doc_size or 
                       self.last_viewport_size != current_viewport_size)
        
        # Aktualisiere gespeicherte Größen
        if size_changed:
            self.last_doc_size = current_doc_size
            self.last_viewport_size = current_viewport_size
            
        return self.cache_dirty or size_changed

    def update_cache(self):
        """Maximal optimierter Cache-Update."""
        if not self.editor or not self.should_update_cache():
            return

        # Neues Cache-Bild erstellen
        self.cached_image = QImage(
            self.width(),
            self.height(),
            QImage.Format_ARGB32_Premultiplied
        )
        self.cached_image.fill(self.colors['background'])

        painter = QPainter(self.cached_image)
        painter.setRenderHint(QPainter.Antialiasing)

        # Dokumentgröße berechnen
        doc = self.editor.document()
        doc_height = doc.size().height()
        viewport_height = self.editor.viewport().height()
        
        if doc_height <= 0:
            painter.end()
            self.cache_dirty = False
            return

        # Skalierungsfaktor berechnen
        scale_y = float(self.height()) / max(doc_height, viewport_height)
        scale_y *= 0.85

        # Font setzen
        mini_font = self.editor.font()
        mini_font.setPointSize(1)
        painter.setFont(mini_font)

        # Konstanten
        max_width = self.width() - 12
        ascent = self.font_metrics.ascent()

        # Sichtbarer Bereich
        scrollbar = self.editor.verticalScrollBar()
        visible_top = scrollbar.value()
        visible_bottom = visible_top + viewport_height
        
        # Code-Blöcke zeichnen
        block = doc.firstBlock()
        last_y = -1
        block_count = 0

        # Batch-Verarbeitung für bessere Performance
        render_batch = []
        
        while block.isValid() and block_count < 2000:  # Reduzierte Block-Anzahl für bessere Performance
            # Block-Position
            y_pos = self.editor.blockBoundingGeometry(block).y()
            block_height = self.editor.blockBoundingRect(block).height()
            
            # Sichtbarkeitsoptimierung
            if y_pos > visible_bottom + viewport_height:
                break
            if y_pos + block_height < visible_top - viewport_height:
                block = block.next()
                continue

            scaled_y = int(y_pos * scale_y)
            if scaled_y - last_y < 1:
                scaled_y = last_y + 1

            if 0 <= scaled_y <= self.height():
                text = block.text()
                if text.strip():
                    indent_level = len(text) - len(text.lstrip())
                    x_start = 6 + (indent_level * 1.5)
                    
                    # Verwende gecachtes Rendering
                    render_items = self.cache_block(
                        block,
                        block.layout().formats(),
                        text,
                        x_start,
                        max_width
                    )
                    
                    # Füge zum Batch hinzu
                    for color, x_pos, render_text in render_items:
                        render_batch.append((color, x_pos, scaled_y + ascent, render_text))
                    
                    last_y = scaled_y
                    block_count += 1

            block = block.next()

        # Batch-Rendering aller Textelemente
        for color, x_pos, y_pos, text in render_batch:
            painter.setPen(color)
            painter.drawText(x_pos, y_pos, text)

        painter.end()
        self.cache_dirty = False

    def mark_cache_dirty(self):
        """Cache als veraltet markieren."""
        self.cache_dirty = True
        # Cache leeren wenn zu groß
        if len(self.block_cache) > 5000:
            self.block_cache.clear()
        self.update_timer.start(150)

    def delayed_update(self):
        """Verzögertes Update durchführen."""
        if self.cache_dirty:
            self.update_cache()
        self.update()

    def smooth_scroll_update(self):
        """Sanfte Scroll-Animation."""
        self.update_viewport_rect()
        self.update()

    def update_viewport_rect(self):
        """Aktualisiert den sichtbaren Bereich mit korrigierter Größe."""
        if not self.editor:
            return

        # Dokumentgröße und Viewport
        doc = self.editor.document()
        doc_height = doc.size().height()
        viewport_height = self.editor.viewport().height()
        
        # Berechne den Anteil des sichtbaren Bereichs
        visible_ratio = viewport_height / float(max(doc_height, viewport_height))
        
        # Korrigiere die Höhe des Indikators
        # Begrenzen auf maximal 30% der Minimap-Höhe
        indicator_height = min(int(self.height() * visible_ratio), int(self.height() * 0.3))
        indicator_height = max(20, indicator_height)  # Mindesthöhe 20px
        
        # Berechne die Position basierend auf der Scroll-Position
        scrollbar = self.editor.verticalScrollBar()
        if scrollbar.maximum() <= 0:
            indicator_top = 0
        else:
            scroll_ratio = scrollbar.value() / float(scrollbar.maximum())
            available_space = self.height() - indicator_height
            indicator_top = int(scroll_ratio * available_space)
        
        # Neue Zielposition setzen
        self.target_viewport_rect = QRect(
            0,
            indicator_top,
            self.width(),
            indicator_height
        )
        
        # Sanfte Animation zum Ziel
        if not self.viewport_rect.isValid():
            self.viewport_rect = self.target_viewport_rect
        else:
            self.viewport_rect = QRect(
                self.viewport_rect.left(),
                int(0.6 * self.viewport_rect.top() + 0.4 * self.target_viewport_rect.top()),
                self.viewport_rect.width(),
                self.target_viewport_rect.height()
            )
        
        self.update()

    def paintEvent(self, event):
        """Verbesserte Darstellung mit Animationen."""
        if self.cache_dirty:
            self.update_cache()
            
        if not self.cached_image:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Cache zeichnen
        painter.drawImage(0, 0, self.cached_image)

        # Viewport-Bereich mit Verlaufseffekt
        if self.viewport_rect.isValid():
            # Hintergrund mit Verlauf
            gradient = QLinearGradient(
                0, self.viewport_rect.top(),
                0, self.viewport_rect.bottom()
            )
            gradient.setColorAt(0, QColor(255, 255, 255, 10))
            gradient.setColorAt(0.5, QColor(255, 255, 255, 15))
            gradient.setColorAt(1, QColor(255, 255, 255, 10))
            
            painter.fillRect(self.viewport_rect, gradient)
            
            # Dezenter Rahmen
            pen = QPen(self.colors['viewport_border'])
            pen.setWidth(1)
            painter.setPen(pen)
            painter.drawRect(self.viewport_rect)

            # Scroll-Indikator
            painter.fillRect(
                0, self.viewport_rect.top(),
                2, self.viewport_rect.height(),
                self.colors['scroll_bar']
            )

    def mousePressEvent(self, event):
        """Präzise Klick-Navigation."""
        if event.button() == Qt.LeftButton:
            self.scroll_to_position(event.pos().y())

    def mouseMoveEvent(self, event):
        """Smooth Drag-Scrolling."""
        if event.buttons() & Qt.LeftButton:
            self.scroll_to_position(event.pos().y())

    def scroll_to_position(self, y_pos):
        """Präzise Scroll-Position-Berechnung."""
        if not self.editor:
            return

        # Position relativ zum Dokument berechnen
        doc_height = self.editor.document().size().height()
        viewport_height = self.editor.viewport().height()
        
        # Scroll-Position mit Offset berechnen
        scroll_ratio = y_pos / float(self.height())
        scroll_pos = int((doc_height - viewport_height) * scroll_ratio)
        scroll_pos = max(0, min(scroll_pos, self.editor.verticalScrollBar().maximum()))
        
        # Scroll durchführen
        self.editor.verticalScrollBar().setValue(scroll_pos)
