# -*- coding: utf-8 -*-
import os
import shutil
import tempfile
import subprocess

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from maya.app.general.mayaMixin import MayaQWidgetBaseMixin  # for parent ui to maya


tool_path = os.path.dirname(__file__)
EXE_FILE = os.path.join(tool_path, 'bot_logger.exe')

PROGECTS = "#MGS", "#alaska", "#ardena", "#amber", "#wwz", "#bvr", "#thunder", "#redsand", "#ISS2", "#codex"

UPDATE_CHAT_ID = '-1001907629793'
ARDENA_UPDATE_CHAT_ID = '-1002160641481'
TEST_CHAT_ID = '476369950'


class ComboBoxGrp(QWidget):
    def __init__(self, label, parent=None):
        QWidget.__init__(self, parent)

        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        if label:
            self.label = QLabel(label)
            self.layout.addWidget(self.label)

        self.combo_box = QComboBox()
        self.layout.addWidget(self.combo_box)

    def addItem(self, item):
        self.combo_box.addItem(item)

    def addItems(self, item_list):
        self.combo_box.addItems(item_list)

    def value(self):
        return self.label.text(), self.combo_box.currentText()

    def currentText(self):
        return self.combo_box.currentText()

    def clear(self):
        self.combo_box.clear()


class TextFieldButtonGrp(MayaQWidgetBaseMixin, QWidget):

    def __init__(self, label='Label', button=True, buttonLabel='Button', add_selected=False, parent=None,  ):
        QWidget.__init__(self, parent)
        self.label = label
        self.buttonLabel = buttonLabel

        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        self.label = QLabel(label)
        self.layout.addWidget(self.label)

        self.line_edit = QLineEdit()
        self.line_edit.setClearButtonEnabled(True)
        self.layout.addWidget(self.line_edit)
        if button:
            self.button = QPushButton(self.buttonLabel)
            self.layout.addWidget(self.button)

        if add_selected:
            self.button.setText("Add selected")
            self.button.clicked.connect(self.add_sel_object)

    def add_sel_object(self):
        sel = cmds.ls(sl=True)[0]
        self.line_edit.setText(sel)

    def value(self):
        return self.label.text(), self.line_edit.text()

    def text(self):
        return self.line_edit.text()

    def setText(self, text):
        self.line_edit.setText(text)

    def set_fixed_hight(self, val):
        self.button.setFixedHeight(val)
        self.line_edit.setFixedHeight(val)
        self.label.setFixedHeight(val)


class RadioButtonGrp(MayaQWidgetBaseMixin, QWidget):

    def __init__(self, label='test', labelArray=[], parent=None):
        QWidget.__init__(self, parent)
        self.label = label

        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        self.label = QLabel(label)
        self.layout.addWidget(self.label)

        self.grp = QButtonGroup()
        for i, lbl in enumerate(labelArray):
            button = QRadioButton(lbl)
            if not i:
                button.setChecked(True)
            self.layout.addWidget(button)
            self.grp.addButton(button)

    def value(self):
        return self.label.text(), self.grp.checkedButton().text()

    def select(self):
        return self.grp.checkedButton().text()



