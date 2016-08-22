"""ExcelResponse for maja_newsletter"""
import datetime

import pytz

from django.conf import settings
try:
    from django.db.models.query import QuerySet

    ValuesQuerySet = QuerySet
except ImportError:
    from django.db.models.query import QuerySet, ValuesQuerySet
from django.http import HttpResponse
from django.utils import timezone


class ExcelResponse(HttpResponse):
    """ExcelResponse feeded by queryset"""

    def __init__(self, data, output_name='excel_data', headers=None,
                 force_csv=False, encoding='utf8'):
        import StringIO
        output = StringIO.StringIO()
        output, mimetype, file_ext = make_excel_content(data, output, headers, force_csv, encoding)
        super(ExcelResponse, self).__init__(content=output.getvalue(),
                                            mimetype=mimetype)
        self['Content-Disposition'] = 'attachment;filename="%s.%s"' % (
            output_name.replace('"', '\"'), file_ext
        )


def _make_naive(value):
    if isinstance(value, basestring):
        return value
    if timezone.is_aware(value):
        return timezone.make_naive(value, pytz.timezone(settings.TIME_ZONE))
    return value


def make_excel_content(data, output=None, headers=None, force_csv=False, encoding='utf8'):
    valid_data = False
    if isinstance(data, QuerySet):
        data = list(data.values())
    elif isinstance(data, ValuesQuerySet):
        data = list(data)
    if hasattr(data, '__getitem__'):
        if isinstance(data[0], dict):
            if headers is None:
                headers = data[0].keys()
            data = [[row[col] for col in headers] for row in data]
            data.insert(0, headers)
        if hasattr(data[0], '__getitem__'):
            valid_data = True
    assert valid_data is True, 'ExcelResponse requires a sequence of sequences'

    # Excel has a limit on number of rows; if we have more than that, make a csv
    use_xls = False
    if len(data) <= 65536 and force_csv is not True:
        try:
            import xlwt
        except ImportError:
            pass
        else:
            use_xls = True
    if use_xls:
        book = xlwt.Workbook(encoding=encoding)
        sheet = book.add_sheet('Sheet 1')
        styles = {'datetime': xlwt.easyxf(num_format_str='yyyy-mm-dd hh:mm:ss'),
                  'date': xlwt.easyxf(num_format_str='yyyy-mm-dd'),
                  'time': xlwt.easyxf(num_format_str='hh:mm:ss'),
                  'default': xlwt.Style.default_style}
        for rowx, row in enumerate(data):
            for colx, value in enumerate(row):
                if isinstance(value, datetime.datetime):
                    cell_style = styles['datetime']
                elif isinstance(value, datetime.date):
                    cell_style = styles['date']
                elif isinstance(value, datetime.time):
                    cell_style = styles['time']
                else:
                    cell_style = styles['default']
                if colx in (3, 10):
                    value = _make_naive(value)
                sheet.write(rowx, colx, value, style=cell_style)
        book.save(output)
        mimetype = 'application/vnd.ms-excel'
        file_ext = 'xls'
    else:
        for rowx, row in enumerate(data):
            out_row = []
            for colx, value in enumerate(row):
                if not isinstance(value, basestring):
                    value = unicode(value)
                if colx in (3, 10):
                    value = _make_naive(value)
                value = value.encode(encoding)
                out_row.append(value.replace('"', '""'))
            output.write('"%s"\n' % '","'.join(out_row))
        mimetype = 'text/csv'
        file_ext = 'csv'
    output.seek(0)
    return output, mimetype, file_ext
