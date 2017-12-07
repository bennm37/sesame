# Copyright 2017 University of Maryland.
#
# This file is part of Sesame. It is subject to the license terms in the file
# LICENSE.rst found in the top-level directory of this distribution.

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
 
import os
from ast import literal_eval as ev
import numpy as np 
import logging

from .plotbox import *
from .common import parseSettings, slotError
from ..analyzer import Analyzer
from ..plotter import plot


class Analysis(QWidget):
    def __init__(self, parent):
        super(Analysis, self).__init__(parent)

        self.table = parent

        self.tabLayout = QVBoxLayout()
        self.setLayout(self.tabLayout)

        self.hlayout = QHBoxLayout()
        self.tabLayout.addLayout(self.hlayout)


        #==============================================
        # Upload data and settings
        #==============================================
        prepare = QVBoxLayout()
        self.hlayout.addLayout(prepare)

        FileBox = QGroupBox("Import data")
        dataLayout = QVBoxLayout()

        # Select and remove buttons
        btnsLayout = QHBoxLayout()
        self.dataBtn = QPushButton("Select files...")
        self.dataBtn.clicked.connect(self.browse)
        self.dataRemove = QPushButton("Remove selected")
        self.dataRemove.clicked.connect(self.remove)
        btnsLayout.addWidget(self.dataBtn)
        btnsLayout.addWidget(self.dataRemove)
        dataLayout.addLayout(btnsLayout)

        # List itself
        self.dataList = QListWidget()
        self.dataList.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.dataList.setDragDropMode(QAbstractItemView.InternalMove)
        dataLayout.addWidget(self.dataList)
        FileBox.setLayout(dataLayout)
        prepare.addWidget(FileBox)

        twoDBox = QGroupBox("Surface plot")
        twoDLayout = QVBoxLayout()
        self.quantity = QComboBox()
        quantities = ["Choose one", "Electron quasi-Fermi level",\
        "Hole quasi-Fermi level", "Electrostatic potential",\
        "Electron density", "Hole density", "Bulk SRH recombination",\
        "Electron current", "Hole current"]
        self.quantity.addItems(quantities)
        twoDLayout.addWidget(self.quantity)
        self.plotBtnS = QPushButton("Plot")
        self.plotBtnS.clicked.connect(self.surfacePlot)
        twoDLayout.addWidget(self.plotBtnS)
        twoDBox.setLayout(twoDLayout)
        prepare.addWidget(twoDBox)

        oneDBox = QGroupBox("Linear plot")
        oneDLayout = QVBoxLayout()
        form = QFormLayout()
        self.Xdata = QLineEdit()
        form.addRow("X data", self.Xdata)
        self.quantity2 = QComboBox()
        quantities = ["Choose one", "Band diagram",\
        "Electron quasi-Fermi level", "Hole quasi-Fermi level",\
        "Electrostatic potential","Electron density",\
        "Hole density", "Bulk SRH recombination",\
        "Electron current along x", "Electron current along y",\
        "Hole current along x", "Hole current along y",\
        "Full steady state current"]
        self.quantity2.addItems(quantities)
        form.addRow("Y data", self.quantity2)
        oneDLayout.addLayout(form)
        self.plotBtn = QPushButton("Plot")
        self.plotBtn.clicked.connect(self.linearPlot)
        oneDLayout.addWidget(self.plotBtn)
        oneDBox.setLayout(oneDLayout)
        prepare.addWidget(oneDBox)
 

        #==============================================
        # Surface plot
        #==============================================
        self.surfaceLayout = QVBoxLayout()
        self.hlayout.addLayout(self.surfaceLayout)

        self.surfaceBox = QGroupBox("Surface plot")
        self.vlayout = QVBoxLayout()
        self.surfaceBox.setLayout(self.vlayout)
        self.surfaceLayout.addWidget(self.surfaceBox)

        self.surfaceFig = MplWindow()
        self.vlayout.addWidget(self.surfaceFig)

        #==============================================
        # Linear plot
        #==============================================
        self.linearLayout = QVBoxLayout()
        self.hlayout.addLayout(self.linearLayout)

        self.linearBox = QGroupBox("Linear plot")
        self.vlayout2 = QVBoxLayout()
        self.linearBox.setLayout(self.vlayout2)
        self.linearLayout.addWidget(self.linearBox)

        self.linearFig = MplWindow()
        self.vlayout2.addWidget(self.linearFig)

    def browse(self):
        dialog = QFileDialog()
        paths = dialog.getOpenFileNames(self, "Select files")[0]
        for i, path in enumerate(paths):
            path = os.path.basename(path)
            self.dataList.insertItem (i, path )

    def remove(self):
        # remove the selected files from the list
        for i in self.dataList.selectedItems():
            self.dataList.takeItem(self.dataList.row(i))

    @slotError("bool")
    def surfacePlot(self, checked):
        # get system
        settings = self.table.build.getSystemSettings()
        system = parseSettings(settings)

        # get data from file
        files = [x.text() for x in self.dataList.selectedItems()]
        if len(files) == 0:
            return
        elif len(files) > 1:
            msg = QMessageBox()
            msg.setWindowTitle("Processing error")
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Select a single data file for a surface plot.")
            msg.setEscapeButton(QMessageBox.Ok)
            msg.exec_()
            return
        else:
            fileName = files[0]
            data = np.load(fileName)

            # make an instance of the Analyzer
            az = Analyzer(system, data)

            # scalings
            vt = system.scaling.energy
            N  = system.scaling.density
            G  = system.scaling.generation

            # plot
            txt = self.quantity.currentText()
            self.surfaceFig.figure.clear()
            if txt == "Electron quasi-Fermi level":
                dataMap = vt * az.efn
                title = r'$\mathregular{E_{F_n}}$ [eV]'
            if txt == "Hole quasi-Fermi level":
                dataMap = vt * az.efp
                title = r'$\mathregular{E_{F_p}}$ [eV]'
            if txt == "Electrostatic potential":
                dataMap = vt * az.v
                title = r'$\mathregular{V}$ [eV]'
            if txt == "Electron density":
                dataMap = N * az.electron_density() * 1e-6
                title = r'n [$\mathregular{cm^{-3}}$]'
            if txt == "Hole density":
                dataMap = N * az.hole_density() * 1e-6
                title = r'p [$\mathregular{cm^{-3}}$]'
            if txt == "Bulk SRH recombination":
                dataMap = G * az.bulk_srh_rr() * 1e-6
                title = r'Bulk SRH [$\mathregular{cm^{-3}s^{-1}}$]'
            
            if txt != "Electron current" and txt != "Hole current":
                plot(system, dataMap, scale=1e-6, cmap='viridis',\
                     fig=self.surfaceFig.figure, title=title)
 
            if txt == "Electron current":
                az.current_map(True, 'viridis', 1e6, fig=self.surfaceFig.figure)

            if txt == "Hole current":
                az.current_map(False, 'viridis', 1e6, fig=self.surfaceFig.figure)

            self.surfaceFig.canvas.draw()

    @slotError("bool")
    def linearPlot(self, checked):
        # get data files names
        files = [x.text() for x in self.dataList.selectedItems()]
        if len(files) == 0:
            return

        # get system
        settings = self.table.build.getSystemSettings()
        system = parseSettings(settings)

        # scalings
        vt = system.scaling.energy
        N  = system.scaling.density
        G  = system.scaling.generation
        J  = system.scaling.current

        # clear the figure
        self.linearFig.figure.clear()

        # test what kind of plot we are making
        Xdata = ev(self.Xdata.text())
        txt = self.quantity2.currentText()

        # loop over the files and plot
        for fdx, fileName in enumerate(files):
            data = np.load(fileName)
            az = Analyzer(system, data)

            # get sites and coordinates of a line or else
            if isinstance(Xdata[0], tuple):
                if system.dimension == 1:
                    X = system.xpts
                    sites = np.arange(system.nx, dtype=int)
                if system.dimension == 2:
                    X, sites = az.line(system, Xdata[0], Xdata[1])
                    X = X * system.scaling.length
            else:
                X = Xdata



            # get the corresponding Y data
            if txt == "Electron quasi-Fermi level":
                Ydata = vt * az.efn[sites]
                YLabel = r'$\mathregular{E_{F_n}}$ [eV]'
            if txt == "Hole quasi-Fermi level":
                Ydata = vt * az.efp[sites]
                YLabel = r'$\mathregular{E_{F_p}}$ [eV]'
            if txt == "Electrostatic potential":
                Ydata = vt * az.v[sites]
                YLabel = 'V [eV]'
            if txt == "Electron density":
                Ydata = N * az.electron_density()[sites] * 1e-6
                YLabel = r'n [$\mathregular{cm^{-3}}$]'
            if txt == "Hole density":
                Ydata = N * az.hole_density()[sites] * 1e-6
                YLabel = r'p [$\mathregular{cm^{-3}}$]'
            if txt == "Bulk SRH recombination":
                Ydata = G * az.bulk_srh_rr()[sites] * 1e-6
                YLabel = r'Bulk SRH [$\mathregular{cm^{-3}s^{-1}}$]'
            if txt == "Electron current along x":
                Ydata = J * az.electron_current(component='x')[sites] * 1e-4
                YLabel = r'$\mathregular{J_{n,x}\ [A\cdot cm^{-2}]}$'
            if txt == "Hole current along x":
                Ydata = J * az.hole_current(component='x')[sites] * 1e-4
                YLabel = r'$\mathregular{J_{p,x}\ [A\cdot cm^{-2}]}$'
            if txt == "Electron current along y":
                Ydata = J * az.electron_current(component='y')[sites] * 1e-4
                YLabel = r'$\mathregular{J_{n,y}\ [A\cdot cm^{-2}]}$'
            if txt == "Hole current along y":
                Ydata = J * az.hole_current(component='y')[sites] * 1e-4
                YLabel = r'$\mathregular{J_{p,y}\ [A\cdot cm^{-2}]}$'
            if txt == "Full steady state current":
                Ydata = J * az.full_current() * 1e-4
                if system.dimension == 1:
                    YLabel = r'J [$\mathregular{A\cdot cm^{-2}}$]'
                if system.dimension == 2:
                    YLabel = r'J [$\mathregular{A\cdot cm^{-2}}$]'

            # plot
            if txt != "Band diagram": # everything except band diagram
                ax = self.linearFig.figure.add_subplot(111)
                if txt == "Full steady state current":
                    ax.plot(X[fdx], Ydata, 'ko')
                    ax.set_ylabel(YLabel)
                else:
                    X = X * 1e6  # set length in um
                    ax.plot(X, Ydata)
                    ax.set_ylabel(YLabel)
                    ax.set_xlabel(r'Position [$\mathregular{\mu m}$]')
            else:
                az.band_diagram((Xdata[0], Xdata[1]), fig=self.linearFig.figure)
                
            self.linearFig.canvas.draw()
