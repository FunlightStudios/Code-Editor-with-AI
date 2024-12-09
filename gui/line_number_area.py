from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPainter, QColor

class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor
        
    def sizeHint(self):
        return QSize(self.editor.get_line_number_area_width(), 0)
        
    def paintEvent(self, event):
        if not self.editor._line_numbers_enabled:
            return
            
        # Hintergrund zeichnen
        painter = QPainter(self)
        bg_color = QColor(self.editor.theme_styles['line_numbers_bg'])
        painter.fillRect(event.rect(), bg_color)

        # Sichtbaren Bereich des Editors ermitteln
        block = self.editor.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.editor.blockBoundingGeometry(block).translated(self.editor.contentOffset()).top()
        bottom = top + self.editor.blockBoundingRect(block).height()

        # Zeilennummern zeichnen
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor(self.editor.theme_styles['line_numbers_fg']))
                painter.drawText(
                    0, int(top),
                    self.width() - 2, self.editor.fontMetrics().height(),
                    Qt.AlignRight, number
                )

            block = block.next()
            top = bottom
            bottom = top + self.editor.blockBoundingRect(block).height()
            block_number += 1
