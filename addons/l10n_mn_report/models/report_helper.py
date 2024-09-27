# -*- coding: utf-8 -*-
import re
import sys

sys.stdout.encoding


def verbose_numeric(amount):
    # Тоон утгыг үгээр илэрхийлэх функц
    if type(amount) in (int, float):
        amount = '%.2f' % amount
    res = []
    result = u''
    # Форматаас болоод . -ын оронд , орсон байвал засна.
    amount = amount.replace(',', '.')
    subamount = ''
    if '.' in amount:
        stramount = amount
        amount = stramount[:stramount.find('.')]
        subamount = stramount[stramount.find('.') + 1:]
    i = 0
    length = len(amount)
    if length == 0 or float(amount) == 0:
        res.append(u'тэг ')
        if len(subamount) > 0 and float(subamount) > 0:
            result2 = verbose_numeric(subamount)
            res.append(result2[0])
        return res

    try:
        while i < length:
            c = length - i
            if c % 3 == 0:
                c -= 3
            else:
                while c % 3 != 0:
                    c -= 1
            place = c / 3
            i1 = length - c
            tmp = amount[i:i1]
            j = 0
            if tmp == '000':
                i = i1
                continue
            while j < len(tmp):
                char = int(tmp[j])
                p = len(tmp) - j
                if char == 1:
                    if p == 3:
                        result += u'нэг зуун '
                    elif p == 2:
                        result += u'арван '
                    elif p == 1:
                        result += u'нэг '
                elif char == 2:
                    if p == 3:
                        result += u'хоёр зуун '
                    elif p == 2:
                        result += u'хорин '
                    elif p == 1:
                        result += u'хоёр '
                elif char == 3:
                    if p == 3:
                        result += u'гурван зуун '
                    elif p == 2:
                        result += u'гучин '
                    elif p == 1:
                        result += u'гурван '
                elif char == 4:
                    if p == 3:
                        result += u'дөрвөн зуун '
                    elif p == 2:
                        result += u'дөчин '
                    elif p == 1:
                        result += u'дөрвөн '
                elif char == 5:
                    if p == 3:
                        result += u'таван зуун '
                    elif p == 2:
                        result += u'тавин '
                    elif p == 1:
                        result += u'таван '
                elif char == 6:
                    if p == 3:
                        result += u'зургаан зуун '
                    elif p == 2:
                        result += u'жаран '
                    elif p == 1:
                        result += u'зургаан '
                elif char == 7:
                    if p == 3:
                        result += u'долоон зуун '
                    elif p == 2:
                        result += u'далан '
                    elif p == 1:
                        result += u'долоон '
                elif char == 8:
                    if p == 3:
                        result += u'найман зуун '
                    elif p == 2:
                        result += u'наян '
                    elif p == 1:
                        result += u'найман '
                elif char == 9:
                    if p == 3:
                        result += u'есөн зуун '
                    elif p == 2:
                        result += u'ерэн '
                    elif p == 1:
                        result += u'есөн '

                j += 1
            # -------- end while j < len(tmp)
            if place == 3:
                result += u'тэрбум '
            elif place == 2:
                result += u'сая '
            elif place == 1:
                if int(amount[i1:-1]) == 0:
                    if int(subamount) == 0:
                        result += u'мянган '
                    else:
                        result += u'мянга '
                else:
                    result += u'мянга '
            i = i1
        res.append(result)
        # ---------- end while i < len(amount)
    except Exception:
        return False
    if len(subamount) > 0 and float(subamount) > 0:
        result2 = verbose_numeric(subamount)
        res.append(result2[0])
    return res


def comma_me(value, decimals=2, separator=","):
    """ transform a number into a number with thousand separators """
    if separator == ".":
        separator = "'"
    if type(value) is int:
        value = str(('%.' + str(decimals) + 'f') % float(value))
    elif type(value) is float:
        value = str(('%.' + str(decimals) + 'f') % value)
    else:
        value = str(value)
    orig = value
    new = re.sub("^(-?\d+)(\d{3})", "\g<1>" + separator + "\g<2>", value)
    """Доорх comment-ийг устгаж болохгүй дараа ашиглагдаж магадгүй"""
