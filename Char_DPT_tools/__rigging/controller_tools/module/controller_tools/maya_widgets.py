from PySide2.QtCore import QSettings, Qt
from PySide2.QtWidgets import *
from maya.app.general.mayaMixin import MayaQWidgetBaseMixin  # for parent ui to maya
import maya.cmds as cmds

class ButtonGrp(QWidget):
    def __init__(self, label='', labelArray=[], parent=None, checkable=False):
        QWidget.__init__(self, parent)
        self.label = label
        self.button_list = list()

        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(3)
        self.setLayout(self.layout)

        if label:
            self.label = QLabel(label)
            self.layout.addWidget(self.label)

        self.grp = QButtonGroup()
        for i, lbl in enumerate(labelArray):
            button = QPushButton(lbl)
            button.setCheckable(checkable)
            if not i:
                button.setChecked(True)
            self.layout.addWidget(button)
            self.grp.addButton(button)
            self.button_list.append(button)


class CheckBoxGrp(MayaQWidgetBaseMixin, QWidget):

    def __init__(self, attribut, parent=None):
        QWidget.__init__(self, parent)

        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        self.label = QLabel(attribut)
        self.layout.addWidget(self.label)

        self.check_box  = QCheckBox()
        self.layout.addWidget(self.check_box )

    def value(self):
        return self.label.text(), bool(self.check_box.checkState())


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


class FloatSliderGrp(MayaQWidgetBaseMixin, QWidget):

    def __init__(self, attribut, parent=None):
        QWidget.__init__(self, parent)

        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        self.label = QLabel(attribut)
        self.layout.addWidget(self.label)

        self.slider = QSlider()
        self.slider.setRange(1, 50)
        self.slider.setSliderPosition(10)
        self.slider.setOrientation(Qt.Horizontal)
        self.layout.addWidget(self.slider)

        self.line_edit = QLineEdit()

        self.layout.addWidget(self.line_edit)
        self.line_edit.setText(str(1.0))
        self.slider.valueChanged.connect(self.valueHandler)

    def valueHandler(self, value):
        scaledValue = float(value) / 10
        self.line_edit.setText(str(scaledValue))

    def value(self):
        return self.label.text(), float(self.line_edit.text())

    def setRange(self, start, end):
        self.slider.setRange(start * 10, end * 10)

    def setValue(self, value):
        self.slider.setValue(value * 10)


class intSliderGrp(MayaQWidgetBaseMixin, QWidget):

    def __init__(self, attribut, value=1, parent=None):
        QWidget.__init__(self, parent, )

        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        self.label = QLabel(attribut)

        self.layout.addWidget(self.label)

        self.slider = QSlider()
        self.slider.setRange(1, 50)
        self.slider.setSliderPosition(value)
        self.slider.setOrientation(Qt.Horizontal)
        self.layout.addWidget(self.slider)

        self.spin_box = QSpinBox()

        self.layout.addWidget(self.spin_box)
        self.spin_box.setValue(value)

        self.slider.valueChanged.connect(self.spin_box.setValue)
        self.spin_box.valueChanged.connect(self.slider.setValue)

    def value(self):
        return self.label.text(), self.spin_box.value()

    def setRange(self, start, end):
        self.slider.setRange(start, end)

    def setValue(self, value):
        self.slider.setValue(value )
        self.spin_box.setValue(value)


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


class UiTemplate(MayaQWidgetBaseMixin, QMainWindow):
    def __init__(self):
        super(UiTemplate, self).__init__()
        self.widget_list = list()
        self.settings_file = None

    def add_menu(self):
        # menu_bar
        self.menu_bar = QMenuBar()
        self.setMenuBar(self.menu_bar)
        self.menu = QMenu("Help")
        self.menu_bar.addMenu(self.menu)

        self.help_action = QAction("Help", self)
        self.menu.addAction(self.help_action)

        self.about_script_action = QAction("About script", self)
        self.menu.addAction(self.about_script_action)

    def get_data(self, widget_list):
        data = dict()
        for widget in widget_list:
            text, val = widget.value()
            data[text] = val
        return data

    def load_settings(self, set_settings):
        """
        If settings not exist - load default settings
        """
        try:
            if self.settings_file:
                settings = QSettings(self.settings_file, QSettings.IniFormat)
                if settings.contains("ui settings"):
                    data = settings.value("ui settings")
                    set_settings(data)
                if settings.contains("ui position"):
                    x, y = settings.value("ui position")
                    self.move(int(x), int(y))
        except Exception as message:
            print(message)

    def closeEvent(self, evt):
        """
        When window closed it save fields settings
        """
        if self.settings_file:
            settings = QSettings(self.settings_file, QSettings.IniFormat)
            data = self.get_data(self.widget_list)
            settings.setValue("ui settings", data)
            settings.setValue("ui position", [self.x(), self.y()])

    @staticmethod
    def text_dialog(text_data):
        """
        'Help window' or 'About program' text dialog
        """
        help_dialog = QMessageBox()
        help_dialog.setWindowFlags(Qt.WindowStaysOnTopHint)

        if "Latest updates:" in text_data:
            help_dialog.setWindowTitle("About program")
        else:
            help_dialog.setWindowTitle("Help window")

        help_dialog.setText(text_data)
        help_dialog.setStandardButtons(QMessageBox.Cancel)
        help_dialog.exec_()

    def align_labels(self, widgets):

        labels = []

        for w in widgets:
            if hasattr(w, "label") and isinstance(w.label, QLabel):
                labels.append(w.label)

        if not labels:
            return

        max_width = max(label.sizeHint().width() for label in labels)

        for label in labels:
            label.setFixedWidth(max_width)

