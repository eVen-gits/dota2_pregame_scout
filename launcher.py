import os, sys, io, random

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5 import uic

import argparse

class MyWidget(QWidget):
    def __init__(self, core_ptr=None):
        QWidget.__init__(self)
        self.core = core_ptr


        self.ui_small = uic.loadUi('./ui/player_card_small.ui')
        self.ui_large = uic.loadUi('./ui/player_card_large.ui')

        self.layout = QStackedLayout()
        self.layout.addWidget(self.ui_small)
        self.layout.addWidget(self.ui_large)


        self.size = [
            self.ui_small.height(),
            self.ui_large.height()
        ]

        self.setMaximumHeight(min(self.size))

        self.small = True
        self.setLayout(self.layout)

        self.ui_small.mousePressEvent = self.toggle_view
        self.ui_large.mousePressEvent = self.toggle_view

        self.show()

    def toggle_view(self, *nargs, **kwargs):
        self.small = not self.small

        self.layout.setCurrentIndex(0 if self.small else 1)
        self.setMaximumHeight(
            self.size[0] if self.small else self.size[1]
        )

class ScoutMainWindow(QMainWindow):
    def __init__(self, core_ptr=None):
        QMainWindow.__init__(self)
        self.core = core_ptr

        #Window code
        self.ui = uic.loadUi('./ui/main_window.ui')
        self.setCentralWidget(self.ui)

        self.ui.btnParse.clicked.connect(self.add_dummy_players)

        self.ui.actionClear.triggered.connect(self.clear)


    def add_dummy_players(self, *nargs, **kwargs):
        for i in range(10):
            w = MyWidget()
            self.ui.scroll_container.layout().addWidget(w)

    def clear(self, *nargs, **kwargs):
        for i in reversed(range(self.ui.scroll_container.layout().count())):
            self.ui.scroll_container.layout().itemAt(i).widget().setParent(None)

if __name__ == '__main__':
    app = QApplication(sys.argv)

    #TODO:
    #core = Core()
    core = None

    window = ScoutMainWindow(core)
    window.show()

    app.exec_()
    sys.exit(app.exit())