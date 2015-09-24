# -*- coding: utf-8 -*-
#
# Copyright 2014-2015 Stefan van den Akker <srvandenakker.dev@gmail.com>
#
# This file is part of Supplementary Buttons for Anki.
#
# Supplementary Buttons for Anki is free software: you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# Supplementary Buttons for Anki is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
# Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with Supplementary Buttons for Anki. If not, see http://www.gnu.org/licenses/.


import os
import re
import sys

from anki.utils import json
from aqt import editor, mw
from anki.hooks import wrap
from PyQt4 import QtGui, QtCore
import BeautifulSoup

import const


# Helper class
##################################################

class Utility(object):
    """Utility class with all helper functions that are needed throughout
    the addon. All methods are static, and all fields are constants."""

    # Constants
    ##################################################

    const.PROGRAM_NAME = "Supplementary Buttons for Anki"
    const.VERSION = "0.6.1"
    const.YEAR_START = 2014
    const.YEAR_LAST = 2015
    const.ANKIWEB_URL = "https://ankiweb.net/shared/info/162313389"
    const.GITHUB_URL = "https://github.com/Neftas/supplementary-buttons-anki"
    const.EMAIL = "srvandenakker.dev@gmail.com"

    # Linux, Mac OS, Windows, etc
    const.PLATFORM = sys.platform

    # size of the dialog windows
    const.DIALOG_SIZE_X = 350
    const.DIALOG_SIZE_Y = 200

    const.HTML_TAGS = ("b", "i", "u", "span", "font", "sup", "sub", "dl", "dt", "dd",
                 "code", "s", "pre", "kbd", "a", "strike", "blockquote", "abbr")

    const.HEADING_TAGS = ("h1", "h2", "h3", "h4", "h5", "h6")

    const.CODE_AND_PRE_CLASS = "c"

    # Methods
    ##################################################

    @staticmethod
    def counter(start=0, step=1):
        """Generator that creates infinite numbers."""
        num = start
        while True:
            yield num
            num += step

    @staticmethod
    def set_icon(button, name, preferences):
        """Define the path for the icon the corresponding
        button should have."""
        icon_path = os.path.join(preferences.addons_folder(),
            "extra_buttons/icons/{}.png".format(name))
        button.setIcon(QtGui.QIcon(icon_path))

    @staticmethod
    def escape_html_chars(s):
        """Escape HTML characters in a string. Return a safe string."""
        html_escape_table = {
            "&": "&amp;",
            '"': "&quot;",
            "'": "&apos;",
            ">": "&gt;",
            "<": "&lt;",
        }

        return "".join(html_escape_table.get(c, c) for c in s)

    @staticmethod
    def check_alignment(s):
        """Return the alignment of a table based on input s. If s not in the list,
        return the default value."""
        alignments = {":-": "left", ":-:": "center", "-:": "right"}
        default = "left"
        if not s in alignments:
            return default
        return alignments[s]

    @staticmethod
    def check_size_heading(s):
        """Determine by counting the number of leading hashes in the string the
        size of the heading. Return an int that is the length of the hashes."""
        regex = re.compile(r"^(#+)")
        if s.strip().startswith("#"):
            return len(regex.match(s).group(1))
        else:
            return -1

    @staticmethod
    def strip_leading_whitespace(s):
        """Remove leading whitespace from a string s. Whitespace is defined as
        a space, a tab or a non-breakable space."""
        while True:
            if s.startswith(" "):
                s = s.lstrip()
            elif s.startswith("&nbsp;"):
                s = s.lstrip("&nbsp;")
            else:
                break
        return s

    @staticmethod
    def create_horizontal_rule():
        frame = QtGui.QFrame()
        frame.setFrameShape(QtGui.QFrame.HLine)
        frame.setFrameShadow(QtGui.QFrame.Sunken)
        return frame

# Preferences
##################################################

class Preferences(object):

    def __init__(self, mw):
        self.main_window = mw
        self.addon_path = os.path.join(self.addons_folder(),
                "extra_buttons", ".extra_buttons_prefs")
        self._default_conf = {"class_name": const.CODE_AND_PRE_CLASS,
                             "last_bg_color": "#00f",
                             "fixed_ol_type": "",
                             "Show <code> button": True,
                             "Show unordered list button": True,
                             "Show ordered list button": True,
                             "Show strikethrough button": True,
                             "Show code block button": True,
                             "Show horizontal rule button": True,
                             "Show indent button": True,
                             "Show outdent button": True,
                             "Show definition list button": True,
                             "Show table button": True,
                             "Show keyboard button": True,
                             "Show create link buttons": True,
                             "Show background color button": True,
                             "Show blockquote button": True,
                             "Show justify buttons": True,
                             "Show heading button": True,
                             "Show abbreviation button": True}
        self.prefs = None

        try:
            with open(self.addon_path, "r") as f:
                self.prefs = json.load(f)
        except:
            # file does not exist or is corrupted: fall back to default
            with open(self.addon_path, "w") as f:
                self.prefs = self._default_conf
                json.dump(self.prefs, f)
        else:
            # add items that are not in prefs, but should be (e.g. after update)
            for key, value in self._default_conf.iteritems():
                if self.prefs.get(key) is None:
                    self.prefs[key] = value
            # delete items in prefs that should not be there (e.g. after update)
            for key in self.prefs.keys()[:]:
                if self._default_conf.get(key) is None:
                    del self.prefs[key]
            self.save_prefs()

    def addons_folder(self):
        """Return the addon folder used by Anki."""
        return self.main_window.pm.addonFolder()

    def save_prefs(self):
        """Save the preferences to disk."""
        with open(self.addon_path, "w") as f:
            json.dump(self.prefs, f)

    # def set_css_class_name_code_pre(self):
    #     """Sets the CSS styling for the <code> and <pre> tags."""

    #     current_text = self.prefs.get("class_name", "")

    #     text, ok = QtGui.QInputDialog.getText(self.main_window,
    #         "Set class for <code> and <pre>",
    #         "Enter a class name for your custom CSS &lt;code&gt; and &lt;pre&gt; style",
    #         QtGui.QLineEdit.Normal, current_text)

    #     if ok:
    #         self.prefs["class_name"] = text
    #         self.save_prefs()


# Menu
##################################################

