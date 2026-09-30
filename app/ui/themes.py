"""Application-wide Qt Style Sheets and the shared DocuConvert color system."""

LIGHT_STYLESHEET = """
* { font-size: 13px; }
QWidget#root { color: #26332c; }
QWidget#root, QWidget#content, QWidget#page, QWidget#jobPage { background: #f3f4f1; color: #26332c; }
QWidget#sidebar { background: #e9ece7; border-right: 1px solid #d8ded8; }
QLabel#brandIcon { border: 1px solid #d4ddd4; border-radius: 12px; background: #f8faf7; }
QLabel#brandName { color: #26332c; font-size: 16px; font-weight: 700; }
QLabel#brandSub, QLabel#sectionLabel { color: #5d6b61; font-size: 10px; font-weight: 700; }
QLabel#sectionLabel { padding: 4px 9px; }
QPushButton#navButton { text-align: left; padding: 10px 12px; border-radius: 8px; border: 1px solid transparent; color: #526159; background: transparent; font-weight: 600; }
QPushButton#navButton:hover { background: #e0e7df; color: #2f4937; }
QPushButton#navButton:checked { color: #244d32; background: #dce8dc; border-color: #c6d8c8; font-weight: 700; }
QFrame#privacyCard, QFrame#surface, QFrame#tipCard, QFrame#fileDropList, QFrame#statusPanel { border: 1px solid #dce2dc; border-radius: 10px; background: #fafbf9; }
QFrame#privacyCard { background: #e2e9e1; border-color: #d0dbd0; }
QLabel#privacyTitle, QLabel#tipEyebrow { color: #4e6a55; font-size: 10px; font-weight: 700; }
QLabel#breadcrumb { color: #5d6b61; font-size: 11px; }
QLabel#pageTitle { color: #26332c; font-size: 27px; font-weight: 700; }
QLabel#sectionHeading { color: #303c34; font-size: 16px; font-weight: 700; }
QLabel#mutedText { color: #59685e; font-size: 13px; }
QLabel#tinyMuted, QLabel#formatsLabel { color: #5d6b61; font-size: 11px; }
QLabel#dropTitle { color: #2e4335; font-size: 17px; font-weight: 700; }
QFrame#dropZone { border: 1px dashed #9bac9d; border-radius: 12px; background: #f8faf7; }
QFrame#dropZone:hover { border-color: #64806b; background: #f0f5ef; }
QPushButton#primaryButton { color: #ffffff; background: #416c4c; border: 1px solid #416c4c; border-radius: 7px; padding: 9px 17px; font-weight: 700; }
QPushButton#primaryButton:hover { background: #345a3f; border-color: #345a3f; }
QPushButton#primaryButton:pressed { background: #294b34; }
QPushButton#primaryButton:disabled { color: #f4f6f3; background: #899b8d; border-color: #899b8d; }
QPushButton#dangerButton { color: #ffffff; background: #a4423a; border: 1px solid #a4423a; border-radius: 7px; padding: 7px 12px; font-weight: 700; }
QPushButton#dangerButton:hover { background: #87352f; border-color: #87352f; }
QPushButton#secondaryButton, QPushButton#quietButton { color: #42544a; background: #f8faf7; border: 1px solid #d3dcd4; border-radius: 7px; padding: 7px 12px; }
QPushButton#secondaryButton:hover, QPushButton#quietButton:hover { border-color: #91a593; background: #eef3ed; }
QPushButton#textButton { color: #416c4c; background: transparent; border: 0; font-weight: 700; }
QPushButton#textButton:hover { color: #294b34; }
QLineEdit#inputField, QComboBox, QSpinBox, QListWidget#fileList { color: #2b3830; border: 1px solid #d3dcd4; border-radius: 6px; padding: 7px 9px; background: #ffffff; selection-background-color: #dce8dc; }
QLineEdit#inputField:focus, QComboBox:focus, QSpinBox:focus { border: 1px solid #62816a; }
QComboBox, QSpinBox { min-height: 20px; }
QComboBox QAbstractItemView { color: #26332c; background: #ffffff; border: 1px solid #91a593; selection-color: #26332c; selection-background-color: #dce8dc; outline: 0; }
QComboBox QAbstractItemView::item { min-height: 28px; padding: 4px 8px; }
QComboBox::drop-down { width: 28px; border: 0; }
QComboBox::down-arrow { image: url(__LIGHT_ARROW__); width: 12px; height: 12px; }
QListWidget#fileList { padding: 4px; }
QListWidget#fileList::item { padding: 7px; border-radius: 4px; }
QListWidget#fileList::item:selected { color: #263c2d; background: #e4eee3; }
QCheckBox, QRadioButton { color: #4d5b52; spacing: 7px; }
QCheckBox::indicator, QRadioButton::indicator { width: 15px; height: 15px; }
QLabel#warningText { color: #754c2f; background: #f6eee4; border: 1px solid #e8d6c1; border-radius: 7px; padding: 8px; }
QLabel#emptyFilesHint { color: #5d6b61; font-size: 12px; }
QFrame#statusPanel { background: #edf3ec; border-color: #d4e1d3; }
QProgressBar#jobProgress { border: 0; border-radius: 6px; background: #dce6da; min-height: 10px; max-height: 10px; }
QProgressBar#jobProgress::chunk { background: #62816a; border-radius: 6px; }
QLabel#progressValue { color: #416c4c; font-size: 11px; font-weight: 700; }
QPushButton#toolCard { text-align: left; border: 1px solid #dce2dc; border-radius: 10px; background: #fafbf9; }
QPushButton#toolCard:hover { border-color: #a6b8a7; background: #f3f7f2; }
QPushButton#toolCard:focus { border: 2px solid #62816a; }
QPushButton#toolCard:pressed { background: #e9f0e8; }
QLabel#toolIcon { border: 1px solid #e2e8e1; border-radius: 10px; background: #f1f5f0; }
QLabel#cardTitle { color: #2c3931; font-size: 13px; font-weight: 700; }
QLabel#formatPill { color: #52665a; font-size: 9px; font-weight: 700; padding: 4px 6px; border: 1px solid #dce4dc; border-radius: 5px; background: #f2f6f1; }
QLabel#openToolLabel { color: #5d6b61; font-size: 10px; }
QLabel#statusText { color: #627067; font-size: 11px; }
QLabel#statusDot { color: #4f7959; font-size: 11px; }
QLabel#statusWarning { color: #754c2f; background: #f6eee4; border: 1px solid #e8d6c1; border-radius: 7px; padding: 8px; }
QLabel#statusError { color: #843b35; background: #f7e9e7; border: 1px solid #e8cfcb; border-radius: 7px; padding: 8px; }
QLabel#statusSuccess { color: #285b35; background: #e8f2e8; border: 1px solid #cee1cf; border-radius: 7px; padding: 8px; }
QFrame#dependencyNotice { border: 1px solid #e8d6c1; border-radius: 8px; background: #f6eee4; }
QWidget#historyRow { border: 1px solid #dce2dc; border-radius: 8px; background: #fafbf9; }
QListWidget#historyList { border: 0; background: transparent; }
QLabel#historyTitle { color: #303c34; font-weight: 700; }
QLabel#historyStatus_completed, QLabel#historyStatus_failed, QLabel#historyStatus_cancelled { border-radius: 6px; padding: 5px 8px; font-weight: 700; }
QLabel#historyStatus_completed { color: #285b35; background: #e8f2e8; }
QLabel#historyStatus_failed { color: #843b35; background: #f7e9e7; }
QLabel#historyStatus_cancelled { color: #6b5b35; background: #f2eee0; }
QScrollArea { border: 0; background: transparent; }
QScrollArea QWidget#scrollContents { background: transparent; }
QScrollBar:vertical { width: 10px; background: transparent; margin: 2px; }
QScrollBar::handle:vertical { background: #c4cec5; border-radius: 4px; min-height: 28px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
"""

