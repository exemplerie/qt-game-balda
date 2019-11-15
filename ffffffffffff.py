from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import QtGui

import sqlite3
import copy
import pymorphy2
import random
import sys

ALPHABIT = list('АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ')
STATUSES = {0: 'Выберите букву и вставьте ее \nв свободную клетку.', 1: 'Покажите слово от первой \nдо последней буквы.',
            2: 'Конец игры.'}
MORPH = pymorphy2.MorphAnalyzer()
PLAYERS = ['player1', 'player2']


class Pos(QWidget):
    def __init__(self, x, y, f):
        super(Pos, self).__init__()

        self.setMouseTracking(True)

        self.setFixedSize(QSize(500 // f, 500 // f))

        self.is_filled = False
        self.prom_fill = False
        self.is_letter = False
        self.letter = None

        self.x = x
        self.y = y

    def set_letter(self, letter):
        if not self.is_letter:
            if letter:
                self.is_letter = True
                self.letter = letter
                self.update()

    def reset(self):
        self.is_filled = False
        self.letter = None
        self.is_letter = False
        self.update()

    def paintEvent(self, event):
        qp = QPainter(self)
        qp.setRenderHint(QPainter.Antialiasing)
        colors = [QColor('#faf694'), QColor('#f7d15f')]

        r = event.rect()

        if self.is_filled or self.prom_fill:
            color = colors[window.current_player]
            outer, inner = Qt.black, color
        else:
            outer, inner = Qt.black, QColor('#D7D7D7')

        qp.fillRect(r, QBrush(inner))
        pen = QPen(outer)
        pen.setWidth(1)
        qp.setPen(pen)
        qp.drawRect(r)

        if self.is_letter:
            qp.setPen(Qt.black)
            qp.setFont(QFont("Arial", 30))
            qp.drawText(r, Qt.AlignCenter, self.letter)

    def enterEvent(self, e):
        self.prom_fill = True
        self.update()

    def leaveEvent(self, e):
        self.prom_fill = False
        window.update()

    def highlighting(self):
        if self.is_letter:
            if len(window.current_word) > 0:
                comp_cell = window.current_word[len(window.current_word) - 1]
                if self not in window.current_word and ((comp_cell.x == self.x and abs(self.y - comp_cell.y) == 1) or (
                        comp_cell.y == self.y and abs(self.x - comp_cell.x) == 1)):
                    window.current_word.append(self)
                    self.is_filled = True
            else:
                window.current_word.append(self)
                self.is_filled = True
            self.update()
        print([j.letter for j in window.current_word])



    def mousePressEvent(self, e):
        print(window.game_status)
        if (e.button() == Qt.LeftButton) and window.game_status == STATUSES[0]:
            if not self.is_letter and window.remembered_alphabit_letter and window.field.check_heighbor_cells(self):
                self.set_letter(window.remembered_alphabit_letter)
                window.field.last_letter = (self.x, self.y)
                self.update()
                window.game_status = STATUSES[1]
                window.set_guide()
        elif (e.button() == Qt.LeftButton) and window.game_status == STATUSES[1]:
            self.highlighting()
        window.set_guide()


class Field(QWidget):
    def __init__(self, word, field):
        super(Field, self).__init__()
        self.f_size = field
        print(self.f_size)
        self.setMouseTracking(True)
        self.word = word
        self.grid = QGridLayout()
        self.grid.setSpacing(0)
        self.setLayout(self.grid)
        self.grid.setHorizontalSpacing(0)
        self.orig_cells_objects = [[None for j in range(self.f_size)] for i in range(self.f_size)]
        self.last_letter = None
        self.init_map()
        self.cells_objects = copy.copy(self.orig_cells_objects)

    def init_map(self):
        for x in range(0, self.f_size):
            for y in range(0, self.f_size):
                a = Pos(x, y, self.f_size)
                if x == self.f_size // 2:
                    a.set_letter(self.word[y])
                self.grid.addWidget(a, x, y)
                self.orig_cells_objects[x][y] = a

    def reset_map(self):
        for x in range(0, self.f_size):
            for y in range(0, self.f_size):
                self.cells_objects[x][y].is_filled = False

    def check_heighbor_cells(self, cell):
        if cell.x > 0:
            if self.cells_objects[cell.x - 1][cell.y].is_letter:
                return True
        if cell.y > 0:
            if self.cells_objects[cell.x][cell.y - 1].is_letter:
                return True
        if cell.x < 4:
            if self.cells_objects[cell.x + 1][cell.y].is_letter:
                return True
        if cell.y < 4:
            if self.cells_objects[cell.x][cell.y + 1].is_letter:
                return True
        return False


class MainWindow(QWidget):
    def __init__(self, *args):
        super(MainWindow, self).__init__()
        self.field_size = 5
        if args:
            self.players = args[0]
            self.field_size = int(args[1])
        else:
            self.players = ['player1', 'player2']
        self.remembered_alphabit_letter = None
        self.current_word = []
        self.game_status = STATUSES[0]
        self.current_player = 0
        self.p_counts = [0, 0]
        self.p_words = {0: [], 1:[]}

        self.field = Field(self.generate_word(), self.field_size)
        self.setGeometry(100, 100, 900, 700)

        self.table = QTableWidget(self)
        self.table.setColumnCount(2)
        self.table.setMaximumSize(500, 250)
        self.table.setHorizontalHeaderLabels(self.players)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)

        self.word_description = QPlainTextEdit(self)
        self.word_description.setReadOnly(True)
        self.word_description.setMaximumSize(500, 250)

        self.counts = QLabel(self)
        self.counts.setText(str(self.p_counts[0]) + ' : ' + str(self.p_counts[1]))
        self.counts.setMaximumSize(130, 100)
        font2 = QtGui.QFont()
        font2.setFamily('LuzSans-Book')
        font2.setPointSize(30)
        self.counts.setFont(font2)

        self.guide_label = QLabel()
        font = QtGui.QFont()
        font.setFamily('Tw Cen MT')
        font.setPointSize(12)
        self.guide_label.setFont(font)
        self.now_move = QLabel(self)
        self.now_move.setText('Сейчас ход: ' + self.players[self.current_player])
        font3 = QtGui.QFont()
        font3.setFamily('LuzSans-Book')
        font3.setPointSize(20)
        self.now_move.setFont(font3)


        self.delete_letter_btn = QPushButton(self)
        self.delete_letter_btn.setText('Удалить букву')
        self.delete_letter_btn.setMinimumSize(100, 50)
        self.delete_letter_btn.setEnabled(False)
        self.delete_letter_btn.clicked.connect(self.delete_letter)
        self.delete_word_btn = QPushButton(self)
        self.delete_word_btn.setText('Удалить слово')
        self.delete_word_btn.setMinimumSize(100, 50)
        self.delete_word_btn.setEnabled(False)
        self.delete_word_btn.clicked.connect(self.delete_word)
        self.add_word_btn = QPushButton(self)
        self.add_word_btn.setMinimumSize(100, 50)
        self.add_word_btn.clicked.connect(self.make_a_move)
        self.pass_move_btn = QPushButton()
        self.pass_move_btn.setText('Пропустить ход')
        self.pass_move_btn.setMinimumSize(100, 50)
        self.pass_move_btn.clicked.connect(self.pass_move)
        self.new_game_btn = QPushButton(self)
        self.new_game_btn.setText('Начать заново')
        self.new_game_btn.setMinimumSize(100, 50)
        self.new_game_btn.clicked.connect(self.close)
        self.new_game_btn.hide()

        self.main_vb = QVBoxLayout(self)
        self.upper_hb = QHBoxLayout(self)
        self.table_vb = QVBoxLayout(self)
        self.btn_vb = QVBoxLayout(self)
        self.btn_vb.setGeometry(QRect(0, 0, 0 ,0))
        self.game_field_vb = QVBoxLayout(self)
        self.count_hb = QHBoxLayout(self)
        self.count_hb.addWidget(self.counts)

        self.main_vb.addLayout(self.upper_hb)
        self.upper_hb.addLayout(self.game_field_vb)
        self.game_field_vb.addStretch(1)
        self.game_field_vb.addWidget(self.field)
        self.game_field_vb.addStretch(1)
        self.upper_hb.addLayout(self.btn_vb)
        self.btn_vb.addWidget(self.now_move)
        self.btn_vb.addWidget(self.guide_label)
        self.btn_vb.addWidget(self.add_word_btn)
        self.btn_vb.addWidget(self.delete_letter_btn)
        self.btn_vb.addWidget(self.delete_word_btn)
        self.btn_vb.addWidget(self.pass_move_btn)
        self.upper_hb.addLayout(self.table_vb)
        self.table_vb.addLayout(self.count_hb)
        self.table_vb.addWidget(self.table)
        self.table_vb.addWidget(self.word_description)
        self.main_vb.setSpacing(50)

        self.setLayout(self.main_vb)

        self.init_alphabit()
        self.set_guide()
        self.game_over()
        self.setFont(font)

    def reset_map(self):
        for x in range(0, self.field_size):
            for y in range(0, self.field_size):
                w = self.grid.itemAtPosition(y, x).widget()
                w.reset()

    def init_alphabit(self):
        a = QWidget(self)
        a.grid = QGridLayout(self)
        a.grid.setSpacing(0)
        a.setLayout(a.grid)
        for x in range(0, 3):
            for y in range(0, 13):
                new = QPushButton(self)
                new.setText(ALPHABIT[x * 10 + y])
                new.setMinimumSize(0, 50)
                font = QtGui.QFont()
                font.setPointSize(20)
                font.setWeight(50)
                new.setFont(font)
                new.clicked.connect(self.alphabit_letter_is_pressed)
                a.grid.addWidget(new, x, y)
        self.main_vb.addWidget(a)

    def generate_word(self):
        global cur
        result = cur.execute("""SELECT * FROM words WHERE LENGTH(word)=""" + str(self.field_size)).fetchall()
        self.first_word = random.choice(result)[1]
        return self.first_word

    def alphabit_letter_is_pressed(self):
        self.remembered_alphabit_letter = self.sender().text()

    def set_guide(self):
        self.guide_label.setText(self.game_status)
        if self.game_status == STATUSES[0] or self.game_status == STATUSES[1]:
            self.add_word_btn.hide()
        if self.game_status == STATUSES[1] :
            self.delete_letter_btn.setEnabled(True)
            if self.current_word:
                self.add_word_btn.show()
                self.add_word_btn.setText(''.join([x.letter for x in self.current_word]))
                self.delete_word_btn.setEnabled(True)

    def make_a_move(self):
        if self.game_status == STATUSES[1]:
            word = ''.join(j.letter for j in self.current_word)
            if self.check_word(word) and self.field.cells_objects[self.field.last_letter[0]][self.field.last_letter[1]] in self.current_word:
                self.p_counts[self.current_player] += len(word)
                self.p_words[self.current_player].append(word)
                self.set_description(word.lower())
                self.player_change()
                self.game_over()
            else:
                self.guide_label.setText('Подумайте еще раз!')
                self.guide_label.update()
                self.delete_word()

    def check_word(self, word):
        global cur
        result = cur.execute("""SELECT * FROM words
                    WHERE word = ?""",(word,)).fetchone()
        global cur2
        result_2 = cur2.execute("""SELECT * FROM ozhigov
                    WHERE word = ?""",(word.lower(),)).fetchone()
        if (result or result_2) and word not in self.p_words[0] and word not in self.p_words[1] and word != self.first_word:
            return True
        return False

    def update_table(self):
        self.table.setRowCount(len(self.p_words[0]))
        self.table.setItem(len(self.p_words[0]) - 1, self.current_player, QTableWidgetItem(self.p_words[self.current_player][len(self.p_words[0]) - 1]))


    def player_change(self):
        if not self.current_word:
            self.p_words[self.current_player].append('-')
        self.update_table()
        self.counts.setText(str(self.p_counts[0]) + ' : ' + str(self.p_counts[1]))
        if self.current_player == 0:
            self.current_player = 1
        else:
            self.current_player = 0
        self.field.last_letter = None
        self.delete_word()
        self.field.orig_cells_objects = self.field.cells_objects
        self.remembered_alphabit_letter = None
        self.now_move.setText('Сейчас ход: ' + self.players[self.current_player])
        self.delete_letter_btn.setEnabled(False)
        self.game_status = STATUSES[0]
        self.set_guide()

    def delete_letter(self):
        self.field.cells_objects[self.field.last_letter[0]][self.field.last_letter[1]].reset()
        self.game_status = STATUSES[0]
        self.delete_word()
        self.set_guide()
        self.delete_letter_btn.setEnabled(False)

    def delete_word(self):
        self.current_word = []
        self.field.reset_map()
        self.field.update()
        self.add_word_btn.hide()
        self.delete_word_btn.setEnabled(False)

    def pass_move(self):
        if self.field.last_letter:
            self.delete_letter()
        self.player_change()

    def game_over(self):
        if all(z.is_letter for z in [self.field.orig_cells_objects[x][y] for x in range(self.field_size) for y in range(self.field_size)]):
            if self.p_counts[0] == self.p_counts[1]:
                self.now_move.setText('Ничья.')
            else:
                winner = self.p_counts.index(max(self.p_counts))
                self.now_move.setText('Поздравляем, ' + self.players[winner] + '!\nВы победили!')
            self.delete_word_btn.hide()
            self.delete_letter_btn.hide()
            self.add_word_btn.hide()
            self.pass_move_btn.hide()
            self.btn_vb.addWidget(self.new_game_btn)
            self.new_game_btn.show()
            self.game_status = STATUSES[2]

    def set_description(self, word):
        global cur2
        result_2 = cur2.execute("""SELECT * FROM ozhigov
                            WHERE word = ?""", (word.lower(),)).fetchone()
        if result_2:
            des = ' '.join(str(result_2[2][2:]).split('\\n'))
            self.word_description.setPlainText(des)
        else:
            self.word_description.setPlainText('Извините, данное слово отсутсвует в словаре.')


class Begining_Window(QWidget):
    def __init__(self):
        super().__init__()
        self.setGeometry(250, 250, 600, 480)

        m_f = QtGui.QFont()
        m_f.setFamily('Candara')
        m_f.setPointSize(12)
        self.setFont(m_f)

        self.main_label = QLabel(self)
        self.main_label.setText('БАЛДА')
        font = QtGui.QFont()
        font.setFamily('Courier New')
        font.setPointSize(75)
        self.main_label.setFont(font)
        self.setFixedSize(600, 480)
        self.choice = QComboBox(self)
        self.choice.addItems(["3 x 3", "5 x 5", "7 x 7"])
        self.choice.setCurrentIndex(1)
        self.choice.setGeometry(100, 270, 150, 31)
        self.label = QLabel(self)
        self.label.setText('Выберите поле для игры:')
        self.label.setGeometry(100, 230, 200, 20)
        self.name1 = QLabel(self)
        self.name1.setText('Имя первого игрока:')
        self.name2 = QLabel(self)
        self.name2.setText('Имя второго игрока:')
        self.vvod1 = QLineEdit(self)
        self.vvod2 = QLineEdit(self)
        self.name1.setGeometry(340, 200, 150, 20)
        self.name2.setGeometry(340, 290, 150, 20)
        self.vvod1.setGeometry(340, 240, 160, 30)
        self.vvod2.setGeometry(340, 320, 160, 30)
        self.play = QPushButton(self)
        self.play.setGeometry(180, 390, 250, 50)
        self.play.setText('Начать игру')
        self.play.clicked.connect(self.open_second_form)
        self.rules = QPushButton(self)
        self.rules.setGeometry(480, 20, 100, 30)
        self.rules.setText('Правила')
        self.main_label.setGeometry(150, 40, 361, 161)
        self.names = ['player1', 'player2']
        self.rules.clicked.connect(self.open_rules)

    def open_rules(self):
        self.window_rules = Rules()
        self.window_rules.show()

    def open_second_form(self):
        field = self.choice.currentText()
        if self.vvod1.text():
            self.names[0] = self.vvod1.text()
        if self.vvod2.text():
            self.names[1] = self.vvod2.text()
        self.second_form = window
        window.__init__(self.names, field[0])
        self.second_form.show()

class Rules(QWidget):
    def __init__(self):
        super().__init__()
        self.setGeometry(250, 250, 520, 400)
        f = open('rules.txt').read()
        text = QPlainTextEdit(self)
        text.setGeometry(10, 10, 500, 380)
        text.setPlainText(f)
        text.setReadOnly(True)



if __name__ == '__main__':
    con = sqlite3.connect("dic3.db")
    con2 = sqlite3.connect("ozhigov.db")
    cur = con.cursor()
    cur2 = con2.cursor()
    app = QApplication(sys.argv)
    window = MainWindow()
    window2 = Begining_Window()
    window2.show()
    sys.exit(app.exec())