class ExtraButtons_Options(QtGui.QMenu):
    """Display the various options in the main menu."""

    def __init__(self, mw, preferences):
        super(ExtraButtons_Options, self).__init__()
        self.mw = mw
        self.preferences = preferences
        self.listOfRadioButtons = list()

    def button_switch(self, state):
        """Puts a button either on or off. Reverses current state."""
        source = self.sender()
        name = source.text()
        current_state = self.preferences.prefs[name]
        if bool(state) != current_state:
            self.preferences.prefs[name] = not current_state

    def create_checkbox(self, name, mw):
        checkbox = QtGui.QCheckBox(name, self)
        if self.preferences.prefs[name]:
            checkbox.setChecked(True)
        checkbox.stateChanged.connect(self.button_switch)
        return checkbox

    def create_radiobutton(self, name):
        radiobutton = QtGui.QRadioButton(name)
        return radiobutton

    def setup_extra_buttons_options(self):

        sub_menu_title = "&Supplementary buttons add-on (options)"
        sub_menu = mw.form.menuTools.addMenu(sub_menu_title)

        options_action = QtGui.QAction("&Button options...", mw)
        options_action.triggered.connect(self.show_option_dialog)

        about_action = QtGui.QAction("&About {0}...".format(const.PROGRAM_NAME), mw)
        about_action.triggered.connect(self.show_about_dialog)

        # custom_css = QtGui.QAction("&Alter <code> and <pre> CSS...", mw)
        # custom_css.triggered.connect(self.preferences.set_css_class_name_code_pre)

        sub_menu.addAction(options_action)
        # sub_menu.addAction(custom_css)
        sub_menu.addAction(about_action)

    def show_about_dialog(self):
        about_dialog = QtGui.QMessageBox.about(self.mw,
            "About {0} v{1}".format(const.PROGRAM_NAME, const.VERSION),
            """\
        Copyright: <b>Stefan van den Akker</b>, {0}-{1}<br />
        Version: {2}<br />
        Email: <a href="mailto:{3}">{3}</a><br />
        Bugs & feature requests or if you want to help out with code:
            <a href="{4}">Github</a><br /><br />
        Don't forget to rate and share your thoughts on <a href="{5}">AnkiWeb</a>!
            """.format(const.YEAR_START, const.YEAR_LAST, const.VERSION,
                        const.EMAIL, const.GITHUB_URL, const.ANKIWEB_URL)
        )

    def enableRadioButtons(self, checkbox):
        if checkbox.isChecked():
            # enable radio buttons
            for rb in self.listOfRadioButtons:
                rb.setEnabled(True)
        else:
            # disable radiobuttons
            for rb in self.listOfRadioButtons:
                rb.setEnabled(False)

    def show_option_dialog(self):
        option_dialog = QtGui.QDialog(self.mw)
        option_dialog.setWindowTitle("Options for Supplementary Buttons")

        grid = QtGui.QGridLayout()

        # create a dict that has all the relevant buttons to be displayed
        l = [k for k in self.preferences.prefs.keys() if k not in
                ("class_name", "last_bg_color", "fixed_ol_type")]

        # no text highlighting on platforms other Linux
        # if not const.PLATFORM.startswith("linux"):
        #     l.remove("Show background color button")

        # determine number of items in each column in the grid
        num_items = len(l) / 2.0
        num_items = num_items + 0.5 if (num_items % 1.0 > 0.0) else num_items

        # go through the keys in the prefs and make QCheckBoxes for them
        for index, option in enumerate(sorted(l)):
            checkbox = self.create_checkbox(option, mw)
            if index >= num_items:
                col = 1
                row = index - num_items
                grid.addWidget(checkbox, row, col)
            else:
                col = 0
                row = index
                grid.addWidget(checkbox, row, col)

        cssClassLabel = QtGui.QLabel("CSS class for &lt;code&gt; and &lt;pre&gt; code blocks", self)
        cssClassText = QtGui.QLineEdit(self.preferences.prefs.get("class_name"), self)
        cssClassHBox = QtGui.QHBoxLayout()
        cssClassHBox.addWidget(cssClassLabel)
        cssClassHBox.addWidget(cssClassText)

        checkBox = QtGui.QCheckBox("Fix ordered list type", self)
        if self.preferences.prefs["fixed_ol_type"]:
            checkBox.setChecked(True)
        else:
            checkBox.setChecked(False)

        checkBox.stateChanged.connect(lambda: self.enableRadioButtons(checkBox))

        # make sure self.listOfRadioButtons is empty
        # before adding new buttons
        self.listOfRadioButtons = list()
        for type_ol in ("1.", "A.", "a.", "I.", "i."):
            rb = self.create_radiobutton(type_ol)
            self.listOfRadioButtons.append(rb)

        ol_type = self.preferences.prefs.get("fixed_ol_type")
        if not ol_type:
            self.listOfRadioButtons[0].toggle()
        else:
            for rb in self.listOfRadioButtons:
                if ol_type == rb.text():
                    rb.toggle()
                    break

        buttonGroup = QtGui.QButtonGroup(self)

        numRadioButton = 0
        for rb in self.listOfRadioButtons:
            buttonGroup.addButton(rb, numRadioButton)
            numRadioButton += 1

        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(checkBox)
        for rb in self.listOfRadioButtons:
            if not checkBox.isChecked():
                rb.setEnabled(False)
            hbox.addWidget(rb)

        button_box = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok |
                QtGui.QDialogButtonBox.Cancel)
        button_box.accepted.connect(option_dialog.accept)
        button_box.rejected.connect(option_dialog.reject)

        vbox = QtGui.QVBoxLayout()
        vbox.addLayout(grid)
        vbox.addWidget(Utility.create_horizontal_rule())
        vbox.addLayout(cssClassHBox)
        vbox.addWidget(Utility.create_horizontal_rule())
        vbox.addLayout(hbox)
        vbox.addWidget(button_box)

        option_dialog.setLayout(vbox)

        if option_dialog.exec_() == QtGui.QDialog.Accepted:
            if checkBox.isChecked():
                selectedRadioButton = buttonGroup.id(buttonGroup.checkedButton())
                self.preferences.prefs["fixed_ol_type"] = (
                        self.listOfRadioButtons[selectedRadioButton].text())
            else:
                self.preferences.prefs["fixed_ol_type"] = ""

            # change CSS class for <code> and <pre>
            self.preferences.prefs["class_name"] = cssClassText.text()

            # save preferences to disk
            self.preferences.save_prefs()


# Buttons
##################################################

