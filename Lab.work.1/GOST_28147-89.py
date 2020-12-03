"""
ГОСТ 28147-89 шифр работающий в 1 режиме:
    EC - Electronic Codebook - Режим простой замены
    
Программа работает в двух режимах:
    mode = 1 - дешифровка
    mode = 0 - шифрование
"""

import random
import math
import sys
import argparse
import textwrap

class GOST_28147_89():

    def __init__(self, key):
        self.key = key
        self.set_key()
        self.set_s_box()
        self.C1 = 0x1010104
        self.C2 = 0x1010101
    
    def set_key(self):
        # Генерация ключа
        if self.key == None:
            k = []
            for _ in range(8):
                tmp = random.getrandbits(32)
                k.append(tmp)
            self.subkeys = k
        # Настройка ключа, который был введен
        else:
            tmp = (4 - self.key.bit_length() % 4) % 4
            tmp_key = int(('0b1' + '0' * (self.key.bit_length() + tmp)), 2) | self.key
            tmp_key = str(bin(tmp_key))[3:]
            self.subkeys = []
            for _ in range(8):
                self.subkeys.append(int(('0b' + tmp_key[:32]), 2))
                tmp_key = tmp_key[32:]
                
    def set_s_box(self):
        self.s_box = [ # Сгенерированно на сайте https://planetcalc.com/5843/
            [4, 10, 12, 2, 0, 5, 14, 9, 3, 11, 15, 6, 13, 1, 7, 8],
            [11, 4, 7, 8, 10, 2, 5, 12, 3, 14, 1, 9, 15, 0, 13, 6],
            [2, 9, 11, 14, 5, 7, 8, 13, 15, 10, 6, 12, 4, 3, 0, 1],
            [7, 3, 4, 12, 5, 11, 8, 13, 14, 0, 2, 10, 9, 15, 1, 6],
            [5, 9, 3, 13, 4, 1, 11, 8, 14, 10, 2, 6, 0, 15, 12, 7],
            [6, 4, 1, 3, 9, 12, 0, 7, 15, 11, 5, 13, 14, 2, 8, 10],
            [1, 8, 4, 11, 15, 7, 14, 9, 2, 0, 3, 13, 5, 10, 12, 6],
            [1, 5, 8, 11, 2, 14, 6, 10, 9, 4, 3, 7, 12, 13, 0, 15]
        ]
    
    # Разделение 64 битов данных на 2 части
    def left_right(self, data):
        n1 = data & 0xFFFFFFFF
        n2 = data >> 32
        return (n1, n2)

    def replacement_table(self, s):
        ans = 0
        for i in range(8):
            # Получение 4-х битов в конце за счет сдвига
            tmp = s >> 4*i & 0xF
            ans += self.s_box[i][tmp] << 4*i
        return ans

    def main_step(self, data, sub_key):
        n1, n2 = self.left_right(data)
        S = (n1 + sub_key) % 4294967296
        S = self.replacement_table(S)
        S = (S << 11) & 0xFFFFFFFF | S >> 21
        S = S ^ n2
        n2 = n1
        n1 = S
        return n2 << 32 | n1

    def cycle_32_Z(self, data):
        for _ in range(3):
            for j in range(8):
                data = self.main_step(data, self.subkeys[j])
        for j in range(7, -1, -1):
            data = self.main_step(data, self.subkeys[j])
        n2, n1 = self.left_right(data)
        return n2 << 32 | n1
    
    def cycle_32_R(self, data):
        for j in range(8):
            data = self.main_step(data, self.subkeys[j])
        for _ in range(3):
            for j in range(7, -1, -1):
                data = self.main_step(data, self.subkeys[j])
        n2, n1 = self.left_right(data)
        return n2 << 32 | n1
    
    # Разделение входных данных на блоки по 64 бита
    def make_block(self, data):
        tmp = (4 - data.bit_length() % 4) % 4
        data = int(('0b1' + '0' * (data.bit_length() + tmp)), 2) | data
        ans = []
        tmp_data = str(bin(data))[3:]
        CTR_blocks = math.ceil(len(tmp_data) / 64)
        for _ in range(CTR_blocks-1):
            block = '0b' + tmp_data[:64]
            tmp_data = tmp_data[64:]
            ans.append(int(block, 2))
        block = '0b' + tmp_data
        ans.append(int(block, 2))
        return ans
    
    def EC(self, data, mode=0):
        # Добавление нулей в начале для полного шестнадцатеричного значения
        tmp = (4 - data.bit_length() % 4) % 4
        tmp_data = int(('0b1' + '0' * (data.bit_length() + tmp)), 2) | data
        tmp_data = str(bin(tmp_data))[3:]
        # Проверка дляинны файла на делимость на 64
        if len(tmp_data) % 64 != 0:
            print("\nДлина данных: ", len(tmp_data))
            print("\nОшибка! Не делится на 64!")
            raise ZeroDivisionError
        plain_text = self.make_block(data)
        ans = 0
        for i in range(len(plain_text)):
            if mode:
                crypt_text = self.cycle_32_Z(plain_text[i])
            else:
                crypt_text = self.cycle_32_R(plain_text[i])
            ans = ans << 64 | crypt_text    
        return ans, int('0x' + ''.join([hex(x)[2:] for x in self.subkeys]), 16)