if __name__ == '__main__':
    from PySide2.QtWidgets import *
    from PySide2.QtCore import Qt
    import os



    class TestAllWidgetsWindow(UiTemplate):
        def __init__(self):
            super(TestAllWidgetsWindow, self).__init__()

            self.setWindowTitle("All Widgets Test Window")
            self.resize(700, 500)


            self.settings_file = os.path.join(os.path.expanduser("~"), "test_widgets_settings.ini")

            self.add_menu()


            central = QWidget()
            self.setCentralWidget(central)

            self.main_layout = QVBoxLayout(central)
            self.main_layout.setSpacing(8)

            self.build_ui()
            self.align_labels(self.widget_list + [self.button_grp])



        # ---------- UI ----------
        def build_ui(self):

            # ButtonGrp
            self.button_grp = ButtonGrp(
                label="ButtonGrp:",
                labelArray=["One", "Two", "Three"],
                checkable=True
            )
            self.main_layout.addWidget(self.button_grp)

            # CheckBoxGrp
            self.checkbox_grp = CheckBoxGrp("CheckBoxGrp:")
            self.main_layout.addWidget(self.checkbox_grp)

            # ComboBoxGrp
            self.combo_grp = ComboBoxGrp("ComboBoxGrp:")
            self.combo_grp.addItems(["Item A", "Item B", "Item C"])
            self.main_layout.addWidget(self.combo_grp)

            # FloatSliderGrp
            self.float_slider = FloatSliderGrp("FloatSliderGrp:")
            self.float_slider.setRange(0, 10)
            self.float_slider.setValue(3)
            self.main_layout.addWidget(self.float_slider)

            # IntSliderGrp
            self.int_slider = intSliderGrp("IntSliderGrp:", value=5)
            self.int_slider.setRange(1, 20)
            self.main_layout.addWidget(self.int_slider)

            # RadioButtonGrp
            self.radio_grp = RadioButtonGrp(
                label="RadioButtonGrp:",
                labelArray=["A", "B", "C"]
            )
            self.main_layout.addWidget(self.radio_grp)

            self.text_button_grp = TextFieldButtonGrp(
                label="TextFieldButtonGrp:",
                buttonLabel="Print",
                add_selected=True
            )
            self.main_layout.addWidget(self.text_button_grp)

            self.print_btn = QPushButton("Print All Values")
            self.print_btn.clicked.connect(self.print_values)
            self.main_layout.addWidget(self.print_btn)

            self.main_layout.addStretch()

            self.widget_list = [
                self.checkbox_grp,
                self.combo_grp,
                self.float_slider,
                self.int_slider,
                self.radio_grp,
                self.text_button_grp,
            ]


        def print_values(self):
            data = self.get_data(self.widget_list)
            print("\n=== UI VALUES ===")
            for k, v in data.items():
                print(k, v)

        def apply_settings(self, data_dict):

            for widget in self.widget_list:
                label, _ = widget.value()
                if label in data_dict:
                    val = data_dict[label]


                    if isinstance(widget, CheckBoxGrp):
                        widget.check_box.setChecked(val)

                    elif isinstance(widget, ComboBoxGrp):
                        index = widget.combo_box.findText(val)
                        if index != -1:
                            widget.combo_box.setCurrentIndex(index)

                    elif isinstance(widget, FloatSliderGrp):
                        widget.setValue(val)

                    elif isinstance(widget, intSliderGrp):
                        widget.setValue(val)

                    elif isinstance(widget, RadioButtonGrp):
                        for btn in widget.grp.buttons():
                            if btn.text() == val:
                                btn.setChecked(True)

                    elif isinstance(widget, TextFieldButtonGrp):
                        widget.setText(val)



    def show_test_window():
        global test_widgets_window
        try:
            test_widgets_window.close()
            test_widgets_window.deleteLater()
        except:
            pass

        test_widgets_window = TestAllWidgetsWindow()
        test_widgets_window.show()


    show_test_window()
