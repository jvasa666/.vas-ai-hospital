#!/usr/bin/env python3
"""
VAS Secure Medical Browser
==========================
Ultra-secure, isolated browser for hospital staff and doctors.
"""

import sys
import os
import json
import hashlib
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse
import re

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QTabWidget, QLabel, QMessageBox,
    QDialog, QListWidget, QTextEdit, QStatusBar, QToolBar,
    QInputDialog
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import (
    QWebEnginePage,
    QWebEngineProfile,
    QWebEngineSettings,
    QWebEngineUrlRequestInterceptor,
    QWebEngineUrlRequestInfo,
)
from PyQt6.QtCore import QUrl, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QKeySequence

# ==========================================
# SECURITY CONFIGURATION
# ==========================================

class SecurityConfig:
    """VAS Security Configuration - Medical Grade"""

    ALLOWED_DOMAINS = [
        "pubmed.ncbi.nlm.nih.gov",
        "medlineplus.gov",
        "who.int",
        "cdc.gov",
        "fda.gov",
        "nih.gov",
        "mayoclinic.org",
        "webmd.com",
        "uptodate.com",
        "medscape.com",
        "nejm.org",
        "bmj.com",
        "thelancet.com",
        "drugs.com",
        "rxlist.com",
        "epocrates.com",
        "micromedex.com",
        "jamanetwork.com",
        "nature.com",
        "sciencedirect.com",
        "springer.com",
        "localhost",
        "127.0.0.1",
        "vas-hospital.local",
        "hl7.org",
        "fhir.org",
        "icd.who.int",
        "ama-assn.org",
    ]

    SESSION_TIMEOUT = 30
    MAX_TABS = 5

    ALLOW_DOWNLOADS = False
    ALLOW_COPY_PASTE = True
    ENABLE_SCREENSHOTS = False
    ENABLE_JAVASCRIPT = True
    ENABLE_PLUGINS = False

    AUDIT_LOG_PATH = Path.home() / ".vas-secure-browser" / "audit.db"
    CACHE_ENCRYPTION_KEY = "VAS_SECURE_CACHE_KEY_CHANGE_IN_PROD"

# ==========================================
# URL REQUEST INTERCEPTOR
# ==========================================

class VASRequestInterceptor(QWebEngineUrlRequestInterceptor):
    """Intercepts and blocks unauthorized requests"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.blocked_count = 0
        self.allowed_count = 0

    def interceptRequest(self, info: QWebEngineUrlRequestInfo):
        url = info.requestUrl().toString()
        parsed = urlparse(url)
        domain = parsed.hostname or ""

        if domain.startswith("www."):
            domain = domain[4:]

        is_allowed = any(
            allowed == domain or domain.endswith("." + allowed)
            for allowed in SecurityConfig.ALLOWED_DOMAINS
        )

        if not is_allowed:
            info.block(True)
            self.blocked_count += 1
            print(f"[BLOCKED] {url}")
        else:
            self.allowed_count += 1
            print(f"[ALLOWED] {url}")

# ==========================================
# SECURE WEB PAGE
# ==========================================

class VASSecurePage(QWebEnginePage):
    """Custom web page with security restrictions"""

    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        pass  # suppress console

    def acceptNavigationRequest(self, url, nav_type, is_main_frame):
        domain = urlparse(url.toString()).netloc
        if domain.startswith("www."):
            domain = domain[4:]

        is_allowed = any(
            allowed == domain or domain.endswith("." + allowed)
            for allowed in SecurityConfig.ALLOWED_DOMAINS
        )

        if not is_allowed and is_main_frame:
            QMessageBox.warning(
                None,
                "Access Denied",
                f"Domain not whitelisted: {domain}\n\n"
                f"Contact IT to add trusted medical domains.",
            )
            return False

        return True

# ==========================================
# AUDIT LOGGER
# ==========================================

class AuditLogger:
    """Logs all browser activity for compliance"""

    def __init__(self):
        self.db_path = SecurityConfig.AUDIT_LOG_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                url TEXT,
                user_id TEXT,
                session_id TEXT,
                details TEXT
            )
            """
        )
        conn.commit()
        conn.close()

    def log_event(self, event_type, url=None, user_id=None, session_id=None, details=None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO audit_log (timestamp, event_type, url, user_id, session_id, details)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now().isoformat(),
                event_type,
                url,
                user_id or "unknown",
                session_id or "unknown",
                details,
            ),
        )
        conn.commit()
        conn.close()
        print(f"[AUDIT] {event_type}: {url or details}")

