#!/usr/bin/env python3

# V. 0.2.8

import sys, os, json
from subprocess import Popen
from PyQt6.QtWidgets import (QMainWindow,QApplication,QWidget,QSpinBox,QFormLayout,QTabWidget,QDialog,QMessageBox,QComboBox,QTextEdit,QVBoxLayout,QHBoxLayout,QSizePolicy,QPushButton,QLabel,QLineEdit,QMenu,QAbstractScrollArea)
from PyQt6.QtGui import (QTextCursor,QIcon,QColor,QTextOption,QTextDocument,QImage,QPixmap,QAction,QKeyEvent)
from PyQt6.QtCore import (Qt,QUrl,QByteArray,QEvent,QPoint,QRect,QVariant)
import zipfile
from html.parser import HTMLParser, unescape
import urllib.parse as _parse
from urllib.parse import unquote, urlparse
from PyQt6 import QtPrintSupport
from cfgCfg import *

# home dir
# MY_HOME = os.path.expanduser('~')
# this program working directory
curr_dir = os.getcwd()
os.chdir(curr_dir)

WINW = 1400
WINH = 950

_starting_config = {"background":"", "textcolor":"", "fontfamily":"", "margins":40, "pagezoom":2, "use-css": 1, "use-font": 0, "text-alignment": 0}
_config_file = os.path.join(curr_dir,"config.json")
_settings_conf = None
if not os.path.exists(_config_file):
    try:
        _ff = open(_config_file,"w")
        _data_json = _starting_config
        json.dump(_data_json, _ff, indent = 4)
        _ff.close()
        _settings_conf = _starting_config
    except:
        _error_log("Config file error.")
        sys.exit()
else:
    _ff = open(_config_file, "r")
    _settings_conf = json.load(_ff)
    _ff.close()

#
BACKGROUND = _settings_conf["background"]
TEXTCOLOR = _settings_conf["textcolor"]
FONTFAMILY = _settings_conf["fontfamily"]
MARGINS = _settings_conf["margins"]
PAGEZOOM = _settings_conf["pagezoom"]
TEXTALIGNMENT = _settings_conf["text-alignment"]
USE_STYLESHEET = _settings_conf["use-css"]
USE_EMBEDDED_FONT = _settings_conf["use-font"]

if USE_STYLESHEET == 2:
    USE_EMBEDDED_FONT = 0

try:
    with open("epubreadersize.cfg", "r") as ifile:
        fcontent = ifile.readline()
    aw, ah= fcontent.split(";")
    WINW = int(aw)
    WINH = int(ah)
except:
    WINW = 600
    WINH = 800

############# epub parser #############

# book data
_title = ""
_creator = ""
_date = ""
_language = ""
_subject = ""
_coverage = ""
_rights = ""
_publisher = ""

# ebook data
manifest_list = []

# ebook pages - the page ordering
pages_list = []


class MyHTMLParser(HTMLParser):
    
    def handle_starttag(self, tag, attrs):
        if tag == "item":
            manifest_list.append(attrs)
        # el
        if tag == "dc:title":
            global _title
            _title = "dc:title"
        elif tag == "dc:creator":
            global _creator
            _creator = "dc:creator"
        elif tag == "dc:date":
            global _date
            _date = "dc:date"
        elif tag == "dc:language":
            global _language
            _language = "dc:language"
        elif tag == "dc:subject":
            global _subject
            _subject = "dc:subject"
        elif tag == "dc:coverage":
            global _coverage
            _coverage = "dc:coverage"
        elif tag == "dc:rights":
            global _rights
            _rights = "dc:rights"
        elif tag == "dc:publisher":
            global _publisher
            _publisher = "dc:publisher"
        #
        if tag == "itemref":
            pages_list.append(attrs)

    def handle_endtag(self, tag):
        pass

    def handle_data(self, data):
        global _title
        global _creator
        global _date
        global _language
        global _subject
        global _coverage
        global _rights
        global _publisher
        if _title == "dc:title":
            _title = data
        if _creator == "dc:creator":
            _creator = data
        if _date == "dc:date":
            _date = data
        if _language == "dc:language":
            _language = data
        if _subject == "dc:subject":
            _subject = data
        if _coverage == "dc:coverage":
            _coverage = data
        if _rights == "dc:rights":
            _rights = data
        if _publisher == "dc:publisher":
            _publisher = data

_toc = None
# the ebook images
_list_images = []
# the real pages to read - filename with path
_list_pages = []


def _parse_epub_data(_file):
    parser = MyHTMLParser()
    parser.feed(_file)
    # the ebook images
    for el in manifest_list:
        _is_image = 0
        for ell in el:
            if ell[0] == 'media-type':
                if 'image/' in ell[1]:
                    _is_image = 1
        if _is_image == 1:
            for ell in el:
                if ell[0] == 'href':
                    _list_images.append(ell[1])
    # the real pages to read - filename with path
    for el in pages_list:
        # the page identifier found in the manifest e.g. titlepage
        _p = el[0][1]
        for ell in manifest_list:
            if ('id', _p) in ell:# and ('media-type', 'application/xhtml+xml') in ell:
                for elll in ell:
                    if elll[0] == 'href':
                        _p_name = elll[1]
                        if _p_name[0:2] == "./":
                            _p_name = _p_name[2:]
                        _list_pages.append(_p_name)
    #
    parser.close()

