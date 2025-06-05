#!/usr/bin/env python3

# V. 0.1

import sys, os, json
from PyQt6.QtWidgets import (QMainWindow,QApplication,QWidget,QDialog,QComboBox,QTextEdit,QVBoxLayout,QHBoxLayout,QSizePolicy,QPushButton,QLabel,QLineEdit,QMenu)
from PyQt6.QtGui import (QIcon,QColor,QTextOption,QTextDocument,QImage,QPixmap,QAction)
from PyQt6.QtCore import (Qt,QUrl,QByteArray,QEvent,QPoint)
import zipfile
from html.parser import HTMLParser, unescape
from PyQt6 import QtPrintSupport
from cfgCfg import *

# home dir
# MY_HOME = os.path.expanduser('~')
# this program working directory
curr_dir = os.getcwd()
os.chdir(curr_dir)

WINW = 1400
WINH = 950
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
_css = None
# the ebook images
_list_images = []
# the real pages to read - filename with path
_list_pages = []


def _parse_epub_data(_file):
    parser = MyHTMLParser()
    parser.feed(_file)
    #
    global _css
    for el in manifest_list:
        if ('media-type', 'text/css') in el:
            for ell in el:
                if ell[0] == "href":
                    _css = ell[1]
                    break
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
        #
        self.prev_btn = QPushButton()
        self.prev_btn.setIcon(QIcon().fromTheme("previous", QIcon(os.path.join(curr_dir, "icons", "previous.png"))))
        self.prev_btn.setToolTip("Previous chapter")
        self.button_box.addWidget(self.prev_btn)
        self.prev_btn.clicked.connect(lambda:self.on_change_page(-1))
        #
        self.next_btn = QPushButton()
        self.next_btn.setIcon(QIcon().fromTheme("next", QIcon(os.path.join(curr_dir, "icons", "next.png"))))
        self.next_btn.setToolTip("Next chapter")
        self.button_box.addWidget(self.next_btn)
        self.next_btn.clicked.connect(lambda:self.on_change_page(1))
        #
        self.zoom_in_btn = QPushButton()
        self.zoom_in_btn.setIcon(QIcon().fromTheme("zoom-in", QIcon(os.path.join(curr_dir, "icons", "zoom-in.png"))))
        self.zoom_in_btn.setToolTip("Increase text size")
        self.button_box.addWidget(self.zoom_in_btn)
        self.zoom_in_btn.clicked.connect(lambda:self.on_zoom_action(1))
        #
        self.zoom_out_btn = QPushButton()
        self.zoom_out_btn.setIcon(QIcon().fromTheme("zoom-out", QIcon(os.path.join(curr_dir, "icons", "zoom-out.png"))))
        self.zoom_out_btn.setToolTip("Decrease text size")
        self.button_box.addWidget(self.zoom_out_btn)
        self.zoom_out_btn.clicked.connect(lambda:self.on_zoom_action(-1))
        #
        self.print_btn = QPushButton()
        self.print_btn.setIcon(QIcon().fromTheme("stock_print", QIcon(os.path.join(curr_dir, "icons", "document-print.png"))))
        self.print_btn.setToolTip("Print")
        self.button_box.addWidget(self.print_btn)
        self.print_btn.clicked.connect(self.on_print)
        #
        self.info_btn = QPushButton()
        self.info_btn.setIcon(QIcon(os.path.join(curr_dir,"icons/information.png")))
        # self.info_btn.setToolTip("Epub info")
        self.button_box.addWidget(self.info_btn)
        self.info_btn.setFlat(True)
        # self.info_btn.clicked.connect(self.on_info)
        #
        self.exit_btn = QPushButton()
        self.exit_btn.setIcon(QIcon().fromTheme("application-exit", QIcon(os.path.join(curr_dir, "icons", "exit.png"))))
        self.exit_btn.setToolTip("Close")
        self.button_box.addWidget(self.exit_btn)
        self.exit_btn.clicked.connect(self.close)
        #
        self.text_edit = QTextEdit()
        self.main_box.addWidget(self.text_edit)
        self.text_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.text_edit.setReadOnly(True)
        self.text_edit.document().setDefaultTextOption(QTextOption(Qt.AlignmentFlag.AlignJustify))
        self.text_edit.document().setDocumentMargin(MARGINS)
        # self.text_edit.document().setIndentWidth(24)
        self.text_edit.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse|Qt.TextInteractionFlag.LinksAccessibleByMouse)
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
        #
        self.actual_search = ""
        #
        self.show()
        #
        self.title_list = []
        self.chapter_list = []
        #
        self._opf_file = None
        _ffile = None
        if len(sys.argv) > 1:
            _ffile = sys.argv[1]
        if _ffile and os.path.exists(os.path.realpath(_ffile)) and os.access(_ffile, os.R_OK):
            # the epub in memory
            self.input_zip = None
            # load the epub into memory
            self.load_zip(_ffile)
            #
            self.list_image_full_path = []
            #
            if self._opf_file:
                _parse_epub_data(self._opf_file)
                #
                self.load_image_full_path()
                #
                _info_data = "Title: {}\nCreator: {}\nDate: {}\nLanguage: {}\nSubject: {}\nCoverage: {}\nRights: {}\nPublisher: {}".format(_title,_creator,_date,_language,_subject,_coverage,_rights,_publisher)
                self.info_btn.setToolTip(_info_data)
                #
                self.setWindowTitle(_title)
                #
                self._load_data()
                #
                self._load_page(0)
                #
                self.chap_btn.currentIndexChanged.connect(self.on_chap_changed)
                #
                self.text_edit.mousePressEvent = self.on_mousePressEvent
            #
            self.pop_chap_btn()
    
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
    
    def on_mousePressEvent(self, event):
        if event.type() == QEvent.Type.MouseButtonPress:
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
    
    # set the page from link
    def on_link_pressed(self, _i):
        self.chap_btn.setCurrentIndex(_i)
    
    def on_zoom_action(self, _n):
        if _n == 1:
            self.text_edit.zoomIn()
        elif _n == -1:
            self.text_edit.zoomOut()
            
    def on_print(self):
        dlg = QtPrintSupport.QPrintDialog()
        if dlg.exec():
            _printer = dlg.printer()
            self.text_edit.print(_printer)
    
    def on_info(self):
        pass
    
    def pop_chap_btn(self):
        self.chap_btn.clear()
        self.chap_btn.addItems(_list_pages)
    
    def on_change_page(self, _n):
        curr_idx = self.chap_btn.currentIndex()
        if curr_idx + _n == -1 or curr_idx + _n == self.chap_btn.count():
            return
        self.chap_btn.setCurrentIndex(curr_idx+_n)
        
    def on_chap_changed(self, _idx):
        self._load_page(_idx)
    
    # load and display the page in the document
    def _load_page(self, _n):
        try:
            _page_name = _list_pages[_n]
            _page = None
            try:
                _page = self.input_zip.read(_page_name).decode()
            except:
                for el in self.input_zip.filelist:
                    _llll = len(_page_name)
                    if el.filename[-_llll:] == _page_name:
                        _page = self.input_zip.read(el.filename).decode()
                        break
            # remove the entity block
            _tmp = self.replace_text(_page)
            # replace the image link with their full path
            _ret = self.replace_text_images(_tmp)
            if _ret != None:
                _tmp = _ret
            self.text_edit.setHtml(_tmp)
            self.text_edit.verticalScrollBar().setSliderPosition(0)
            if _n == 0:
                self.text_edit.document().setDefaultTextOption(QTextOption(Qt.AlignmentFlag.AlignCenter))
            else:
                self.text_edit.document().setDefaultTextOption(QTextOption(Qt.AlignmentFlag.AlignJustify))
        except Exception as E:
            print("LOAD PAGE: ", str(E))
            
    # create a list of all images with full path
    def load_image_full_path(self):
        _zip_files = self.input_zip.filelist
        for el in _list_images:
            img_name = os.path.basename(el)
            _l = len(img_name)
            for ell in _zip_files:
                if ell.filename[-_l:] == img_name:
                    self.list_image_full_path.append(ell.filename)
                    break
    
    # replace the original image paths with their full path 
    def replace_text_images(self, _text):
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
                    if os.path.basename(ell) == _img_name:
                        new_text = _text.replace(_text[_pos_start:_pos_end+1],ell)
                        return new_text
                #
                break
        return None
    
    # load and display the page
    def _load_data(self):
        try:
            for _img_name in self.list_image_full_path:
                _img = self.input_zip.read(_img_name)
                qba = QByteArray(_img)
                _img1 = QImage()
                _img1.loadFromData(qba)
                if _img1.width() > self.text_edit.document().size().width():
                    _img1 = _img1.scaledToWidth(int(self.text_edit.document().size().width()-self.text_edit.document().documentMargin()*2), Qt.TransformationMode.SmoothTransformation)
                self.text_edit.document().addResource(QTextDocument.ResourceType.ImageResource, QUrl(_img_name), _img1)
        except Exception as E:
            print("LOAD DATA: ", str(E))
        #
        # # css - USELESS at the moment
        # try:
            # _ll = len(_css)
            # for el in self.input_zip.filelist:
                # if el.filename[-_ll:] == _css:
                    # _css_css = el.filename
                    # file_css = self.input_zip.read(_css_css).decode()
                    # break
        # except Exception as E:
            # print("LOAD CSS: ", str(E))
    
    # OLD
    def _load_data1(self):
        try:
            _base_path = ""
            # images
            for _img_name in _list_images:
                _img_dirname = os.path.dirname(_img_name)
                if _img_dirname:
                    if _img_dirname == "images":
                        _img_name2 = _img_name
                    elif "images" in _img_dirname:
                        _lll = _img_name.find("images/")
                        if _lll != -1:
                            _img_name2 = _img_name[_lll:]
                    _img = self.input_zip.read(os.path.join(_base_path,_img_name))
                    qba = QByteArray(_img)
                    _img1 = QImage()
                    _img1.loadFromData(qba)
                    if _img1.width() > self.text_edit.document().size().width():
                        _img1 = _img1.scaledToWidth(int(self.text_edit.document().size().width()-self.text_edit.document().documentMargin()*2), Qt.TransformationMode.SmoothTransformation)
                    self.text_edit.document().addResource(QTextDocument.ResourceType.ImageResource, QUrl(_img_name2), _img1)
                #
                else:
                    _el = _list_pages[0]
                    _lll = len(_el)
                    for el in self.input_zip.filelist:
                        if el.filename[-_lll:] == _el:
                            _ttt = len(el.filename)
                            _dd = el.filename[0:_ttt-_lll]
                            _img_name2 = _dd+_img_name
                            break
                    _img = self.input_zip.read(_img_name2)
                    qba = QByteArray(_img)
                    _img1 = QImage()
                    _img1.loadFromData(qba)
                    if _img1.width() > self.text_edit.document().size().width():
                        _img1 = _img1.scaledToWidth(int(self.text_edit.document().size().width()-self.text_edit.document().documentMargin()*2), Qt.TransformationMode.SmoothTransformation)
                    self.text_edit.document().addResource(QTextDocument.ResourceType.ImageResource, QUrl(_img_name), _img1)
        except Exception as E:
            print("LOAD DATA: ", str(E))
            pass
        # css
        try:
            _ll = len(_css)
            for el in self.input_zip.filelist:
                if el.filename[-_ll:] == _css:
                    _css_css = el.filename
                    file_css = self.input_zip.read(_css_css).decode()
                    break
        except Exception as E:
            print("LOAD CSS: ", str(E))
        
    # load the epub in memory
    def load_zip(self, _epub):
        self.input_zip = zipfile.ZipFile(_epub, mode="r")
        zip_list = self.input_zip.filelist
        for el in zip_list:
            if el.is_dir():
                continue
            if el.filename.endswith(".opf"):
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
        new_w = self.size().width()
        new_h = self.size().height()
        if new_w != int(WINW) or new_h != int(WINH):
            try:
                ifile = open("epubreadersize.cfg", "w")
                ifile.write("{};{}".format(new_w, new_h))
                ifile.close()
            except Exception as E:
                print("ERROR writing config file: ", str(E))
        #
        QApplication.quit()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    myGUI = dictMainWindow()
    sys.exit(app.exec())
