from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import QtGui

import sqlite3
import copy
import random
import sys

ALPHABIT = list('АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ')
STATUSES = {0: 'Выберите букву и вставьте ее \nв свободную клетку.',
            1: 'Покажите слово от первой \nдо последней буквы. Для отмены \nнажмите правой кнопкой мыши.',
            2: 'Конец игры.'}


class Cell_class(QWidget):  # класс для клеток с буквами
    def __init__(self, x, y, f):
        super(Cell_class, self).__init__()

        self.setFixedSize(QSize(500 // f, 500 // f))

        self.is_filled = False  # закрашена (выбрана)
        self.move_fill = False  # закрашена из-за наведения мышкой
        self.is_letter = False  # есть ли буква внутри
        self.letter = None  # какая буква

        self.x = x  # координаты на сетке клеток (класс Field)
        self.y = y

    def set_letter(self, letter):  # для установки буквы в клетку
        if not self.is_letter and letter:
            self.is_letter = True
            self.letter = letter
            self.update()

    def reset(self):  # приводит к первоначальному (стандартному) виду
        self.is_filled = False
        self.letter = None
        self.is_letter = False
        self.update()

    def paintEvent(self, event):  # функция отрисовки клетки
        qp = QPainter(self)
        qp.setRenderHint(QPainter.Antialiasing)
        colors = [QColor('#97C5D8'), QColor('#FFB180')]

        r = event.rect()

        if self.is_filled or self.move_fill:  # закрашивается при наведении или выделении (нажатии)
            color = colors[window.current_player]
            outer, inner = Qt.black, color
        else:
            outer, inner = Qt.black, QColor('#FEFDF5')

        qp.fillRect(r, QBrush(inner))
        pen = QPen(outer)
        pen.setWidth(1)
        qp.setPen(pen)
        qp.drawRect(r)

        if self.is_letter:  # вставить букву
            qp.setPen(Qt.black)
            qp.setFont(QFont("Arial", 30))
            qp.drawText(r, Qt.AlignCenter, self.letter)

    def enterEvent(self, e):  # наведение мышкой в область клетки (для закрашивания)
        self.move_fill = True
        self.update()

    def leaveEvent(self, e):  # выход мышки из области клетки
        self.move_fill = False
        window.update()

    def highlighting(self):  # проверяет, можно ли выбрать клетку (если есть буква и она рядом с другими выделенными)
        if self.is_letter:
            if len(window.current_word) > 0:
                comp_cell = window.current_word[len(window.current_word) - 1]
                if self not in window.current_word and ((comp_cell.x == self.x and abs(self.y - comp_cell.y) == 1) or (
                        comp_cell.y == self.y and abs(self.x - comp_cell.x) == 1)):
                    window.current_word.append(self)
                    self.is_filled = True
            else:
                window.current_word.append(self)  # добавляет букву в конец вводимого слова
                self.is_filled = True
            self.update()

    def mousePressEvent(self, e):  # варианты при нажатии
        if (e.button() == Qt.LeftButton) and window.game_status == STATUSES[0]:  # вставление буквы
            if not self.is_letter and window.remembered_alphabit_letter.text() and window.field.check_heighbor_cells(
                    self):
                self.set_letter(window.remembered_alphabit_letter.text())  # вставляет выбранную из алфавита букву
                window.field.last_letter = self
                self.update()
                window.game_status = STATUSES[1]
                window.set_guide()
        elif window.game_status == STATUSES[1]:
            if (e.button() == Qt.LeftButton):  # выделение клетки (добавление буквы к текущему слову)
                self.highlighting()
            if (e.button() == Qt.RightButton):  # удаление клетки из текущего слова
                if self.is_filled and self == window.current_word[len(window.current_word) - 1]:
                    window.current_word = window.current_word[:len(window.current_word) - 1]
                    self.is_filled = False
                    self.update()
                if not window.current_word and self == window.field.last_letter:  # удаление буквы из клетки
                    window.delete_letter()

        window.set_guide()


class Field(QWidget):  # класс игрового поля
    def __init__(self, word, field):
        super(Field, self).__init__()
        self.f_size = field  # размер (сколько на сколько ячеек)
        self.word = word  # изначальное слово (по середине)
        self.grid = QGridLayout()
        self.grid.setSpacing(0)
        self.setLayout(self.grid)
        self.grid.setHorizontalSpacing(0)
        self.orig_cells_objects = [[None for j in range(self.f_size)] for i in range(self.f_size)]  # массив клеток
        self.last_letter = None
        self.init_map()
        self.cells_objects = copy.copy(self.orig_cells_objects)  # промежуточный массив клеток
        self.setMaximumSize(520, 520)

    def init_map(self):  # создание поля
        for x in range(0, self.f_size):
            for y in range(0, self.f_size):
                a = Cell_class(x, y, self.f_size)
                if x == self.f_size // 2:
                    a.set_letter(self.word[y])
                self.grid.addWidget(a, x, y)
                self.orig_cells_objects[x][y] = a

    def reset_map(self):  # сброс поля
        for x in range(0, self.f_size):
            for y in range(0, self.f_size):
                self.cells_objects[x][y].is_filled = False

    def check_heighbor_cells(self, cell):  # проверяет, есть ли рядом с выбранной клеткой другие с буквами
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
    def __init__(self, field=5, name1='player1', name2='player2'):
        super(MainWindow, self).__init__()
        self.field_size = field  # размер поля
        self.players = [name1, name2]  # имена игроков
        self.remembered_alphabit_letter = None  # последняя выбранная из алфавита буква
        self.current_word = []  # текущее набираемое слово
        self.game_status = STATUSES[0]  # текущий статус игры
        self.current_player = 0  # чей ход
        self.p_counts = [0, 0]  # счет игры
        self.p_words = {0: [], 1: []}  # все веденные слова

        self.field = Field(self.generate_word(), self.field_size)  # создание поля
        self.setGeometry(100, 100, 900, 700)

        self.table = QTableWidget(self)  # таблица веденных слов
        self.table.setColumnCount(2)
        self.table.setMaximumSize(self.width() // 2, 250)
        self.table.setHorizontalHeaderLabels(self.players)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)

        self.word_description = QPlainTextEdit(self)  # определение слова из словаря
        self.word_description.setReadOnly(True)
        self.word_description.setMaximumSize(self.width() // 2, 250)

        self.counts = QLabel(self)  # счет
        self.counts.setText(str(self.p_counts[0]) + ' : ' + str(self.p_counts[1]))
        self.counts.setMaximumSize(130, 100)
        font2 = QtGui.QFont()
        font2.setFamily('LuzSans-Book')
        font2.setPointSize(30)
        self.counts.setFont(font2)

        self.guide_label = QLabel()  # надпись-руководство (какой сейчас момент игры: ввод, смена хода и т.д.)
        font = QtGui.QFont()
        font.setFamily('Tw Cen MT')
        font.setPointSize(12)
        self.guide_label.setFont(font)
        self.now_move = QLabel(self)  # надпись, кто сейчас ходит
        self.now_move.setText('Сейчас ход: ' + self.players[self.current_player])
        font3 = font2
        font3.setPointSize(20)
        self.now_move.setFont(font3)

        self.delete_letter_btn = QPushButton(self)  # кнопка - удаление буквы
        self.delete_letter_btn.setText('Удалить букву')
        self.delete_letter_btn.setMinimumSize(100, 50)
        self.delete_letter_btn.setEnabled(False)
        self.delete_letter_btn.clicked.connect(self.delete_letter)
        self.delete_word_btn = QPushButton(self)  # кнопка - удаление слова
        self.delete_word_btn.setText('Удалить слово')
        self.delete_word_btn.setMinimumSize(100, 50)
        self.delete_word_btn.setEnabled(False)
        self.delete_word_btn.clicked.connect(self.delete_word)
        self.add_word_btn = QPushButton(self)  # кнопка - добавление слова
        self.add_word_btn.setMinimumSize(100, 50)
        self.add_word_btn.clicked.connect(self.make_a_move)
        self.pass_move_btn = QPushButton()  # кнопка - пропуск хода
        self.pass_move_btn.setText('Пропустить ход')
        self.pass_move_btn.setMinimumSize(100, 50)
        self.pass_move_btn.clicked.connect(self.pass_move)
        self.new_game_btn = QPushButton(self)  # кнопка - новая игра (при окончании предыдущей)
        self.new_game_btn.setText('Начать заново')
        self.new_game_btn.setMinimumSize(100, 50)
        self.new_game_btn.clicked.connect(self.close)
        self.new_game_btn.hide()

        self.main_vb = QVBoxLayout(self)  # блоки для отображения виджетов
        self.upper_hb = QHBoxLayout(self)
        self.table_vb = QVBoxLayout(self)
        self.btn_vb = QVBoxLayout(self)
        self.game_field_vb = QVBoxLayout(self)
        self.count_hb = QHBoxLayout(self)
        self.count_hb.addWidget(self.counts)

        self.main_vb.addLayout(self.upper_hb)  # собираем все
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

        self.init_alphabit()  # создание алфавита
        self.set_guide()  # ставим надпись-руководство
        self.setFont(font)

        self.setStyleSheet('background-color: #EBF0F7')  # стили
        self.table.setStyleSheet('background-color: #FEFDF5')
        self.word_description.setStyleSheet('background-color: #FEFDF5')

        self.sp = list(self.findChildren(QPushButton))
        for x in self.sp:
            x.setStyleSheet('background-color: #FFCFB1')

    def init_alphabit(self):  # алфавит
        a = QWidget(self)
        a.grid = QGridLayout(self)
        a.grid.setSpacing(0)
        a.setLayout(a.grid)
        for x in range(0, 3):
            for y in range(0, 11):
                new = QPushButton(self)
                new.setText(ALPHABIT[x * 11 + y])
                new.setMinimumSize(0, 50)
                font = QtGui.QFont()
                font.setPointSize(20)
                font.setWeight(50)
                new.setFont(font)
                new.clicked.connect(self.alphabit_letter_is_pressed)  # соединяем с нажатием
                a.grid.addWidget(new, x, y)
        self.main_vb.addWidget(a)

    def alphabit_letter_is_pressed(self):
        if self.remembered_alphabit_letter:  # убираем выделение с последней запомненной буквы
            self.remembered_alphabit_letter.setStyleSheet('background-color: #FFCFB1')
        self.remembered_alphabit_letter = self.sender()  # запоминаем последнюю введенную букву
        self.sender().setStyleSheet('background-color: #FF9A5C')

    def generate_word(self):  # с помощью словаря-базы данных выбираем случайное слово для начала игры
        global cur
        result = cur.execute("""SELECT * FROM words WHERE LENGTH(word)=""" + str(self.field_size)).fetchall()
        self.first_word = random.choice(result)[1]
        return self.first_word

    def set_guide(self):  # устанавливает надпись-руководство и меняет кнопки при изменении статуса игры
        self.guide_label.setText(self.game_status)
        if self.game_status == STATUSES[0] or self.game_status == STATUSES[1]:
            self.add_word_btn.hide()  # прячем "ввести слово", если еще не выделена буква
        if self.game_status == STATUSES[1]:
            self.delete_letter_btn.setEnabled(True)  # доступ к кнопке - удалению буквы
            if self.current_word:
                self.add_word_btn.show()  # показываем "ввести слово", если выделена хоть одна буква
                self.add_word_btn.setText(''.join([x.letter for x in self.current_word]))
                self.delete_word_btn.setEnabled(True)  # доступ к кнопке - удалению слова

    def make_a_move(self):  # проверяет и делает ход
        if self.game_status == STATUSES[1]:
            word = ''.join(j.letter for j in self.current_word)  # введенное слово
            if self.check_word(word):  # если прошло проверку
                self.p_counts[self.current_player] += len(word)  # обновление счета
                self.p_words[self.current_player].append(word)  # списка слов
                self.set_description(word.lower())  # значение последнего слова
                self.player_change()  # меняем игрока
                self.game_over()  # проверка на окончание игры
            else:  # слово не прошло проверку
                if self.field.last_letter not in self.current_word:
                    text = 'Слово должно содержать новую букву!'
                elif word in self.p_words[0] or word in self.p_words[1] or word == self.first_word:
                    text = 'Такое слово уже было!\nПридумайте новое.'
                else:
                    text = 'Извините, данного слова нет в \nсловаре. Попробуйте ввести другое.'
                self.guide_label.setText(text)
                self.guide_label.update()
                self.delete_word()

    def check_word(self, word):  # проверка слова
        global cur
        result = cur.execute("""SELECT * FROM words
                    WHERE word = ?""", (word,)).fetchone()  # поиск слова в морфологическом словаре
        global cur2
        result_2 = cur2.execute("""SELECT * FROM ozhigov
                    WHERE word = ?""", (word.lower(),)).fetchone()  # поиск слова в толковом словаре
        if (result or result_2) and word not in self.p_words[0] and word not in self.p_words[
            1] and word != self.first_word and self.field.last_letter in self.current_word:  # нет ли слова в уже введенных и есть ли в нем последняя буква
            return True
        return False

    def update_table(self):  # обновление таблицы слов
        self.table.setRowCount(len(self.p_words[0]))
        self.table.setItem(len(self.p_words[0]) - 1, self.current_player,
                           QTableWidgetItem(self.p_words[self.current_player][len(self.p_words[0]) - 1]))

    def player_change(self):  # смена игрока
        if not self.current_word:
            self.p_words[self.current_player].append('-')  # если пропускает ход
        self.update_table()
        self.counts.setText(str(self.p_counts[0]) + ' : ' + str(self.p_counts[1]))
        if self.current_player == 0:  # смена номера игрока
            self.current_player = 1
        else:
            self.current_player = 0
        self.field.last_letter = None  # сброс промежуточных введений
        self.delete_word()
        self.field.orig_cells_objects = self.field.cells_objects  # обновляем массив клеток
        self.remembered_alphabit_letter.setStyleSheet('background-color: #ffcfb1')  # сброс выделения в алфавите
        self.remembered_alphabit_letter = None
        self.now_move.setText('Сейчас ход: ' + self.players[self.current_player])
        self.delete_letter_btn.setEnabled(False)
        self.game_status = STATUSES[0]
        self.set_guide()

    def delete_letter(self):  # сброс введенной буквы
        self.field.last_letter.reset()
        self.game_status = STATUSES[0]
        self.delete_word()
        self.set_guide()
        self.delete_letter_btn.setEnabled(False)

    def delete_word(self):  # сброс вводимого слова
        self.current_word = []
        self.field.reset_map()
        self.field.update()
        self.add_word_btn.hide()
        self.delete_word_btn.setEnabled(False)

    def pass_move(self):  # пропуск хода
        if self.field.last_letter:
            self.delete_letter()
        self.player_change()

    def set_description(self, word):  # добавление определения слова
        global cur2
        result_2 = cur2.execute("""SELECT * FROM ozhigov
                               WHERE word = ?""", (word.lower(),)).fetchone()
        if result_2:
            des = ' '.join(str(result_2[2][2:]).split('\\n'))
            self.word_description.setPlainText(des)
        else:
            self.word_description.setPlainText('Извините, данное слово отсутсвует в толковом словаре.')

    def game_over(self):  # проверка и действие при окончании игры
        if all(z.is_letter for z in [self.field.orig_cells_objects[x][y] for x in range(self.field_size) for y in
                                     range(self.field_size)]):  # не осталось свободных клеток
            if self.p_counts[0] == self.p_counts[1]:
                text = 'Ничья!'
            else:
                winner = self.p_counts.index(max(self.p_counts))
                text = 'Поздравляем, ' + self.players[winner] + '!\nВы победили!'
            self.now_move.setText('')
            self.guide_label.setText('\tКонец игры.')
            self.the_best_word = max(self.p_words[0] + self.p_words[1], key=len)  # определение самого длинного слова
            text += '\nЛучшее слово за игру:\n' + self.the_best_word
            nt = Win_window(text)  # поздравительное окошко
            self.btn_vb.insertWidget(0, nt)
            self.btn_vb.removeWidget(self.now_move)
            self.delete_word_btn.hide()  # убираем ненужные кнопки
            self.delete_letter_btn.hide()
            self.add_word_btn.hide()
            self.pass_move_btn.hide()
            self.btn_vb.addWidget(self.new_game_btn)
            self.new_game_btn.show()  # добавляем кнопку для новой игры (закрытия старой)
            self.game_status = STATUSES[2]


class Win_window(QWidget):  # поздравительное окошко
    def __init__(self, text):
        super(Win_window, self).__init__()
        self.pixmap = QPixmap('data/image.jpg')
        self.setMinimumSize(350, 350)
        self.image = QLabel(self)
        self.image.setGeometry(0, 60, 300, 300)
        self.image.setPixmap(self.pixmap)
        self.label = QLabel(self)
        self.label.setFont(QFont("LuzSans-Book", 18))
        self.setStyleSheet("font: bold")
        self.label.setText(text)
        self.label.move(10, 100)


class Begining_Window(QWidget):  # начальное окно
    def __init__(self):
        super().__init__()
        self.setGeometry(250, 250, 600, 480)

        m_f = QtGui.QFont()
        m_f.setFamily('Tw Cen MT')
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
        self.rules.clicked.connect(self.open_rules)

        self.setStyleSheet('background-color: #EBF0F7')  # стили
        self.vvod1.setStyleSheet('background-color: #FEFDF5')
        self.vvod2.setStyleSheet('background-color: #FEFDF5')
        self.choice.setStyleSheet("QComboBox{color: black;\n"
                                  "background-color: white;\n"
                                  "background-image: white;}\n")

        self.sp = list(self.findChildren(QPushButton))
        for x in self.sp:
            x.setStyleSheet('background-color: #FFCFB1')

    def open_rules(self):  # открытие правил
        self.window_rules = Rules()
        self.window_rules.show()

    def open_second_form(self):  # открытие самой игры
        field = self.choice.currentText()
        names = ['player1', 'player2']  # базовые имена
        if self.vvod1.text():
            names[0] = self.vvod1.text()
        if self.vvod2.text():
            names[1] = self.vvod2.text()
        self.second_form = window
        window.__init__(int(field[0]), *names)
        self.second_form.show()


class Rules(QWidget):  # окошко с правилами игры
    def __init__(self):
        super().__init__()
        self.setGeometry(250, 250, 520, 400)
        f = open('data/rules.txt').read()
        text = QPlainTextEdit(self)
        text.setGeometry(10, 10, 500, 380)
        text.setPlainText(f)
        text.setReadOnly(True)


if __name__ == '__main__':
    con = sqlite3.connect("data/dic3.db")
    con2 = sqlite3.connect("data/ozhigov.db")
    cur = con.cursor()
    cur2 = con2.cursor()
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = MainWindow()
    window2 = Begining_Window()
    window2.show()
    sys.exit(app.exec())
