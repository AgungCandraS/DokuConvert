"""Large clickable operation card with branded local SVG icon."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout

from app.ui.components.common import icon_path
from app.ui.tool_catalog import ToolDefinition


class ToolCard(QPushButton):
    tool_selected = Signal(str)

    def __init__(
        self,
        tool: ToolDefinition,
    ) -> None:
        super().__init__()
        self.tool_name = tool.name
        self.setObjectName("toolCard")
        self.setFlat(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(112)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setAccessibleName(tool.name)
        self.setToolTip(f"Buka pengaturan {tool.name}")
        row = QHBoxLayout(self)
        row.setContentsMargins(14, 13, 14, 13)
        row.setSpacing(12)

        icon_well = QLabel()
        icon_well.setObjectName("toolIcon")
        icon_well.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_well.setFixedSize(48, 48)
        icon_well.setPixmap(QIcon(str(icon_path(tool.icon))).pixmap(40, 40))
        row.addWidget(icon_well, alignment=Qt.AlignmentFlag.AlignVCenter)

        text = QVBoxLayout()
        text.setSpacing(5)
        top_line = QHBoxLayout()
        top_line.setSpacing(7)
        title = QLabel(tool.name)
        title.setObjectName("cardTitle")
        title.setWordWrap(True)
        top_line.addWidget(title, 1)
        format_label = QLabel(tool.input_formats)
        format_label.setObjectName("formatPill")
        top_line.addWidget(format_label, alignment=Qt.AlignmentFlag.AlignTop)

        description_label = QLabel(tool.description)
        description_label.setObjectName("tinyMuted")
        description_label.setWordWrap(True)
        text.addLayout(top_line)
        text.addWidget(description_label)
        text.addStretch(1)
        row.addLayout(text, 1)

        open_label = QLabel("Buka alat")
        open_label.setObjectName("openToolLabel")
        row.addWidget(open_label, alignment=Qt.AlignmentFlag.AlignVCenter)

        # Child labels are visual only; mouse and keyboard activation belong to the button.
        for child in (icon_well, title, format_label, description_label, open_label):
            child.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.clicked.connect(lambda _checked=False: self.tool_selected.emit(self.tool_name))
