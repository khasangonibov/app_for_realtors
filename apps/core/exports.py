"""
Утилиты для экспорта данных в Excel.
Используем openpyxl — уже установлен в requirements/base.txt.
"""

import io
from datetime import datetime
from django.http import HttpResponse
import openpyxl
from openpyxl.styles import (
    Font, PatternFill, Alignment, Border, Side
)
from openpyxl.utils import get_column_letter


def create_excel_response(filename: str) -> tuple:
    """Создаёт HttpResponse и workbook для Excel файла.
    Возвращает (workbook, worksheet, response).
    """
    wb = openpyxl.Workbook()
    ws = wb.active

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    return wb, ws, response


def style_header_row(ws, headers: list, row: int = 1):
    """Стилизует строку заголовков — синий фон, белый жирный текст."""
    header_fill = PatternFill(
        start_color='1F4E79',
        end_color='1F4E79',
        fill_type='solid',
    )
    header_font = Font(color='FFFFFF', bold=True, size=11)
    header_alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)

    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=row, column=col, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = header_alignment

    ws.row_dimensions[row].height = 30


def style_data_rows(ws, start_row: int, end_row: int, col_count: int):
    """Чередующийся фон строк для читаемости."""
    light_fill = PatternFill(
        start_color='EBF3FB',
        end_color='EBF3FB',
        fill_type='solid',
    )
    border = Border(
        bottom=Side(style='thin', color='DEE2E6')
    )

    for row in range(start_row, end_row + 1):
        for col in range(1, col_count + 1):
            cell = ws.cell(row=row, column=col)
            if row % 2 == 0:
                cell.fill = light_fill
            cell.border = border
            cell.alignment = Alignment(vertical='center', wrap_text=True)


def auto_width_columns(ws, min_width: int = 10, max_width: int = 50):
    """Автоматически подбирает ширину столбцов по содержимому."""
    for col in ws.columns:
        max_length = 0
        col_letter = get_column_letter(col[0].column)

        for cell in col:
            if cell.value:
                length = len(str(cell.value))
                if length > max_length:
                    max_length = length

        adjusted_width = min(max(max_length + 2, min_width), max_width)
        ws.column_dimensions[col_letter].width = adjusted_width


def finalize_excel(wb, ws, response, start_row: int, col_count: int):
    """Финальная стилизация и запись в response."""
    # Закрепляем первую строку (заголовки)
    ws.freeze_panes = 'A2'

    # Стилизуем строки данных
    last_row = ws.max_row
    if last_row >= start_row:
        style_data_rows(ws, start_row, last_row, col_count)

    # Автоширина столбцов
    auto_width_columns(ws)

    # Записываем в response
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    response.write(output.getvalue())

    return response