def setup_buttons(self):

    if preferences.prefs["Show <code> button"]:
        b = self._addButton("text_code", lambda: self.wrap_in_tags("code",
            preferences.prefs["class_name"]), _("Ctrl+,"), _("Code format text (Ctrl+,)"),
            check=False)
        Utility.set_icon(b, "text_code", preferences)

    if preferences.prefs["Show unordered list button"]:
        b = self._addButton("unordered_list", self.toggleUnorderedList,
            _("Ctrl+["), _("Create unordered list (Ctrl+[)"), check=False)
        Utility.set_icon(b, "unordered_list", preferences)

    if preferences.prefs["Show ordered list button"]:
        b = self._addButton("ordered_list", self.toggleOrderedList, _("Ctrl+]"),
            _("Create ordered list (Ctrl+])"), check=False)
        Utility.set_icon(b, "ordered_list", preferences)

    if preferences.prefs["Show strikethrough button"]:
        b = self._addButton("text_strikethrough", self.toggleStrikeThrough,
            _("Alt+Shift+5"), _("Strikethrough text (Alt+Shift+5)"), check=True)
        Utility.set_icon(b, "text_strikethrough", preferences)

    # FIXME: think of better symbol to represent a <pre> block
    if preferences.prefs["Show code block button"]:
        b = self._addButton("text_pre", lambda: self.wrap_in_tags("pre",
            preferences.prefs["class_name"]), _("Ctrl+."),
            tip=_("Create a code block (Ctrl-.)"), check=False)
        Utility.set_icon(b, "text_pre", preferences)

    if preferences.prefs["Show horizontal rule button"]:
        b = self._addButton("hor_rule", self.toggleHorizontalLine, _("Ctrl+shift+alt+-"),
            tip=_("Create a horizontal rule (Ctrl+Shift+Alt+_)"), check=False)
        Utility.set_icon(b, "hor_rule", preferences)

    if preferences.prefs["Show indent button"]:
        b = self._addButton("indent", self.toggleIndent, _("Ctrl+Shift+]"),
            _("Indent text or list (Ctrl+Shift+])"), check=False)
        Utility.set_icon(b, "indent", preferences)

    if preferences.prefs["Show outdent button"]:
        b = self._addButton("outdent", self.toggleOutdent, _("Ctrl+Shift+["),
            _("Outdent text or list (Ctrl+Shift+[)"), check=False)
        Utility.set_icon(b, "outdent", preferences)

    # FIXME: better symbol for <dl>
    if preferences.prefs["Show definition list button"]:
        b = self._addButton("deflist", self.toggleDefList, _("Ctrl+Shift+d"),
            _("Create definition list (Ctrl+Shift+D)"), check=False)
        Utility.set_icon(b, "deflist", preferences)

    if preferences.prefs["Show table button"]:
        b = self._addButton("table", self.toggleTable, _("Ctrl+Shift+3"),
            _("Create a table (Ctrl+Shift+3)"), check=False)
        Utility.set_icon(b, "table", preferences)

    if preferences.prefs["Show keyboard button"]:
        b = self._addButton("kbd", lambda: self.wrap_in_tags("kbd"),
            _("Ctrl+Shift+k"), _("Create a keyboard button (Ctrl+Shift+K)"),
            check=False)
        Utility.set_icon(b, "kbd", preferences)

    if preferences.prefs["Show create link buttons"]:
        b1 = self._addButton("anchor", self.create_hyperlink, _("Ctrl+Shift+h"),
            _("Insert link (Ctrl+Shift+H)"), check=False)
        Utility.set_icon(b1, "anchor", preferences)

        b2 = self._addButton("unlink", self.unlink, _("Ctrl+Shift+Alt+h"),
            _("Unlink (Ctrl+Shift+Alt+H)"), check=False)
        Utility.set_icon(b2, "unlink", preferences)

    if (preferences.prefs["Show background color button"]): # and const.PLATFORM.startswith("linux")):
        b1 = self._addButton("background", self.on_background, _("Ctrl+Shift+b"),
            _("Set background color (Ctrl+Shift+B)"), text=" ")
        self.setup_background_button(b1)
        b2 = self._addButton("change_bg_color", self.on_change_col, _("Ctrl+Shift+n"),
          _("Change color (Ctrl+Shift+N)"), text=u"▾")
        b2.setFixedWidth(12)

    if preferences.prefs["Show blockquote button"]:
        b = self._addButton("blockquote", self.toggleBlockquote,
            _("Ctrl+Shift+Y"), _("Insert blockquote (Ctrl+Shift+Y)"),
            check=False)
        Utility.set_icon(b, "blockquote", preferences)

    if preferences.prefs["Show justify buttons"]:
        b1 = self._addButton("left", self.justifyLeft,
        _("Ctrl+Shift+Alt+l"), _("Align text left (Ctrl+Shift+Alt+L)"),
        check=False)
        Utility.set_icon(b1, "left", preferences)

        b2 = self._addButton("center", self.justifyCenter,
            _("Ctrl+Shift+Alt+b"), _("Align text center (Ctrl+Shift+Alt+B)"),
            check=False)
        Utility.set_icon(b2, "center", preferences)

        b3 = self._addButton("right", self.justifyRight,
            _("Ctrl+Shift+Alt+r"), _("Align text right (Ctrl+Shift+Alt+R)"),
            check=False)
        Utility.set_icon(b3, "right", preferences)

        b4 = self._addButton("justified", self.justifyFull,
            _("Ctrl+Shift+Alt+j"), _("Justify text (Ctrl+Shift+Alt+J)"),
            check=False)
        Utility.set_icon(b4, "justified", preferences)

    if preferences.prefs["Show heading button"]:
        b = self._addButton("heading", self.toggleHeading,
            _("Ctrl+Alt+1"), _("Insert heading (Ctrl+Alt+1)"),
            check=False)
        Utility.set_icon(b, "heading", preferences)

    if preferences.prefs["Show abbreviation button"]:
        b = self._addButton("abbreviation", self.toggleAbbreviation,
            _("Shift+Alt+A"), _("Insert abbreviation (Shift+Alt+A)"),
            check=False)
        Utility.set_icon(b, "abbreviation", preferences)