#        if '.' in new and int(new[-decimals:]) == 0:
#            new = new[:-(decimals+1)]
#            orig = orig[:-(decimals+1)]
    if orig == new:
        return new
    else:
        return comma_me(new, decimals=decimals, separator=separator)


def convert_curr(currency_list, curr, div_curr):
    """Convert currency """
    result = u''
    if not (curr and div_curr):
        curr = u'төгрөг'
        div_curr = u'мөнгө'
    else:
        curr = curr
        div_curr = div_curr

    if currency_list[0]:
        result += u'( %s ' % currency_list[0]
        if len(currency_list) == 1:
            result += u"%s )" % curr
        else:
            result += u'%s ' % curr
    if len(currency_list) == 2:
        result += currency_list[1]
        result += u'%s )' % div_curr
    return result

def get_xsl_column_name(index):
    """ 
        @param index: баганын тоог авах Integer утга байна. /0-с эхэлнэ/
        @return: xslx-н баганын латин нэрийг A:A байдлаар буцаана.
    """
    alphabet = {'0': 'A',  '1':'B',  '2':'C',  '3':'D',  '4':'E',
                '5': 'F',  '6':'G',  '7':'H',  '8':'I',  '9':'J',
                '10':'K',  '11':'L', '12':'M', '13':'N', '14':'O',
                '15':'P',  '16':'Q', '17':'R', '18':'S', '19':'T',
                '20':'U',  '21':'V', '22':'W', '23':'X', '24':'Y', '25':'Z'}
    
    if index <= 25:
        return (alphabet[str(index)] + ":" + alphabet[str(index)])
    else:
        return (alphabet[str(index/26-1)] + alphabet[str(index%26)] + ":" + alphabet[str(index/26-1)] + alphabet[str(index%26)])

def get_column_name_for_calculate(index):
    """ 
        @param index: баганын тоог авах Integer утга байна. /0-с эхэлнэ/
        @return: xslx-н баганын латин нэрийг буцаана.
    """
    column_name = get_xsl_column_name(index).split(':')[0]
    return column_name

def get_sum_formula_from_list(col, list):
    """ 
        @param col: Нийлбэрийг авах баганын индекс. Integer утга байна.
        @param list: Нийлбэрийг авах мөрүүдийн индексийн Integer жагсаалт байна. Жнь: [2, 13]
        @return: =+A2+B13 байдлаар нийлбэрийг олох томъёог буцаана.
    """
    formula = "="
    if list:
        for i in range(len(list)):
            formula += ("+" + get_column_name_for_calculate(col) + str(list[i]))
    return formula

def get_arithmetic_formula(f_col, f_rowx, s_col, s_rowx, oprtr):
    """ 
        @param f_col: Эхний баганын индекс. Integer утга байна.
        @param f_rowx: Эхний мөрийн индекс. Integer утга байна.
        @param s_col: II баганын индекс. Integer утга байна.
        @param s_rowx: II мөрийн индекс. Integer утга байна.
        @param oprtr: '*', '/', '-', '+' гэх мэт арифметик үйлдлүүдийг илэрхийлэх Char утга дамжуулна.
        @return: =A2*B13 байдлаар арифметик томъёог буцаана.
    """
    f_cell_index = get_column_name_for_calculate(f_col) + str(f_rowx+1)
    s_cell_index = get_column_name_for_calculate(s_col) + str(s_rowx+1)
    if oprtr == '/':
        return '=IF(' + s_cell_index + ',' + f_cell_index + oprtr + s_cell_index + ',0)'
    return f_cell_index + oprtr + s_cell_index

def get_sum_formula(startx, endx, coly):
    """ 
        @note: coly баганын startx, endx мөрүүдийн хоорондох нийлбэрийн томъёог буцаана.
        @param startx: Нийлбэр олох эхний мөрийн индекс байна. Integer утга байна.
        @param endx: Нийлбэр олох сүүлийн мөрийн индекс байна. Integer утга байна.
        @param col: Нийлбэр олох баганын индекс байна. Integer утга байна.
        @return: =SUM(A2:B13) байдлаар нийлбэрийг олох томъёог буцаана.
    """
    return "{=SUM(" + get_column_name_for_calculate(coly) + str(startx) + ":" + get_column_name_for_calculate(coly) + str(endx) + ")}"