############ end epub parser #############



class dictMainWindow(QMainWindow):
    
    def __init__(self):
        super(dictMainWindow, self).__init__()
        self.setContentsMargins(2,2,2,2)
        self.setWindowIcon(QIcon(os.path.join(curr_dir,"icons/ebook-reader.png")))
        self.pixel_ratio = self.devicePixelRatio()
        self.resize(int(WINW), int(WINH))
        self.setWindowTitle("Epub reader")
        #
        self.main_box = QVBoxLayout()
        self.main_box.setContentsMargins(0,0,0,0)
        _widget = QWidget()
        _widget.setLayout(self.main_box)
        self.setCentralWidget(_widget)
        #
        self.button_box = QHBoxLayout()
        self.main_box.addLayout(self.button_box)
        #
        self.chap_btn = QComboBox()
        self.button_box.addWidget(self.chap_btn)
        self.chap_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.chap_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        #
        self.prev_btn = QPushButton()
        self.prev_btn.setIcon(QIcon().fromTheme("previous", QIcon(os.path.join(curr_dir, "icons", "previous.png"))))
        self.prev_btn.setToolTip("Previous page")
        self.button_box.addWidget(self.prev_btn)
        self.prev_btn.clicked.connect(lambda:self.on_change_page(-1))
        self.prev_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        #
        self.next_btn = QPushButton()
        self.next_btn.setIcon(QIcon().fromTheme("next", QIcon(os.path.join(curr_dir, "icons", "next.png"))))
        self.next_btn.setToolTip("Next page")
        self.button_box.addWidget(self.next_btn)
        self.next_btn.clicked.connect(lambda:self.on_change_page(1))
        self.next_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        #
        self.zoom_in_btn = QPushButton()
        self.zoom_in_btn.setIcon(QIcon().fromTheme("zoom-in", QIcon(os.path.join(curr_dir, "icons", "zoom-in.png"))))
        self.zoom_in_btn.setToolTip("Increase the text size")
        self.button_box.addWidget(self.zoom_in_btn)
        self.zoom_in_btn.clicked.connect(lambda:self.on_zoom_action(1))
        self.zoom_in_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        #
        self.zoom_out_btn = QPushButton()
        self.zoom_out_btn.setIcon(QIcon().fromTheme("zoom-out", QIcon(os.path.join(curr_dir, "icons", "zoom-out.png"))))
        self.zoom_out_btn.setToolTip("Decrease the text size")
        self.button_box.addWidget(self.zoom_out_btn)
        self.zoom_out_btn.clicked.connect(lambda:self.on_zoom_action(-1))
        self.zoom_out_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        #
        self.menu_btn = QPushButton()
        self.menu_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.menu_btn.setIcon(QIcon(os.path.join(curr_dir,"icons/gear.png")))
        self.menu_in_btn = QMenu()
        self.menu_btn.setMenu(self.menu_in_btn)
        self.button_box.addWidget(self.menu_btn)
        # custom action
        if CUSTOM_ACTIONS != []:
            for el in CUSTOM_ACTIONS:
                _name = el[0]
                _action = el[1]
                _caction = QAction(_name, self)
                if el[2] != "":
                    _caction.setIcon( QIcon(os.path.join(curr_dir, "custom_actions", el[2])) )
                _caction.triggered.connect( lambda checked, item=_action: self.on_cation(item) )
                self.menu_in_btn.addAction(_caction)
            self.menu_in_btn.addSeparator()
        #
        self._action_conf = QAction(QIcon().fromTheme("gtk-preferences", QIcon(os.path.join(curr_dir, "icons", "configurator.png"))),"Settings")
        self.menu_in_btn.addAction(self._action_conf)
        self._action_conf.triggered.connect(self.on_conf)
        #
        self._action_placeholder = QAction(QIcon().fromTheme("bookmark-new", QIcon(os.path.join(curr_dir, "icons", "bookmark-new.png"))),"Bookmark")
        self.menu_in_btn.addAction(self._action_placeholder)
        self._action_placeholder.triggered.connect(self.on_placeholder)
        #
        self._action_info = QAction( QIcon(os.path.join(curr_dir,"icons/information.png")), "Epub info" )
        self.menu_in_btn.addAction(self._action_info)
        self._action_info.triggered.connect(self.on_info)
        #
        self._action_print = QAction(QIcon().fromTheme("stock_print", QIcon(os.path.join(curr_dir, "icons", "document-print.png"))),"Print")
        self.menu_in_btn.addAction(self._action_print)
        self._action_print.triggered.connect(self.on_print)
        #
        self.menu_in_btn.addSeparator()
        #
        self._action_exit = QAction(QIcon().fromTheme("application-exit", QIcon().fromTheme("application-exit", QIcon(os.path.join(curr_dir, "icons", "exit.png")))),"Exit")
        self.menu_in_btn.addAction(self._action_exit)
        self._action_exit.triggered.connect(self.close)
        #
        self.text_edit = QTextEdit()
        self.main_box.addWidget(self.text_edit)
        self.text_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.text_edit.setReadOnly(True)
        self.text_edit.document().setDefaultTextOption(QTextOption(Qt.AlignmentFlag.AlignJustify))
        self.text_edit.document().setDocumentMargin(MARGINS)
        # self.text_edit.document().setIndentWidth(24)
        self.text_edit.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse|Qt.TextInteractionFlag.LinksAccessibleByMouse)
        self.text_edit.setFocus()
        self.text_edit.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        #
        self.change_page = 0
        #
        if PAGEZOOM > 0:
            for i in range(PAGEZOOM):
                self.text_edit.zoomIn()
        elif PAGEZOOM < 0:
            for i in range(abs(PAGEZOOM)):
                self.text_edit.zoomOut()
        #
        if BACKGROUND and TEXTCOLOR:
            self.text_edit.setStyleSheet("background-color: {}; color: {};".format(BACKGROUND,TEXTCOLOR))
        elif BACKGROUND:
            self.text_edit.setStyleSheet("background-color: {};".format(BACKGROUND))
        elif TEXTCOLOR:
            self.text_edit.setStyleSheet("color: {};".format(TEXTCOLOR))
        #
        if FONTFAMILY:
            _font = self.text_edit.font()
            _font.setFamily(FONTFAMILY)
            self.text_edit.setFont(_font)
        #
        self.actual_search = ""
        #
        self.show()
        #
        self.title_list = []
        self.chapter_list = []
        #
        self._opf_file = None
        #
        self._css = []
        # _css file full path
        self._css_css = []
        self._ffile = None
        # the epub in memory
        self.input_zip = None
        if len(sys.argv) > 1:
            self._ffile = os.path.realpath(sys.argv[1])
        if self._ffile and os.path.isfile(self._ffile) and os.path.exists(self._ffile) and os.access(self._ffile, os.R_OK):
            # load the epub into memory
            self.load_zip(self._ffile)
            #
            self.list_image_full_path = []
            #
            self.list_fonts = []
            #
            if self._opf_file:
                _parse_epub_data(self._opf_file)
                if USE_STYLESHEET == 1:
                    self._parse_epub_css(self._opf_file)
                elif USE_STYLESHEET == 2:
                    self.custom_css = ""
                    self.parse_custom_css()
                #
                self.load_image_full_path()
                #
                self._info_data = "Title: {}\nCreator: {}\nDate: {}\nLanguage: {}\nSubject: {}\nCoverage: {}\nRights: {}\nPublisher: {}".format(_title,_creator,_date,_language,_subject,_coverage,_rights,_publisher)
                #
                if _title:
                    self.setWindowTitle(_title)
                else:
                    self.setWindowTitle(os.path.basename(self._ffile))
                #
                self._load_data()
                #
                self.pop_chap_btn()
                #
                self.isStarted = False
                #
                # load all the placeholders
                # full file name - page name - position startxend
                self._placeholders = []
                self.on_load_placeholders()
                ## find the placeholder
                # placeholder position
                self.placeholder_position = ()
                ret = self.find_placeholder()
                if ret:
                    self._load_page(ret)
                    self.chap_btn.setCurrentIndex(ret)
                    self.isStarted = True
                else:
                    self._load_page(0)
                    self.isStarted = True
                #
                self.text_edit.mouseReleaseEvent = self.on_mouseReleaseEvent
                self.text_edit.keyReleaseEvent = self.on_keyReleaseEvent
                #
                self.chap_btn.currentIndexChanged.connect(self.on_chap_changed)
            else:
                MyDialog("Info", "Missed files in the epub.", self)
                self.on_close()
    
    def on_load_placeholders(self):
        try:
            _tmp = None
            with open(os.path.join(curr_dir,"placeholders", "placeholders.txt"), "r") as _f:
                _tmp = _f.readlines()
            i = 0
            for el in _tmp[::3]:
                self._placeholders.append([_tmp[i+0].strip("\n"), _tmp[i+1].strip("\n"), _tmp[i+2].strip("\n")])
                i+=3
        except Exception as E:
            MyDialog("Error", str(E), self)
    
    def find_placeholder(self):
        _page_name = None
        for el in self._placeholders:
            if el[0] == self._ffile:
                x,y = el[2].split("x")
                self.placeholder_position = (int(x),int(y))
                _page_name = el[1]
                break
        #
        if _page_name:
            for i in range(self.chap_btn.count()):
                if self.chap_btn.itemText(i) == _page_name:
                    return i
        else:
            return None
    
    def _parse_epub_css(self, _file):
        # parser = MyHTMLParser()
        # parser.feed(_file)
        #
        for el in manifest_list:
            if ('media-type', 'text/css') in el:
                for ell in el:
                    if ell[0] == "href":
                        if ell[1] not in self._css:
                            _css = ell[1]
                            if _css[0:2] == "./":
                                _css = _css[2:]
                            self._css.append(_css)
                        break
            # fonts
            if USE_EMBEDDED_FONT:
                for ell in el:
                    if ell[0] == "href":
                        if "fonts/" in ell[1]:
                            self.list_fonts.append(ell[1])
        #
        # parser.close()
    
    def parse_custom_css(self):
        custom_css_file = os.path.join(curr_dir,"custom_css","custom_style.css")
        if os.path.exists(custom_css_file) and os.access(custom_css_file, os.R_OK):
            with open(custom_css_file, "r") as _f:
                self.custom_css = _f.read()
        #
        # _fonts = os.listdir(os.path.join(curr_dir,"custom_css","fonts"))
        # try:
            # for el in _fonts:
                # _font = os.path.join(os.path.join(curr_dir,"custom_css","fonts"),el)
                # # self.text_edit.document().addResource(QTextDocument.ResourceType.UserResource, QUrl(_font), QVariant(_font))
                # self.text_edit.document().addResource(QTextDocument.ResourceType.UnknownResource, QUrl(_font), QVariant(_font))
        # except Exception as E:
            # MyDialog("Error", str(E), self)
    
    def wheelEvent(self, event):
        # to top
        if event.angleDelta().y() > 0 and self.text_edit.verticalScrollBar().sliderPosition() == 0:
            curr_idx = self.chap_btn.currentIndex()
            if curr_idx == 0:
                return
            self.chap_btn.setCurrentIndex(curr_idx-1)
            self.text_edit.verticalScrollBar().setSliderPosition(self.text_edit.verticalScrollBar().maximum())
        # to bottom
        elif event.angleDelta().y() < 0 and (self.text_edit.verticalScrollBar().sliderPosition() > 0 or self.text_edit.verticalScrollBar().maximum() == 0):
            curr_idx = self.chap_btn.currentIndex()
            if curr_idx == self.chap_btn.count()-1:
                return
            self.chap_btn.setCurrentIndex(curr_idx+1)
    
    def on_mouseReleaseEvent(self, event):
        if event.type() == QEvent.Type.MouseButtonRelease:
            if event.button() == Qt.MouseButton.LeftButton:
                _pos = event.position()
                _point = QPoint(int(_pos.x()),int(_pos.y()))
                # external link not supported
                #
                _link_text_tmp = self.text_edit.anchorAt(_point).split("#")
                if len(_link_text_tmp) > 1:
                    _link_text = "#".join(_link_text_tmp[:-1])
                else:
                    _link_text = _link_text_tmp[0]
                #
                _link_text_name = os.path.basename(_link_text)
                for el in self.input_zip.filelist:
                    if os.path.basename(el.filename) == _link_text_name:
                        for ell in _list_pages:
                            if os.path.basename(ell) == os.path.basename(el.filename):
                                _link = ell
                                _iii = self.chap_btn.count()
                                for i in range(_iii):
                                    item_text = self.chap_btn.itemText(i)
                                    if os.path.basename(item_text) == os.path.basename(ell):
                                        self.on_link_pressed(i)
                                        return
        return super().mousePressEvent(event)
    
    def on_keyReleaseEvent(self, event):
        if type(event) == QKeyEvent and event.key() == Qt.Key.Key_PageUp:
            pos_u = self.text_edit.verticalScrollBar().sliderPosition()
            pos_minimum = self.text_edit.verticalScrollBar().minimum()
            if self.change_page == pos_minimum:
                self.on_change_page(-1)
            else:
                self.change_page = pos_u
        elif type(event) == QKeyEvent and event.key() == Qt.Key.Key_PageDown:
            pos_d = self.text_edit.verticalScrollBar().sliderPosition()
            pos_maximum = self.text_edit.verticalScrollBar().maximum()
            if self.change_page == pos_maximum:
                self.on_change_page(1)
            else:
                self.change_page = pos_d
        elif type(event) == QKeyEvent and event.key() == Qt.Key.Key_Up:
            self.change_page = self.text_edit.verticalScrollBar().sliderPosition()
        elif type(event) == QKeyEvent and event.key() == Qt.Key.Key_Down:
            self.change_page = self.text_edit.verticalScrollBar().sliderPosition()
        elif type(event) == QKeyEvent and event.key() == Qt.Key.Key_Left:
            self.on_change_page(-1)
        elif type(event) == QKeyEvent and event.key() == Qt.Key.Key_Right:
            self.on_change_page(1)
        return super().keyReleaseEvent(event)
    
    # set the page from link
    def on_link_pressed(self, _i):
        self.chap_btn.setCurrentIndex(_i)
    
    def on_zoom_action(self, _n):
        if _n == 1:
            self.text_edit.zoomIn()
        elif _n == -1:
            self.text_edit.zoomOut()
            
    def on_conf(self):
        confwin = confWin(self)
        
    def on_print(self):
        if self.input_zip:
            dlg = QtPrintSupport.QPrintDialog()
            if dlg.exec():
                _printer = dlg.printer()
                self.text_edit.print(_printer)
    
    # set the placeholder
    def on_placeholder(self):
        if self.input_zip:
            try:
                _file_name = self._ffile
                _current_page = self.chap_btn.currentText()
                _cursor = self.text_edit.textCursor()
                _position = "{}x{}".format(_cursor.selectionStart(),_cursor.selectionEnd())
                _found = None
                ## searching for a previous placeholder
                if self._placeholders:
                    for el in self._placeholders:
                        if el[0] == _file_name:
                            _found = el
                            break
                _sel = self.text_edit.textCursor().selection().toPlainText()
                if _sel:
                    # a previous placeholder has been found
                    if _found:
                        ret = MyDialog("Question", "Do you want to remove the previous bookmark?", self)
                        if ret.result() == QMessageBox.StandardButton.Ok:
                            self._placeholders.remove(_found)
                    #
                    self._placeholders.append([_file_name,_current_page,_position])
                    # update the file
                    _f = open(os.path.join(curr_dir,"placeholders", "placeholders.txt"), "w")
                    for el in self._placeholders:
                        _f.write("{}\n{}\n{}\n".format(el[0],el[1],el[2]))
                    _f.close()
                    if _found:
                        MyDialog("Info", "Bookmark changed.",self)
                    else:
                        MyDialog("Info", "Bookmark added.",self)
                else:
                    if _found:
                        ret = MyDialog("Question", "Do you want to remove the bookmark?", self)
                        if ret.result() == QMessageBox.StandardButton.Ok:
                            self._placeholders.remove(_found)
                            # update the file
                            _f = open(os.path.join(curr_dir,"placeholders", "placeholders.txt"), "w")
                            for el in self._placeholders:
                                _f.write("{}\n{}\n{}\n".format(el[0],el[1],el[2]))
                            _f.close()
                    else:
                        MyDialog("Info", "Select something first.", self)
            except Exception as E:
                MyDialog("Error", str(E), self)
    
    def on_info(self):
        if self.input_zip:
            MyDialog("Epub infos", self._info_data, self)
    
    def on_cation(self, _action):
        if self.input_zip:
            try:
                _sel = self.text_edit.textCursor().selection().toPlainText()
                if _sel:
                    Popen([os.path.join(curr_dir, "custom_actions",_action), _sel, " &"])
            except Exception as E:
                MyDialog("Error", str(E), self)
        
    def pop_chap_btn(self):
        self.chap_btn.clear()
        self.chap_btn.addItems(_list_pages)
    
    def on_change_page(self, _n):
        curr_idx = self.chap_btn.currentIndex()
        if curr_idx + _n == -1 or curr_idx + _n == self.chap_btn.count():
            return
        self.chap_btn.setCurrentIndex(curr_idx+_n)
        self.page_change = 0
        
    def on_chap_changed(self, _idx):
        self._load_page(_idx)
    
    # load and display the page in the document
    def _load_page(self, _n):
        try:
            _page_name = _list_pages[_n]
            _page = None
            try:
                _page = self.input_zip.read(_page_name).decode()
            except Exception as E:
                for el in self.input_zip.filelist:
                    _llll = len(_page_name)
                    if el.filename[-_llll:] == _page_name:
                        _page = self.input_zip.read(el.filename).decode()
                        break
            #
            # remove the entity block
            _tmp = self.replace_text(_page)
            # replace the image link with their full path
            _ret = self.replace_text_images(_tmp)
            if _ret != None:
                _tmp = _ret
            # replace the css path with its full path
            _css_full_path = None
            if USE_STYLESHEET == 1:
                _ret = self.replace_text_css(_tmp)
                if _ret != None:
                    _tmp = _ret[0]
                    _css = _ret[1]
                    if _css:
                        _zip_files = self.input_zip.filelist
                        for el in _zip_files:
                            _l = len(_css)
                            if el.filename[-_l:] == _css:
                                _css_full_path = el
                                break
            #
            self.text_edit.setHtml(_tmp)
            #
            if USE_STYLESHEET == 1 and _css_full_path != None:
                _css_text = self.input_zip.read(_css_full_path.filename).decode()
                self.text_edit.document().setDefaultStyleSheet(_css_text)
            elif USE_STYLESHEET == 2:
                self.text_edit.document().setDefaultStyleSheet(self.custom_css)
            #
            self.text_edit.verticalScrollBar().setSliderPosition(0)
            if TEXTALIGNMENT == 1:
                if _n == 0:
                    self.text_edit.document().setDefaultTextOption(QTextOption(Qt.AlignmentFlag.AlignCenter))
                else:
                    self.text_edit.document().setDefaultTextOption(QTextOption(Qt.AlignmentFlag.AlignJustify))
            # set the placeholder
            if self.isStarted == False:
                if self.placeholder_position != ():
                    _start = self.placeholder_position[0]
                    _end = self.placeholder_position[1]
                    _cursor = self.text_edit.textCursor()
                    _cursor.setPosition(_start)
                    _cursor.setPosition(_end, QTextCursor.MoveMode.KeepAnchor)
                    self.text_edit.setTextCursor(_cursor)
        except Exception as E:
            MyDialog("Error", str(E), self)
            
    # create a list of all images with full path
    def load_image_full_path(self):
        _zip_files = self.input_zip.filelist
        for el in _list_images:
            # img_name = os.path.basename(el)
            img_name = unquote(_parse.urlparse(os.path.basename(el)).path)
            _l = len(img_name)
            for ell in _zip_files:
                if ell.filename[-_l:] == img_name:
                    self.list_image_full_path.append(ell.filename)
                    break
    
    # replace the original image paths with their full path 
    def replace_text_images(self, _text):
        new_text = _text
        for ell in self.list_image_full_path:
            _img_name = os.path.basename(ell)
            if _img_name in new_text:
                _pos = new_text.find(_img_name)
                _pos_end = new_text.find('"', _pos)
                _pos_start = None
                i = 1
                while 1:
                    ret = new_text.find('"', _pos-i)
                    if _pos-i == 0:
                        break
                    elif ret == -1:
                        i+=1
                    elif ret > _pos:
                        i+=1
                        continue
                    else:
                        _pos_start = _pos-i
                        break
                #
                if os.path.basename(ell) == unquote(_parse.urlparse(os.path.basename(_img_name)).path):
                    if new_text[_pos_start-1] == "=":
                        new_text = new_text.replace(new_text[_pos_start:_pos_end+1],'"'+ell+'"')
        #
        new_text = new_text.replace("<image", "<img")
        new_text = new_text.replace("xlink:href=", "src=")
        new_text = new_text.replace("href=", "src=")
        #
        return new_text
    
    # old
    # replace the original image paths with their full path 
    def replace_text_images2(self, _text):
        for _img in _list_images:
            _img_name = os.path.basename(_img)
            if _img_name in _text:
                _image = _img_name
                _pos = _text.find(_image)
                _pos_end = _text.find('"', _pos)
                _pos_start = None
                i = 1
                while 1:
                    ret = _text.find('"', _pos-i)
                    if _pos-i == 0:
                        break
                    elif ret == -1:
                        i+=1
                    elif ret > _pos:
                        i+=1
                        continue
                    else:
                        _pos_start = _pos-i
                        break
                #
                for ell in self.list_image_full_path:
                    # if os.path.basename(ell) == _img_name:
                    if os.path.basename(ell) == unquote(_parse.urlparse(os.path.basename(_img_name)).path):
                        if _text[_pos_start-1] == "=":
                            new_text = _text.replace(_text[_pos_start:_pos_end+1],'"'+ell+'"')
                            return new_text
                #
                break
        return None
    
    # replace the original css path with its full path
    def replace_text_css(self, _text):
        page_css = None
        new_text = _text
        if self._css:
            for _css in self._css:
                page_css = _css
                _css_name = os.path.basename(_css)
                if _css_name in _text:
                    _pos = _text.find(_css_name)
                    _pos_end = _text.find('"', _pos)
                    _pos_start = None
                    i = 1
                    while 1:
                        ret = _text.find('"', _pos-i)
                        if _pos-i == 0:
                            break
                        elif ret == -1:
                            i+=1
                        elif ret > _pos:
                            i+=1
                            continue
                        else:
                            _pos_start = _pos-i
                            break
                    #
                    if _text[_pos_start-1] == "=":
                        for el in self._css_css:
                            if os.path.basename(_css) == os.path.basename(el):
                                new_text = new_text.replace(_text[_pos_start:_pos_end+1],'"'+el+'"')
                                break
                    break
            return [new_text, page_css]
        return None
    
    # load and display the page
    def _load_data(self):
        # images
        try:
            for _img_name in self.list_image_full_path:
                _img = self.input_zip.read(_img_name)
                qba = QByteArray(_img)
                _img1 = QImage()
                _img1.loadFromData(qba)
                if _img1.width() > self.text_edit.document().size().width()-self.text_edit.document().documentMargin()*2:
                    _img1 = _img1.scaledToWidth(int(self.text_edit.document().size().width()-self.text_edit.document().documentMargin()*2), Qt.TransformationMode.SmoothTransformation)
                self.text_edit.document().addResource(QTextDocument.ResourceType.ImageResource, QUrl(_img_name), _img1)
        except Exception as E:
            MyDialog("Error", str(E), self)
        #
        # fonts
        if USE_EMBEDDED_FONT:
            try:
                for el in self.list_fonts:
                    # self.text_edit.document().addResource(QTextDocument.ResourceType.UserResource, QUrl(el), QVariant(el))
                    self.text_edit.document().addResource(QTextDocument.ResourceType.UnknownResource, QUrl(el), QVariant(el))
            except Exception as E:
                MyDialog("Error", str(E), self)
        #### useless
        # # css
        # if USE_STYLESHEET:
            # try:
                # if self._css:
                    # for _css in self._css:
                        # _css_css = None
                        # _ll = len(_css)
                        # for el in self.input_zip.filelist:
                            # if el.filename[-_ll:] == _css:
                                # _css_css = el.filename
                                # file_css = self.input_zip.read(_css_css).decode()
                                # break
                        # #
                        # if _css_css:
                            # _l = len(_css_css)
                            # _zip_files = self.input_zip.filelist
                            # for ell in _zip_files:
                                # if ell.filename[-_l:] == _css_css:
                                    # self._css_css.append(ell.filename)
                                    # self.text_edit.document().addResource(QTextDocument.ResourceType.StyleSheetResource, QUrl(ell.filename), QVariant(ell.filename))
                                    # break
            # except Exception as E:
                # MyDialog("Error", str(E), self)
        
    # load the epub in memory
    def load_zip(self, _epub):
        self.input_zip = zipfile.ZipFile(_epub, mode="r")
        zip_list = self.input_zip.filelist
        for el in zip_list:
            if el.is_dir():
                continue
            elif os.path.dirname(el.filename) != "":
                continue
            elif el.filename.endswith(".opf"):
                self._opf_file = self.input_zip.read(el.filename).decode()
                break
        if self._opf_file == None:
            for el in zip_list:
                if el.is_dir():
                    continue
                elif el.filename.endswith(".opf"):
                    self._opf_file = self.input_zip.read(el.filename).decode()
                    break
        
    def replace_text(self, aaa):
        _start = aaa.find("<!DOCTYPE")
        _end = aaa.find("]>", _start)
        # the block to identify and remove
        bbb = aaa[_start: _end+2]
        _list = []
        ret = bbb.find("<!ENTITY")
        if ret != -1:
            _list.append(ret)
            #
            while ret != -1:
                ret = bbb.find("<!ENTITY", _list[-1]+8)
                if ret != -1:
                    _list.append(ret)
        #
        if _list == []:
            return aaa
        #
        entity_list = []
        for i,el in enumerate(_list[:]):
            if i == len(_list)-1:
                break
            _e = _list[i+1]+_start
            entity_list.append(aaa[ el+_start : _e ].rstrip("\n"))
        #
        entity_list.append(bbb[_list[-1]:].rstrip("\n"))
        if entity_list == []:
            return aaa
        _code_list = []
        for el in entity_list:
            _l = el.split(" ")
            _c = _l[1]
            _d = _l[2].split(";")[0][1:]
            _code_list.append([_c,_d])
        #
        ccc = aaa.replace(bbb, "")
        for el in _code_list:
            ccc = ccc.replace("&{};".format(el[0]), unescape(el[1]))
        #
        return ccc
        
    def closeEvent(self, event):
        self.on_close()
        
    def on_close(self):
        if self.input_zip:
            self.input_zip.close()
        #
        new_w = self.size().width()
        new_h = self.size().height()
        if new_w != int(WINW) or new_h != int(WINH):
            try:
                ifile = open("epubreadersize.cfg", "w")
                ifile.write("{};{}".format(new_w, new_h))
                ifile.close()
            except Exception as E:
                MyDialog("Error", "ERROR writing config file:\n{}".format(str(E)), self)
        #
        QApplication.quit()
        sys.exit()