def wrap_in_tags(self, tag, class_name=None):
    """Wrap selected text in a tag, optionally giving it a class."""
    selection = self.web.selectedText()

    if not selection:
        return

    selection = Utility.escape_html_chars(selection)

    tag_string_begin = ("<{0} class='{1}'>".format(tag, class_name) if
        class_name else "<{0}>".format(tag))
    tag_string_end = "</{0}>".format(tag)

    html = self.note.fields[self.currentField]

    if "<li><br /></li>" in html:
        # an empty list means trouble, because somehow Anki will also make the
        # line in which we want to put a <code> tag a list if we continue
        replacement = tag_string_begin + selection + tag_string_end
        self.web.eval("document.execCommand('insertHTML', false, %s);"
            % json.dumps(replacement))

        self.web.setFocus()
        self.web.eval("focusField(%d);" % self.currentField)
        self.saveNow()

        html_after = self.note.fields[self.currentField]

        if html_after != html:
            # you're in luck!
            return
        else:
            # nothing happened :( this is another Anki bug :( that has to do
            # with <code> tags following <div> tags
            return

    # Due to a bug in Anki or BeautifulSoup, we cannot use a simple
    # wrap operation like with <a>. So this is a very hackish way of making
    # sure that a <code> tag may precede or follow a <div> and that the tag
    # won't eat the character immediately preceding or following it
    pattern = "@%*!"
    len_p = len(pattern)

    # first, wrap the selection up in a pattern that the user is unlikely
    # to use in its own cards
    self.web.eval("wrap('{0}', '{1}')".format(pattern, pattern[::-1]))

    # focus the field, so that changes are saved
    # this causes the cursor to go to the end of the field
    self.web.setFocus()
    self.web.eval("focusField(%d);" % self.currentField)

    self.saveNow()

    html = self.note.fields[self.currentField]

    begin = html.find(pattern)
    end = html.find(pattern[::-1], begin)

    html = (html[:begin] + tag_string_begin + selection + tag_string_end +
            html[end+len_p:])

    # cleanup HTML: change all non-breakable spaces to normal spaces
    html = html.replace("&nbsp;", " ")

    # delete the current HTML and replace it by our new & improved one
    self.note.fields[self.currentField] = html

    # reload the note: this is needed on OS X, because it will otherwise
    # falsely show that the formatting of the element at the start of
    # the HTML has spread across the entire note
    self.loadNote()

    # focus the field, so that changes are saved
    self.web.setFocus()
    self.web.eval("focusField(%d);" % self.currentField)
    self.saveNow()
    self.web.setFocus()
    self.web.eval("focusField(%d);" % self.currentField)

class Abbreviation(object):
    def __init__(self, other, parent_window, selected_text):
        self.other = other
        self.parent_window = parent_window
        self.selected_text = selected_text
        self.abbreviation_dialog()

    def abbreviation_dialog(self):
        """Creates a dialog window where the user can enter data for the HTML
        tag <abbr>, for both the abbreviation and the title attribute."""
        dialog = QtGui.QDialog(self.parent_window)
        dialog.setWindowTitle("Create an abbreviation")
        dialog.resize(350, 200)

        # OK and Cancel button
        ok_button = QtGui.QPushButton("&Ok", dialog)
        ok_button.setEnabled(False)
        ok_button.clicked.connect(lambda: self.insert_abbreviation(
            text_edit.text(), title_edit.text()))
        ok_button.clicked.connect(dialog.hide)

        cancel_button = QtGui.QPushButton("&Cancel", dialog)
        cancel_button.clicked.connect(dialog.hide)
        cancel_button.setAutoDefault(True)

        # two labels: one for the text, one for the title attribute
        text_label = QtGui.QLabel("Text:")
        title_label = QtGui.QLabel("Title:")

        # two text fields: one for the text, one for the content of the title attribute
        text_edit = QtGui.QLineEdit()
        text_edit.setPlaceholderText("Text")
        text_edit.textChanged.connect(lambda: self.enable_ok_button(
            ok_button, text_edit.text(), title_edit.text()))

        title_edit = QtGui.QLineEdit();
        title_edit.setPlaceholderText("Abbreviation")
        title_edit.textChanged.connect(lambda: self.enable_ok_button(
            ok_button, text_edit.text(), title_edit.text()))

        # if user already selected text, we put it in the text edit field
        if self.selected_text:
            text_edit.setText(self.selected_text)

        hbox = QtGui.QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(cancel_button)
        hbox.addWidget(ok_button)

        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(text_label)
        vbox.addWidget(text_edit)
        vbox.addWidget(title_label)
        vbox.addWidget(title_edit)
        vbox.addLayout(hbox)

        dialog.setLayout(vbox)

        title_edit.setFocus()

        dialog.exec_()

    def enable_ok_button(self, button, text, title):
        if text and title:
            button.setEnabled(True)
        else:
            button.setEnabled(False)

    def insert_abbreviation(self, text, title):
        # escape HTML
        text = Utility.escape_html_chars(text)
        title = Utility.escape_html_chars(title)
        # unicode
        assert isinstance(text, unicode)
        assert isinstance(text, unicode)
        # create new tag
        result = u"<abbr title='{0}'>{1}</abbr>".format(title, text)
        # insert the new tag into the card
        self.other.web.eval("document.execCommand('insertHTML', false, %s);"
            % json.dumps(result))

class OrderedList(QtGui.QDialog):
    def __init__(self, other, parent_window, preferences, fixed=False):
        super(OrderedList, self).__init__(parent_window)
        self.other = other
        self.preferences = preferences

        if not fixed:
            self.setupGUI()
        else:
            self.insertOrderedList(self.preferences.prefs["fixed_ol_type"][0], 1)

    def setupGUI(self):
        self.setWindowTitle("Choose format for ordered list")
        # self.resize(const.DIALOG_SIZE_X, const.DIALOG_SIZE_Y)

        stylesheet = """
        QGroupBox { border: 1px inset lightgrey;
                            border-radius: 5px;
                            margin-top: 10px;
                            font-weight: bold; }
        QGroupBox::title {  subcontrol-origin: margin;
                            subcontrol-position: top;
                            padding:0 3px 0 3px; }
        """

        groupbox = QtGui.QGroupBox("Type", self)
        groupbox.setStyleSheet(stylesheet)

        # stylesheet for the radio buttons
        self.setStyleSheet("QRadioButton { font-weight: bold; }")

        radio_button1 = QtGui.QRadioButton("1.", self)
        radio_button1.setChecked(True)
        radio_button2 = QtGui.QRadioButton("A.", self)
        radio_button3 = QtGui.QRadioButton("a.", self)
        radio_button4 = QtGui.QRadioButton("I.", self)
        radio_button5 = QtGui.QRadioButton("i.", self)

        radio_button_group = QtGui.QButtonGroup(self)
        radio_button_group.addButton(radio_button1)
        radio_button_group.setId(radio_button1, 1)
        radio_button_group.addButton(radio_button2)
        radio_button_group.setId(radio_button2, 2)
        radio_button_group.addButton(radio_button3)
        radio_button_group.setId(radio_button3, 3)
        radio_button_group.addButton(radio_button4)
        radio_button_group.setId(radio_button4, 4)
        radio_button_group.addButton(radio_button5)
        radio_button_group.setId(radio_button5, 5)

        radio_vbox = QtGui.QVBoxLayout(self)
        radio_vbox.addWidget(radio_button1)
        radio_vbox.addWidget(radio_button2)
        radio_vbox.addWidget(radio_button3)
        radio_vbox.addWidget(radio_button4)
        radio_vbox.addWidget(radio_button5)

        groupbox.setLayout(radio_vbox)

        start_label = QtGui.QLabel("<b>Start:</b>", self)

        spinbox = QtGui.QSpinBox(self)
        spinbox.setMinimum(1)
        spinbox.setMaximum(100)
        # get value with .value()

        spinbox_vbox = QtGui.QVBoxLayout()
        spinbox_vbox.addWidget(start_label)
        spinbox_vbox.addWidget(spinbox)
        spinbox_vbox.addStretch(1)

        button_box = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok |
            QtGui.QDialogButtonBox.Cancel, QtCore.Qt.Horizontal, self)

        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        spinbox_vbox.addWidget(button_box)

        hbox = QtGui.QHBoxLayout(self);
        hbox.addWidget(groupbox)
        hbox.addLayout(spinbox_vbox)

        self.setLayout(hbox)

        if self.exec_() == QtGui.QDialog.Accepted:
            type_of_list = {
                    1: "1",
                    2: "A",
                    3: "a",
                    4: "I",
                    5: "i"
            }

            choice = type_of_list.get(
                    radio_button_group.id(radio_button_group.checkedButton()), "1")

            self.insertOrderedList(choice, spinbox.value())

    def insertOrderedList(self, type_of_list, start_num):
        """Create a new ordered list based on the input of the user.
        type_of_list is a string ("1", "A", "a", "I", "i") and
        start_num is an integer."""
        print type_of_list
        print start_num
        self.other.web.eval("""
            document.execCommand('insertOrderedList');
            var olElem = window.getSelection().focusNode.parentNode;
            if (olElem.toString() !== "[object HTMLOListElement]") {
                olElem = olElem.parentNode;
            }
            olElem.setAttribute("type", "%s");
            olElem.setAttribute("start", "%s");
            olElem.style.marginLeft = "20px";
            """ % (type_of_list, str(start_num))
        )