DARK_STYLESHEET = """
* { font-size: 13px; }
QWidget#root { color: #e3e9e4; }
QWidget#root, QWidget#content, QWidget#page, QWidget#jobPage { background: #202722; color: #e3e9e4; }
QWidget#sidebar { background: #1d241f; border-right: 1px solid #374239; }
QLabel#brandIcon { border: 1px solid #435147; border-radius: 12px; background: #29342c; }
QLabel#brandName { color: #e7ede8; font-size: 16px; font-weight: 700; }
QLabel#brandSub, QLabel#sectionLabel { color: #a0afa3; font-size: 10px; font-weight: 700; }
QLabel#sectionLabel { padding: 4px 9px; }
QPushButton#navButton { text-align: left; padding: 10px 12px; border-radius: 8px; border: 1px solid transparent; color: #b8c3ba; background: transparent; font-weight: 600; }
QPushButton#navButton:hover { background: #2b362e; color: #edf3ee; }
QPushButton#navButton:checked { color: #e2efe3; background: #304336; border-color: #435e49; font-weight: 700; }
QFrame#privacyCard, QFrame#surface, QFrame#tipCard, QFrame#fileDropList, QFrame#statusPanel { border: 1px solid #39453c; border-radius: 10px; background: #252e28; }
QFrame#privacyCard { background: #29372d; border-color: #3b5140; }
QLabel#privacyTitle, QLabel#tipEyebrow { color: #b5d0b8; font-size: 10px; font-weight: 700; }
QLabel#breadcrumb { color: #a8b5ab; font-size: 11px; }
QLabel#pageTitle { color: #ecf1ed; font-size: 27px; font-weight: 700; }
QLabel#sectionHeading { color: #dce5dd; font-size: 16px; font-weight: 700; }
QLabel#mutedText { color: #b0bcb2; font-size: 13px; }
QLabel#tinyMuted, QLabel#formatsLabel { color: #9eaca1; font-size: 11px; }
QLabel#dropTitle { color: #e3ece4; font-size: 17px; font-weight: 700; }
QFrame#dropZone { border: 1px dashed #657a69; border-radius: 12px; background: #252e28; }
QFrame#dropZone:hover { border-color: #8fab93; background: #2b382e; }
QPushButton#primaryButton { color: #ffffff; background: #4c7757; border: 1px solid #4c7757; border-radius: 7px; padding: 9px 17px; font-weight: 700; }
QPushButton#primaryButton:hover { background: #5a8765; border-color: #5a8765; }
QPushButton#primaryButton:pressed { background: #3d6548; }
QPushButton#primaryButton:disabled { color: #d7ded8; background: #526456; border-color: #526456; }
QPushButton#dangerButton { color: #ffffff; background: #a74740; border: 1px solid #a74740; border-radius: 7px; padding: 7px 12px; font-weight: 700; }
QPushButton#dangerButton:hover { background: #c15c53; border-color: #c15c53; }
QPushButton#secondaryButton, QPushButton#quietButton { color: #d0dbd1; background: #2b352e; border: 1px solid #455248; border-radius: 7px; padding: 7px 12px; }
QPushButton#secondaryButton:hover, QPushButton#quietButton:hover { border-color: #708575; background: #333f36; }
QPushButton#textButton { color: #b4d0b8; background: transparent; border: 0; font-weight: 700; }
QPushButton#textButton:hover { color: #d5e7d7; }
QLineEdit#inputField, QComboBox, QSpinBox, QListWidget#fileList { color: #e1e9e2; border: 1px solid #465349; border-radius: 6px; padding: 7px 9px; background: #202822; selection-background-color: #3b5941; }
QLineEdit#inputField:focus, QComboBox:focus, QSpinBox:focus { border: 1px solid #8cad91; }
QComboBox, QSpinBox { min-height: 20px; }
QComboBox QAbstractItemView { color: #e3e9e4; background: #252e28; border: 1px solid #708575; selection-color: #ffffff; selection-background-color: #3b5941; outline: 0; }
QComboBox QAbstractItemView::item { min-height: 28px; padding: 4px 8px; }
QComboBox::drop-down { width: 28px; border: 0; }
QComboBox::down-arrow { image: url(__DARK_ARROW__); width: 12px; height: 12px; }
QListWidget#fileList { padding: 4px; }
QListWidget#fileList::item { padding: 7px; border-radius: 4px; }
QListWidget#fileList::item:selected { color: #edf4ee; background: #34483a; }
QCheckBox, QRadioButton { color: #bfcbc1; spacing: 7px; }
QCheckBox::indicator, QRadioButton::indicator { width: 15px; height: 15px; }
QLabel#warningText { color: #e5c5a6; background: #3c332b; border: 1px solid #63513f; border-radius: 7px; padding: 8px; }
QLabel#emptyFilesHint { color: #a7b3a9; font-size: 12px; }
QFrame#statusPanel { background: #2a382d; border-color: #405844; }
QProgressBar#jobProgress { border: 0; border-radius: 6px; background: #3a493c; min-height: 10px; max-height: 10px; }
QProgressBar#jobProgress::chunk { background: #8eae93; border-radius: 6px; }
QLabel#progressValue { color: #b4d0b8; font-size: 11px; font-weight: 700; }
QPushButton#toolCard { text-align: left; border: 1px solid #39453c; border-radius: 10px; background: #252e28; }
QPushButton#toolCard:hover { border-color: #617966; background: #2b362e; }
QPushButton#toolCard:focus { border: 2px solid #8cad91; }
QPushButton#toolCard:pressed { background: #303d33; }
QLabel#toolIcon { border: 1px solid #3b493e; border-radius: 10px; background: #2c382f; }
QLabel#cardTitle { color: #e2eae3; font-size: 13px; font-weight: 700; }
QLabel#formatPill { color: #bacabd; font-size: 9px; font-weight: 700; padding: 4px 6px; border: 1px solid #455348; border-radius: 5px; background: #2d392f; }
QLabel#openToolLabel { color: #a9b6ab; font-size: 10px; }
QLabel#statusText { color: #aebbb0; font-size: 11px; }
QLabel#statusDot { color: #a4c3a8; font-size: 11px; }
QLabel#statusWarning { color: #e5c5a6; background: #3c332b; border: 1px solid #63513f; border-radius: 7px; padding: 8px; }
QLabel#statusError { color: #f0b5ae; background: #432f2e; border: 1px solid #684442; border-radius: 7px; padding: 8px; }
QLabel#statusSuccess { color: #b9dbbe; background: #293a2e; border: 1px solid #405a45; border-radius: 7px; padding: 8px; }
QFrame#dependencyNotice { border: 1px solid #63513f; border-radius: 8px; background: #3c332b; }
QWidget#historyRow { border: 1px solid #39453c; border-radius: 8px; background: #252e28; }
QListWidget#historyList { border: 0; background: transparent; }
QLabel#historyTitle { color: #dce5dd; font-weight: 700; }
QLabel#historyStatus_completed, QLabel#historyStatus_failed, QLabel#historyStatus_cancelled { border-radius: 6px; padding: 5px 8px; font-weight: 700; }
QLabel#historyStatus_completed { color: #b9dbbe; background: #293a2e; }
QLabel#historyStatus_failed { color: #f0b5ae; background: #432f2e; }
QLabel#historyStatus_cancelled { color: #ddd1a9; background: #3b382a; }
QScrollArea { border: 0; background: transparent; }
QScrollArea QWidget#scrollContents { background: transparent; }
QScrollBar:vertical { width: 10px; background: transparent; margin: 2px; }
QScrollBar::handle:vertical { background: #4b5b4e; border-radius: 4px; min-height: 28px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
"""
