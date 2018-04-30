'''
串口调试
'''

from PyQt5.QtWidgets import (QMainWindow, QHBoxLayout, QVBoxLayout, QGridLayout, QTextBrowser,
 QAction, QComboBox, QLabel, QPushButton, QSplitter, QFrame, QApplication, QWidget, qApp,
 QMessageBox, QTextEdit, QGroupBox, QCheckBox, QLineEdit)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon, QIntValidator

import serial
from serial.tools import list_ports

import sys


class MySerial(QMainWindow):
    
    def __init__(self):

        super(MySerial, self).__init__()

        self.receiveData = ''
        self.receiveDataSTR = ''
        self.receiveDataHEX = ''
        self.receiveDataDEC = ''
        self.receiveDataType = 'STR'

        self.sendCount = 0
        self.receiveCount = 0
        self.serialState = '关闭'
        self.sendState = '停止'
        self.receiveState = '停止'

        self.receiveTimer = QTimer()
        self.sendRegularlyTimer = QTimer()

        self.initUI()
        self.mySerial = None

        
    def initUI(self):
        
        # 菜单栏设置
        self.menubarSet()

        # 状态栏设置
        self.statusbarSet()
        
        # 三大模块
        leftFra = QFrame()
        leftFra.setFrameShape(QFrame.StyledPanel)
        sendGB = QGroupBox('发送区')
        receiceGB = QGroupBox('接收区')


        # 左上侧：串口参数模块 
        leftTopLayout = QGridLayout()
        leftTopLayout.addWidget(QLabel('串口'), 0, 0)
        self.serialCB = QComboBox()
        leftTopLayout.addWidget(self.serialCB, 0, 1)
        leftTopLayout.addWidget(QLabel('波特率'), 1, 0)
        self.baudrateCB = QComboBox()
        leftTopLayout.addWidget(self.baudrateCB, 1, 1)
        leftTopLayout.addWidget(QLabel('校验位'), 2, 0)
        self.parityCB = QComboBox()
        leftTopLayout.addWidget(self.parityCB, 2, 1)
        leftTopLayout.addWidget(QLabel('数据位'), 3, 0)
        self.bytesizeCB = QComboBox()
        leftTopLayout.addWidget(self.bytesizeCB, 3, 1)
        leftTopLayout.addWidget(QLabel('停止位'), 4, 0)
        self.stopbitCB = QComboBox()
        leftTopLayout.addWidget(self.stopbitCB, 4, 1)
        self.openAndCloseBTN = QPushButton('打开串口')
        leftTopLayout.addWidget(self.openAndCloseBTN, 5, 0, 1, 2)

        self.initSerialDevice()
        self.initBaudrate()
        self.initParity()
        self.initBytesize()
        self.initStopbit()
        self.initOpenAndCloseBTN()

        leftTopGB = QGroupBox('串口参数配置')
        leftTopGB.setLayout(leftTopLayout)


        # 左中侧：发送参数设置
        leftCenterLayout = QGridLayout()
        self.sendDataTypeHEXCB = QCheckBox('HEX类型')
        leftCenterLayout.addWidget(self.sendDataTypeHEXCB, 0, 0)
        leftCenterLayout.addWidget(QLabel('(默认STR类型)'), 0, 1, 1, 2)
        self.sendRegularlyCB= QCheckBox('定时发送')
        leftCenterLayout.addWidget(self.sendRegularlyCB, 1, 0)
        self.sendRegularlyTimeTE = QLineEdit('1000')
        self.sendRegularlyTimeTE.setValidator(QIntValidator(20, 3600000, self.sendRegularlyTimeTE))
        leftCenterLayout.addWidget(self.sendRegularlyTimeTE, 1, 1)
        leftCenterLayout.addWidget(QLabel('ms/次'), 1, 2)
        self.sendBTN = QPushButton('发送')
        leftCenterLayout.addWidget(self.sendBTN, 2, 0, 1, 2)
        self.sendClear = QPushButton('清空')
        leftCenterLayout.addWidget(self.sendClear, 2, 2)

        self.sendRegularlyCB.clicked.connect(self.sendRegularlyAction)
        self.sendBTN.clicked.connect(self.sendAction)
        self.sendClear.clicked.connect(self.clearSendDataActoin)

        leftCenterGB = QGroupBox('发送配置')
        leftCenterGB.setLayout(leftCenterLayout)

    
        # 左下侧：接收参数设置
        leftButtomLayout = QGridLayout()
        leftButtomLayout.addWidget(QLabel('类型(默认：STR)'), 0, 0, 1, 3)
        self.receiveDataTypeSTRCB = QCheckBox('STR')
        self.receiveDataTypeSTRCB.setChecked(True)
        leftButtomLayout.addWidget(self.receiveDataTypeSTRCB, 1, 0)
        self.receiveDataTypeHEXCB = QCheckBox('HEX')
        leftButtomLayout.addWidget(self.receiveDataTypeHEXCB, 1, 1)
        self.receiveDataTypeDECCB = QCheckBox('HEX->DEC')
        leftButtomLayout.addWidget(self.receiveDataTypeDECCB, 1, 2)
        self.receiveBTN = QPushButton('接收')
        leftButtomLayout.addWidget(self.receiveBTN, 2, 0)
        self.receiveStopBTN = QPushButton('停止')
        leftButtomLayout.addWidget(self.receiveStopBTN, 2, 1)
        self.receiveClearBTN = QPushButton('清空')
        leftButtomLayout.addWidget(self.receiveClearBTN, 2, 2)

        self.receiveBTN.clicked.connect(self.startReceive)
        self.receiveStopBTN.clicked.connect(self.stopReceiveAction)
        self.receiveClearBTN.clicked.connect(self.clearReceiveDataAction)
        self.receiveDataTypeSTRCB.clicked.connect(self.receiveDataTypeChangedAction)
        self.receiveDataTypeHEXCB.clicked.connect(self.receiveDataTypeChangedAction)
        self.receiveDataTypeDECCB.clicked.connect(self.receiveDataTypeChangedAction)

        leftButtomGB = QGroupBox('接收配置')
        leftButtomGB.setLayout(leftButtomLayout)


        # 左侧：模块布局
        vbox = QVBoxLayout()
        vbox.addWidget(leftTopGB)
        vbox.addWidget(leftCenterGB)
        vbox.addWidget(leftButtomGB)
        vbox.addStretch(1)
        self.clearAllBTN = QPushButton('清空所有信息')
        self.clearAllBTN.clicked.connect(self.clearAllAction)
        vbox.addWidget(self.clearAllBTN)
        leftFra.setLayout(vbox)
        leftFra.setMaximumWidth(250)


        # 右侧：上下——发送接受模块
        self.sendLE = QLineEdit('Hello')
        self.receiveTB = QTextBrowser()
        vboxS = QVBoxLayout()
        vboxS.addWidget(self.sendLE)
        sendGB.setLayout(vboxS)
        vboxR = QVBoxLayout()
        vboxR.addWidget(self.receiveTB)
        receiceGB.setLayout(vboxR)
        splitterV = QSplitter(Qt.Vertical)
        splitterV.addWidget(sendGB)
        splitterV.addWidget(receiceGB)


        ###########
        self.sendDataTypeHEXCB.clicked.connect(self.sendDataInit)

        # 全局布局
        hbox = QHBoxLayout()
        hbox.addWidget(leftFra)
        hbox.addWidget(splitterV)

        widget = QWidget()
        widget.setLayout(hbox)
        self.setCentralWidget(widget)

        self.resize(700, 500)
        self.setWindowTitle('串口小助手')
        self.show()


    def menubarSet(self):
        self.menubar = self.menuBar()

        fileMenu = self.menubar.addMenu('文件(&F)')
        # 退出
        fileMenu.addSeparator()
        exitAction = QAction(QIcon('img/logout.png') ,'退出(&E)', self, shortcut = 'Ctrl+Q', triggered = qApp.quit)
        fileMenu.addAction(exitAction)
        
        # setMenu = self.menubar.addMenu('设置(&S)')
        helpMenu = self.menubar.addMenu('帮助(&H)')
        aboutQt = QAction("About &Qt", self, triggered=QApplication.instance().aboutQt, shortcut = 'Ctrl+A')
        helpMenu.addAction(aboutQt)
    

    def statusbarSet(self):
        self.statusbar = self.statusBar()
        self.statusbar.setStyleSheet('QStatusBar {background: #dedede}')
        receiveStr= '接收字节数:' + str(self.receiveCount)
        sendStr = '发送字节数:' + str(self.sendCount)
        self.RSCountLBL = QLabel('%-10s|%-10s' % (sendStr, receiveStr))
        serialStateStr = '串口:' + self.serialState
        sendStateStr = '定时发送:' + self.sendState
        receiveStateStr = '接收:' + self.receiveState
        self.serialStateLBL = QLabel('|%-10s' % (serialStateStr))
        self.sendStateLBL = QLabel('|%-10s' % (sendStateStr))
        self.receiveStateLBL = QLabel('|%-10s' % (receiveStateStr))

        self.statusbar.addWidget(self.RSCountLBL)
        self.statusbar.addWidget(self.serialStateLBL)
        self.statusbar.addWidget(self.sendStateLBL)
        self.statusbar.addWidget(self.receiveStateLBL)
    

    def updataStatusbar(self):
        self.statusbar.removeWidget(self.RSCountLBL)
        self.statusbar.removeWidget(self.serialStateLBL)
        self.statusbar.removeWidget(self.sendStateLBL)
        self.statusbar.removeWidget(self.receiveStateLBL)
        if self.mySerial.is_open:
            self.serialState = '已开'
        else:
            self.serialState = '关闭'
        if self.sendRegularlyTimer.isActive():
            self.sendState = '已开'
        else:
            self.sendState = '停止'
        if self.receiveTimer.isActive():
            self.receiveState = '已开'
        else:
            self.receiveState = '停止'
        self.statusbarSet()

    
    def initSerialDevice(self):
        serialList = list_ports.comports()
        for serialN in serialList:
            self.serialCB.addItem(serialN.device)


    def initBaudrate(self):
        baudrateList = serial.Serial.BAUDRATES
        for baudrate in baudrateList:
            self.baudrateCB.addItem(str(baudrate))
        self.baudrateCB.setCurrentIndex(self.baudrateCB.findText('9600'))

    
    def initParity(self):
        paritiesList = serial.Serial.PARITIES
        for parity in paritiesList:
            self.parityCB.addItem(str(parity))

    
    def initBytesize(self):
        bytesizeList = serial.Serial.BYTESIZES
        for bytesize in bytesizeList:
            self.bytesizeCB.addItem(str(bytesize))
        self.bytesizeCB.setCurrentIndex(self.bytesizeCB.findText('8'))
    

    def initStopbit(self):
        stopbitList = serial.Serial.STOPBITS
        for stopbit in stopbitList:
            self.stopbitCB.addItem(str(stopbit))

    
    def initOpenAndCloseBTN(self):
        self.openAndCloseBTN.clicked.connect(self.openAndCloseSerialAction)


    def initSerial(self):
        self.mySerial = serial.Serial()
        self.mySerial.baudrate = int(self.baudrateCB.currentText())
        self.mySerial.parity = self.parityCB.currentText()
        self.mySerial.bytesize = int(self.bytesizeCB.currentText())
        self.mySerial.stopbits = float(self.stopbitCB.currentText())
        self.mySerial.timeout = 0.05
        self.mySerial.port = self.serialCB.currentText()


    def openAndCloseSerialAction(self):
        state = self.openAndCloseBTN.text()
        if state == '打开串口':
            self.initSerial()
            if self.mySerial.port == None or self.mySerial.port == '':
                QMessageBox.question(self, '注意', '请选择串口！',  QMessageBox.Yes)
            else:
                try:
                    self.mySerial.open()
                except Exception as e:
                    QMessageBox.question(self, '注意', '串口已被占用，请先关闭', QMessageBox.Yes)
                    return
            self.serialCB.setDisabled(True)
            self.baudrateCB.setDisabled(True)
            self.parityCB.setDisabled(True)
            self.bytesizeCB.setDisabled(True)
            self.stopbitCB.setDisabled(True)
            self.openAndCloseBTN.setText('关闭串口')
        else:
            self.serialCB.setDisabled(False)
            self.baudrateCB.setDisabled(False)
            self.parityCB.setDisabled(False)
            self.bytesizeCB.setDisabled(False)
            self.stopbitCB.setDisabled(False)
            self.openAndCloseBTN.setText('打开串口')
            self.mySerial.close()

        self.updataStatusbar()

    
    def sendAction(self):
        content = self.sendLE.text()
        if self.sendDataTypeHEXCB.isChecked():
            try:
                content = bytes().fromhex(content)
            except ValueError as e:
                try:
                    content = bytes().fromhex(content + '0')
                except expression as identifier:
                    QMessageBox.question(self, '注意', '请按照十六进制形式书写！', QMessageBox.Yes)
        else:
            content = content.encode()
        if self.serialIsOpen():
            lenAdd= self.mySerial.write(content)
            self.sendCount += lenAdd
            
            self.startReceive()
            self.receiveAction()

    
    def serialIsOpen(self):
        if self.mySerial == None or self.mySerial.is_open == False:
            QMessageBox.question(self, '注意', '请先打开串口', QMessageBox.Yes)
            return False
        return True

    
    def startReceive(self):
        if self.serialIsOpen():
            self.receiveTimer.setInterval(1000)
            self.receiveTimer.start()
            self.receiveTimer.timeout.connect(self.receiveAction)
            
            self.updataStatusbar()

    
    def receiveAction(self):
        if self.serialIsOpen():
            data = self.mySerial.read(50)    # bytes类型，且假设：接收到的数据为16进制形式的
            if len(data) == 0:
                return
            self.receiveCount += len(data)

            if '\'\\x' in str(data):
                self.receiveDataHEX += self.strAddSpace(data.hex())
                self.receiveDataDEC = self.hexToDec(self.receiveDataHEX)

                self.receiveDataSTR += data.decode()
                # if self.receiveDataTypeSTRCB.isChecked():
                #     self.receiveDataTypeSTRCB.setCheckable(False)
                #     self.receiveDataTypeSTRCB.setDisabled(True)
                #     self.receiveDataTypeHEXCB.setChecked(True)
                #     self.receiveDataType = 'HEX'
                # else:
                #     self.receiveDataTypeSTRCB.setDisabled(True)

            else:
                # self.receiveDataTypeSTRCB.setDisabled(False)
                
                self.receiveDataSTR += data.decode()
                self.receiveDataHEX += self.strToHex(data.decode())
                self.receiveDataDEC = self.hexToDec(self.receiveDataHEX)

            if self.receiveDataType == 'HEX':
                self.receiveData = self.receiveDataHEX
            elif self.receiveDataType == 'STR':
                self.receiveData = self.receiveDataSTR
            elif self.receiveDataType == 'HEX->DEC':
                self.receiveData = self.receiveDataDEC

            self.receiveTB.setText(self.receiveData)

            self.updataStatusbar()


    def clearReceiveDataAction(self):
        self.receiveData = ''
        self.receiveDataHEX = ''
        self.receiveDataDEC = ''
        self.receiveDataSTR = ''
        self.receiveTB.clear()

    
    def clearSendDataActoin(self):
        self.sendLE.clear()

    
    def strAddSpace(self, staData):
        results = ''
        for i in range(0, len(staData), 2):
            results += staData[i: i+2] + ' '
        return results

    
    def strToHex(self, strData):
        hexStr = ''
        for i in range(len(strData)):
            asciiVal = ord(strData[i])
            temp = str(hex(asciiVal))[-2:]
            hexStr += temp + ' '
        return hexStr

    
    def hexToDec(self, strData):
        '''
        输出的字符串，以空格隔开，得到一个个8位的16进制表示的数
        '''
        strList = strData.split()
        decStr = ''
        for hexStr in strList:
            decStr += str(int(hexStr, 16)) + ' '
        return decStr[:-1]
    

    def receiveDataTypeChangedAction(self):
        currentType = self.sender().text()
        if self.sender().isChecked() == False:
            self.receiveDataType = 'HEX'
            self.receiveDataTypeHEXCB.setChecked(True)
        else:
            self.receiveDataType = currentType
            typeList = [self.receiveDataTypeHEXCB, self.receiveDataTypeDECCB, self.receiveDataTypeSTRCB]
            for dataType in typeList:
                if currentType != dataType.text() and dataType.isChecked():
                    dataType.setChecked(False)
        if self.receiveDataType == 'STR':
            self.receiveData = self.receiveDataSTR
        elif self.receiveDataType == 'HEX':
            self.receiveData = self.receiveDataHEX
        elif self.receiveDataType == 'HEX->DEC':
            self.receiveData = self.receiveDataDEC
        self.receiveTB.setText(self.receiveData)

    
    def sendRegularlyAction(self):
        if self.serialIsOpen() == False:
           self.sendRegularlyCB.setChecked(False) 
           return
        if self.sendRegularlyCB.isChecked():
            timeInterval = int(self.sendRegularlyTimeTE.text())
            self.sendRegularlyTimer.setInterval(timeInterval)
            self.sendRegularlyTimer.start()
            self.sendRegularlyTimer.timeout.connect(self.doSendRegularlyAction)
        else:
            self.sendRegularlyTimeTE.setDisabled(False)
            if self.sendRegularlyTimer.isActive():
                self.sendRegularlyTimer.stop()

        self.sendRegularlyTimeTE.setDisabled(True)
        self.updataStatusbar()
    

    def doSendRegularlyAction(self):
        self.sendAction()


    def stopReceiveAction(self):
        if self.mySerial != None and self.mySerial.is_open == False:
            return
        else:
            self.receiveTimer.stop()
        
        self.updataStatusbar()

    
    def clearStatusMessage(self):
        self.receiveCount = 0
        self.sendCount = 0
        self.updataStatusbar()


    def clearAllAction(self):
        self.clearSendDataActoin()
        self.clearReceiveDataAction()
        self.clearStatusMessage()


    def sendDataInit(self):
        if self.sendDataTypeHEXCB.isChecked():
            self.sendLE.setText('11 22 33 44')
        else:
            self.sendLE.setText('hello')
        



if __name__ == '__main__':

    app = QApplication(sys.argv)
    ms = MySerial()
    sys.exit(app.exec_())