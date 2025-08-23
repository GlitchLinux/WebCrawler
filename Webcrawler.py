#!/usr/bin/env python3

import os
import gi

# Set GTK theme to dark
os.environ['GTK_THEME'] = 'Orchis:dark'

# Now, you can use GTK for your GUI
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import sys
import os
import json
import requests
from urllib.parse import urljoin, urlparse, unquote
from bs4 import BeautifulSoup
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QListWidget, QListWidgetItem, QLabel, 
                             QLineEdit, QProgressBar, QFileDialog, QMessageBox,
                             QSplitter, QTextEdit, QFrame, QTreeWidget, QTreeWidgetItem,
                             QTableWidget, QTableWidgetItem, QHeaderView, QMenuBar,
                             QMenu, QToolBar, QStatusBar, QMainWindow, QComboBox,
                             QDialog, QSpinBox, QCheckBox, QGridLayout, QFontDialog,
                             QScrollArea)
from PyQt6.QtGui import QIcon, QFont, QPalette, QColor, QAction, QFontDatabase, QPixmap
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize, QUrl

# Try to import WebEngine, fall back to simple text view if not available
try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    WEBENGINE_AVAILABLE = True
except ImportError:
    WEBENGINE_AVAILABLE = False
    print("PyQt6-WebEngine not available. Surf mode will use simple text rendering.")

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.setWindowTitle('WebCrawler Settings')
        self.setModal(True)
        self.setMinimumSize(400, 300)
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout()
        
        # Font settings
        font_group = QFrame()
        font_layout = QGridLayout()
        
        font_layout.addWidget(QLabel('Font Family:'), 0, 0)
        self.font_combo = QComboBox()
        font_layout.addWidget(self.font_combo, 0, 1)
        
        font_layout.addWidget(QLabel('Font Size:'), 1, 0)
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 72)
        self.font_size_spin.setValue(12)
        font_layout.addWidget(self.font_size_spin, 1, 1)
        
        self.font_dialog_button = QPushButton('Choose Font...')
        self.font_dialog_button.clicked.connect(self.open_font_dialog)
        font_layout.addWidget(self.font_dialog_button, 2, 0, 1, 2)
        
        # Now populate fonts AFTER widgets are created
        self.populate_fonts()
        
        font_group.setLayout(font_layout)
        layout.addWidget(QLabel('Font Settings'))
        layout.addWidget(font_group)
        
        # View settings
        view_group = QFrame()
        view_layout = QVBoxLayout()
        
        self.show_tree_check = QCheckBox('Show Directory Tree')
        self.show_tree_check.setChecked(True)
        view_layout.addWidget(self.show_tree_check)
        
        self.show_info_check = QCheckBox('Show File Information Panel')
        self.show_info_check.setChecked(True)
        view_layout.addWidget(self.show_info_check)
        
        self.show_toolbar_check = QCheckBox('Show Toolbar')
        self.show_toolbar_check.setChecked(True)
        view_layout.addWidget(self.show_toolbar_check)
        
        self.show_statusbar_check = QCheckBox('Show Status Bar')
        self.show_statusbar_check.setChecked(True)
        view_layout.addWidget(self.show_statusbar_check)
        
        view_group.setLayout(view_layout)
        layout.addWidget(QLabel('View Settings'))
        layout.addWidget(view_group)
        
        # Preview settings
        preview_group = QFrame()
        preview_layout = QVBoxLayout()
        
        self.show_image_preview_check = QCheckBox('Enable Image Preview')
        self.show_image_preview_check.setChecked(False)
        preview_layout.addWidget(self.show_image_preview_check)
        
        self.show_text_preview_check = QCheckBox('Enable Text File Preview')
        self.show_text_preview_check.setChecked(False)
        preview_layout.addWidget(self.show_text_preview_check)
        
        preview_group.setLayout(preview_layout)
        layout.addWidget(QLabel('Preview Settings'))
        layout.addWidget(preview_group)
        
        # Download settings
        download_group = QFrame()
        download_layout = QGridLayout()
        
        download_layout.addWidget(QLabel('Default Download Path:'), 0, 0)
        self.download_path_edit = QLineEdit()
        self.download_path_edit.setText(os.path.join(os.path.expanduser('~'), 'Downloads'))
        download_layout.addWidget(self.download_path_edit, 0, 1)
        
        self.browse_download_path_button = QPushButton('Browse...')
        self.browse_download_path_button.clicked.connect(self.browse_download_path)
        download_layout.addWidget(self.browse_download_path_button, 0, 2)
        
        download_group.setLayout(download_layout)
        layout.addWidget(QLabel('Download Settings'))
        layout.addWidget(download_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.apply_button = QPushButton('Apply')
        self.apply_button.clicked.connect(self.apply_settings)
        button_layout.addWidget(self.apply_button)
        
        self.ok_button = QPushButton('OK')
        self.ok_button.clicked.connect(self.accept_settings)
        button_layout.addWidget(self.ok_button)
        
        self.cancel_button = QPushButton('Cancel')
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
    def populate_fonts(self):
        font_db = QFontDatabase
        families = font_db.families()
        self.font_combo.addItems(families)
        
        # Try to set current font
        if self.parent_window:
            current_font = self.parent_window.custom_font
            index = self.font_combo.findText(current_font.family())
            if index >= 0:
                self.font_combo.setCurrentIndex(index)
            self.font_size_spin.setValue(current_font.pointSize())
            
    def open_font_dialog(self):
        current_font = QFont(self.font_combo.currentText(), self.font_size_spin.value())
        font, ok = QFontDialog.getFont(current_font, self)
        if ok:
            self.font_combo.setCurrentText(font.family())
            self.font_size_spin.setValue(font.pointSize())
            
    def load_settings(self, settings):
        if 'font_family' in settings:
            index = self.font_combo.findText(settings['font_family'])
            if index >= 0:
                self.font_combo.setCurrentIndex(index)
        if 'font_size' in settings:
            self.font_size_spin.setValue(settings['font_size'])
        if 'show_tree' in settings:
            self.show_tree_check.setChecked(settings['show_tree'])
        if 'show_info' in settings:
            self.show_info_check.setChecked(settings['show_info'])
        if 'show_toolbar' in settings:
            self.show_toolbar_check.setChecked(settings['show_toolbar'])
        if 'show_statusbar' in settings:
            self.show_statusbar_check.setChecked(settings['show_statusbar'])
        if 'show_image_preview' in settings:
            self.show_image_preview_check.setChecked(settings['show_image_preview'])
        if 'show_text_preview' in settings:
            self.show_text_preview_check.setChecked(settings['show_text_preview'])
        if 'default_download_path' in settings:
            self.download_path_edit.setText(settings['default_download_path'])
    
    def browse_download_path(self):
        """Browse for download directory"""
        directory = QFileDialog.getExistingDirectory(
            self, 
            'Select Download Directory',
            self.download_path_edit.text()
        )
        if directory:
            self.download_path_edit.setText(directory)
            
    def get_settings(self):
        return {
            'font_family': self.font_combo.currentText(),
            'font_size': self.font_size_spin.value(),
            'show_tree': self.show_tree_check.isChecked(),
            'show_info': self.show_info_check.isChecked(),
            'show_toolbar': self.show_toolbar_check.isChecked(),
            'show_statusbar': self.show_statusbar_check.isChecked(),
            'show_image_preview': self.show_image_preview_check.isChecked(),
            'show_text_preview': self.show_text_preview_check.isChecked(),
            'default_download_path': self.download_path_edit.text()
        }
        
    def apply_settings(self):
        if self.parent_window:
            self.parent_window.apply_settings(self.get_settings())
            
    def accept_settings(self):
        self.apply_settings()
        self.accept()

class DownloadThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, url, filepath):
        super().__init__()
        self.url = url
        self.filepath = filepath
        
    def run(self):
        try:
            response = requests.get(self.url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(self.filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress_percent = int((downloaded / total_size) * 100)
                            self.progress.emit(progress_percent)
                        
            self.finished.emit(True, f"Downloaded successfully to {self.filepath}")
        except Exception as e:
            self.finished.emit(False, f"Download failed: {str(e)}")

class MultiDownloadManager(QThread):
    file_progress = pyqtSignal(int, int, str)  # file_index, progress_percent, filename
    overall_progress = pyqtSignal(int, int, str, int)  # completed_files, total_files, current_filename, current_file_percent
    finished = pyqtSignal(bool, str)
    
    def __init__(self, download_items, download_path):
        super().__init__()
        self.download_items = download_items  # List of (url, filename) tuples
        self.download_path = download_path
        self.completed_files = 0
        
    def run(self):
        try:
            total_files = len(self.download_items)
            
            for i, (url, filename) in enumerate(self.download_items):
                filepath = os.path.join(self.download_path, filename)
                
                # Download file
                response = requests.get(url, stream=True)
                response.raise_for_status()
                
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_size > 0:
                                progress_percent = int((downloaded / total_size) * 100)
                                self.file_progress.emit(i, progress_percent, filename)
                                self.overall_progress.emit(self.completed_files, total_files, filename, progress_percent)
                
                self.completed_files += 1
            
            self.finished.emit(True, f"Successfully downloaded {total_files} files")
            
        except Exception as e:
            self.finished.emit(False, f"Download failed: {str(e)}")

class WebCrawler(QMainWindow):
    def __init__(self):
        super().__init__()
        self.base_url = "https://glitchlinux.wtf/FILES/"
        self.current_url = self.base_url
        self.history = []
        self.history_index = -1
        self.download_thread = None
        self.multi_download_manager = None
        self.current_items = []
        self.sort_column = 0
        self.sort_order = Qt.SortOrder.AscendingOrder
        self.view_mode = 'list'  # Default to list view instead of details
        self.surf_mode = False  # Toggle for web browser mode
        
        # Set up paths for assets
        self.app_dir = "/usr/local/bin/WebCrawler"
        self.icons_dir = os.path.join(self.app_dir, "WebCrawler-Icons")
        self.ui_icons_dir = os.path.join(self.icons_dir, "Webcrawler-UI-actions")
        self.fonts_dir = os.path.join(self.app_dir, "WebCrawler-fonts")
        self.settings_file = os.path.join(self.app_dir, "savefile.cfg")
        
        # Default settings
        self.settings = {
            'font_family': 'FiraCode',
            'font_size': 12,
            'show_tree': True,
            'show_info': True,
            'show_toolbar': True,
            'show_statusbar': True,
            'view_mode': 'list',
            'show_image_preview': False,
            'show_text_preview': False,
            'default_download_path': os.path.join(os.path.expanduser('~'), 'Downloads'),
            'surf_mode': False,
            'bookmarks': []
        }
        
        # Search functionality
        self.search_active = False
        self.search_results = []
        self.current_search_index = -1
        
        self.load_settings()
        self.load_custom_font()
        self.initUI()
        self.apply_settings(self.settings)
        
        # Load start page or default homepage
        start_page_url = self.get_start_page_url()
        if start_page_url:
            self.current_url = start_page_url
            self.url_edit.setText(start_page_url)
            if self.surf_mode:
                if self.webengine_available:
                    self.web_view.setUrl(QUrl(start_page_url))
                else:
                    self.load_html_as_text(start_page_url)
            else:
                self.load_directory(start_page_url)
        else:
            # Load default homepage
            self.load_directory(self.current_url)

    def load_settings(self):
        """Load settings from savefile.cfg"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    saved_settings = json.load(f)
                    self.settings.update(saved_settings)
        except Exception as e:
            print(f"Error loading settings: {e}")
    
    def save_settings(self):
        """Save settings to savefile.cfg"""
        try:
            os.makedirs(self.app_dir, exist_ok=True)
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def get_ui_icon(self, icon_name):
        """Get UI action icon if available"""
        icon_path = os.path.join(self.ui_icons_dir, f"{icon_name}.png")
        if os.path.exists(icon_path):
            return QIcon(icon_path)
        return None

    def load_custom_font(self):
        """Load FiraCode font from the fonts directory"""
        font_path = os.path.join(self.fonts_dir, "FiraCode-Regular.ttf")
        if os.path.exists(font_path):
            font_id = QFontDatabase.addApplicationFont(font_path)
            if font_id != -1:
                font_families = QFontDatabase.applicationFontFamilies(font_id)
                if font_families:
                    self.custom_font = QFont(font_families[0], self.settings['font_size'])
                    return
        
        # Fallback to system font
        self.custom_font = QFont(self.settings['font_family'], self.settings['font_size'])

    def initUI(self):
        self.setWindowTitle('WebCrawler - Apache File Index Browser')
        self.setGeometry(100, 100, 1200, 800)

        # Set the same dark theme as the original script
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        # Custom selection colors
        palette.setColor(QPalette.ColorRole.Highlight, QColor(105, 105, 105))  # #696969
        palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
        self.setPalette(palette)

        # Create menu bar
        self.create_menu_bar()
        
        # Create toolbar
        self.create_toolbar()
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # Address bar
        address_layout = QHBoxLayout()
        address_layout.addWidget(QLabel('Location:'))
        
        self.url_edit = QLineEdit()
        self.url_edit.setText(self.current_url)
        self.url_edit.setFont(QFont('Monospace', 10))
        address_layout.addWidget(self.url_edit)
        
        self.go_button = QPushButton('Go')
        self.go_button.setMaximumWidth(50)
        address_layout.addWidget(self.go_button)
        
        main_layout.addLayout(address_layout)

        # Main content area with splitter
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel with directory tree
        self.left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        tree_label = QLabel('Directory Tree')
        tree_label.setFont(QFont('SansSerif', 10, QFont.Weight.Bold))
        left_layout.addWidget(tree_label)
        
        self.directory_tree = QTreeWidget()
        self.directory_tree.setHeaderLabel('Folders')
        self.directory_tree.setMaximumWidth(250)
        self.directory_tree.setMinimumWidth(200)
        left_layout.addWidget(self.directory_tree)
        
        self.left_panel.setLayout(left_layout)
        self.main_splitter.addWidget(self.left_panel)
        
        # Middle panel with file view and info
        self.middle_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # File view area
        file_view_widget = QWidget()
        file_view_layout = QVBoxLayout()
        file_view_layout.setContentsMargins(0, 0, 0, 0)
        
        # View controls
        view_controls_layout = QHBoxLayout()
        view_controls_layout.addWidget(QLabel('View:'))
        
        self.view_combo = QComboBox()
        self.view_combo.addItems(['Details', 'List', 'Icons'])
        self.view_combo.setCurrentText('List')
        view_controls_layout.addWidget(self.view_combo)
        
        view_controls_layout.addStretch()
        
        # Sort controls
        view_controls_layout.addWidget(QLabel('Sort by:'))
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(['Name', 'Size', 'Type', 'Modified'])
        view_controls_layout.addWidget(self.sort_combo)
        
        self.sort_order_button = QPushButton()
        sort_asc_icon = self.get_ui_icon('view-sort-ascending')
        if sort_asc_icon:
            self.sort_order_button.setIcon(sort_asc_icon)
            self.sort_order_button.setText('')
        else:
            self.sort_order_button.setText('↑')
        self.sort_order_button.setMaximumWidth(30)
        self.sort_order_button.setToolTip('Toggle sort order')
        view_controls_layout.addWidget(self.sort_order_button)
        
        view_controls_layout.addStretch()
        
        # Download controls in top right
        download_controls_layout = QHBoxLayout()
        
        self.main_download_button = QPushButton('Download')
        download_icon = self.get_ui_icon('document-save-as')
        if download_icon:
            self.main_download_button.setIcon(download_icon)
        self.main_download_button.setEnabled(False)
        self.main_download_button.clicked.connect(self.download_selected_files)
        download_controls_layout.addWidget(self.main_download_button)
        
        self.download_settings_button = QPushButton()
        gear_icon = self.get_ui_icon('system-run')
        if gear_icon:
            self.download_settings_button.setIcon(gear_icon)
            self.download_settings_button.setText('')
        else:
            self.download_settings_button.setText('⚙')
        self.download_settings_button.setMaximumWidth(30)
        self.download_settings_button.setToolTip('Download Settings')
        self.download_settings_button.clicked.connect(self.open_download_settings)
        download_controls_layout.addWidget(self.download_settings_button)
        
        view_controls_layout.addLayout(download_controls_layout)
        
        file_view_layout.addLayout(view_controls_layout)
        
        # File table/list widget container
        self.file_view_container = QWidget()
        file_view_container_layout = QVBoxLayout()
        file_view_container_layout.setContentsMargins(0, 0, 0, 0)
        
        # Table view (details)
        self.file_table = QTableWidget()
        self.file_table.setColumnCount(4)
        self.file_table.setHorizontalHeaderLabels(['Name', 'Size', 'Type', 'Modified'])
        self.file_table.setFont(self.custom_font)
        self.file_table.hide()  # Hide by default - list view is default
        
        # List view (simple list) - now default
        self.file_list = QListWidget()
        self.file_list.setFont(self.custom_font)
        self.file_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)  # Enable multi-selection
        # self.file_list.hide()  # Don't hide - this is the default view
        
        # Icon view (grid with large icons)
        self.icon_view = QListWidget()
        self.icon_view.setViewMode(QListWidget.ViewMode.IconMode)
        self.icon_view.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.icon_view.setGridSize(QSize(80, 80))
        self.icon_view.setIconSize(QSize(48, 48))
        self.icon_view.setFont(self.custom_font)
        self.icon_view.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)  # Enable multi-selection
        self.icon_view.hide()  # Hidden by default
        
        file_view_container_layout.addWidget(self.file_table)
        file_view_container_layout.addWidget(self.file_list)
        file_view_container_layout.addWidget(self.icon_view)
        self.file_view_container.setLayout(file_view_container_layout)
        
        # Web browser view (if available) or fallback text view
        self.webengine_available = WEBENGINE_AVAILABLE
        if self.webengine_available:
            try:
                self.web_view = QWebEngineView()
                
                # Configure WebEngine to appear more like a regular browser
                profile = self.web_view.page().profile()
                profile.setHttpUserAgent("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
                
                # Enable cookies and persistent storage
                profile.setPersistentCookiesPolicy(profile.PersistentCookiesPolicy.ForcePersistentCookies)
                
                self.web_view.urlChanged.connect(self.web_url_changed)
                self.web_view.loadFinished.connect(self.web_load_finished)
                print("WebEngine initialized successfully with browser-like settings")
            except Exception as e:
                print(f"WebEngine initialization failed: {e}")
                # Fall back to text view
                self.webengine_available = False
                self.web_view = QTextEdit()
                self.web_view.setReadOnly(True)
                self.web_view.setFont(self.custom_font)
        else:
            # Fallback to simple text view for HTML content
            self.web_view = QTextEdit()
            self.web_view.setReadOnly(True)
            self.web_view.setFont(self.custom_font)
        
        self.web_view.hide()
        file_view_container_layout.addWidget(self.web_view)
        
        # Configure table
        header = self.file_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        self.file_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.file_table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)  # Enable multi-selection
        self.file_table.setAlternatingRowColors(False)
        self.file_table.setSortingEnabled(True)
        
        file_view_layout.addWidget(self.file_view_container)
        file_view_widget.setLayout(file_view_layout)
        self.middle_splitter.addWidget(file_view_widget)
        
        # Info panel
        self.info_widget = QWidget()
        info_layout = QVBoxLayout()
        
        self.info_label = QLabel('File Information')
        self.info_label.setFont(QFont('SansSerif', 10, QFont.Weight.Bold))
        info_layout.addWidget(self.info_label)
        
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setFont(QFont('Monospace', 9))
        info_layout.addWidget(self.info_text)
        
        # Download controls
        download_layout = QHBoxLayout()
        self.download_button = QPushButton('Download')
        download_icon = self.get_ui_icon('document-save-as')
        if download_icon:
            self.download_button.setIcon(download_icon)
        self.download_button.setEnabled(False)
        download_layout.addWidget(self.download_button)
        
        self.open_folder_button = QPushButton('Open Download Folder')
        folder_icon = self.get_ui_icon('folder-new')
        if folder_icon:
            self.open_folder_button.setIcon(folder_icon)
        download_layout.addWidget(self.open_folder_button)
        download_layout.addStretch()
        
        info_layout.addLayout(download_layout)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        info_layout.addWidget(self.progress_bar)
        
        self.info_widget.setLayout(info_layout)
        self.info_widget.setMaximumHeight(200)
        self.info_widget.setMinimumHeight(150)
        self.middle_splitter.addWidget(self.info_widget)
        
        self.main_splitter.addWidget(self.middle_splitter)
        
        # Text preview panel (initially hidden)
        self.text_preview_panel = QWidget()
        text_preview_layout = QVBoxLayout()
        text_preview_layout.setContentsMargins(0, 0, 0, 0)
        
        text_preview_label = QLabel('Text Preview')
        text_preview_label.setFont(QFont('SansSerif', 10, QFont.Weight.Bold))
        text_preview_layout.addWidget(text_preview_label)
        
        self.text_preview = QTextEdit()
        self.text_preview.setReadOnly(True)
        self.text_preview.setFont(self.custom_font)
        # Set dark background with white text for preview
        preview_palette = QPalette()
        preview_palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
        preview_palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        self.text_preview.setPalette(preview_palette)
        text_preview_layout.addWidget(self.text_preview)
        
        self.text_preview_panel.setLayout(text_preview_layout)
        self.text_preview_panel.hide()
        self.main_splitter.addWidget(self.text_preview_panel)
        
        # Set splitter proportions
        self.main_splitter.setSizes([250, 950, 0])  # Third panel hidden initially
        self.middle_splitter.setSizes([600, 200])
        
        main_layout.addWidget(self.main_splitter)
        
        # Image preview overlay (initially hidden)
        self.image_preview_overlay = QWidget(self)
        self.image_preview_overlay.setStyleSheet("""
            QWidget {
                background-color: rgba(53, 53, 53, 240);
                border: 2px solid #555;
                border-radius: 8px;
            }
        """)
        
        overlay_layout = QVBoxLayout()
        overlay_layout.setContentsMargins(5, 5, 5, 5)
        
        # Image preview header
        image_header_layout = QHBoxLayout()
        self.image_preview_label = QLabel('Image Preview')
        self.image_preview_label.setFont(QFont('SansSerif', 9, QFont.Weight.Bold))
        self.image_preview_label.setStyleSheet("color: white;")
        image_header_layout.addWidget(self.image_preview_label)
        
        # Close button for image preview
        self.close_image_preview_btn = QPushButton('×')
        self.close_image_preview_btn.setMaximumSize(20, 20)
        self.close_image_preview_btn.setStyleSheet("""
            QPushButton {
                background-color: #666;
                color: white;
                border: none;
                border-radius: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #888;
            }
        """)
        self.close_image_preview_btn.clicked.connect(self.hide_image_preview)
        image_header_layout.addWidget(self.close_image_preview_btn)
        
        overlay_layout.addLayout(image_header_layout)
        
        # Scrollable image container
        self.image_scroll = QScrollArea()
        self.image_scroll.setWidgetResizable(True)
        self.image_scroll.setStyleSheet("QScrollArea { border: none; }")
        
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("QLabel { background-color: black; }")
        self.image_scroll.setWidget(self.image_label)
        
        overlay_layout.addWidget(self.image_scroll)
        self.image_preview_overlay.setLayout(overlay_layout)
        self.image_preview_overlay.hide()

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage('Ready')

        # Connect signals
        self.go_button.clicked.connect(self.navigate_to_url)
        self.url_edit.returnPressed.connect(self.navigate_to_url)
        self.file_table.itemDoubleClicked.connect(self.item_double_clicked)
        self.file_table.itemSelectionChanged.connect(self.selection_changed)
        self.file_table.itemSelectionChanged.connect(self.update_download_button_state)
        self.file_list.itemDoubleClicked.connect(self.list_item_double_clicked)
        self.file_list.itemSelectionChanged.connect(self.list_selection_changed)
        self.file_list.itemSelectionChanged.connect(self.update_download_button_state)
        self.icon_view.itemDoubleClicked.connect(self.icon_item_double_clicked)
        self.icon_view.itemSelectionChanged.connect(self.icon_selection_changed)
        self.icon_view.itemSelectionChanged.connect(self.update_download_button_state)
        self.download_button.clicked.connect(self.download_file)
        self.open_folder_button.clicked.connect(self.open_download_folder)
        self.directory_tree.itemClicked.connect(self.tree_item_clicked)
        self.view_combo.currentTextChanged.connect(self.change_view)
        self.sort_combo.currentTextChanged.connect(self.sort_files)
        self.sort_order_button.clicked.connect(self.toggle_sort_order)
        self.file_table.horizontalHeader().sectionClicked.connect(self.header_clicked)
        
        # Initialize surf mode
        self.update_surf_mode_icon()
        self.update_bookmarks_visibility()

        self.update_navigation_buttons()

    def create_menu_bar(self):
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        refresh_action = QAction('Refresh', self)
        refresh_icon = self.get_ui_icon('view-refresh')
        if refresh_icon:
            refresh_action.setIcon(refresh_icon)
        refresh_action.setShortcut('F5')
        refresh_action.triggered.connect(self.refresh_current)
        file_menu.addAction(refresh_action)
        
        file_menu.addSeparator()
        
        settings_action = QAction('Settings...', self)
        settings_icon = self.get_ui_icon('system-run')
        if settings_icon:
            settings_action.setIcon(settings_icon)
        settings_action.setShortcut('Ctrl+,')
        settings_action.triggered.connect(self.open_settings)
        file_menu.addAction(settings_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('Exit', self)
        exit_icon = self.get_ui_icon('application-exit')
        if exit_icon:
            exit_action.setIcon(exit_icon)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu('View')
        
        # View mode submenu
        view_mode_menu = view_menu.addMenu('View Mode')
        
        details_action = QAction('Details', self)
        details_icon = self.get_ui_icon('view-list')
        if details_icon:
            details_action.setIcon(details_icon)
        details_action.setCheckable(True)
        details_action.setChecked(True)
        details_action.triggered.connect(lambda: self.set_view_mode('details'))
        view_mode_menu.addAction(details_action)
        
        list_action = QAction('List', self)
        list_icon = self.get_ui_icon('view-list-bullet')
        if list_icon:
            list_action.setIcon(list_icon)
        list_action.setCheckable(True)
        list_action.triggered.connect(lambda: self.set_view_mode('list'))
        view_mode_menu.addAction(list_action)
        
        icons_action = QAction('Icons', self)
        icons_icon = self.get_ui_icon('view-grid')
        if icons_icon:
            icons_action.setIcon(icons_icon)
        icons_action.setCheckable(True)
        icons_action.triggered.connect(lambda: self.set_view_mode('icons'))
        view_mode_menu.addAction(icons_action)
        
        view_menu.addSeparator()
        
        # Panel visibility
        self.tree_action = QAction('Show Directory Tree', self)
        tree_icon = self.get_ui_icon('sidebar-show')
        if tree_icon:
            self.tree_action.setIcon(tree_icon)
        self.tree_action.setCheckable(True)
        self.tree_action.setChecked(True)
        self.tree_action.triggered.connect(self.toggle_tree_panel)
        view_menu.addAction(self.tree_action)
        
        self.info_action = QAction('Show File Information', self)
        info_icon = self.get_ui_icon('view-reveal')
        if info_icon:
            self.info_action.setIcon(info_icon)
        self.info_action.setCheckable(True)
        self.info_action.setChecked(True)
        self.info_action.triggered.connect(self.toggle_info_panel)
        view_menu.addAction(self.info_action)
        
        self.toolbar_action = QAction('Show Toolbar', self)
        self.toolbar_action.setCheckable(True)
        self.toolbar_action.setChecked(True)
        self.toolbar_action.triggered.connect(self.toggle_toolbar)
        view_menu.addAction(self.toolbar_action)
        
        self.statusbar_action = QAction('Show Status Bar', self)
        self.statusbar_action.setCheckable(True)
        self.statusbar_action.setChecked(True)
        self.statusbar_action.triggered.connect(self.toggle_statusbar)
        view_menu.addAction(self.statusbar_action)
        
        view_menu.addSeparator()
        
        home_action = QAction('Home', self)
        home_icon = self.get_ui_icon('go-home')
        if home_icon:
            home_action.setIcon(home_icon)
        home_action.setShortcut('Ctrl+H')
        home_action.triggered.connect(self.go_home)
        view_menu.addAction(home_action)
        
        up_action = QAction('Up', self)
        up_icon = self.get_ui_icon('up')
        if up_icon:
            up_action.setIcon(up_icon)
        up_action.setShortcut('Alt+Up')
        up_action.triggered.connect(self.go_up)
        view_menu.addAction(up_action)
        
        view_menu.addSeparator()
        
        # Preview toggles
        self.image_preview_action = QAction('Enable Image Preview', self)
        preview_icon = self.get_ui_icon('view-reveal')
        if preview_icon:
            self.image_preview_action.setIcon(preview_icon)
        self.image_preview_action.setCheckable(True)
        self.image_preview_action.setChecked(False)
        self.image_preview_action.triggered.connect(self.toggle_image_preview)
        view_menu.addAction(self.image_preview_action)
        
        self.text_preview_action = QAction('Enable Text Preview', self)
        text_icon = self.get_ui_icon('view-paged')
        if text_icon:
            self.text_preview_action.setIcon(text_icon)
        self.text_preview_action.setCheckable(True)
        self.text_preview_action.setChecked(False)
        self.text_preview_action.triggered.connect(self.toggle_text_preview)
        view_menu.addAction(self.text_preview_action)
        
        view_menu.addSeparator()
        
        # Search menu
        search_menu_action = QAction('Search', self)
        search_icon = self.get_ui_icon('search')
        if search_icon:
            search_menu_action.setIcon(search_icon)
        search_menu_action.setShortcut('Ctrl+F')
        search_menu_action.triggered.connect(self.toggle_search)
        view_menu.addAction(search_menu_action)
        
        # Navigation menu
        nav_menu = menubar.addMenu('Navigation')
        
        # Add bookmark action
        add_bookmark_menu_action = QAction('Add Bookmark', self)
        add_bookmark_menu_action.setShortcut('Ctrl+D')
        add_bookmark_menu_action.triggered.connect(self.add_current_bookmark)
        nav_menu.addAction(add_bookmark_menu_action)
        
        manage_bookmarks_menu_action = QAction('Manage Bookmarks', self)
        manage_bookmarks_menu_action.setShortcut('Ctrl+Shift+B')
        manage_bookmarks_menu_action.triggered.connect(self.manage_bookmarks)
        nav_menu.addAction(manage_bookmarks_menu_action)

    def create_toolbar(self):
        self.toolbar = self.addToolBar('Navigation')
        self.toolbar.setMovable(False)
        
        # Navigation buttons
        self.back_action = QAction('Back', self)
        back_icon = self.get_ui_icon('left')
        if back_icon:
            self.back_action.setIcon(back_icon)
        else:
            self.back_action.setText('← Back')
        self.back_action.triggered.connect(self.go_back)
        self.toolbar.addAction(self.back_action)
        
        self.forward_action = QAction('Forward', self)
        forward_icon = self.get_ui_icon('right')
        if forward_icon:
            self.forward_action.setIcon(forward_icon)
        else:
            self.forward_action.setText('Forward →')
        self.forward_action.triggered.connect(self.go_forward)
        self.toolbar.addAction(self.forward_action)
        
        self.toolbar.addSeparator()
        
        self.up_action = QAction('Up', self)
        up_icon = self.get_ui_icon('up')
        if up_icon:
            self.up_action.setIcon(up_icon)
        else:
            self.up_action.setText('↑ Up')
        self.up_action.triggered.connect(self.go_up)
        self.toolbar.addAction(self.up_action)
        
        self.home_action = QAction('Home', self)
        home_icon = self.get_ui_icon('go-home')
        if home_icon:
            self.home_action.setIcon(home_icon)
        else:
            self.home_action.setText('🏠 Home')
        self.home_action.triggered.connect(self.go_home)
        self.toolbar.addAction(self.home_action)
        
        self.toolbar.addSeparator()
        
        self.refresh_action = QAction('Refresh', self)
        refresh_icon = self.get_ui_icon('view-refresh')
        if refresh_icon:
            self.refresh_action.setIcon(refresh_icon)
        else:
            self.refresh_action.setText('🔄 Refresh')
        self.refresh_action.triggered.connect(self.refresh_current)
        self.toolbar.addAction(self.refresh_action)
        
        self.toolbar.addSeparator()
        
        # Search functionality
        self.search_action = QAction('Search', self)
        search_icon = self.get_ui_icon('search')
        if search_icon:
            self.search_action.setIcon(search_icon)
            self.search_action.setText('')  # Remove text, show only icon
        else:
            self.search_action.setText('Search')
        self.search_action.setShortcut('Ctrl+F')
        self.search_action.setToolTip('Search (Ctrl+F)')
        self.search_action.triggered.connect(self.toggle_search)
        self.toolbar.addAction(self.search_action)
        
        # Search input field (initially hidden)
        self.search_field = QLineEdit()
        self.search_field.setMaximumWidth(150)
        self.search_field.setPlaceholderText('Search...')
        self.search_field.returnPressed.connect(self.perform_search)
        self.search_field.textChanged.connect(self.search_text_changed)
        self.search_field.hide()
        self.toolbar.addWidget(self.search_field)
        
        self.toolbar.addSeparator()
        
        # Bookmarks button (only visible in surf mode)
        self.bookmarks_action = QAction('Bookmarks', self)
        bookmarks_icon = self.get_ui_icon('view-more')
        if bookmarks_icon:
            self.bookmarks_action.setIcon(bookmarks_icon)
            self.bookmarks_action.setText('')  # Remove text, show only icon
        else:
            self.bookmarks_action.setText('Bookmarks')  # Fallback text if no icon
        self.bookmarks_action.triggered.connect(self.show_bookmarks_menu)
        self.bookmarks_action.setVisible(False)  # Hidden by default
        self.toolbar.addAction(self.bookmarks_action)
        
        self.toolbar.addSeparator()
        
        # Surf mode toggle
        self.surf_mode_action = QAction('Surf Mode', self)
        self.update_surf_mode_icon()
        self.surf_mode_action.setCheckable(True)
        self.surf_mode_action.setChecked(False)
        self.surf_mode_action.triggered.connect(self.toggle_surf_mode)
        self.toolbar.addAction(self.surf_mode_action)

    def add_to_history(self, url):
        if self.history_index < len(self.history) - 1:
            self.history = self.history[:self.history_index + 1]
        
        self.history.append(url)
        self.history_index = len(self.history) - 1
        self.update_navigation_buttons()

    def update_navigation_buttons(self):
        self.back_action.setEnabled(self.history_index > 0)
        self.forward_action.setEnabled(self.history_index < len(self.history) - 1)

    def load_directory(self, url):
        self.status_bar.showMessage('Loading...')
        self.file_table.setRowCount(0)
        self.info_text.clear()
        self.current_items = []
        
        try:
            # Use browser-like headers to avoid being flagged as a bot
            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            response = requests.get(url, timeout=10, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all links in the directory listing
            links = soup.find_all('a', href=True)
            
            for link in links:
                href = link['href']
                text = link.get_text().strip()
                
                # Skip parent directory link, sorting links, and empty links
                if href in ['/', '?C=N;O=D', '?C=M;O=A', '?C=S;O=A', '?C=D;O=A'] or not text:
                    continue
                
                # Get additional info from the table row
                row = link.find_parent('tr')
                size = ""
                modified = ""
                if row:
                    cells = row.find_all('td')
                    if len(cells) >= 4:
                        modified = cells[2].get_text().strip()
                        size = cells[3].get_text().strip()
                
                # Determine if it's a directory or web-navigable file
                is_directory = href.endswith('/') or '[DIR]' in str(row)
                is_web_file = not is_directory and self.is_web_navigable_file(text)
                
                item_data = {
                    'type': 'directory' if (is_directory or is_web_file) else 'file',
                    'href': href,
                    'name': text,
                    'size': size if not (is_directory or is_web_file) else '',
                    'modified': modified,
                    'is_web_file': is_web_file
                }
                
                self.current_items.append(item_data)
            
            self.current_url = url
            self.url_edit.setText(url)
            self.populate_file_views()
            self.update_directory_tree()
            self.status_bar.showMessage(f'Loaded {len(self.current_items)} items')
            
        except requests.RequestException as e:
            self.status_bar.showMessage(f'Error: {str(e)}')
            QMessageBox.warning(self, 'Error', f'Failed to load directory:\n{str(e)}')

    def get_file_icon(self, filename, is_directory=False, is_web_file=False):
        """Get appropriate icon for file type"""
        if is_directory or is_web_file:
            if is_web_file:
                # Use web/internet icon for web files if available
                web_icon_path = os.path.join(self.icons_dir, "internet.png")
                if os.path.exists(web_icon_path):
                    return QIcon(web_icon_path)
            
            # Default folder icon
            folder_icon_path = os.path.join(self.icons_dir, "folder.png")
            if os.path.exists(folder_icon_path):
                return QIcon(folder_icon_path)
            return QIcon('/usr/share/icons/folder.png')  # Fallback
        
        # Get file extension
        _, ext = os.path.splitext(filename.lower())
        ext = ext.lstrip('.')  # Remove the dot
        
        # Special cases for compound extensions
        if filename.lower().endswith('.tar.gz'):
            ext = 'tar'
        elif filename.lower().endswith('.tar.xz'):
            ext = 'tar'
        elif filename.lower().endswith('.tar.lzma'):
            ext = 'tar.lzma'
        
        # Look for PNG icons first (they work better)
        png_icon_path = os.path.join(self.icons_dir, f"{ext}.png")
        if os.path.exists(png_icon_path):
            return QIcon(png_icon_path)
        
        # Fallback icons for common types
        fallback_map = {
            'txt': 'txt.png',
            'py': 'py.png',
            'sh': 'sh.png',
            'json': 'json.png',
            'xml': 'xml.png',
            'yaml': 'yaml.png',
            'yml': 'yaml.png',
            'mp3': 'mp3.png',
            'mp4': 'mp4.png',
            'pdf': 'pdf.png',
            'iso': 'iso.png',
            'img': 'img.png',
            'deb': 'deb.png',
            'tar': 'tar.png',
            'gz': 'gzip.png',
            'xz': 'xz.png',
            '7z': '7z.png',
            'zip': 'application-x-tar.png',
            'vhd': 'vhd.png',
            'vdi': 'vdi.png',
            'appimage': 'appimage.png',
            'apk': 'apk.png',
            'cfg': 'cfg.png',
            'efi': 'efi.png',
            'java': 'java.png',
            'pgp': 'pgp.png'
        }
        
        if ext in fallback_map:
            fallback_path = os.path.join(self.icons_dir, fallback_map[ext])
            if os.path.exists(fallback_path):
                return QIcon(fallback_path)
        
        # Default unknown file icon
        unknown_path = os.path.join(self.icons_dir, "unknown.png")
        if os.path.exists(unknown_path):
            return QIcon(unknown_path)
        
        return None

    def populate_file_views(self):
        """Populate all file views with current items"""
        self.populate_file_table()
        self.populate_file_list()
        self.populate_icon_view()

    def populate_file_table(self):
        # Sort items
        self.sort_items()
        
        self.file_table.setRowCount(len(self.current_items))
        
        for row, item in enumerate(self.current_items):
            # Name column with icon
            name_item = QTableWidgetItem()
            
            # Get appropriate icon
            is_web_file = item.get('is_web_file', False)
            icon = self.get_file_icon(item['name'], item['type'] == 'directory', is_web_file)
            if icon:
                name_item.setIcon(icon)
            
            name_item.setText(item['name'])
            name_item.setData(Qt.ItemDataRole.UserRole, item)
            self.file_table.setItem(row, 0, name_item)
            
            # Size column
            size_item = QTableWidgetItem(item['size'])
            self.file_table.setItem(row, 1, size_item)
            
            # Type column
            type_item = QTableWidgetItem(item['type'].title())
            self.file_table.setItem(row, 2, type_item)
            
            # Modified column
            modified_item = QTableWidgetItem(item['modified'])
            self.file_table.setItem(row, 3, modified_item)

    def populate_file_list(self):
        """Populate the simple list view"""
        self.sort_items()
        self.file_list.clear()
        
        for item in self.current_items:
            list_item = QListWidgetItem()
            is_web_file = item.get('is_web_file', False)
            icon = self.get_file_icon(item['name'], item['type'] == 'directory', is_web_file)
            if icon:
                list_item.setIcon(icon)
            list_item.setText(item['name'])
            list_item.setData(Qt.ItemDataRole.UserRole, item)
            self.file_list.addItem(list_item)
    
    def populate_icon_view(self):
        """Populate the icon grid view"""
        self.sort_items()
        self.icon_view.clear()
        
        for item in self.current_items:
            icon_item = QListWidgetItem()
            is_web_file = item.get('is_web_file', False)
            icon = self.get_file_icon(item['name'], item['type'] == 'directory', is_web_file)
            if icon:
                icon_item.setIcon(icon)
            icon_item.setText(item['name'])
            icon_item.setData(Qt.ItemDataRole.UserRole, item)
            self.icon_view.addItem(icon_item)

    def sort_items(self):
        sort_key_map = {
            'Name': lambda x: x['name'].lower(),
            'Size': lambda x: self.parse_size(x['size']),
            'Type': lambda x: (x['type'] == 'file', x['name'].lower()),  # Directories first
            'Modified': lambda x: x['modified']
        }
        
        sort_key = self.sort_combo.currentText()
        if sort_key in sort_key_map:
            reverse = self.sort_order == Qt.SortOrder.DescendingOrder
            self.current_items.sort(key=sort_key_map[sort_key], reverse=reverse)

    def parse_size(self, size_str):
        if not size_str or size_str == '-':
            return 0
        
        # Parse size strings like "1.2M", "345K", "2.1G"
        size_str = size_str.strip()
        if size_str[-1].upper() in 'KMGT':
            multipliers = {'K': 1024, 'M': 1024**2, 'G': 1024**3, 'T': 1024**4}
            try:
                return float(size_str[:-1]) * multipliers[size_str[-1].upper()]
            except:
                return 0
        try:
            return float(size_str)
        except:
            return 0

    def update_directory_tree(self):
        # Simple tree update - could be enhanced to show full tree structure
        self.directory_tree.clear()
        
        # Add current path components
        path_parts = self.current_url.replace(self.base_url, '').strip('/').split('/')
        if path_parts == ['']:
            path_parts = []
        
        root_item = QTreeWidgetItem(self.directory_tree)
        root_item.setText(0, 'FILES')
        root_item.setData(0, Qt.ItemDataRole.UserRole, self.base_url)
        
        current_item = root_item
        current_url = self.base_url
        
        for part in path_parts:
            if part:
                current_url = urljoin(current_url, part + '/')
                child_item = QTreeWidgetItem(current_item)
                child_item.setText(0, part)
                child_item.setData(0, Qt.ItemDataRole.UserRole, current_url)
                current_item = child_item
        
        self.directory_tree.expandAll()
        if current_item:
            self.directory_tree.setCurrentItem(current_item)

    # Settings and UI control methods
    def open_settings(self):
        """Open the settings dialog"""
        dialog = SettingsDialog(self)
        dialog.load_settings(self.settings)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.settings.update(dialog.get_settings())
            self.save_settings()
            self.apply_settings(self.settings)
    
    def apply_settings(self, settings):
        """Apply settings to the UI"""
        # Update font
        self.custom_font = QFont(settings['font_family'], settings['font_size'])
        self.file_table.setFont(self.custom_font)
        self.file_list.setFont(self.custom_font)
        self.icon_view.setFont(self.custom_font)
        
        # Update UI visibility
        self.left_panel.setVisible(settings['show_tree'])
        self.tree_action.setChecked(settings['show_tree'])
        
        self.info_widget.setVisible(settings['show_info'])
        self.info_action.setChecked(settings['show_info'])
        
        self.toolbar.setVisible(settings['show_toolbar'])
        self.toolbar_action.setChecked(settings['show_toolbar'])
        
        self.status_bar.setVisible(settings['show_statusbar'])
        self.statusbar_action.setChecked(settings['show_statusbar'])
        
        # Update preview modes
        if 'show_image_preview' in settings:
            self.image_preview_action.setChecked(settings['show_image_preview'])
            if settings['show_image_preview']:
                self.enable_image_preview()
            else:
                self.disable_image_preview()
        
        if 'show_text_preview' in settings:
            self.text_preview_action.setChecked(settings['show_text_preview'])
            if settings['show_text_preview']:
                self.enable_text_preview()
            else:
                self.disable_text_preview()

    def toggle_image_preview(self):
        """Toggle image preview mode"""
        enabled = self.image_preview_action.isChecked()
        self.settings['show_image_preview'] = enabled
        if enabled:
            self.enable_image_preview()
        else:
            self.disable_image_preview()
        self.save_settings()
    
    def toggle_text_preview(self):
        """Toggle text preview mode"""
        enabled = self.text_preview_action.isChecked()
        self.settings['show_text_preview'] = enabled
        if enabled:
            self.enable_text_preview()
        else:
            self.disable_text_preview()
        self.save_settings()
    
    def enable_image_preview(self):
        """Enable image preview functionality"""
        self.image_preview_action.setChecked(True)
        # Image preview will show on demand
    
    def disable_image_preview(self):
        """Disable image preview functionality"""
        self.image_preview_action.setChecked(False)
        self.hide_image_preview()
    
    def enable_text_preview(self):
        """Enable text preview panel"""
        self.text_preview_action.setChecked(True)
        self.text_preview_panel.show()
        # Split view: browser on left, text preview on right
        self.main_splitter.setSizes([250, 475, 475])
    
    def disable_text_preview(self):
        """Disable text preview panel"""
        self.text_preview_action.setChecked(False)
        self.text_preview_panel.hide()
        self.main_splitter.setSizes([250, 950, 0])
    
    def show_image_preview(self, url):
        """Show image preview overlay"""
        if not self.settings.get('show_image_preview', False):
            return
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            response = requests.get(url, timeout=10, headers=headers)
            response.raise_for_status()
            
            pixmap = QPixmap()
            if pixmap.loadFromData(response.content):
                # Calculate overlay size (20% of main window)
                overlay_width = int(self.width() * 0.2)
                overlay_height = int(self.height() * 0.2)
                
                # Scale image to fit while maintaining aspect ratio
                scaled_pixmap = pixmap.scaled(
                    overlay_width - 40, overlay_height - 60,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                
                self.image_label.setPixmap(scaled_pixmap)
                
                # Position overlay in lower right corner
                x = self.width() - overlay_width - 20
                y = self.height() - overlay_height - 60
                self.image_preview_overlay.setGeometry(x, y, overlay_width, overlay_height)
                self.image_preview_overlay.show()
                
        except Exception as e:
            print(f"Error loading image: {e}")
    
    def hide_image_preview(self):
        """Hide image preview overlay"""
        self.image_preview_overlay.hide()
    
    def show_text_preview(self, url):
        """Show text file preview in right panel"""
        if not self.settings.get('show_text_preview', False):
            return
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            response = requests.get(url, timeout=10, headers=headers)
            response.raise_for_status()
            
            # Try to decode as text
            text_content = response.content.decode('utf-8', errors='replace')
            
            # Limit preview size for performance
            if len(text_content) > 100000:  # 100KB limit
                text_content = text_content[:100000] + "\n\n[Preview truncated - file too large]"
            
            self.text_preview.setPlainText(text_content)
            
        except Exception as e:
            self.text_preview.setPlainText(f"Error loading text file: {str(e)}")
    
    def clear_text_preview(self):
        """Clear text preview panel"""
        self.text_preview.clear()
    
    def is_image_file(self, filename):
        """Check if file is an image"""
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg', '.ico'}
        _, ext = os.path.splitext(filename.lower())
        return ext in image_extensions
    
    def is_text_file(self, filename):
        """Check if file is a text file"""
        text_extensions = {'.txt', '.py', '.js', '.html', '.htm', '.css', '.json', '.xml', '.yaml', '.yml', 
                          '.md', '.rst', '.log', '.cfg', '.conf', '.ini', '.sh', '.bash', '.bat', '.ps1',
                          '.c', '.cpp', '.h', '.hpp', '.java', '.php', '.rb', '.go', '.rs', '.swift',
                          '.sql', '.csv', '.tsv', '.rtf'}
        _, ext = os.path.splitext(filename.lower())
        return ext in text_extensions
    
    def resizeEvent(self, event):
        """Handle window resize - reposition image preview"""
        super().resizeEvent(event)
        if hasattr(self, 'image_preview_overlay') and self.image_preview_overlay.isVisible():
            # Reposition image preview overlay
            overlay_width = int(self.width() * 0.2)
            overlay_height = int(self.height() * 0.2)
            x = self.width() - overlay_width - 20
            y = self.height() - overlay_height - 60
            self.image_preview_overlay.setGeometry(x, y, overlay_width, overlay_height)
    
    def update_surf_mode_icon(self):
        """Update the surf mode icon"""
        if self.surf_mode:
            icon_path = os.path.join(self.ui_icons_dir, "toggle-on.png")
        else:
            icon_path = os.path.join(self.ui_icons_dir, "toggle-off.png")
        
        if os.path.exists(icon_path):
            self.surf_mode_action.setIcon(QIcon(icon_path))
        else:
            # Fallback text
            self.surf_mode_action.setText("Web" if self.surf_mode else "Files")
    
    def toggle_surf_mode(self):
        """Toggle surf mode on/off"""
        try:
            self.surf_mode = self.surf_mode_action.isChecked()
            self.settings['surf_mode'] = self.surf_mode
            self.update_surf_mode_icon()
            self.update_bookmarks_visibility()
            
            if self.surf_mode:
                self.enter_surf_mode()
            else:
                self.exit_surf_mode()
            
            self.save_settings()
        except Exception as e:
            print(f"Error toggling surf mode: {e}")
            self.status_bar.showMessage(f"Error toggling surf mode: {e}")
            # Reset to safe state
            self.surf_mode = False
            self.surf_mode_action.setChecked(False)
            self.settings['surf_mode'] = False
            self.exit_surf_mode()

    def update_bookmarks_visibility(self):
        """Show/hide bookmarks button based on surf mode"""
        self.bookmarks_action.setVisible(self.surf_mode)

    # Bookmarks functionality
    def show_bookmarks_menu(self):
        """Show bookmarks dropdown menu"""
        menu = QMenu(self)
        
        # Add current page to bookmarks
        add_bookmark_action = QAction('Add Current Page', self)
        add_bookmark_action.triggered.connect(self.add_current_bookmark)
        menu.addAction(add_bookmark_action)
        
        # Manage bookmarks
        manage_bookmarks_action = QAction('Manage Bookmarks...', self)
        manage_bookmarks_action.triggered.connect(self.manage_bookmarks)
        menu.addAction(manage_bookmarks_action)
        
        if self.settings.get('bookmarks'):
            menu.addSeparator()
            
            # Show start page (first bookmark) with special indicator
            if len(self.settings['bookmarks']) > 0:
                start_page = self.settings['bookmarks'][0]
                start_page_action = QAction(f"[START] {start_page['title']}", self)
                start_page_action.setToolTip(f"Start Page: {start_page['url']}")
                start_page_action.triggered.connect(lambda: self.navigate_to_bookmark(start_page['url']))
                menu.addAction(start_page_action)
                
                # Show other bookmarks if any
                if len(self.settings['bookmarks']) > 1:
                    menu.addSeparator()
                    for bookmark in self.settings['bookmarks'][1:]:
                        bookmark_action = QAction(bookmark['title'], self)
                        bookmark_action.setToolTip(bookmark['url'])
                        bookmark_action.triggered.connect(lambda checked, url=bookmark['url']: self.navigate_to_bookmark(url))
                        menu.addAction(bookmark_action)
        
        # Show menu at bookmarks button position
        button_rect = self.toolbar.actionGeometry(self.bookmarks_action)
        menu_pos = self.toolbar.mapToGlobal(button_rect.bottomLeft())
        menu.exec(menu_pos)

    def add_current_bookmark(self):
        """Add current URL as bookmark"""
        if not self.current_url:
            return
        
        # Get page title if available
        title = self.current_url
        if self.webengine_available and hasattr(self.web_view, 'title'):
            page_title = self.web_view.title()
            if page_title:
                title = page_title
        
        # Simple dialog to get bookmark name
        from PyQt6.QtWidgets import QInputDialog
        bookmark_name, ok = QInputDialog.getText(
            self, 'Add Bookmark', 'Bookmark name:', text=title
        )
        
        if ok and bookmark_name:
            bookmark = {
                'title': bookmark_name,
                'url': self.current_url
            }
            
            if 'bookmarks' not in self.settings:
                self.settings['bookmarks'] = []
            
            # Check if bookmark already exists
            for existing in self.settings['bookmarks']:
                if existing['url'] == self.current_url:
                    existing['title'] = bookmark_name  # Update title
                    self.save_settings()
                    self.status_bar.showMessage(f'Updated bookmark: {bookmark_name}')
                    return
            
            # Add new bookmark
            self.settings['bookmarks'].append(bookmark)
            self.save_settings()
            self.status_bar.showMessage(f'Added bookmark: {bookmark_name}')

    def manage_bookmarks(self):
        """Open bookmarks management dialog"""
        dialog = QDialog(self)
        dialog.setWindowTitle('Manage Bookmarks')
        dialog.setModal(True)
        dialog.setMinimumSize(500, 400)
        
        layout = QVBoxLayout()
        
        # Instructions
        info_label = QLabel('First bookmark in list is automatically used as start page')
        info_label.setStyleSheet("QLabel { font-weight: bold; color: #0066cc; }")
        layout.addWidget(info_label)
        
        # Bookmarks list
        bookmarks_list = QListWidget()
        if 'bookmarks' in self.settings:
            for i, bookmark in enumerate(self.settings['bookmarks']):
                prefix = "[START] " if i == 0 else ""
                item = QListWidgetItem(f"{prefix}{bookmark['title']} - {bookmark['url']}")
                item.setData(Qt.ItemDataRole.UserRole, bookmark)
                bookmarks_list.addItem(item)
        
        layout.addWidget(QLabel('Bookmarks:'))
        layout.addWidget(bookmarks_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        # Move up/down buttons
        move_up_button = QPushButton('Move Up')
        def move_bookmark_up():
            current_row = bookmarks_list.currentRow()
            if current_row > 0:
                bookmark = self.settings['bookmarks'].pop(current_row)
                self.settings['bookmarks'].insert(current_row - 1, bookmark)
                self.refresh_bookmarks_list(bookmarks_list)
                bookmarks_list.setCurrentRow(current_row - 1)
        move_up_button.clicked.connect(move_bookmark_up)
        button_layout.addWidget(move_up_button)
        
        move_down_button = QPushButton('Move Down')
        def move_bookmark_down():
            current_row = bookmarks_list.currentRow()
            if current_row >= 0 and current_row < len(self.settings['bookmarks']) - 1:
                bookmark = self.settings['bookmarks'].pop(current_row)
                self.settings['bookmarks'].insert(current_row + 1, bookmark)
                self.refresh_bookmarks_list(bookmarks_list)
                bookmarks_list.setCurrentRow(current_row + 1)
        move_down_button.clicked.connect(move_bookmark_down)
        button_layout.addWidget(move_down_button)
        
        button_layout.addStretch()
        
        edit_button = QPushButton('Edit')
        def edit_bookmark():
            current_item = bookmarks_list.currentItem()
            if current_item:
                bookmark = current_item.data(Qt.ItemDataRole.UserRole)
                from PyQt6.QtWidgets import QInputDialog
                new_title, ok = QInputDialog.getText(
                    dialog, 'Edit Bookmark', 'Bookmark name:', text=bookmark['title']
                )
                if ok and new_title:
                    bookmark['title'] = new_title
                    self.refresh_bookmarks_list(bookmarks_list)
        
        edit_button.clicked.connect(edit_bookmark)
        button_layout.addWidget(edit_button)
        
        delete_button = QPushButton('Delete')
        def delete_bookmark():
            current_item = bookmarks_list.currentItem()
            if current_item:
                current_row = bookmarks_list.currentRow()
                self.settings['bookmarks'].pop(current_row)
                self.refresh_bookmarks_list(bookmarks_list)
        
        delete_button.clicked.connect(delete_bookmark)
        button_layout.addWidget(delete_button)
        
        button_layout.addStretch()
        
        close_button = QPushButton('Close')
        def close_dialog():
            self.save_settings()
            dialog.accept()
        
        close_button.clicked.connect(close_dialog)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        dialog.setLayout(layout)
        dialog.exec()
    
    def refresh_bookmarks_list(self, bookmarks_list):
        """Refresh the bookmarks list display"""
        bookmarks_list.clear()
        for i, bookmark in enumerate(self.settings['bookmarks']):
            prefix = "[START] " if i == 0 else ""
            item = QListWidgetItem(f"{prefix}{bookmark['title']} - {bookmark['url']}")
            item.setData(Qt.ItemDataRole.UserRole, bookmark)
            bookmarks_list.addItem(item)

    def get_start_page_url(self):
        """Get the start page URL (first bookmark)"""
        if self.settings.get('bookmarks') and len(self.settings['bookmarks']) > 0:
            return self.settings['bookmarks'][0]['url']
        return None

    def navigate_to_bookmark(self, url):
        """Navigate to bookmarked URL"""
        self.add_to_history(self.current_url)
        if self.surf_mode:
            if self.webengine_available:
                self.web_view.setUrl(QUrl(url))
            else:
                self.load_html_as_text(url)
            self.current_url = url
            self.url_edit.setText(url)
        else:
            self.load_directory(url)

    # Search functionality
    def toggle_search(self):
        """Toggle search field visibility"""
        print(f"Toggle search called - current visibility: {self.search_field.isVisible()}")  # Debug
        try:
            if self.search_field.isVisible():
                self.search_field.hide()
                self.search_active = False
                self.clear_search_highlighting()
                print("Search field hidden")  # Debug
            else:
                self.search_field.show()
                self.search_field.setFocus()
                self.search_active = True
                print("Search field shown and focused")  # Debug
        except Exception as e:
            print(f"Error in toggle_search: {e}")

    def search_text_changed(self, text):
        """Handle search text changes for real-time search"""
        if len(text) >= 2:  # Start searching after 2 characters
            self.perform_search()
        elif len(text) == 0:
            self.clear_search_highlighting()

    def perform_search(self):
        """Perform search in current view"""
        search_text = self.search_field.text().lower()
        if not search_text:
            return
        
        self.search_results = []
        self.current_search_index = -1
        
        if self.surf_mode:
            # Search in web view
            if self.webengine_available:
                # For WebEngine, use built-in find functionality
                self.web_view.findText(search_text)
                self.status_bar.showMessage(f"Searching for: {search_text}")
            else:
                # For text view, highlight matching text
                self.search_in_text_view(search_text)
        else:
            # Search in file manager views
            self.search_in_file_views(search_text)

    def search_in_text_view(self, search_text):
        """Search in text view (fallback web view)"""
        if hasattr(self.web_view, 'toPlainText'):
            content = self.web_view.toPlainText()
            cursor = self.web_view.textCursor()
            
            # Find all occurrences
            index = 0
            while True:
                index = content.lower().find(search_text, index)
                if index == -1:
                    break
                self.search_results.append(index)
                index += len(search_text)
            
            if self.search_results:
                self.current_search_index = 0
                self.highlight_search_result()
                self.status_bar.showMessage(f'Found {len(self.search_results)} matches')
            else:
                self.status_bar.showMessage('No matches found')

    def search_in_file_views(self, search_text):
        """Search in file manager views"""
        matching_items = []
        
        # Search through current items
        for i, item in enumerate(self.current_items):
            if search_text in item['name'].lower():
                matching_items.append(i)
        
        self.search_results = matching_items
        
        if matching_items:
            self.current_search_index = 0
            self.highlight_file_search_result()
            self.status_bar.showMessage(f'Found {len(matching_items)} matching files')
        else:
            self.status_bar.showMessage('No matching files found')

    def highlight_search_result(self):
        """Highlight current search result in text view"""
        if not self.search_results or self.current_search_index < 0:
            return
        
        if hasattr(self.web_view, 'textCursor'):
            cursor = self.web_view.textCursor()
            cursor.setPosition(self.search_results[self.current_search_index])
            cursor.movePosition(cursor.MoveOperation.Right, cursor.MoveMode.KeepAnchor, len(self.search_field.text()))
            self.web_view.setTextCursor(cursor)

    def highlight_file_search_result(self):
        """Highlight current search result in file views"""
        if not self.search_results or self.current_search_index < 0:
            return
        
        item_index = self.search_results[self.current_search_index]
        
        # Clear previous selections
        self.file_table.clearSelection()
        self.file_list.clearSelection()
        self.icon_view.clearSelection()
        
        # Highlight in appropriate view
        if self.file_table.isVisible():
            self.file_table.selectRow(item_index)
            self.file_table.scrollToItem(self.file_table.item(item_index, 0))
        elif self.file_list.isVisible():
            self.file_list.setCurrentRow(item_index)
            self.file_list.scrollToItem(self.file_list.item(item_index))
        elif self.icon_view.isVisible():
            self.icon_view.setCurrentRow(item_index)
            self.icon_view.scrollToItem(self.icon_view.item(item_index))

    def clear_search_highlighting(self):
        """Clear search highlighting"""
        self.search_results = []
        self.current_search_index = -1
        
        if self.surf_mode:
            if self.webengine_available:
                self.web_view.findText("")  # Clear WebEngine search
        else:
            # Clear file view selections
            self.file_table.clearSelection()
            self.file_list.clearSelection()
            self.icon_view.clearSelection()
    
    def enter_surf_mode(self):
        """Enter web browser mode"""
        try:
            # Hide file manager components
            self.file_table.hide()
            self.file_list.hide()
            self.icon_view.hide()
            
            # Show web browser
            self.web_view.show()
            
            # Load current URL in web view with error handling
            if self.webengine_available:
                try:
                    # Validate URL before loading
                    if self.current_url and self.current_url.startswith(('http://', 'https://')):
                        self.web_view.setUrl(QUrl(self.current_url))
                    else:
                        # Fallback to base URL if current URL is invalid
                        self.web_view.setUrl(QUrl(self.base_url))
                    self.surf_mode_action.setToolTip("Switch to File Manager mode")
                    self.status_bar.showMessage("Web browser mode - HTML rendering enabled")
                except Exception as e:
                    print(f"WebEngine error: {e}")
                    self.status_bar.showMessage(f"WebEngine error: {e}")
                    # Fall back to text mode
                    self.load_html_as_text(self.current_url)
            else:
                # Load HTML content as text
                self.load_html_as_text(self.current_url)
                self.surf_mode_action.setToolTip("Switch to File Manager mode (Simple HTML view)")
                self.status_bar.showMessage("Simple HTML mode - text rendering only")
        except Exception as e:
            print(f"Error entering surf mode: {e}")
            self.status_bar.showMessage(f"Error entering surf mode: {e}")
            # Force exit surf mode if there's an error
            self.surf_mode = False
            self.surf_mode_action.setChecked(False)
            self.exit_surf_mode()
    
    def exit_surf_mode(self):
        """Exit web browser mode and return to file manager"""
        # Hide web browser
        self.web_view.hide()
        
        # Show appropriate file manager view based on current view mode
        if self.view_mode == 'details':
            self.file_table.show()
        elif self.view_mode == 'list':
            self.file_list.show()
        elif self.view_mode == 'icons':
            self.icon_view.show()
        
        self.surf_mode_action.setToolTip("Switch to Web Browser mode")
        self.status_bar.showMessage("File manager mode")
        
        # Reload current directory to refresh file listing
        self.load_directory(self.current_url)

    def load_html_as_text(self, url):
        """Load HTML content as text for fallback mode"""
        try:
            if url and url.startswith(('http://', 'https://')):
                # Use browser-like headers to avoid being flagged as a bot
                headers = {
                    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                }
                
                response = requests.get(url, timeout=10, headers=headers)
                response.raise_for_status()
                if hasattr(self.web_view, 'setPlainText'):
                    self.web_view.setPlainText(response.text)
                else:
                    # Fallback if web_view doesn't have setPlainText
                    self.web_view.setHtml(f"<pre>{response.text}</pre>")
            else:
                if hasattr(self.web_view, 'setPlainText'):
                    self.web_view.setPlainText("Invalid URL or empty content")
                else:
                    self.web_view.setHtml("<p>Invalid URL or empty content</p>")
        except Exception as e:
            error_msg = f"Error loading content: {str(e)}"
            print(error_msg)
            if hasattr(self.web_view, 'setPlainText'):
                self.web_view.setPlainText(error_msg)
            else:
                self.web_view.setHtml(f"<p>{error_msg}</p>")
    
    def web_url_changed(self, url):
        """Handle URL changes in web view (WebEngine only)"""
        if self.surf_mode and self.webengine_available:
            new_url = url.toString()
            if new_url != self.current_url:
                # Update address bar
                self.url_edit.setText(new_url)
                self.current_url = new_url
                # Add to history
                self.add_to_history(self.current_url)
    
    def web_load_finished(self, success):
        """Handle web page load completion (WebEngine only)"""
        if self.webengine_available:
            if success:
                self.status_bar.showMessage("Page loaded successfully")
            else:
                self.status_bar.showMessage("Failed to load page")
    
    def set_view_mode(self, mode):
        """Change the file view mode"""
        self.view_mode = mode
        self.settings['view_mode'] = mode
        
        # Hide all views
        self.file_table.hide()
        self.file_list.hide()
        self.icon_view.hide()
        
        # Show selected view
        if mode == 'details':
            self.file_table.show()
            self.view_combo.setCurrentText('Details')
        elif mode == 'list':
            self.file_list.show()
            self.view_combo.setCurrentText('List')
        elif mode == 'icons':
            self.icon_view.show()
            self.view_combo.setCurrentText('Icons')
        
        self.save_settings()
    
    def toggle_tree_panel(self):
        """Toggle directory tree visibility"""
        visible = not self.left_panel.isVisible()
        self.left_panel.setVisible(visible)
        self.tree_action.setChecked(visible)
        self.settings['show_tree'] = visible
        self.save_settings()
    
    def toggle_info_panel(self):
        """Toggle file info panel visibility"""
        visible = not self.info_widget.isVisible()
        self.info_widget.setVisible(visible)
        self.info_action.setChecked(visible)
        self.settings['show_info'] = visible
        self.save_settings()
    
    def toggle_toolbar(self):
        """Toggle toolbar visibility"""
        visible = not self.toolbar.isVisible()
        self.toolbar.setVisible(visible)
        self.toolbar_action.setChecked(visible)
        self.settings['show_toolbar'] = visible
        self.save_settings()
    
    def toggle_statusbar(self):
        """Toggle status bar visibility"""
        visible = not self.status_bar.isVisible()
        self.status_bar.setVisible(visible)
        self.statusbar_action.setChecked(visible)
        self.settings['show_statusbar'] = visible
        self.save_settings()

    # Download functionality
    def update_download_button_state(self):
        """Update download button enabled state based on selection"""
        has_files_selected = self.get_selected_files() is not None
        self.main_download_button.setEnabled(has_files_selected)
    
    def get_selected_files(self):
        """Get list of selected file items"""
        selected_files = []
        
        if self.file_table.isVisible():
            selected_rows = set()
            for item in self.file_table.selectedItems():
                selected_rows.add(item.row())
            
            for row in selected_rows:
                name_item = self.file_table.item(row, 0)
                if name_item:
                    data = name_item.data(Qt.ItemDataRole.UserRole)
                    if data and data['type'] == 'file':
                        selected_files.append(data)
                        
        elif self.file_list.isVisible():
            for item in self.file_list.selectedItems():
                data = item.data(Qt.ItemDataRole.UserRole)
                if data and data['type'] == 'file':
                    selected_files.append(data)
                    
        elif self.icon_view.isVisible():
            for item in self.icon_view.selectedItems():
                data = item.data(Qt.ItemDataRole.UserRole)
                if data and data['type'] == 'file':
                    selected_files.append(data)
        
        return selected_files if selected_files else None
    
    def open_download_settings(self):
        """Open download settings dialog"""
        dialog = QDialog(self)
        dialog.setWindowTitle('Download Settings')
        dialog.setModal(True)
        dialog.setMinimumSize(400, 150)
        
        layout = QVBoxLayout()
        
        # Download path setting
        path_layout = QGridLayout()
        path_layout.addWidget(QLabel('Default Download Path:'), 0, 0)
        
        path_edit = QLineEdit()
        path_edit.setText(self.settings.get('default_download_path', 
                         os.path.join(os.path.expanduser('~'), 'Downloads')))
        path_layout.addWidget(path_edit, 0, 1)
        
        browse_button = QPushButton('Browse...')
        def browse_path():
            directory = QFileDialog.getExistingDirectory(dialog, 'Select Download Directory', path_edit.text())
            if directory:
                path_edit.setText(directory)
        browse_button.clicked.connect(browse_path)
        path_layout.addWidget(browse_button, 0, 2)
        
        layout.addLayout(path_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        ok_button = QPushButton('OK')
        def accept_settings():
            self.settings['default_download_path'] = path_edit.text()
            self.save_settings()
            dialog.accept()
        ok_button.clicked.connect(accept_settings)
        button_layout.addWidget(ok_button)
        
        cancel_button = QPushButton('Cancel')
        cancel_button.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        dialog.setLayout(layout)
        dialog.exec()
    
    def download_selected_files(self):
        """Download all selected files"""
        selected_files = self.get_selected_files()
        if not selected_files:
            return
        
        download_path = self.settings.get('default_download_path', 
                                        os.path.join(os.path.expanduser('~'), 'Downloads'))
        
        # Ensure download directory exists
        os.makedirs(download_path, exist_ok=True)
        
        # Prepare download items
        download_items = []
        for file_data in selected_files:
            url = urljoin(self.current_url, file_data['href'])
            filename = unquote(file_data['name'])
            download_items.append((url, filename))
        
        # Show status bar if hidden
        if not self.status_bar.isVisible():
            self.status_bar.setVisible(True)
            self.statusbar_action.setChecked(True)
            self.settings['show_statusbar'] = True
            self.save_settings()
        
        # Start multi-file download
        self.multi_download_manager = MultiDownloadManager(download_items, download_path)
        self.multi_download_manager.file_progress.connect(self.update_file_progress)
        self.multi_download_manager.overall_progress.connect(self.update_overall_progress)
        self.multi_download_manager.finished.connect(self.multi_download_finished)
        self.multi_download_manager.start()
        
        # Disable download button during download
        self.main_download_button.setEnabled(False)
    
    def update_file_progress(self, file_index, progress_percent, filename):
        """Update individual file download progress"""
        pass
    
    def update_overall_progress(self, completed_files, total_files, current_filename, current_file_percent):
        """Update overall download progress in status bar"""
        if total_files > 1:
            self.status_bar.showMessage(
                f"{completed_files + 1}/{total_files} files | {current_filename} - {current_file_percent}%"
            )
        else:
            self.status_bar.showMessage(f"Downloading {current_filename} - {current_file_percent}%")
    
    def multi_download_finished(self, success, message):
        """Handle completion of multi-file download"""
        self.main_download_button.setEnabled(True)
        self.status_bar.showMessage(message)
        
        if success:
            QMessageBox.information(self, 'Download Complete', message)
        else:
            QMessageBox.warning(self, 'Download Failed', message)
        
        # Re-enable download button based on current selection
        self.update_download_button_state()

    # File type detection
    def is_web_navigable_file(self, filename):
        """Check if file should be treated as navigable web content"""
        web_extensions = {'.html', '.htm', '.php', '.asp', '.aspx', '.jsp', '.cgi'}
        _, ext = os.path.splitext(filename.lower())
        return ext in web_extensions

    def is_html_file(self, filename):
        """Check if file is an HTML file"""
        html_extensions = {'.html', '.htm', '.php', '.asp', '.aspx', '.jsp', '.cgi'}
        _, ext = os.path.splitext(filename.lower())
        return ext in html_extensions

    # Navigation methods
    def navigate_to_url(self):
        url = self.url_edit.text().strip()
        if url:
            self.add_to_history(self.current_url)
            if self.surf_mode:
                # In surf mode, load URL in web view
                if self.webengine_available:
                    self.web_view.setUrl(QUrl(url))
                else:
                    self.load_html_as_text(url)
                self.current_url = url
            else:
                # In file mode, load as directory listing
                self.load_directory(url)

    def go_back(self):
        if self.history_index > 0:
            self.history_index -= 1
            url = self.history[self.history_index]
            if self.surf_mode:
                if self.webengine_available:
                    self.web_view.setUrl(QUrl(url))
                else:
                    self.load_html_as_text(url)
                self.current_url = url
                self.url_edit.setText(url)
            else:
                self.load_directory(url)
            self.update_navigation_buttons()

    def go_forward(self):
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            url = self.history[self.history_index]
            if self.surf_mode:
                if self.webengine_available:
                    self.web_view.setUrl(QUrl(url))
                else:
                    self.load_html_as_text(url)
                self.current_url = url
                self.url_edit.setText(url)
            else:
                self.load_directory(url)
            self.update_navigation_buttons()

    def go_up(self):
        if self.current_url != self.base_url:
            if self.current_url.endswith('/'):
                parent_url = '/'.join(self.current_url.rstrip('/').split('/')[:-1]) + '/'
            else:
                parent_url = '/'.join(self.current_url.split('/')[:-1]) + '/'
            
            if parent_url.startswith(self.base_url.rstrip('/')):
                self.add_to_history(self.current_url)
                if self.surf_mode:
                    if self.webengine_available:
                        self.web_view.setUrl(QUrl(parent_url))
                    else:
                        self.load_html_as_text(parent_url)
                    self.current_url = parent_url
                    self.url_edit.setText(parent_url)
                else:
                    self.load_directory(parent_url)

    def go_home(self):
        # Check if there's a start page set (first bookmark)
        start_page_url = self.get_start_page_url()
        if start_page_url:
            target_url = start_page_url
        else:
            target_url = self.base_url
            
        if self.current_url != target_url:
            self.add_to_history(self.current_url)
            if self.surf_mode:
                if self.webengine_available:
                    self.web_view.setUrl(QUrl(target_url))
                else:
                    self.load_html_as_text(target_url)
                self.current_url = target_url
                self.url_edit.setText(target_url)
            else:
                self.load_directory(target_url)

    def refresh_current(self):
        if self.surf_mode:
            if self.webengine_available:
                self.web_view.reload()
            else:
                self.load_html_as_text(self.current_url)
        else:
            self.load_directory(self.current_url)

    # Event handlers for different views
    def item_double_clicked(self, item):
        data = item.data(Qt.ItemDataRole.UserRole)
        self.handle_item_action(data)

    def list_item_double_clicked(self, item):
        """Handle double-click in list view"""
        data = item.data(Qt.ItemDataRole.UserRole)
        self.handle_item_action(data)
    
    def icon_item_double_clicked(self, item):
        """Handle double-click in icon view"""
        data = item.data(Qt.ItemDataRole.UserRole)
        self.handle_item_action(data)
    
    def handle_item_action(self, data):
        """Handle double-click action on any item"""
        if data and data['type'] == 'directory':
            new_url = urljoin(self.current_url, data['href'])
            self.add_to_history(self.current_url)
            if self.surf_mode:
                # In surf mode, load in web view
                if self.webengine_available:
                    self.web_view.setUrl(QUrl(new_url))
                else:
                    self.load_html_as_text(new_url)
                self.current_url = new_url
                self.url_edit.setText(new_url)
            else:
                # In file mode, load as directory listing
                self.load_directory(new_url)
        elif data and data['type'] == 'file':
            # Handle file clicks based on type and mode
            if self.is_html_file(data['name']):
                new_url = urljoin(self.current_url, data['href'])
                if self.surf_mode:
                    # In surf mode, render HTML in web view
                    if self.webengine_available:
                        self.web_view.setUrl(QUrl(new_url))
                    else:
                        self.load_html_as_text(new_url)
                    self.current_url = new_url
                    self.url_edit.setText(new_url)
                else:
                    # In file mode, treat as navigable directory-like content
                    self.add_to_history(self.current_url)
                    self.load_directory(new_url)

    def tree_item_clicked(self, item):
        url = item.data(0, Qt.ItemDataRole.UserRole)
        if url and url != self.current_url:
            self.add_to_history(self.current_url)
            self.load_directory(url)

    def selection_changed(self):
        selected_items = self.file_table.selectedItems()
        if selected_items:
            # Get the first column item which contains our data
            row = selected_items[0].row()
            name_item = self.file_table.item(row, 0)
            data = name_item.data(Qt.ItemDataRole.UserRole)
            self.update_info_panel(data)
        else:
            self.clear_info_panel()

    def list_selection_changed(self):
        """Handle selection change in list view"""
        selected_items = self.file_list.selectedItems()
        if selected_items:
            data = selected_items[0].data(Qt.ItemDataRole.UserRole)
            self.update_info_panel(data)
        else:
            self.clear_info_panel()
    
    def icon_selection_changed(self):
        """Handle selection change in icon view"""
        selected_items = self.icon_view.selectedItems()
        if selected_items:
            data = selected_items[0].data(Qt.ItemDataRole.UserRole)
            self.update_info_panel(data)
        else:
            self.clear_info_panel()
    
    def update_info_panel(self, data):
        """Update the file information panel"""
        info_text = f"Name: {data['name']}\n"
        info_text += f"Type: {data['type'].title()}\n"
        if data['size']:
            info_text += f"Size: {data['size']}\n"
        if data['modified']:
            info_text += f"Modified: {data['modified']}\n"
        info_text += f"URL: {urljoin(self.current_url, data['href'])}"
        
        self.info_text.setPlainText(info_text)
        self.download_button.setEnabled(data['type'] == 'file')
        
        # Handle preview for files
        if data['type'] == 'file':
            file_url = urljoin(self.current_url, data['href'])
            filename = data['name']
            
            # Clear previous previews
            self.hide_image_preview()
            self.clear_text_preview()
            
            # Show appropriate preview
            if self.is_image_file(filename):
                self.show_image_preview(file_url)
            elif self.is_text_file(filename):
                self.show_text_preview(file_url)
        else:
            # Clear previews for directories
            self.hide_image_preview()
            self.clear_text_preview()
    
    def clear_info_panel(self):
        """Clear the file information panel"""
        self.info_text.clear()
        self.download_button.setEnabled(False)
        self.hide_image_preview()
        self.clear_text_preview()
    
    def clear_info_panel(self):
        """Clear the file information panel"""
        self.info_text.clear()
        self.download_button.setEnabled(False)

    def change_view(self, view_type):
        """Handle view mode change from combo box"""
        if view_type == 'Details':
            self.set_view_mode('details')
        elif view_type == 'List':
            self.set_view_mode('list')
        elif view_type == 'Icons':
            self.set_view_mode('icons')

    def sort_files(self):
        self.populate_file_views()

    def toggle_sort_order(self):
        if self.sort_order == Qt.SortOrder.AscendingOrder:
            self.sort_order = Qt.SortOrder.DescendingOrder
            sort_desc_icon = self.get_ui_icon('view-sort-descending')
            if sort_desc_icon:
                self.sort_order_button.setIcon(sort_desc_icon)
                self.sort_order_button.setText('')
            else:
                self.sort_order_button.setText('↓')
        else:
            self.sort_order = Qt.SortOrder.AscendingOrder
            sort_asc_icon = self.get_ui_icon('view-sort-ascending')
            if sort_asc_icon:
                self.sort_order_button.setIcon(sort_asc_icon)
                self.sort_order_button.setText('')
            else:
                self.sort_order_button.setText('↑')
        self.populate_file_views()

    def header_clicked(self, logical_index):
        columns = ['Name', 'Size', 'Type', 'Modified']
        if logical_index < len(columns):
            self.sort_combo.setCurrentText(columns[logical_index])
            self.sort_files()

    def download_file(self):
        # Get selected item from the currently visible view
        data = None
        if self.file_table.isVisible():
            selected_items = self.file_table.selectedItems()
            if selected_items:
                row = selected_items[0].row()
                name_item = self.file_table.item(row, 0)
                data = name_item.data(Qt.ItemDataRole.UserRole)
        elif self.file_list.isVisible():
            selected_items = self.file_list.selectedItems()
            if selected_items:
                data = selected_items[0].data(Qt.ItemDataRole.UserRole)
        elif self.icon_view.isVisible():
            selected_items = self.icon_view.selectedItems()
            if selected_items:
                data = selected_items[0].data(Qt.ItemDataRole.UserRole)
        
        if not data or data['type'] != 'file':
            return
        
        file_url = urljoin(self.current_url, data['href'])
        filename = unquote(data['name'])
        
        save_path, _ = QFileDialog.getSaveFileName(
            self, 
            'Save File', 
            os.path.join(os.path.expanduser('~'), 'Downloads', filename),
            'All Files (*)'
        )
        
        if save_path:
            self.start_download(file_url, save_path)

    def start_download(self, url, filepath):
        self.download_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_bar.showMessage(f'Downloading {os.path.basename(filepath)}...')
        
        self.download_thread = DownloadThread(url, filepath)
        self.download_thread.progress.connect(self.update_download_progress)
        self.download_thread.finished.connect(self.download_finished)
        self.download_thread.start()

    def update_download_progress(self, progress):
        self.progress_bar.setValue(progress)

    def download_finished(self, success, message):
        self.download_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_bar.showMessage(message)
        
        if success:
            QMessageBox.information(self, 'Download Complete', message)
        else:
            QMessageBox.warning(self, 'Download Failed', message)

    def open_download_folder(self):
        download_path = os.path.join(os.path.expanduser('~'), 'Downloads')
        os.system(f'xdg-open "{download_path}"')
    
    def closeEvent(self, event):
        """Save settings when closing the application"""
        self.save_settings()
        event.accept()

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        if event.key() == Qt.Key.Key_F3:
            # F3 for next search result
            if self.search_active and self.search_results:
                self.current_search_index = (self.current_search_index + 1) % len(self.search_results)
                if self.surf_mode:
                    self.highlight_search_result()
                else:
                    self.highlight_file_search_result()
        elif event.key() == Qt.Key.Key_F3 and event.modifiers() == Qt.KeyboardModifier.ShiftModifier:
            # Shift+F3 for previous search result
            if self.search_active and self.search_results:
                self.current_search_index = (self.current_search_index - 1) % len(self.search_results)
                if self.surf_mode:
                    self.highlight_search_result()
                else:
                    self.highlight_file_search_result()
        elif event.key() == Qt.Key.Key_Escape:
            # Escape to close search
            if self.search_active:
                self.toggle_search()
        else:
            super().keyPressEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    browser = WebCrawler()
    browser.show()
    sys.exit(app.exec())
