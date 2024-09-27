# -*- coding: utf-8 -*-
import math

from odoo.tools.translate import _


font_sizes = {
    'number': 375,
    'filter': 450,
    'created_on': 375,
    'name': 600,  # Times New Roman 16px bold
    'title': 450,
    'group': 375,
    'content': 306
}


class ReportExcelFitSheetWrapper(object):
    """Эксел тайлангийн агуулгаас хамаарч нүдний хэмжээг автоматаар тохируулах класс.
        Ашиглахдаа:
        1. sheet = ReportExcelFitSheetWrapper(book.add_sheet(sheet_name))
        2. write болон write_merge функцийг дуудахдаа дараах аргументуудыг дамжуулж ашиглана.
            no_merge: (boolean) write функцийг дуудах бол заавал True байна.
                Жишээ нь: sheet.write(1, 1, 'label', no_merge=True).
            size: ('number', 'filter', 'created_on', 'name', 'title', 'group', 'content')
                'number': Тайлангийн дугаар эксел руу бичиж байгаа бол
                'filter': Тайлангийн шүүлтүүр эксел руу бичиж байгаа бол
                'created_on': Тайлангийн огноо эксел руу бичиж байгаа бол
                'name': Тайлангийн нэр эксел руу бичиж байгаа бол
                'title': Тайлангийн хүснэгтийн гарчиг эксел руу бичиж байгаа бол
                'group': Тайлангийн хүснэгтийн бүлэг эксел руу бичиж байгаа бол
                'content': Тайлангийн хүснэгтийн агуулга эксел руу бичиж байгаа бол
                Жишээ нь: sheet.write_merge(1, 1, 1, 15, 'Report Name', size='name').
            group: (boolean) Бүлэглэлт эксел руу бичиж байгаа бол заавал True байна.
            rotated: (boolean) Босоо чиглэлтэй утга эксел руу бичиж байгаа бол заавал True байна.
    """
    def __init__(self, sheet):
        self.sheet = sheet
        self.widths = dict()
        self.heights = dict()

    def write(self, r, c, label, *args, **kwargs):
        no_merge = kwargs.pop('no_merge', None)
        group = kwargs.pop('group', None)
        if not label:
            if group:
                label = _('Undefined')
            else:
                label = ''
        rotated = kwargs.pop('rotated', None)
        size = kwargs.pop('size', None)

        self.sheet.write(r, c, label, *args, **kwargs)

        if no_merge:
            if ('%s' % label).find('\n') >= 0:
                width, height = self.fitWidthHeight('%s' % label, size, rotated)
                if height > self.heights.get(r, 0):
                    self.heights[r] = height
                    self.sheet.row(r).height = height
            else:
                width = self.fitWidth('%s' % label, size, rotated)
            width = min(int(math.ceil(width)), 65535)
            if width > self.widths.get(c, 0):
                self.widths[c] = width
                self.sheet.col(c).width = width

    def write_merge(self, r1, r2, c1, c2, label, *args, **kwargs):
        group = kwargs.pop('group', None)
        if not label:
            if group:
                label = _('Undefined')
            else:
                label = ''
        rotated = kwargs.pop('rotated', None)
        size = kwargs.pop('size', None)

        self.sheet.write_merge(r1, r2, c1, c2, label, *args, **kwargs)

        if ('%s' % label).find('\n') >= 0:
            width, height = self.fitWidthHeight('%s' % label, size, rotated)
            if c1 == c2:
                merged_rows = r2 - r1 + 1
                one_row_height = height / merged_rows
                for i in range(r1, r2 + 1):
                    if one_row_height > self.heights.get(i, 0):
                        self.heights[i] = one_row_height
                        self.sheet.row(i).height = one_row_height
        else:
            width = self.fitWidth('%s' % label, size, rotated)
        width = min(int(math.ceil(width)), 65535)
        if r1 == r2:
            merged_columns = c2 - c1 + 1
            one_column_width = width / merged_columns
            for i in range(c1, c2 + 1):
                if one_column_width > self.widths.get(i, 0):
                    self.widths[i] = one_column_width
                    self.sheet.col(i).width = one_column_width

    def fitlinewidth(self, data, size, rotated):
        units = 220
        if not rotated:
            if size in font_sizes:
                units += font_sizes[size] * len(data)
            else:
                units += font_sizes['name'] * len(data)
        else:
            if size in font_sizes:
                units += font_sizes[size] * 1.2
            else:
                units += font_sizes['name'] * 1.2
        return units

    def fitWidth(self, data, size, rotated):
        return max(self.fitlinewidth(line, size, rotated) for line in data.split('\n'))

    def fitWidthHeight(self, data, size, rotated):
        units = 220
        lines = data.split('\n')
        if not rotated:
            width = max(self.fitlinewidth(line, size, rotated) for line in lines)
            height = int(len(lines) * units * 1.2)
        else:
            width = int(len(lines) * units * 1.2)
            height = max(self.fitlinewidth(line, size, not rotated) for line in lines) * 1.2
        return width, height

    def __getattr__(self, attr):
        return getattr(self.sheet, attr)