def create_hyperlink(self):
    dialog = QtGui.QDialog(self.parentWindow)
    dialog.setWindowTitle("Create a hyperlink")
    dialog.resize(const.DIALOG_SIZE_X, const.DIALOG_SIZE_Y)

    ok_button_anchor = QtGui.QPushButton("&OK", dialog)
    ok_button_anchor.setEnabled(False)
    ok_button_anchor.clicked.connect(lambda: self.insert_anchor(
        url_edit.text(), urltext_edit.text()))
    ok_button_anchor.clicked.connect(dialog.hide)

    ok_button_anchor.setAutoDefault(True)

    cancel_button_anchor = QtGui.QPushButton("&Cancel", dialog)
    cancel_button_anchor.clicked.connect(dialog.hide)
    cancel_button_anchor.setAutoDefault(True)

    url_label = QtGui.QLabel("Link to:")
    url_edit = QtGui.QLineEdit()
    url_edit.setPlaceholderText("URL")
    url_edit.textChanged.connect(lambda: self.enable_ok_button(ok_button_anchor,
        url_edit.text(), urltext_edit.text()))

    urltext_label = QtGui.QLabel("Text to display:")
    urltext_edit = QtGui.QLineEdit()
    urltext_edit.setPlaceholderText("Text")
    urltext_edit.textChanged.connect(lambda: self.enable_ok_button(ok_button_anchor,
        url_edit.text(), urltext_edit.text()))

    # if user already selected text, put it in urltext_edit
    selection = self.web.selectedText()
    if selection:
        urltext_edit.setText(selection)

    button_box = QtGui.QHBoxLayout()
    button_box.addStretch(1)
    button_box.addWidget(cancel_button_anchor)
    button_box.addWidget(ok_button_anchor)

    dialog_vbox = QtGui.QVBoxLayout()
    dialog_vbox.addWidget(url_label)
    dialog_vbox.addWidget(url_edit)
    dialog_vbox.addWidget(urltext_label)
    dialog_vbox.addWidget(urltext_edit)
    dialog_vbox.addLayout(button_box)

    dialog.setLayout(dialog_vbox)

    # give url_edit focus
    url_edit.setFocus()

    dialog.exec_()

def enable_ok_button(self, button, url, text):
    if url and text:
        button.setEnabled(True)
    else:
        button.setEnabled(False)

def insert_anchor(self, url, text):
    """Inserts a HTML anchor <a> into the text field, using url as hyperlink
    and text as text to-be-displayed."""
    # check for valid URL
    pattern = re.compile("(?i)https?://")
    match = re.match(pattern, url)
    if not match:
        url = "http://" + url

    text = Utility.escape_html_chars(text)

    replacement = u"<a href=\"{0}\">{1}</a>".format(url, text)

    self.web.eval("document.execCommand('insertHTML', false, %s);"
                  % json.dumps(replacement))

def unlink(self):
    self.web.eval("setFormat('unlink')")

def toggleUnorderedList(self):
    self.web.eval("""
        document.execCommand('insertUnorderedList');
        var ulElem = window.getSelection().focusNode.parentNode;
        if (ulElem.toString() !== "[object HTMLUListElement]") {
            ulElem = ulElem.parentNode;
        }
        ulElem.style.marginLeft = "20px";
        """
    )

def toggleOrderedList(self):
    if preferences.prefs["fixed_ol_type"]:
        ol = OrderedList(self, self.parentWindow, preferences, True)
    else:
        ol = OrderedList(self, self.parentWindow, preferences)

def toggleStrikeThrough(self):
    self.web.eval("setFormat('strikeThrough')")

def togglePre(self):
    self.web.eval("setFormat('formatBlock', 'pre')")

def toggleHorizontalLine(self):
    self.web.eval("setFormat('insertHorizontalRule')")

def toggleIndent(self):
    self.web.eval("setFormat('indent')")

def toggleOutdent(self):
    self.web.eval("setFormat('outdent')")

