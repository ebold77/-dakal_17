# -*- coding: utf-8 -*-
import xlwt


class ReportExcelCellStyles:
    """OdERP эксел тайлангийн үндсэн хэлбэржүүлэлтүүд.
        Ашиглахдаа:
        write болон write_merge функцийн style аргументэд дараах утгуудыг дамжуулж ашиглана.
            'number_xf': Тайлангийн дугаар эксел руу бичиж байгаа бол
            'filter_xf': Тайлангийн шүүлтүүр эксел руу бичиж байгаа бол
            'datetime_xf': Тайлангийн огноо эксел руу бичиж байгаа бол
            'name_xf': Тайлангийн нэр эксел руу бичиж байгаа бол
            'title_xf': Тайлангийн хүснэгтийн гарчиг эксел руу бичиж байгаа бол
            'group_xf': Тайлангийн хүснэгтийн бүлэг эксел руу бичиж байгаа бол
            'content_text_xf': Тайлангийн хүснэгтийн текст агуулга эксел руу бичиж байгаа бол
            'content_number_xf': Тайлангийн хүснэгтийн дугаарлалт эксел руу бичиж байгаа бол
            'content_float_xf': Тайлангийн хүснэгтийн тоон агуулга эксел руу бичиж байгаа бол
            Жишээ нь: sheet.write_merge(5, 1, 'Type', style='content_text_xf')
    """
    name_xf = xlwt.easyxf('font: name Times New Roman, height 320, bold on; align: horz center, vert center, wrap on;')
    number_xf = xlwt.easyxf('font: name Times New Roman, height 200, bold on; align: horz right, vert center, wrap on;')
    datetime_xf = xlwt.easyxf('font: name Times New Roman, height 200, bold on; align: horz right, vert center, wrap on;')
    filter_xf = xlwt.easyxf('font: name Times New Roman, height 200, bold on; align: horz left, vert center, wrap on;')
    title_xf = xlwt.easyxf('font: name Times New Roman, height 240, bold on; align: horz center, vert center, wrap on; pattern: pattern solid, fore_color sky_blue; borders: top thin, left thin, bottom thin, right thin;')
    group_xf = xlwt.easyxf('font: name Times New Roman, height 200, bold on; align: horz left, vert center, wrap on; pattern: pattern solid, fore_color pale_blue; borders: top thin, left thin, bottom thin, right thin;')
    content_number_xf = xlwt.easyxf('font: name Times New Roman, height 180; align: horz center, vert center, wrap on; borders: top thin, left thin, bottom thin, right thin;')
    content_text_xf = xlwt.easyxf('font: name Times New Roman, height 180; align: horz left, vert center, wrap on; borders: top thin, left thin, bottom thin, right thin;')
    content_float_xf = xlwt.easyxf('font: name Times New Roman, height 180; align: horz right, vert center, wrap on; borders: top thin, left thin, bottom thin, right thin;', num_format_str='#,##0.00')

    """xlsxwriter-т зориулсан форматууд
    """
    format_name = {
        'font_name': 'Times New Roman',
        'font_size': 16,
        'bold': True,
        'align': 'center',
        'valign': 'vcenter'
    }

    format_date = {
        'font_name': 'Times New Roman',
        'font_size': 10,
        'bold': True,
        'align': 'right',
        'valign': 'vcenter'
    }

    format_filter = {
        'font_name': 'Times New Roman',
        'font_size': 10,
        'bold': True,
        'align': 'left',
        'valign': 'vcenter'
    }

    format_filter_right = {
        'font_name': 'Times New Roman',
        'font_size': 10,
        'bold': True,
        'align': 'right',
        'valign': 'vcenter'
    }
    
    format_filter_center = {
        'font_name': 'Times New Roman',
        'font_size': 10,
        'bold': True,
        'align': 'center',
        'valign': 'vcenter'
    }

    format_title = {
        'font_name': 'Times New Roman',
        'font_size': 11,
        'bold': True,
        'align': 'center',
        'valign': 'vcenter',
        'border': 1,
        'text_wrap': 1,
        'bg_color': '#C9E3F3'
    }

    format_color_title = {
        'font_name': 'Times New Roman',
        'font_size': 11,
        'bold': True,
        'align': 'center',
        'valign': 'vcenter',
        'border': 1,
        'text_wrap': 1,
        'bg_color': '#83CAFF'
    }

    format_title_left = {
        'font_name': 'Times New Roman',
        'font_size': 10,
        'bold': True,
        'align': 'left',
        'valign': 'vcenter',
        'border': 1,
        'bg_color': '#C9E3F3',
    }

    format_title_small = {
        'font_name': 'Times New Roman',
        'font_size': 10,
        'bold': True,
        'align': 'center',
        'valign': 'vcenter',
        'border': 1,
        'text_wrap': 1,
        'bg_color': '#C9E3F3'
    }

    format_title_small_color = {
        'font_name': 'Times New Roman',
        'font_size': 10,
        'bold': True,
        'align': 'center',
        'valign': 'vcenter',
        'border': 1,
        'text_wrap': 1,
        'bg_color': '#C9E3F3'
    }

    format_title_float = {
        'font_name': 'Times New Roman',
        'font_size': 10,
        'bold': True,
        'align': 'right',
        'valign': 'vcenter',
        'border': 1,
        'bg_color': '#C9E3F3',
        'num_format': '#,##0.00'
    }

    format_title_float_center = {
        'font_name': 'Times New Roman',
        'font_size': 10,
        'bold': True,
        'align': 'center',
        'valign': 'vcenter',
        'border': 1,
        'bg_color': '#C9E3F3',
        'num_format': '#,##0'
    }

    format_title_float_border = {
        'font_name': 'Times New Roman',
        'font_size': 9,
        'bold': True,
        'align': 'right',
        'valign': 'vcenter',
        'border': 1,
        'bg_color': '#C9E3F3',
        'border_color': '#95cae9',
        'num_format': '#,##0.00'
    }

    format_title_color = {
        'font_name': 'Times New Roman',
        'font_size': 10,
        'bold': True,
        'align': 'center',
        'valign': 'vcenter',
        'border': 1,
        'text_wrap': 1,
        'bg_color': '#C9E3F3',
        'border_color': '#95cae9',
    }

    format_title_border = {
        'font_name': 'Times New Roman',
        'font_size': 10,
        'bold': True,
        'align': 'center',
        'valign': 'vcenter',
        'border': 1,
        'text_wrap': 1,
        'bg_color': '#C9E3F3',
        'border_color': '#95cae9',
    }

    format_sub_title_float = {
        'font_name': 'Times New Roman',
        'font_size': 10,
        'bold': True,
        'align': 'right',
        'valign': 'vcenter',
        'border': 1,
        'bg_color': '#ccffff',
        'num_format': '#,##0.00'
    }

    format_sub_title = {
        'font_name': 'Times New Roman',
        'font_size': 10,
        'bold': True,
        'align': 'left',
        'valign': 'vcenter',
        'border': 1,
        'bg_color': '#ccffff',
    }

    format_sub_title_center = {
        'font_name': 'Times New Roman',
        'font_size': 10,
        'bold': True,
        'align': 'center',
        'valign': 'vcenter',
        'border': 1,
        'bg_color': '#ccffff',
    }
    
    format_content_header = {
        'font_name': 'Times New Roman',
        'font_size': 12,
        'bold': True,
        'align': 'center',
        'valign': 'vcenter',
        'border': 1,
        'text_wrap': 1,
        'bg_color': '#CFE7F5',
    }

    format_group = {
        'font_name': 'Times New Roman',
        'font_size': 10,
        'bold': True,
        'align': 'center',
        'valign': 'vcenter',
        'border': 1,
        'text_wrap': 1,
        'bg_color': '#E4F3FB'
    }

    format_group2 = {
        'font_name': 'Times New Roman',
        'font_size': 10,
        'bold': True,
        'align': 'center',
        'valign': 'vcenter',
        'border': 1,
        'text_wrap': 1,
        'bg_color': '#FDEBD0'
    }

    format_group_color_border = {
        'font_name': 'Times New Roman',
        'font_size': 10,
        'bold': True,
        'align': 'center',
        'valign': 'vcenter',
        'border': 1,
        'bg_color': '#E4F3FB',
        'border_color': '#95cae9',
    }

    format_group_border = {
        'font_name': 'Times New Roman',
        'font_size': 10,
        'bold': True,
        'align': 'center',
        'valign': 'vcenter',
        'border': 1,
        'border_color': '#95cae9',
    }

    format_group_right = {
        'font_name': 'Times New Roman',
        'font_size': 10,
        'bold': True,
        'align': 'right',
        'valign': 'vcenter',
        'border': 1,
        'bg_color': '#E4F3FB'
    }

    format_group_left = {
        'font_name': 'Times New Roman',
        'font_size': 10,
        'bold': True,
        'align': 'left',
        'valign': 'vcenter',
        'border': 1,
        'bg_color': '#E4F3FB'
    }

    format_group2_left = {
        'font_name': 'Times New Roman',
        'font_size': 10,
        'bold': True,
        'align': 'left',
        'valign': 'vcenter',
        'border': 1,
        'bg_color': '#FDEBD0'
    }

    format_content_left_color = {
        'font_name': 'Times New Roman',
        'font_size': 9,
        'align': 'left',
        'valign': 'vcenter',
        'border': 1,
        'border_color': '#95cae9'
    }

    format_group_left_border = {
        'font_name': 'Times New Roman',
        'font_size': 10,
        'bold': True,
        'align': 'left',
        'valign': 'vcenter',
        'border': 1,
        'bg_color': '#E4F3FB',
        'border_color': '#95cae9',
    }

    format_group_number = {
        'font_name': 'Times New Roman',
        'font_size': 10,
        'bold': True,
        'align': 'center',
        'valign': 'vcenter',
        'border': 1,
        'bg_color': '#E4F3FB'
    }

    format_group_float = {
        'font_name': 'Times New Roman',
        'font_size': 10,
        'bold': True,
        'align': 'right',
        'valign': 'vcenter',
        'border': 1,
        'bg_color': '#E4F3FB',
        'num_format': '#,##0.00'
    }

    format_group2_float = {
        'font_name': 'Times New Roman',
        'font_size': 10,
        'bold': True,
        'align': 'right',
        'valign': 'vcenter',
        'border': 1,
        'bg_color': '#FDEBD0',
        'num_format': '#,##0.00'
    }

    format_group_percent = {
        'font_name': 'Times New Roman',
        'font_size': 10,
        'bold': True,
        'align': 'right',
        'valign': 'vcenter',
        'border': 1,
        'bg_color': '#E4F3FB',
        'num_format': '#,##0.00%'
    }

    format_group_float_border = {
        'font_name': 'Times New Roman',
        'font_size': 10,
        'bold': True,
        'align': 'right',
        'valign': 'vcenter',
        'top': 1,
        'bottom': 1,
        'border_color': '#66bdff',
        'num_format': '#,##0.00'
    }

    format_group_float_color = {
        'font_name': 'Times New Roman',
        'font_size': 10,
        'font_color': '#0033CC',
        'bold': True,
        'align': 'right',
        'valign': 'vcenter',
        'top': 1,
        'bottom': 1,
        'bg_color': '#E4F3FB',
        'num_format': '#,##0.00'
    }

    format_group_float_color_border = {
        'font_name': 'Times New Roman',
        'font_size': 10,
        'bold': True,
        'align': 'right',
        'valign': 'vcenter',
        'top': 1,
        'bottom': 1,
        'bg_color': '#E4F3FB',
        'border_color': '#66bdff',
        'num_format': '#,##0.00'
    }

    format_content_text = {
        'font_name': 'Times New Roman',
        'font_size': 9,
        'align': 'justify',
        'valign': 'vcenter',
        'border': 1
    }
    
    format_content_text_color = {
        'font_name': 'Times New Roman',
        'font_size': 10,
        'bold': True,
        'align': 'justify',
        'valign': 'vcenter',
        'border': 1,
        'bg_color': '#F2F8FD',
    }
    
    format_content_center_text_color = {
        'font_name': 'Times New Roman',
        'font_size': 10,
        'bold': True,
        'align': 'center',
        'valign': 'vcenter',
        'border': 1,
        'bg_color': '#F2F8FD',
    }

    format_content_percent = {
        'font_name': 'Times New Roman',
        'font_size': 9,
        'align': 'right',
        'valign': 'vcenter',
        'border': 1,
        'num_format': '#,##0.00%'
    }
    
    format_content_percent_bold = {
        'font_name': 'Times New Roman',
        'font_size': 9,
        'bold': True,
        'align': 'right',
        'valign': 'vcenter',
        'border': 1,
        'num_format': '#,##0.00%'
    }
    
    format_content_percent_color = {
        'font_name': 'Times New Roman',
        'font_size': 10,
        'bold': True,
        'align': 'right',
        'valign': 'vcenter',
        'border': 1,
        'bg_color': '#F2F8FD',
        'num_format': '#,##0.00%'
    }

    format_content_center = {
        'font_name': 'Times New Roman',
        'font_size': 9,
        'align': 'center',
        'valign': 'vcenter',
        'border': 1
    }

    format_content_float_border = {
        'font_name': 'Times New Roman',
        'font_size': 9,
        'align': 'right',
        'valign': 'vcenter',
        'border': 1,
        'border_color': '#95cae9',
        'num_format': '#,##0.00'
    }

    format_content_center_border = {
        'font_name': 'Times New Roman',
        'font_size': 9,
        'align': 'center',
        'valign': 'vcenter',
        'border': 1,
        'border_color': '#95cae9'
    }

    format_content_right = {
        'font_name': 'Times New Roman',
        'font_size': 9,
        'align': 'right',
        'valign': 'vcenter',
        'border': 1
    }

    format_content_left = {
        'font_name': 'Times New Roman',
        'font_size': 9,
        'align': 'left',
        'valign': 'vcenter',
        'border': 1
    }

    format_content_number = {
        'font_name': 'Times New Roman',
        'font_size': 9,
        'align': 'center',
        'valign': 'vcenter',
        'border': 1,
    }

    format_content_float = {
        'font_name': 'Times New Roman',
        'font_size': 9,
        'align': 'right',
        'valign': 'vcenter',
        'border': 1,
        'num_format': '#,##0.00'
    }

    format_content_float_center = {
        'font_name': 'Times New Roman',
        'font_size': 9,
        'align': 'center',
        'valign': 'vcenter',
        'border': 1,
        'num_format': '#,##0.00'
    }

    format_content_float_color = {
        'font_name': 'Times New Roman',
        'font_size': 9,
        'font_color': '#0033CC',
        'align': 'right',
        'valign': 'vcenter',
        'border': 1,
        'num_format': '#,##0.00'
    }

    format_content_float_fcolor = {
        'font_name': 'Times New Roman',
        'font_size': 9,
        'font_color': '#0033CC',
        'align': 'right',
        'valign': 'vcenter',
        'border': 1,
        'num_format': '#,##0.00'
    }

    format_content_date = {
        'font_name': 'Times New Roman',
        'font_size': 9,
        'align': 'center',
        'valign': 'vcenter',
        'border': 1,
        'num_format': 'yyyy-mm-dd'
    }

    format_content_time = {
        'font_name': 'Times New Roman',
        'font_size': 9,
        'align': 'center',
        'valign': 'vcenter',
        'border': 1,
        'num_format': 'hh:mm:ss'
    }

    format_content_datetime = {
        'font_name': 'Times New Roman',
        'font_size': 9,
        'align': 'center',
        'valign': 'vcenter',
        'border': 1,
        'num_format': 'yyyy-mm-dd hh:mm:ss'
    }

    format_content_bold_text = {
        'font_name': 'Times New Roman',
        'font_size': 9,
        'bold': True,
        'align': 'center',
        'valign': 'vcenter',
        'border': 1
    }

    format_content_bold_right = {
        'font_name': 'Times New Roman',
        'font_size': 9,
        'bold': True,
        'align': 'right',
        'valign': 'vcenter',
        'border': 1
    }

    format_content_bold_left = {
        'font_name': 'Times New Roman',
        'font_size': 9,
        'bold': True,
        'align': 'left',
        'valign': 'vcenter',
        'border': 1
    }

    format_content_bold_number = {
        'font_name': 'Times New Roman',
        'font_size': 9,
        'bold': True,
        'align': 'center',
        'valign': 'vcenter',
        'border': 1,
    }

    format_content_bold_number_color = {
        'font_name': 'Times New Roman',
        'font_size': 9,
        'bold': True,
        'align': 'center',
        'valign': 'vcenter',
        'border': 1,
        'bg_color': '#CFE7F5',
    }

    format_content_bold_float = {
        'font_name': 'Times New Roman',
        'font_size': 9,
        'bold': True,
        'align': 'right',
        'valign': 'vcenter',
        'border': 1,
        'num_format': '#,##0.00'
    }

    format_content_bold_float_color = {
        'font_name': 'Times New Roman',
        'font_size': 9,
        'font_color': '#0033CC',
        'bold': True,
        'align': 'right',
        'valign': 'vcenter',
        'border': 1,
        'num_format': '#,##0.00'
    }

    format_content_center_color = {
        'font_name': 'Times New Roman',
        'font_size': 9,
        'font_color': '#0033CC',
        'align': 'center',
        'valign': 'vcenter',
        'border': 1,
        'bg_color': '#DDDDDD'
    }
    
    # Улаан текст
    format_content_center_red_text  = {
            'font_name': 'Times New Roman',
            'font_size': 10,
            'font_color': '#ff4000',
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'text_wrap': True,
            'num_format': '#,##0.00'
    }
    
    # Цэнхэр текст
    format_content_center_blue_text  = {
        'font_name': 'Times New Roman',
        'font_size': 10,
        'font_color': '#4169E1',
        'align': 'center',
        'valign': 'vcenter',
        'border': 1,
        'text_wrap': True,
        'num_format': '#,##0.00'
    }
    
    # Ногоон текст
    format_content_center_green_text  = {
        'font_name': 'Times New Roman',
        'font_size': 10,
        'font_color': '#00a65d',
        'align': 'center',
        'valign': 'vcenter',
        'border': 1,
        'text_wrap': True,
        'num_format': '#,##0.00'
    }

    # Саарал фонтой бараан ногоон текст
    format_content_center_green_text_greyed_out = {
        'font_name': 'Times New Roman',
        'font_size': 10,
        'font_color': '#037751',
        'align': 'center',
        'valign': 'vcenter',
        'border': 1,
        'text_wrap': True,
        'num_format': '#,##0.00',
        'bg_color': '#dddddd'
    }
    
    format_content_center_color_red = {
        'font_name': 'Times New Roman',
        'font_size': 9,
        'font_color': '#ff0000',
        'align': 'center',
        'valign': 'vcenter',
        'border': 1,
        'num_format': '#,##0.00'
    }
    format_content_float_redcolor = {
        'font_name': 'Times New Roman',
        'font_size': 10,
        'font_color': '#ff4000',
        'align': 'right',
        'valign': 'vcenter',
        'border': 1,
        'num_format': '#,##0.00'
    }

    format_content_center_color_green = {
        'font_name': 'Times New Roman',
        'font_size': 9,
        'font_color': '#00ff00',
        'align': 'center',
        'valign': 'vcenter',
        'border': 1,
        'num_format': '#,##0.00'
    }
    format_content_center_float = {
        'font_name': 'Times New Roman',
        'font_size': 9,
        'align': 'center',
        'valign': 'vcenter',
        'border': 1,
        'text_wrap': 1,
        'num_format': '#,##0.00'
    }

    # Саарал фонтой хар текст
    format_content_center_float_greyed_out = {
        'font_name': 'Times New Roman',
        'font_size': 9,
        'align': 'center',
        'valign': 'vcenter',
        'border': 1,
        'text_wrap': 1,
        'num_format': '#,##0.00',
        'bg_color': '#dddddd'
    }

    format_content_right_float = {
        'font_name': 'Times New Roman',
        'font_size': 9,
        'align': 'right',
        'valign': 'vcenter',
        'border': 1,
        'text_wrap': 1,
        'num_format': '#,##0.00'
    }

    format_content_left_bold_float = {
        'font_name': 'Times New Roman',
        'font_size': 9,
        'align': 'left',
        'valign': 'vcenter',
        'border': 1,
        'text_wrap': 1,
        'bold': True,
        'num_format': '#,##0.00'
    }

    format_content_left_float = {
        'font_name': 'Times New Roman',
        'font_size': 9,
        'align': 'left',
        'valign': 'vcenter',
        'border': 1,
        'num_format': '#,##0.00'
    }

    format_content_noborder = {
        'font_name': 'Times New Roman',
        'font_size': 9,
        'align': 'justify',
        'valign': 'vcenter',
        'text_wrap': 1
    }

    format_content_center_noborder = {
        'font_name': 'Times New Roman',
        'font_size': 9,
        'align': 'center',
        'valign': 'vcenter'
    }

    format_content_center_color_noborder = {
        'font_name': 'Times New Roman',
        'font_size': 9,
        'font_color': '#0033CC',
        'align': 'center',
        'valign': 'vcenter',
    }

    format_content_float_noborder = {
        'font_name': 'Times New Roman',
        'font_size': 9,
        'align': 'right',
        'valign': 'vcenter',
        'num_format': '#,##0.00'
    }

    format_content_float_color_noborder = {
        'font_name': 'Times New Roman',
        'font_size': 9,
        'font_color': '#0033CC',
        'align': 'right',
        'valign': 'vcenter',
        'num_format': '#,##0.00'
    }

    format_footer_float = {
        'font_name': 'Times New Roman',
        'font_size': 9,
        'bold': True,
        'align': 'right',
        'valign': 'vcenter',
        'border': 1,
        'bg_color': '#CFE7F5',
        'num_format': '#,##0.00'
    }