# ==========================================
# SECURE BROWSER WIDGET
# ==========================================

class VASSecureBrowser(QWidget):
    url_changed = pyqtSignal(QUrl)
    title_changed = pyqtSignal(str)

    def __init__(self, profile, audit_logger, parent=None):
        super().__init__(parent)
        self.audit_logger = audit_logger
        self.profile = profile
        self.session_id = hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8]
        self._setup_ui()
        self._setup_security()

    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.web_view = QWebEngineView()
        self.page = VASSecurePage(self.profile, self.web_view)
        self.web_view.setPage(self.page)

        layout.addWidget(self.web_view)
        self.setLayout(layout)

        self.web_view.urlChanged.connect(self._on_url_changed)
        self.web_view.titleChanged.connect(self._on_title_changed)
        self.web_view.loadFinished.connect(self._on_load_finished)

    def _setup_security(self):
        s = self.web_view.settings()
        s.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled,
                       SecurityConfig.ENABLE_JAVASCRIPT)
        s.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled,
                       SecurityConfig.ENABLE_PLUGINS)
        s.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, False)
        s.setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, False)
        s.setAttribute(QWebEngineSettings.WebAttribute.AutoLoadImages, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.DnsPrefetchEnabled, False)

    def _on_url_changed(self, url):
        self.audit_logger.log_event(
            "NAVIGATE",
            url=url.toString(),
            session_id=self.session_id,
        )
        self.url_changed.emit(url)

    def _on_title_changed(self, title):
        self.title_changed.emit(title)

    def _on_load_finished(self, success):
        if success:
            self.page.runJavaScript(
                """
                document.addEventListener('contextmenu', e => e.preventDefault());
                document.querySelectorAll('script[src*="analytics"], script[src*="tracking"]')
                    .forEach(el => el.remove());
                """
            )

    def navigate_to(self, url):
        if isinstance(url, str):
            url = QUrl(url)
        self.web_view.setUrl(url)

    def get_url(self):
        return self.web_view.url().toString()

    def get_title(self):
        return self.web_view.title()

# ==========================================
# MAIN BROWSER WINDOW
# ==========================================

class VASSecureBrowserWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.audit_logger = AuditLogger()
        self.session_start = datetime.now()
        self.last_activity = datetime.now()

        self.profile = QWebEngineProfile("VASSecureProfile", self)
        self.profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.MemoryHttpCache)
        self.profile.setPersistentCookiesPolicy(
            QWebEngineProfile.PersistentCookiesPolicy.NoPersistentCookies
        )

        self.interceptor = VASRequestInterceptor(self)
        self.profile.setUrlRequestInterceptor(self.interceptor)

        self._setup_ui()
        self._setup_timers()
        self._setup_shortcuts()

        self.audit_logger.log_event("SESSION_START", details="VAS Secure Browser launched")

        self.setWindowTitle("VAS Secure Medical Browser")
        self.resize(1400, 900)
        self._show_welcome_page()

    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        self._create_toolbar()
        self._create_address_bar()

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self._close_tab)
        self.tabs.currentChanged.connect(self._on_tab_changed)
        layout.addWidget(self.tabs)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self._update_status()

        central_widget.setLayout(layout)
        self._add_new_tab()

    def _create_toolbar(self):
        toolbar = QToolBar("Navigation")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        back_btn = QAction("← Back", self)
        back_btn.triggered.connect(lambda: self._current_browser().web_view.back())
        toolbar.addAction(back_btn)

        fwd_btn = QAction("Forward →", self)
        fwd_btn.triggered.connect(lambda: self._current_browser().web_view.forward())
        toolbar.addAction(fwd_btn)

        reload_btn = QAction("⟳ Reload", self)
        reload_btn.triggered.connect(lambda: self._current_browser().web_view.reload())
        toolbar.addAction(reload_btn)

        home_btn = QAction("🏠 Home", self)
        home_btn.triggered.connect(self._show_welcome_page)
        toolbar.addAction(home_btn)

        toolbar.addSeparator()

        new_tab_btn = QAction("+ New Tab", self)
        new_tab_btn.triggered.connect(self._add_new_tab)
        toolbar.addAction(new_tab_btn)

        toolbar.addSeparator()

        whitelist_btn = QAction("🛡️ Whitelist", self)
        whitelist_btn.triggered.connect(self._show_whitelist_manager)
        toolbar.addAction(whitelist_btn)

        audit_btn = QAction("📋 Audit Log", self)
        audit_btn.triggered.connect(self._show_audit_log)
        toolbar.addAction(audit_btn)

    def _create_address_bar(self):
        address_widget = QWidget()
        address_layout = QHBoxLayout()
        address_layout.setContentsMargins(5, 5, 5, 5)

        self.security_label = QLabel("🔒 SECURE")
        self.security_label.setStyleSheet(
            "QLabel { color: green; font-weight: bold; padding: 5px; "
            "background: #e8f5e9; border-radius: 3px; }"
        )
        address_layout.addWidget(self.security_label)

        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Enter medical resource URL...")
        self.url_bar.returnPressed.connect(self._navigate_to_url)
        address_layout.addWidget(self.url_bar, stretch=1)

        go_btn = QPushButton("Go")
        go_btn.clicked.connect(self._navigate_to_url)
        address_layout.addWidget(go_btn)

        address_widget.setLayout(address_layout)
        toolbar = self.addToolBar("Address")
        toolbar.setMovable(False)
        toolbar.addWidget(address_widget)

    def _setup_timers(self):
        self.timeout_timer = QTimer()
        self.timeout_timer.timeout.connect(self._check_session_timeout)
        self.timeout_timer.start(60000)

        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_status)
        self.status_timer.start(5000)

    def _setup_shortcuts(self):
        a = QAction("New Tab", self, shortcut=QKeySequence("Ctrl+T"),
                    triggered=self._add_new_tab)
        self.addAction(a)

        a = QAction("Close Tab", self, shortcut=QKeySequence("Ctrl+W"),
                    triggered=lambda: self._close_tab(self.tabs.currentIndex()))
        self.addAction(a)

        a = QAction("Focus Address Bar", self, shortcut=QKeySequence("Ctrl+L"),
                    triggered=self.url_bar.setFocus)
        self.addAction(a)

    def _add_new_tab(self):
        if self.tabs.count() >= SecurityConfig.MAX_TABS:
            QMessageBox.warning(
                self,
                "Tab Limit",
                f"Maximum {SecurityConfig.MAX_TABS} tabs allowed for security.",
            )
            return

        browser = VASSecureBrowser(self.profile, self.audit_logger, self)
        browser.url_changed.connect(self._on_browser_url_changed)
        browser.title_changed.connect(
            lambda title: self._on_browser_title_changed(browser, title)
        )

        idx = self.tabs.addTab(browser, "New Tab")
        self.tabs.setCurrentIndex(idx)
        self.audit_logger.log_event("TAB_OPENED")
        self._update_activity()

    def _close_tab(self, index):
        if self.tabs.count() <= 1:
            return
        self.tabs.removeTab(index)
        self.audit_logger.log_event("TAB_CLOSED")
        self._update_activity()

    def _current_browser(self):
        return self.tabs.currentWidget()

    def _on_tab_changed(self, index):
        browser = self.tabs.widget(index)
        if browser:
            self.url_bar.setText(browser.get_url())
            self._update_activity()

    def _on_browser_url_changed(self, url):
        if self.sender() == self._current_browser():
            self.url_bar.setText(url.toString())
        self._update_activity()

    def _on_browser_title_changed(self, browser, title):
        index = self.tabs.indexOf(browser)
        if index >= 0:
            self.tabs.setTabText(
                index, title[:30] + "..." if len(title) > 30 else title
            )

    def _navigate_to_url(self):
        url = self.url_bar.text().strip()
        if not url:
            return
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        browser = self._current_browser()
        if browser:
            browser.navigate_to(url)
            self._update_activity()

    def _show_welcome_page(self):
        browser = self._current_browser()
        if not browser:
            return
        html = "<html><body><h1>VAS Secure Medical Browser</h1></body></html>"
        browser.web_view.setHtml(html)

    def _show_whitelist_manager(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Domain Whitelist Manager")
        dialog.resize(600, 500)

        layout = QVBoxLayout()
        info = QLabel("✅ Whitelisted Domains (sites staff can access):")
        layout.addWidget(info)

        list_widget = QListWidget()
        list_widget.addItems(sorted(SecurityConfig.ALLOWED_DOMAINS))
        layout.addWidget(list_widget)

        btn_layout = QHBoxLayout()

        add_btn = QPushButton("➕ Add Domain")
        add_btn.clicked.connect(lambda: self._add_domain(list_widget))
        btn_layout.addWidget(add_btn)

        remove_btn = QPushButton("➖ Remove Domain")
        remove_btn.clicked.connect(lambda: self._remove_domain(list_widget))
        btn_layout.addWidget(remove_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)
        dialog.setLayout(layout)
        dialog.exec()

    def _add_domain(self, list_widget):
        """Add domain to whitelist"""
        domain, ok = QInputDialog.getText(
            self,
            "Add Domain",
            "Enter domain to whitelist (e.g., medlineplus.gov or localhost):"
        )
        
        if ok and domain:
            raw = domain.strip().lower()
            
            # If user pastes a full URL, normalize to hostname
            from urllib.parse import urlparse
            parsed = urlparse(raw)
            if parsed.hostname:
                domain = parsed.hostname
            else:
                # no scheme; strip port if present (localhost:3002 -> localhost)
                domain = raw.split(":", 1)[0]
            
            if domain not in SecurityConfig.ALLOWED_DOMAINS:
                SecurityConfig.ALLOWED_DOMAINS.append(domain)
                list_widget.addItem(domain)
                self.audit_logger.log_event("WHITELIST_ADD", details=domain)
                QMessageBox.information(self, "Success", f"Added {domain} to whitelist")

    def _remove_domain(self, list_widget):
        current = list_widget.currentItem()
        if current:
            domain = current.text()
            SecurityConfig.ALLOWED_DOMAINS.remove(domain)
            list_widget.takeItem(list_widget.row(current))
            self.audit_logger.log_event("WHITELIST_REMOVE", details=domain)

    def _show_audit_log(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Security Audit Log")
        dialog.resize(900, 600)

        layout = QVBoxLayout()
        info = QLabel(
            f"📋 Session started: {self.session_start.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        layout.addWidget(info)

        log_text = QTextEdit()
        log_text.setReadOnly(True)
        layout.addWidget(log_text)

        conn = sqlite3.connect(self.audit_logger.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT timestamp, event_type, url, details
            FROM audit_log
            ORDER BY id DESC
            LIMIT 1000
            """
        )
        logs = []
        for row in cursor.fetchall():
            timestamp, event_type, url, details = row
            line = f"[{timestamp}] {event_type:20s}"
            if url:
                line += f" | {url}"
            if details:
                line += f" | {details}"
            logs.append(line)
        conn.close()

        log_text.setPlainText("\n".join(logs))

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

        dialog.setLayout(layout)
        dialog.exec()

    def _check_session_timeout(self):
        inactive_time = datetime.now() - self.last_activity
        if inactive_time > timedelta(minutes=SecurityConfig.SESSION_TIMEOUT):
            self.audit_logger.log_event("SESSION_TIMEOUT", details="Automatic logout")
            QMessageBox.warning(
                self,
                "Session Timeout",
                f"Session expired after {SecurityConfig.SESSION_TIMEOUT} minutes of "
                "inactivity.\n\nThe browser will now close for security.",
            )
            self.close()

    def _update_activity(self):
        self.last_activity = datetime.now()

    def _update_status(self):
        session_duration = datetime.now() - self.session_start
        inactive_time = datetime.now() - self.last_activity
        status_text = (
            f"🔒 Secure Session | "
            f"⏱ Session: {session_duration.seconds // 60}m | "
            f"💤 Idle: {inactive_time.seconds // 60}m | "
            f"📊 Tabs: {self.tabs.count()}/{SecurityConfig.MAX_TABS} | "
            f"🛡️ Blocked: {self.interceptor.blocked_count} | "
            f"✅ Allowed: {self.interceptor.allowed_count}"
        )
        self.status_bar.showMessage(status_text)

    def closeEvent(self, event):
        self.audit_logger.log_event("SESSION_END", details="Browser closed")
        event.accept()

# ==========================================
# MAIN APPLICATION
# ==========================================

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("VAS Secure Medical Browser")
    app.setStyle("Fusion")
    window = VASSecureBrowserWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