class DefList(QtGui.QDialog):
    """Creates a definition list with one or more terms and descriptions."""
    def __init__(self, other, parentWindow, selection=None):
        super(DefList, self).__init__()
        # other is whatever self is in the other methods
        self.other = other
        self.parentWindow = parentWindow
        self.selection = selection
        self.data = list()
        self.setupUI()

    def setupUI(self):
        self.widget = QtGui.QDialog(self.parentWindow)
        # self.widget.resize(500, 300)
        self.widget.setWindowTitle("Add a definition list")

        self.dt_part = QtGui.QLineEdit(self.widget)
        self.dt_part.setPlaceholderText("definition term")
        dl_part_label = QtGui.QLabel("Definition term:")

        self.dd_part = QtGui.QTextEdit(self.widget)
        self.dd_part.setAcceptRichText(False)
        if self.selection:
            self.dd_part.setText(self.selection)
        dd_part_label = QtGui.QLabel("Definition description:")

        addButton = QtGui.QPushButton("&Add more", self.widget)
        addButton.clicked.connect(self.addMore)

        buttonBox = QtGui.QDialogButtonBox(self.widget)
        buttonBox.addButton(addButton, QtGui.QDialogButtonBox.ActionRole)
        buttonBox.addButton(QtGui.QDialogButtonBox.Ok)
        buttonBox.addButton(QtGui.QDialogButtonBox.Cancel)

        buttonBox.accepted.connect(self.widget.accept)
        buttonBox.rejected.connect(self.widget.reject)

        vbox = QtGui.QVBoxLayout(self.widget)
        vbox.addWidget(dl_part_label)
        vbox.addWidget(self.dt_part)
        vbox.addWidget(dd_part_label)
        vbox.addWidget(self.dd_part)
        vbox.addWidget(buttonBox)

        self.widget.setLayout(vbox)

        if self.widget.exec_() == QtGui.QDialog.Accepted:
            # we won't allow any empty terms
            if not self.dt_part.text() == "":
                self.data.append((self.dt_part.text(), self.dd_part.toPlainText()))

            # if OK button pressed, but empty self.data list
            if not self.data:
                return

            # create all the terms and descriptions
            result = "<dl>"
            for key, value in self.data:
                key = Utility.escape_html_chars(key)
                value = Utility.escape_html_chars(value)
                result = result + "<dt><b>" + key + "</b></dt><dd>" + \
                    value + "</dd>"

            # we need the break <br /> at the end to "get out" of the <dl>
            result = result + "</dl><br />"

            self.other.web.eval("document.execCommand('insertHTML', false, %s);"
                % json.dumps(result))

    def addMore(self):
        """Adds a new definition term and description."""
        if not self.dt_part.text() == "":
            self.data.append((self.dt_part.text(), self.dd_part.toPlainText()))
        self.dt_part.clear()
        self.dd_part.clear()
        self.dt_part.setFocus()

def toggleDefList(self):
    selection = self.web.selectedText()
    dl = DefList(self, self.parentWindow, selection if selection else None)

def create_table_from_selection(self):
    """Create a table out of the selected text."""
    selection = self.web.selectedText()

    # there is no text to make a table from
    if not selection:
        return False

    # there is a single line of text
    if not selection.count("\n"):
        return False

    # there is no content in table
    if all(c in ("|", "\n") for c in selection):
        return False

    # split on newlines
    first = [x for x in selection.split(u"\n") if x]

    # split on pipes
    second = list()
    for elem in first[:]:
        new_elem = [x.strip() for x in elem.split("|")]
        new_elem = [Utility.escape_html_chars(word) for word in new_elem]
        second.append(new_elem)

    # keep track of the max number of cols so as to make all rows of equal len
    max_num_cols = len(max(second, key=len))

    # decide how much horizontal space each column may take
    width = 100 / max_num_cols

    # check for "-|-|-"
    if all(x.strip(":") in ("-", "") for x in second[1]):
        start = 2
        align_line = second[1]
        len_align_line = len(align_line)
        if len_align_line < max_num_cols:
            align_line += ["-"] * (max_num_cols - len_align_line)
        alignments = list()
        for elem in second[1]:
            alignments.append(Utility.check_alignment(elem))
    else:
        alignments = ["left"] * max_num_cols
        start = 1

    # create a table
    head_row = u""
    for elem, alignment in zip(second[0], alignments):
        head_row += (u"<th align=\"{0}\" style=\"width: {1}%; padding: 5px;"
            "border-bottom: 2px solid #00B3FF\">{2}</th>".format(alignment, width, elem))
    extra_cols = u""
    if len(second[0]) < max_num_cols:
        diff = len(second[0]) - max_num_cols
        assert diff < 0, "Difference between len(second[0]) and max_num_cols is positive"
        for alignment in alignments[diff:]:
            extra_cols += (u"<th align=\"{0}\" style=\"width: {1}%; padding: 5px;"
                           "border-bottom: 2px solid #00B3FF\"></th>".format(alignment, width))
    head_row += extra_cols

    body_rows = u""
    for row in second[start:]:
        body_rows += u"<tr>"
        for elem, alignment in zip(row, alignments):
            body_rows += (u"<td style=\"text-align: {0}; padding: 5px; border-bottom:"
                          u"1px solid #B0B0B0\">{1}</td>".format(alignment, elem))
        # if particular row is not up to par with number of cols
        extra_cols = ""
        if len(row) < max_num_cols:
            diff = len(row) - max_num_cols
            assert diff < 0, "Difference between len(row) and max_num_cols is positive"
            for alignment in alignments[diff:]:
                extra_cols += (u"<td style=\"text-align: {0}; padding: 5px; border-bottom:"
                    "1px solid #B0B0B0\"></td>".format(alignment))
        body_rows += extra_cols + "</tr>"

    html = u"""
    <table style="width: 100%; border-collapse: collapse;">
        <thead>
            <tr>
                {0}
            </tr>
        </thead>
        <tbody>
            {1}
        </tbody>
    </table>""".format(head_row, body_rows)

    self.web.eval("document.execCommand('insertHTML', false, %s);"
        % json.dumps(html))

    return None

def toggleTable(self):
    """Set the number of columns and rows for a new table."""

    # if the user has selected text, try to make a table out of it
    if self.web.selectedText():
        ret = self.create_table_from_selection()
        if ret != False:
            return None

    dialog = QtGui.QDialog(self.parentWindow)
    dialog.setWindowTitle("Enter columns and rows")

    form = QtGui.QFormLayout()
    form.addRow(QtGui.QLabel("Enter the number of columns and rows"))

    columnSpinBox = QtGui.QSpinBox(dialog)
    columnSpinBox.setMinimum(1)
    columnSpinBox.setMaximum(10)
    columnSpinBox.setValue(2)
    columnLabel = QtGui.QLabel("Number of columns:")
    form.addRow(columnLabel, columnSpinBox)

    rowSpinBox = QtGui.QSpinBox(dialog)
    rowSpinBox.setMinimum(1)
    rowSpinBox.setMaximum(20)
    rowSpinBox.setValue(3)
    rowLabel = QtGui.QLabel("Number of rows:")
    form.addRow(rowLabel, rowSpinBox)

    buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok |
        QtGui.QDialogButtonBox.Cancel, QtCore.Qt.Horizontal, dialog)

    buttonBox.accepted.connect(dialog.accept)
    buttonBox.rejected.connect(dialog.reject)

    form.addRow(buttonBox)

    dialog.setLayout(form)

    if dialog.exec_() == QtGui.QDialog.Accepted:

        num_columns = columnSpinBox.value()
        num_rows = rowSpinBox.value() - 1

        num_header = Utility.counter(start=1, step=1)
        num_data = Utility.counter(start=1, step=1)

        # set width of each column equal
        width = 100 / num_columns

        header_column = "".join("<th align=\"left\" style=\"width: {0}%; padding: 5px;"
            "border-bottom: 2px solid #00B3FF\">header{1}</th>".format(width,
                next(num_header)) for _ in xrange(num_columns))
        body_column = "".join("<td style=\"padding: 5px; border-bottom:"
            "1px solid #B0B0B0\">data{}</td>".format(next(num_data))
            for _ in xrange(num_columns))
        body_row = "<tr>{}</tr>".format(body_column) * num_rows

        html = """
        <table style="width: 100%; border-collapse: collapse;">
            <thead><tr>{0}</tr></thead>
            <tbody>{1}</tbody>
        </table>""".format(header_column, body_row)

        self.web.eval("document.execCommand('insertHTML', false, %s);"
            % json.dumps(html))

