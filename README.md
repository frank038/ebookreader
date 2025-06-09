# ebookreader
Simple epub reader - free to use and modify

Requirements:
- pyqt6

Usage: ./ebookreader.py file.epub

This program may work or may not work (it depends on the epub files).

Features:
- navigation by chapters
- navigation by mouse
- navigation by buttons
- zoom
- printing (of the current chapter)
- basic epub info (just put the mouse pointer over the info button)
- custom background colour, text colour, margins, initial zoom level (in the cfgCfg.py)
- clickable ebook links (not external links)
- the window size is stored
- custom scripts on selected text: a sample script is shipped: searching for a meaning of a word with Wordnet; the command line wn and yad are required
- bookmarks: one bookmark for each book: just select something and bookmark it; the bookmark can be changed (just repeat the action on another selection), and removed (do not select nothing).

This program can be considered complete about its features.

![My image](https://github.com/frank038/ebookreader/blob/main/screenshot01.jpg)
