from PySide6.QtGui import QFont, QColor, QTextFormat
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPlainTextEdit, QTextEdit


class TextEditWindow(QWidget):
    def __init__(self, text: str | None = None):
        super().__init__()
        self.text = text

        self.layout = QVBoxLayout(self)

        self.editor = QPlainTextEdit()
        self.editor.setPlainText(text or "")

        font = QFont("Consolas", 10)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.editor.setFont(font)

        self.editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.editor.setTabStopDistance(4 * self.editor.fontMetrics().horizontalAdvance(" "))

        self.editor.setStyleSheet("""
            QPlainTextEdit {
                background: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3a3a3a;
                selection-background-color: #264f78;
            }
        """)

        self.editor.cursorPositionChanged.connect(self.highlight_current_line)
        self.highlight_current_line()

        self.layout.addWidget(self.editor)

    def highlight_current_line(self):
        extra = []

        if not self.editor.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            selection.format.setBackground(QColor("#2a2d2e"))
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            selection.cursor = self.editor.textCursor()
            selection.cursor.clearSelection()
            extra.append(selection)

        self.editor.setExtraSelections(extra)