def setup_background_button(self, but):
    self.background_frame = QtGui.QFrame()
    self.background_frame.setAutoFillBackground(True)
    self.background_frame.setFocusPolicy(QtCore.Qt.NoFocus)
    self.bg_color = preferences.prefs.get("last_bg_color", "#00f")
    self.on_bg_color_changed()
    hbox = QtGui.QHBoxLayout()
    hbox.addWidget(self.background_frame)
    hbox.setMargin(5)
    but.setLayout(hbox)

# use last background color
def on_background(self):
    self._wrap_with_bg_color(self.bg_color)

# choose new color
def on_change_col(self):
    new = QtGui.QColorDialog.getColor(QtGui.QColor(self.bg_color), None)
    # native dialog doesn't refocus us for some reason
    self.parentWindow.activateWindow()
    if new.isValid():
        self.bg_color = new.name()
        self.on_bg_color_changed()
        self._wrap_with_bg_color(self.bg_color)

def _update_background_button(self):
    self.background_frame.setPalette(QtGui.QPalette(QtGui.QColor(self.bg_color)))

def on_bg_color_changed(self):
    self._update_background_button()
    preferences.prefs["last_bg_color"] = self.bg_color
    preferences.save_prefs()

def _wrap_with_bg_color(self, color):
    """Wrap the selected text in an appropriate tag with a background color."""
    # On Linux, the standard 'hiliteColor' method works. On Windows and OSX
    # the formatting seems to get filtered out by Anki itself

    self.web.eval("""
        if (!setFormat('hiliteColor', '%s')) {
            setFormat('backcolor', '%s');
        }
        """ % (color, color))

    if not const.PLATFORM.startswith("linux"):
        # remove all Apple style classes thus enabling
        # text highlighting for other platforms besides Linux
        self.web.eval("""
        var matches = document.querySelectorAll(".Apple-style-span");
        for (var i = 0; i < matches.length; i++) {
            matches[i].removeAttribute("class");
        }
        """)


def power_remove_format(self):
    """Remove formatting from selected text."""
    # For Windows and OS X we need to override the standard removeFormat
    # method, because it currently doesn't work as it should in (Anki 2.0.31).
    # Specifically, the background-color <span> gives trouble. This method
    # should work fine in all but a few rare cases that are easily avoided,
    # such as a <pre> at the beginning of the HTML.

    selection = self.web.selectedText()

    # normal removeFormat method
    self.web.eval("setFormat('removeFormat');")

    self.web.eval("setFormat('selectAll')")
    complete_sel = self.web.selectedText()

    # if we have selected the complete card, we can remove more thoroughly
    if selection == complete_sel:
        self.remove_garbage()

    # deselect all text
    self.web.eval("window.getSelection().removeAllRanges();")

    if const.PLATFORM.startswith("linux"):
        # refocus on the field we're editing
        self.web.eval("focusField(%d);" % self.currentField)
        return

    # reload the note: this is needed on OS X and possibly Windows to
    # display in the editor that the markup is indeed gone
    self.loadNote()

    self.saveNow()
    self.web.setFocus()
    self.web.eval("focusField(%d);" % self.currentField)

def remove_garbage(self):
    """Remove HTML that doesn't get deleted automatically."""
    self.saveNow()
    self.web.setFocus()
    self.web.eval("focusField(%d);" % self.currentField)

    html = self.note.fields[self.currentField]
    soup = BeautifulSoup.BeautifulSoup(html)

    print "Old soup:", repr(soup)

    for tag in const.HEADING_TAGS + const.HTML_TAGS:
        for match in soup.findAll(tag):
            match.replaceWithChildren()

    print "New soup:", repr(soup)

    self.note.fields[self.currentField] = unicode(soup)
    self.loadNote()

def toggleBlockquote(self):
    self.web.eval("setFormat('formatBlock', 'blockquote');")

def justifyCenter(self):
    self.web.eval("setFormat('justifyCenter');")

def justifyLeft(self):
    self.web.eval("setFormat('justifyLeft');")

def justifyRight(self):
    self.web.eval("setFormat('justifyRight');")

def justifyFull(self):
    self.web.eval("setFormat('justifyFull');")

def toggleHeading(self):
    selection = self.web.selectedHtml()
    if not selection:
        # if no text is selected, show a dialog
        self.create_custom_heading()
        return
    print "HTML before:\t", repr(selection)
    soup = BeautifulSoup.BeautifulSoup(selection)
    size = Utility.check_size_heading(soup.text)
    print "size:\t", repr(size)
    if size == -1:
        self.create_custom_heading(soup.text)
        return
    # remove all headings from selection
    for tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
        for match in soup.findAll(tag):
            match.replaceWithChildren()

    # delete leading hashes
    relevant_text = soup.text[size:]
    relevant_text = Utility.strip_leading_whitespace(relevant_text)

    # wrap new heading around the selection
    result_soup = BeautifulSoup.BeautifulSoup()
    tag = BeautifulSoup.Tag(result_soup, "h{0!s}".format(size))
    result_soup.insert(0, tag)
    tag.insert(0, relevant_text)

    print "Resultant soup:", repr(result_soup)

    self.web.eval("document.execCommand('insertHTML', false, %s);"
        % json.dumps(unicode(result_soup)))

    self.cleanup_headers()