# Обертка для общения с пользователем
def create_parser(): # https://habr.com/ru/company/ruvds/blog/440654/
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--chk', action='store_const', const=True,
            help="Осуществление шифрования и расшифрования по входным данным")
    parser.add_argument('-m', '--mode', choices=['0', '1'], default='0', 
            help="Выбор режима шифрования:\n\t0 - для шифрования\n\t1 - для расшифрования",
            metavar='MODE')
    parser.add_argument('--alg', choices=['EC'], required=True,
            help="Выбор алгоритма шифрования:\nEC - Режим простой замены")
    parser.add_argument('-r', '--read', type=argparse.FileType(), required=True,
            help="Путь к файлу с входными данными",
            metavar='FILE')
    parser.add_argument('-w', '--write', type=argparse.FileType(mode='w'),
            help="Путь к файлу с выходными данными\nПо умолчанию вывод результатов осуществляется в командную строку",
            metavar='FILE')
    return parser

# Точка входа в программу
def input_processing():
    parser = create_parser()
    namespace = parser.parse_args(sys.argv[1:])
    # Инициализация режима работы
    mode = 1 if namespace.mode == '1' else 0
    # Получение шифрключа
    if mode:
        print("\nПожалуйста, введите ключ в шестнадцатеричном формате (пример: 0x...): ")
        key = input()
        key = int(key, 16)
    else:
        key = None
    # Инициализация класса
    try:
        gost = GOST_28147_89(key)
    except ValueError:
        print("\nОшибка! Ключ не в шестнадцатеричном формате (пример: 0x...).\n")
        sys.exit()
    # Считывание текста
    try:
        text = namespace.read.read()
        if mode == 0:
            text = int('0x' + text.encode().hex(), 16)
        else:
            text = int(text, 16)
    finally:
        namespace.read.close()

    # Выбор режима шифрования
    ## Режим простой замены
    if namespace.alg == 'EC':
        if namespace.chk != None:
            print("\n___Режим простой замены (EC)___\n")
            print("\nОткрытый текст:\n", bytes.fromhex(hex(text)[2:]).decode())
            ans, _ = gost.EC(text, mode=0)
            print("\nШифротекст:\n", hex(ans))
            ans, _ = gost.EC(ans, mode=1)
            print("\nДешифрованный текст:\n", bytes.fromhex(hex(ans)[2:]).decode())
        else:
            ans, key = gost.EC(text, mode)
            print("\nКлюч:\n", hex(key))
    else: print('\nПопробуйте еще раз!\n')
    ## Обработка режима вывода
    if mode:
        ans = bytes.fromhex(hex(ans)[2:]).decode()
    if namespace.chk == None:       
        if namespace.write != None:
            if mode:
                namespace.write.write(ans)
            else:
                namespace.write.write(hex(ans))
            print("\nФайл готов!\n")
            namespace.write.close()
        else:
            if mode:
                print("\nРасшифрованный текст:")
                print(ans)
            else:
                print("\nШифротекст:")
                print(hex(ans))

if __name__ == "__main__":
    random.seed()
    try:
        input_processing()
    except ZeroDivisionError:
        print('\nПопробуйте еще раз!')
    except Exception as e:
        print("\nПроизошла ошабка:\t", e)