# configurator
class confWin(QDialog):
    def __init__(self, parent=None):
        super(confWin, self).__init__(None)
        self.setWindowTitle("Configurator")
        self.setObjectName("confwin")
        self.setGeometry(0,0,100,100)
        self.window = parent
        #
        self.vbox = QVBoxLayout()
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        # 
        self.vbox.setContentsMargins(2,2,2,2)
        self.setLayout(self.vbox)
        #
        self.tab_w = QTabWidget()
        self.tab_w.setContentsMargins(0,0,0,0)
        self.tab_w.setMovable(False)
        self.tab_w.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        # self.tab_w.setWidgetResizable(True)
        self.vbox.addWidget(self.tab_w, stretch = 10)
        ######
        ### panel tab
        p_widget = QWidget()
        self.tab_w.insertTab(0, p_widget, "Settings")
        p_box = QVBoxLayout()
        p_box.setContentsMargins(0,0,0,0)
        p_widget.setLayout(p_box)
        #
        pform = QFormLayout()
        p_box.addLayout(pform)
        #
        self._background = QLineEdit()
        self._background.setText(BACKGROUND)
        # self._background.setToolTip("In the form: #rrggbb\nThe text colour has to be also setted.")
        self._background.setToolTip("In the form: #rrggbb")
        pform.addRow("Background colour ", self._background)
        #
        self._textcolor = QLineEdit()
        self._textcolor.setText(TEXTCOLOR)
        # self._textcolor.setToolTip("In the form: #rrggbb\nThe background colour has to be also setted.")
        self._textcolor.setToolTip("In the form: #rrggbb")
        pform.addRow("Text colour ", self._textcolor)
        #
        self._font_family = QLineEdit()
        self._font_family.setText(FONTFAMILY)
        self._font_family.setToolTip("Font family name, e.g. Serif or Sans\nLeave empty for the default font")
        pform.addRow("Font family ", self._font_family)
        #
        self._margins = QSpinBox()
        self._margins.setMaximum(1000)
        self._margins.setValue(MARGINS)
        pform.addRow("Page margins ", self._margins)
        #
        self._page_zoom = QSpinBox()
        self._page_zoom.setMaximum(100)
        self._page_zoom.setValue(PAGEZOOM)
        pform.addRow("Page zoom ", self._page_zoom)
        #
        self._stylesheet = QComboBox()
        self._stylesheet.addItems(["No", "Yes", "Custom"])
        self._stylesheet.setCurrentIndex(USE_STYLESHEET)
        pform.addRow("Use the book stylesheets ", self._stylesheet)
        #
        self._fonts = QComboBox()
        self._fonts.addItems(["No", "Yes"])
        self._fonts.setCurrentIndex(USE_EMBEDDED_FONT)
        pform.addRow("Use the book fonts ", self._fonts)
        #
        self._page_alignment = QComboBox()
        self._page_alignment.addItems(["Default", "Justify"])
        self._page_alignment.setCurrentIndex(TEXTALIGNMENT)
        pform.addRow("Text alignment ", self._page_alignment)
        #####
        ##### buttons
        box_btn = QHBoxLayout()
        self.vbox.addLayout(box_btn)
        ok_btn = QPushButton(" OK ")
        box_btn.addWidget(ok_btn)
        ok_btn.clicked.connect(self.on_ok)
        #
        close_btn = QPushButton("Close")
        box_btn.addWidget(close_btn)
        close_btn.clicked.connect(self.close)
        #
        self.exec()
    
    def on_ok(self):
        global BACKGROUND
        global TEXTCOLOR
        global FONTFAMILY
        global MARGINS
        global PAGEZOOM
        global TEXTALIGNMENT
        global USE_STYLESHEET
        global USE_EMBEDDED_FONT
        global _settings_conf
        try:
            BACKGROUND = self._background.text()
            _settings_conf["background"] = BACKGROUND
            TEXTCOLOR = self._textcolor.text()
            _settings_conf["textcolor"] = TEXTCOLOR
            FONTFAMILY = self._font_family.text()
            _settings_conf["fontfamily"] = FONTFAMILY
            MARGINS = self._margins.value()
            _settings_conf["margins"] = MARGINS
            _starting_zoom = PAGEZOOM
            PAGEZOOM = self._page_zoom.value()
            _settings_conf["pagezoom"] = PAGEZOOM
            USE_STYLESHEET = self._stylesheet.currentIndex()
            _settings_conf["use-css"] = USE_STYLESHEET
            USE_EMBEDDED_FONT = self._fonts.currentIndex()
            _settings_conf["use-font"] = USE_EMBEDDED_FONT
            TEXTALIGNMENT = self._page_alignment.currentIndex()
            _settings_conf["text-alignment"] = TEXTALIGNMENT
            #
            # write the configuration back
            _ff = open(_config_file,"w")
            json.dump(_settings_conf, _ff, indent = 4)
            _ff.close()
            # set the settings
            if BACKGROUND and TEXTCOLOR:
                self.window.text_edit.setStyleSheet("background-color: {}; color: {};".format(BACKGROUND,TEXTCOLOR))
            if FONTFAMILY:
                _font = self.window.text_edit.font()
                _font.setFamily(FONTFAMILY)
                self.window.text_edit.setFont(_font)
            if MARGINS:
                self.window.text_edit.document().setDocumentMargin(MARGINS)
            if (PAGEZOOM-_starting_zoom) > 0:
                for i in range((PAGEZOOM-_starting_zoom)):
                    self.window.text_edit.zoomIn()
            elif (PAGEZOOM-_starting_zoom) < 0:
                for i in range(abs((PAGEZOOM-_starting_zoom))):
                    self.window.text_edit.zoomOut()
        except Exception as E:
            MyDialog("Error", str(E), None)
        #
        self.close()

# type - message - parent
class MyDialog(QMessageBox):
    def __init__(self, *args):
        super(MyDialog, self).__init__(args[-1])
        if args[0] == "Error":
            self.setIcon(QMessageBox.Icon.Critical)
            self.setStandardButtons(QMessageBox.StandardButton.Ok)
        elif args[0] == "Question":
            self.setIcon(QMessageBox.Icon.Question)
            self.setStandardButtons(QMessageBox.StandardButton.Ok|QMessageBox.StandardButton.Cancel)
        elif args[0] == "Info":
            self.setIcon(QMessageBox.Icon.Information)
            self.setStandardButtons(QMessageBox.StandardButton.Ok)
        else:
            self.setStandardButtons(QMessageBox.StandardButton.Ok)
        #
        self.setWindowIcon(QIcon(os.path.join(curr_dir,"icons/dialog.png")))
        self.setWindowTitle(args[0])
        self.resize(50,50)
        self.setText(args[1])
        retval = self.exec()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    myGUI = dictMainWindow()
    sys.exit(app.exec())
