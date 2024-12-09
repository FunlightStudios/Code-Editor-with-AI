from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
    QComboBox, QSpinBox, QLabel, QCheckBox,
    QDialogButtonBox, QTabWidget, QWidget, QPushButton
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.FramelessWindowHint)
        self.parent = parent
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
        # Windsurf-Style für das Fenster
        self.setStyleSheet("""
            QDialog {
                background: #1E1E1E;
                color: #FFFFFF;
                border: 1px solid #3C3C3C;
            }
            QWidget#titleBar {
                background: #1E1E1E;
                border-bottom: 1px solid #3C3C3C;
            }
            QLabel#titleLabel {
                color: #FFFFFF;
                padding: 0 10px;
            }
            QPushButton#closeButton {
                background: transparent;
                border: none;
                color: #FFFFFF;
                padding: 6px 12px;
            }
            QPushButton#closeButton:hover {
                background: #E81123;
            }
            QTabWidget::pane {
                border: 1px solid #3C3C3C;
                background: #1E1E1E;
                top: -1px;
            }
            QTabWidget::tab-bar {
                left: 0px;
            }
            QTabBar::tab {
                background: #2D2D2D;
                color: #FFFFFF;
                padding: 8px 16px;
                border: none;
                border-right: 1px solid #3C3C3C;
            }
            QTabBar::tab:selected {
                background: #094771;
            }
            QTabBar::tab:hover:!selected {
                background: rgba(255, 255, 255, 0.1);
            }
            QGroupBox {
                border: 1px solid #3C3C3C;
                border-radius: 0px;
                margin-top: 1em;
                padding-top: 1em;
                color: #FFFFFF;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 3px;
                color: #FFFFFF;
            }
            QComboBox {
                background: #2D2D2D;
                border: 1px solid #3C3C3C;
                border-radius: 0px;
                color: #FFFFFF;
                padding: 5px;
                min-width: 6em;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border: none;
            }
            QComboBox:hover {
                background: #3D3D3D;
            }
            QSpinBox {
                background: #2D2D2D;
                border: 1px solid #3C3C3C;
                border-radius: 0px;
                color: #FFFFFF;
                padding: 5px;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background: #3C3C3C;
                border: none;
                width: 16px;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background: #4C4C4C;
            }
            QCheckBox {
                color: #FFFFFF;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 1px solid #3C3C3C;
                border-radius: 0px;
                background: #2D2D2D;
            }
            QCheckBox::indicator:checked {
                background: #094771;
            }
            QCheckBox::indicator:hover {
                border-color: #4C4C4C;
            }
            QLabel {
                color: #FFFFFF;
            }
            QPushButton {
                background: #2D2D2D;
                border: 1px solid #3C3C3C;
                border-radius: 0px;
                color: #FFFFFF;
                padding: 6px 16px;
                min-width: 80px;
            }
            QPushButton:hover {
                background: #3D3D3D;
            }
            QPushButton:pressed {
                background: #094771;
            }
            QDialogButtonBox {
                border-top: 1px solid #3C3C3C;
                padding: 10px;
            }
        """)
        
        self._setup_ui()
        
        # Mausverfolgungs-Variablen für Fensterbewegung
        self._drag_pos = None

    def _setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(1, 1, 1, 1)  # 1px Rand für das gesamte Fenster
        main_layout.setSpacing(0)
        self.setLayout(main_layout)
        
        # Benutzerdefinierte Titelleiste
        title_bar = QWidget()
        title_bar.setObjectName("titleBar")
        title_bar.setFixedHeight(30)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(10, 0, 0, 0)  # Linker Abstand für den Titel
        title_layout.setSpacing(0)
        
        # Titel
        title_label = QLabel(self.parent.tr("Einstellungen"))
        title_label.setObjectName("titleLabel")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        # Schließen-Button
        close_button = QPushButton("✕")
        close_button.setObjectName("closeButton")
        close_button.setFixedSize(40, 30)
        close_button.clicked.connect(self.close)
        title_layout.addWidget(close_button)
        
        main_layout.addWidget(title_bar)
        
        # Content Layout
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(10, 10, 10, 10)
        
        # Tabs für Kategorien
        self.tab_widget = QTabWidget()
        content_layout.addWidget(self.tab_widget)

        # Erscheinungsbild Tab
        appearance_tab = QWidget()
        appearance_layout = QVBoxLayout()
        appearance_tab.setLayout(appearance_layout)
        
        # Theme Gruppe
        theme_group = QGroupBox(self.parent.tr("Theme"))
        theme_layout = QVBoxLayout()
        self.theme_combo = QComboBox()
        
        # Theme-Optionen direkt als "dark" und "light" speichern
        self.theme_options = {
            self.parent.tr("Dark Theme"): "dark",
            self.parent.tr("Light Theme"): "light"
        }
        self.theme_combo.addItems(list(self.theme_options.keys()))
        
        # Aktuelles Theme auswählen
        current_theme_text = next(key for key, value in self.theme_options.items() 
                                if value == self.parent.current_theme)
        self.theme_combo.setCurrentText(current_theme_text)
        
        theme_layout.addWidget(self.theme_combo)
        theme_group.setLayout(theme_layout)
        appearance_layout.addWidget(theme_group)
        
        # Schrift Gruppe
        font_group = QGroupBox(self.parent.tr("Font"))
        font_layout = QVBoxLayout()
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 72)
        self.font_size_spin.setValue(
            self.parent.tab_widget.currentWidget().font().pointSize()
            if self.parent.tab_widget.count() > 0
            else 11
        )
        font_layout.addWidget(QLabel(self.parent.tr("Font Size") + ":"))
        font_layout.addWidget(self.font_size_spin)
        font_group.setLayout(font_layout)
        appearance_layout.addWidget(font_group)
        
        appearance_layout.addStretch()
        self.tab_widget.addTab(appearance_tab, self.parent.tr("Appearance"))

        # Sprache Tab
        language_tab = QWidget()
        language_layout = QVBoxLayout()
        language_tab.setLayout(language_layout)
        
        # Sprache Gruppe
        language_group = QGroupBox(self.parent.tr("Language"))
        language_layout_inner = QVBoxLayout()
        self.language_combo = QComboBox()
        available_languages = list(self.parent.translations.keys())
        available_languages.sort()
        self.language_combo.addItems(available_languages)
        self.language_combo.setCurrentText(self.parent.current_language)
        language_layout_inner.addWidget(self.language_combo)
        language_group.setLayout(language_layout_inner)
        language_layout.addWidget(language_group)
        language_layout.addStretch()
        self.tab_widget.addTab(language_tab, self.parent.tr("Language"))

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
        self.tab_size_spin.setValue(4)
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
        self.tab_widget.addTab(editor_tab, self.parent.tr("Editor Settings"))
        
        main_layout.addLayout(content_layout)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.Ok).setText(self.parent.tr("OK"))
        button_box.button(QDialogButtonBox.Cancel).setText(self.parent.tr("Cancel"))
        main_layout.addWidget(button_box)
        
        # Event-Handler für Fensterbewegung
        title_bar.mousePressEvent = self._title_bar_mouse_press
        title_bar.mouseMoveEvent = self._title_bar_mouse_move

    def _title_bar_mouse_press(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            
    def _title_bar_mouse_move(self, event):
        if self._drag_pos is not None:
            self.move(event.globalPos() - self._drag_pos)

    def accept(self):
        """Wird aufgerufen, wenn der Benutzer auf OK klickt."""
        settings = self.get_settings()
        
        # Theme aktualisieren
        if settings['theme'] != self.parent.current_theme:
            self.parent.current_theme = settings['theme']
            self.parent.editor_window.update_theme(settings['theme'] == 'dark')
        
        # Sprache aktualisieren
        if settings['language'] != self.parent.current_language:
            self.parent.current_language = settings['language']
            self.parent.update_translations()
        
        # Editor-Einstellungen aktualisieren
        editor = self.parent.editor_window.get_current_editor()
        if editor:
            editor.setFont(QFont(editor.font().family(), settings['font_size']))
            editor.set_line_numbers_visible(settings['show_line_numbers'])
            editor.set_auto_indent(settings['auto_indent'])
            editor.setTabStopWidth(settings['tab_size'] * editor.fontMetrics().width(' '))
        
        super().accept()

    def get_settings(self):
        # Theme direkt als "dark" oder "light" zurückgeben
        theme_text = self.theme_combo.currentText()
        theme = self.theme_options[theme_text]
        
        return {
            'theme': theme,
            'language': self.language_combo.currentText(),
            'font_size': self.font_size_spin.value(),
            'tab_size': self.tab_size_spin.value(),
            'auto_indent': self.auto_indent.isChecked(),
            'show_line_numbers': self.show_line_numbers.isChecked()
        }
