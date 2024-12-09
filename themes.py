"""Theme-Definitionen für den Code Editor."""
from PySide6.QtGui import QColor, QPalette
from PySide6.QtCore import Qt

class WindsurfTheme:
    """Basis-Theme-Klasse im Windsurf-Stil."""
    
    @staticmethod
    def apply_theme(app, is_dark=True):
        """Wendet das Theme auf die gesamte Anwendung an."""
        palette = QPalette()
        
        if is_dark:
            # Windsurf Dark Theme
            background = QColor("#1E1E1E")
            foreground = QColor("#FFFFFF")
            selection = QColor("#264F78")
            highlight = QColor("#2977C9")
            
            # Dunklere Akzentfarben
            accent1 = QColor("#252526")  # Für Menüs
            accent2 = QColor("#333333")  # Für aktive Elemente
            
        else:
            # Windsurf Light Theme
            background = QColor("#FFFFFF")
            foreground = QColor("#000000")
            selection = QColor("#ADD6FF")
            highlight = QColor("#2977C9")
            
            # Hellere Akzentfarben
            accent1 = QColor("#F3F3F3")  # Für Menüs
            accent2 = QColor("#E8E8E8")  # Für aktive Elemente

        # Grundlegende Farben
        palette.setColor(QPalette.Window, background)
        palette.setColor(QPalette.WindowText, foreground)
        palette.setColor(QPalette.Base, background)
        palette.setColor(QPalette.AlternateBase, accent1)
        palette.setColor(QPalette.Text, foreground)
        palette.setColor(QPalette.Button, accent1)
        palette.setColor(QPalette.ButtonText, foreground)
        
        # Highlight und Selection
        palette.setColor(QPalette.Highlight, highlight)
        palette.setColor(QPalette.HighlightedText, QColor("white"))

        # Disabled Farben
        palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor("#6D6D6D"))
        palette.setColor(QPalette.Disabled, QPalette.Text, QColor("#6D6D6D"))
        palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor("#6D6D6D"))
        
        app.setPalette(palette)

    @staticmethod
    def get_editor_styles(is_dark=True):
        """Gibt die Stylesheet-Definitionen für den Editor zurück."""
        if is_dark:
            return {
                'background': "#1E1E1E",
                'foreground': "#D4D4D4",
                'selection_background': "#264F78",
                'current_line': "#282828",
                'line_numbers_bg': "#1E1E1E",
                'line_numbers_fg': "#858585",
                'matched_brackets': "#2977C9",
                
                # Syntax-Highlighting
                'keyword': "#569CD6",
                'string': "#CE9178",
                'comment': "#6A9955",
                'function': "#DCDCAA",
                'class': "#4EC9B0",
                'number': "#B5CEA8",
                'operator': "#D4D4D4",
            }
        else:
            return {
                'background': "#FFFFFF",
                'foreground': "#000000",
                'selection_background': "#ADD6FF",
                'current_line': "#F5F5F5",
                'line_numbers_bg': "#F8F8F8",
                'line_numbers_fg': "#237893",
                'matched_brackets': "#2977C9",
                
                # Syntax-Highlighting
                'keyword': "#0000FF",
                'string': "#A31515",
                'comment': "#008000",
                'function': "#795E26",
                'class': "#267F99",
                'number': "#098658",
                'operator': "#000000",
            }
