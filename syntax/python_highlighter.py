from PySide6.QtCore import Qt
from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont

class PythonHighlighter(QSyntaxHighlighter):
    """Syntax Highlighter für Python-Code im Windsurf-Stil."""

    def __init__(self, parent=None, theme_styles=None):
        super().__init__(parent)
        self.theme_styles = theme_styles or {}
        self.initialize_formats()

    def initialize_formats(self):
        """Initialisiert die Formatierungen für verschiedene Syntax-Elemente."""
        self.formats = {
            'keyword': self.create_format(self.theme_styles.get('keyword', "#569CD6")),
            'string': self.create_format(self.theme_styles.get('string', "#CE9178")),
            'comment': self.create_format(self.theme_styles.get('comment', "#6A9955")),
            'function': self.create_format(self.theme_styles.get('function', "#DCDCAA")),
            'class': self.create_format(self.theme_styles.get('class', "#4EC9B0")),
            'number': self.create_format(self.theme_styles.get('number', "#B5CEA8")),
            'operator': self.create_format(self.theme_styles.get('operator', "#D4D4D4")),
        }

    def create_format(self, color):
        """Erstellt ein Textformat mit der angegebenen Farbe."""
        text_format = QTextCharFormat()
        text_format.setForeground(QColor(color))
        return text_format

    def update_theme(self, theme_styles):
        """Aktualisiert die Farben basierend auf dem aktuellen Theme."""
        self.theme_styles = theme_styles
        self.initialize_formats()
        self.rehighlight()

    def highlightBlock(self, text):
        """Hebt einen Textblock entsprechend der Python-Syntax hervor."""
        # Keywords
        keywords = [
            'and', 'as', 'assert', 'break', 'class', 'continue', 'def',
            'del', 'elif', 'else', 'except', 'False', 'finally', 'for',
            'from', 'global', 'if', 'import', 'in', 'is', 'lambda', 'None',
            'nonlocal', 'not', 'or', 'pass', 'raise', 'return', 'True',
            'try', 'while', 'with', 'yield'
        ]
        
        for word in text.split():
            if word in keywords:
                index = text.index(word)
                self.setFormat(index, len(word), self.formats['keyword'])

        # Strings (einfache und doppelte Anführungszeichen)
        quote_chars = ['"', "'"]
        for quote in quote_chars:
            in_string = False
            start_pos = 0
            
            for i, char in enumerate(text):
                if char == quote and (i == 0 or text[i-1] != '\\'):
                    if not in_string:
                        start_pos = i
                        in_string = True
                    else:
                        self.setFormat(start_pos, i - start_pos + 1, self.formats['string'])
                        in_string = False

        # Kommentare
        if '#' in text:
            comment_pos = text.index('#')
            self.setFormat(comment_pos, len(text) - comment_pos, self.formats['comment'])

        # Funktionen und Klassen
        import re
        # Funktionsdefinitionen
        func_matches = re.finditer(r'def\s+(\w+)\s*\(', text)
        for match in func_matches:
            self.setFormat(match.start(1), len(match.group(1)), self.formats['function'])

        # Klassendefinitionen
        class_matches = re.finditer(r'class\s+(\w+)\s*[:\(]', text)
        for match in class_matches:
            self.setFormat(match.start(1), len(match.group(1)), self.formats['class'])

        # Zahlen
        number_pattern = r'\b\d+\b'
        for match in re.finditer(number_pattern, text):
            self.setFormat(match.start(), match.end() - match.start(), self.formats['number'])

        # Operatoren
        operators = ['+', '-', '*', '/', '//', '%', '**', '=', '==', '!=', '<', '>', '<=', '>=']
        for op in operators:
            pos = 0
            while True:
                pos = text.find(op, pos)
                if pos == -1:
                    break
                self.setFormat(pos, len(op), self.formats['operator'])
                pos += len(op)
