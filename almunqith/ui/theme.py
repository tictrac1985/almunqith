"""Dark theme stylesheet (colors from the approved mockup)."""

DARK_QSS = """
* { font-family: 'Segoe UI', Tahoma, sans-serif; }
QMainWindow, QWidget { background: #11141b; color: #eef2ff; }
QLabel { background: transparent; }
QLabel#subtitle { color: #8b93a7; font-size: 13px; }
QLabel#warning { background: #3a2a12; border: 1px solid #a16207;
                 color: #fbbf24; border-radius: 8px; padding: 9px 14px; }
QLabel#okstatus { color: #4ade80; }
QLabel#badstatus { color: #f87171; }
QLabel#stepchip { color: #8b93a7; padding: 4px 12px; font-size: 12px; }
QLabel#stepchip[active="true"] { background: #3b82f6; color: white;
                                 border-radius: 13px; }
QPushButton { background: #1c2333; border: 1px solid #2a3040;
              border-radius: 10px; padding: 10px 18px; color: #eef2ff;
              font-size: 14px; }
QPushButton:hover { border-color: #3b82f6; }
QPushButton:disabled { color: #565d6e; }
QPushButton#primary { background: #2563eb; border: none; font-weight: bold;
                      padding: 11px 34px; font-size: 15px; }
QPushButton#primary:hover { background: #3b82f6; }
QPushButton#primary:disabled { background: #1c2333; color: #565d6e; }
QPushButton#success { background: #16a34a; border: none; font-weight: bold;
                      padding: 11px 28px; font-size: 15px; }
QPushButton#card { text-align: right; padding: 16px; font-size: 14px; }
QPushButton#card:checked { border: 2px solid #3b82f6; }
QPushButton#typebtn { font-size: 16px; padding: 22px; }
QPushButton#typebtn:checked { border: 2px solid #3b82f6; background: #1d2a45; }
QProgressBar { background: #1c2333; border: none; border-radius: 8px;
               height: 16px; text-align: center; color: white; }
QProgressBar::chunk { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                      stop:0 #3b82f6, stop:1 #2563eb); border-radius: 8px; }
QListWidget { background: #151926; border: 1px solid #2a3040;
              border-radius: 10px; }
QListWidget::item { color: #c7cede; padding: 4px; }
QListWidget::item:selected { background: #1d2a45; }
QTabWidget::pane { border: 1px solid #2a3040; border-radius: 8px; }
QTabBar::tab { background: #1c2333; color: #8b93a7; padding: 7px 16px;
               border-top-left-radius: 8px; border-top-right-radius: 8px; }
QTabBar::tab:selected { background: #3b82f6; color: white; }
QCheckBox { color: #c7cede; }
QScrollArea { border: none; }
"""