def create_custom_heading(self, selected_text=None):
    dialog = QtGui.QDialog(self.parentWindow)
    dialog.setWindowTitle("Create custom heading")

    text_label = QtGui.QLabel("Text:", dialog)
    text_line_edit = QtGui.QLineEdit(dialog)
    if selected_text:
        text_line_edit.setText(selected_text)

    text_hbox = QtGui.QHBoxLayout()
    text_hbox.addWidget(text_label)
    text_hbox.addWidget(text_line_edit)

    stylesheet = """
    QGroupBox { border: 1px inset lightgrey;
                        border-radius: 5px;
                        margin-top: 10px;
                        font-weight: bold; }
    QGroupBox::title {  subcontrol-origin: margin;
                        subcontrol-position: top;
                        padding:0 3px 0 3px; }
    """

    groupbox = QtGui.QGroupBox("Choose a size", dialog)
    groupbox.setStyleSheet(stylesheet)

    radio_button1 = QtGui.QRadioButton("Biggest", dialog)
    radio_button1.setChecked(True)
    radio_button2 = QtGui.QRadioButton("Big", dialog)
    radio_button3 = QtGui.QRadioButton("Medium", dialog)
    radio_button4 = QtGui.QRadioButton("Small", dialog)
    radio_button5 = QtGui.QRadioButton("Smaller", dialog)
    radio_button6 = QtGui.QRadioButton("Tiny", dialog)

    radio_button_group = QtGui.QButtonGroup(dialog)
    radio_button_group.addButton(radio_button1)
    radio_button_group.setId(radio_button1, 1)
    radio_button_group.addButton(radio_button2)
    radio_button_group.setId(radio_button2, 2)
    radio_button_group.addButton(radio_button3)
    radio_button_group.setId(radio_button3, 3)
    radio_button_group.addButton(radio_button4)
    radio_button_group.setId(radio_button4, 4)
    radio_button_group.addButton(radio_button5)
    radio_button_group.setId(radio_button5, 5)
    radio_button_group.addButton(radio_button6)
    radio_button_group.setId(radio_button6, 6)

    radio_hbox = QtGui.QHBoxLayout()
    radio_hbox.addWidget(radio_button1)
    radio_hbox.addWidget(radio_button2)
    radio_hbox.addWidget(radio_button3)
    radio_hbox.addWidget(radio_button4)
    radio_hbox.addWidget(radio_button5)
    radio_hbox.addWidget(radio_button6)

    groupbox.setLayout(radio_hbox)

    button_box = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok |
        QtGui.QDialogButtonBox.Cancel, QtCore.Qt.Horizontal, dialog)

    button_box.accepted.connect(dialog.accept)
    button_box.rejected.connect(dialog.reject)

    vbox = QtGui.QVBoxLayout()
    vbox.addLayout(text_hbox)
    vbox.addStretch(1)
    vbox.addWidget(groupbox)
    vbox.addWidget(button_box)

    vbox.setSizeConstraint(QtGui.QLayout.SetFixedSize)

    dialog.setLayout(vbox)

    if dialog.exec_() == QtGui.QDialog.Accepted:
        text = unicode(text_line_edit.text())
        # print "Text:", repr(text)
        size_heading = radio_button_group.id(radio_button_group.checkedButton())
        heading_tag = "h" + str(size_heading)
        # print "Checked button:", repr(size_heading)
        if text == "":
            return
        else:
            text = Utility.escape_html_chars(text)
            start_tag = "<{0}>".format(heading_tag)
            end_tag = "</{0}>".format(heading_tag)
            if selected_text:
                self.web.eval("wrap('{0}', '{1}')".format(start_tag, end_tag))
                self.cleanup_headers()
            else:
                result = u"{0}{1}{2}".format(start_tag, text, end_tag)
                # print "RESULT:", result
                self.web.eval("document.execCommand('insertHTML', false, %s);"
                    % json.dumps(unicode(result)))

def cleanup_headers(self):
    """Clean up empty headers from the card."""
    self.saveNow()
    self.web.setFocus()
    self.web.eval("focusField(%d);" % self.currentField)

    html = self.note.fields[self.currentField]
    # print "HTML:", html
    soup = BeautifulSoup.BeautifulSoup(html)

    for tag in const.HEADING_TAGS:
        print tag
        for match in soup.findAll(tag):
            print "match.parent.name:", match.parent.name
            if match.parent.name in const.HEADING_TAGS:
                match.parent.replaceWithChildren()

    # print "Result HTML:", soup

    self.note.fields[self.currentField] = unicode(soup)
    self.loadNote()

def toggleAbbreviation(self):
    selected = self.web.selectedText()
    abbreviation = Abbreviation(self, self.parentWindow, selected)

editor.Editor.toggleAbbreviation = toggleAbbreviation
editor.Editor.remove_garbage = remove_garbage
editor.Editor.cleanup_headers = cleanup_headers
editor.Editor.create_custom_heading = create_custom_heading
editor.Editor.toggleHeading = toggleHeading
editor.Editor.unlink = unlink
editor.Editor.justifyFull = justifyFull
editor.Editor.justifyRight = justifyRight
editor.Editor.justifyLeft = justifyLeft
editor.Editor.justifyCenter = justifyCenter
editor.Editor.toggleBlockquote = toggleBlockquote
editor.Editor.removeFormat = power_remove_format
editor.Editor.on_background = on_background
editor.Editor.setup_background_button = setup_background_button
editor.Editor.on_bg_color_changed = on_bg_color_changed
editor.Editor._update_background_button = _update_background_button
editor.Editor.on_change_col = on_change_col
editor.Editor._wrap_with_bg_color = _wrap_with_bg_color
editor.Editor.create_table_from_selection = create_table_from_selection
editor.Editor.enable_ok_button = enable_ok_button
editor.Editor.insert_anchor = insert_anchor
editor.Editor.create_hyperlink = create_hyperlink
editor.Editor.wrap_in_tags = wrap_in_tags
editor.Editor.toggleOrderedList = toggleOrderedList
editor.Editor.toggleUnorderedList = toggleUnorderedList
editor.Editor.toggleStrikeThrough = toggleStrikeThrough
editor.Editor.togglePre = togglePre
editor.Editor.toggleHorizontalLine = toggleHorizontalLine
editor.Editor.toggleIndent = toggleIndent
editor.Editor.toggleOutdent = toggleOutdent
editor.Editor.toggleDefList = toggleDefList
editor.Editor.toggleTable = toggleTable
editor.Editor.setupButtons = wrap(editor.Editor.setupButtons, setup_buttons)

preferences = Preferences(mw)
mw.ExtraButtons_Options = ExtraButtons_Options(mw, preferences)
mw.ExtraButtons_Options.setup_extra_buttons_options()