class Messager_Ui(MayaQWidgetBaseMixin, QMainWindow):
    def __init__(self):
        super(Messager_Ui, self).__init__()

        self.users = {"": ""}
        self.setWindowTitle("Send message to bot v.02")
        self.centralwidget = QWidget(self)
        self.setCentralWidget(self.centralwidget)
        self.layout = QVBoxLayout(self.centralwidget)

        self.settings_file = QSettings(os.path.join(tempfile.gettempdir(), 'messager_ui.ini'), QSettings.IniFormat)
        QTextCodec.setCodecForLocale(QTextCodec.codecForName("UTF-8"))

        self.lebel = QLabel("Message text:")
        self.layout.addWidget(self.lebel)

        self.text_edit = QTextEdit()
        self.layout.addWidget(self.text_edit)

        self.asset_line_edit = TextFieldButtonGrp(label="Asset name:", button=False)
        self.layout.addWidget(self.asset_line_edit)

        self.combo_box = ComboBoxGrp("Progect:")
        self.combo_box.addItems(PROGECTS)
        self.layout.addWidget(self.combo_box)

        self.teg_RBG = RadioButtonGrp(label="Action tag: ", labelArray=["#upd", "#add", "#fix", "#remove"])
        self.layout.addWidget(self.teg_RBG)

        self.image_line_edit = TextFieldButtonGrp(label="Image path:", buttonLabel='Add from clipboard')
        self.layout.addWidget(self.image_line_edit)
        self.image_line_edit.button.clicked.connect(self.paste_from_clipboard)

        self.image_line_edit.button.setFixedWidth(110)

        self.destination_combo_box = ComboBoxGrp("Message to:")
        self.destination_combo_box.addItems(self.get_users())
        self.layout.addWidget(self.destination_combo_box)

        self.button = QPushButton("Send")
        self.layout.addWidget(self.button)
        self.button.clicked.connect(self.send_message)

        self.widget_list = [self.teg_RBG, self.combo_box]
        self.load_settings()


    def send_message(self):
        try:
            message = u'{}'.format(self.text_edit.toPlainText())
            asset = self.asset_line_edit.value()[1]
            image = self.image_line_edit.value()[1]
            tag = self.teg_RBG.value()[1]
            progect = self.combo_box.value()[1]
            message_to = self.users[self.destination_combo_box.value()[1]]
            message_to = " @"+message_to if message_to else ""

            file_path = os.path.join(tempfile.gettempdir(), 'data_file.txt')

            data_list = [message.encode('utf-8'),
                         "#" + asset + " " + progect + " " + tag + message_to,
                         "$IMAGE"+image,
                         "$ID"+UPDATE_CHAT_ID,
                         "$ACTIONsend_message"]

            with open(file_path, 'w') as f:
                for item in data_list:
                    f.write(item+'\n')

            shutil.copy(file_path, 'U:\\AssetStorage\\bug_report')
            subprocess.call([EXE_FILE])

            if progect == PROGECTS[2]:
                with open(file_path, 'w') as f:
                    for item in data_list:
                        if UPDATE_CHAT_ID in item:
                            item = item.replace(UPDATE_CHAT_ID, ARDENA_UPDATE_CHAT_ID)
                            print(item)

                        f.write(item + '\n')

                shutil.copy(file_path, 'U:\\AssetStorage\\bug_report')
                subprocess.call([EXE_FILE])

            self.image_line_edit.setText('')

            try:
                if image:
                    os.remove(image)
            except Exception as message:
                print(message)

        except Exception as message:
            print(message)


    def get_users(self):
        # coding: utf8
        file_path = os.path.join(tempfile.gettempdir(), 'data_file.txt')

        data_list = [ "$ID-1001907629793", "$ACTIONget_users"]
        with open(file_path, 'w') as f:
            for item in data_list:
                f.write(item+'\n')

        shutil.copy(file_path, 'U:\\AssetStorage\\bug_report')
        subprocess.call([EXE_FILE])
        users_list = ["",]
        with open(file_path, 'r') as file:
            for member in file:
                name, user = member.strip().split('$USERNAME')
                self.users[name] = user
                users_list.append(name)
        os.remove(file_path)
        return users_list


    def paste_from_clipboard(self):
        clipboard = QApplication.clipboard()
        icon = clipboard.image()
        if icon:
            file_path = os.path.join(tempfile.gettempdir(), 'tmp_image.png')
            result = icon.save(file_path)
            if result:
                file_path = file_path.replace("\\", "/")
                self.image_line_edit.setText(file_path)

    def closeEvent(self, evt):
        """
        When window closed it save fields settings
        """
        if self.settings_file:
            settings = QSettings(self.settings_file, QSettings.IniFormat)
            data = self.get_data(self.widget_list)
            settings.setValue("ui settings", data)
            settings.setValue("ui position", [self.x(), self.y()])

    def load_settings(self):
        """
        If settings not exist - load default settings
        """
        try:
            if self.settings_file:
                settings = QSettings(self.settings_file, QSettings.IniFormat)
                if settings.contains("ui settings"):
                    data = settings.value("ui settings")
                    for button in self.teg_RBG.grp.buttons():
                        if button.text() == data[u'Action tag: ']:
                            button.setChecked(True)
                            break

                    self.combo_box.combo_box.setCurrentText(data['Progect:'])

                if settings.contains("ui position"):
                    x, y = settings.value("ui position")
                    self.move(int(x), int(y))
        except Exception as message:
            print(message)

    def get_data(self, widget_list):
        data = dict()
        for widget in widget_list:
            text, val = widget.value()
            data[text] = val
        return data


def message_to_bot():
    dyn_win = Messager_Ui()
    dyn_win.show()



message_to_bot()
