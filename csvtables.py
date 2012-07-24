import re
import csv
from itertools import chain
from collections import namedtuple
from copy import deepcopy

nonalpha = re.compile(r'[^A-Za-z0-9_]')

def levenshtein(s1, s2):
    if len(s1) < len(s2):
        return levenshtein(s2, s1)
    if not s1:
        return len(s2)
 
    previous_row = xrange(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            # j+1 instead of j since previous_row and
            # current_row are one character longer
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
 
    return previous_row[-1]

def slugify(arg):
    return nonalpha.sub('', '_'.join(arg.lower().split()))

def fix_leading_digit(arg):
    return arg if not arg[0].isdigit() else '_' + arg

def make_identifiers(headers):
    ids = [fix_leading_digit(slugify(col)) for col in headers]
    if len(ids) > len(set(ids)):
        raise Exception('Duplicate names in headers')
    return ids

def pprinttable(rows):
    if len(rows) > 1:
        headers = rows[0]._fields
        lens = []
        for i in range(len(rows[0])):
            lens.append(
                len(max(
                    [x[i] for x in rows] + [headers[i]],
                    key=lambda x:len(str(x))
                ))
            )
        formats = []
        hformats = []
        for i in range(len(rows[0])):
            if isinstance(rows[0][i], int):
                formats.append("%%%dd" % lens[i])
            else:
                formats.append("%%-%ds" % lens[i])
            hformats.append("%%-%ds" % lens[i])
        pattern = " | ".join(formats)
        hpattern = " | ".join(hformats)
        separator = "-+-".join(['-' * n for n in lens])
        data = []
        data.append(hpattern % tuple(headers))
        data.append(separator)
        for line in rows:
            data.append(pattern % tuple(line))
        return '\n'.join(data)
    elif len(rows) == 1:
        row = rows[0]
        hwidth = len(max(row._fields,key=lambda x: len(x)))
        data = []
        for i in range(len(row)):
            data.append("%*s = %s" % (hwidth,row._fields[i],row[i]))
        return '\n'.join(data)

def make_table(filename, headers=True):
    table = None
    with open(filename) as f:
        csv_data = csv.reader(f)
        table = Table(*csv_data, headers=headers)
    return table

class Table(object):

    def __init__(self, *args, **kwargs):
        arg_iterator = iter(args)
        self.has_headers = kwargs.get('headers', True)
        if self.has_headers:
            self.headers = make_identifiers(arg_iterator.next())
            self.Row = namedtuple('Row', ' '.join(self.headers))
            #print self.Row._fields
            self.data = [self.Row._make(row) for row in arg_iterator]
        else:
            self.data = [tuple(row) for row in arg_iterator]

    def __getitem__(self, key):
        if isinstance(key, int):
            return self.data[key]
        elif isinstance(key, str):
            if not self.has_headers:
                raise Exception("Expected int. Cannot access headerless data with string keys.")
            pos = self.headers.index(key)
            return [row[pos] for row in self.data]
        elif isinstance(key, tuple):
            poses = [self.headers.index(k) for k in key]
            headers = [[self.headers[p] for p in poses]]
            rows = ([row[p] for p in poses] for row in self.data)
            return Table(*chain(headers,rows))
        elif hasattr(key, '__call__'):
            headers = [self.headers]
            rows = (row for row in self.data if key(row))
            return Table(*chain(headers, rows))
        else:
            raise Exception("Unexpected item: type - " + type(key))

    def __iter__(self):
        return (row for row in self.data)

    def __len__(self):
        return len(self.data)

    def pprint(self):
        print pprinttable(self.data)

    def sort(self, key):
        if isinstance(key, str):
            pos = self.headers.index(key)
            self.data.sort(lambda x,y: cmp(x[pos], y[pos]))
        elif isinstance(key, int):
            self.data.sort(lambda x,y: cmp(x[key], y[pos]))
        elif hasattr(key, '__call__'):
            self.data.sort(key)
        else:
            self.data.sort()

    def pop(self):
        return self.data.pop()

    def copy(self):
        return deepcopy(self)

    def pop(self):
        return self.data.pop()

    def add_col(self, col_name, func):
        headers = self.headers[:]
        headers.append(col_name)
        rows = (
            chain(
                row,
                [func(row),]
            ) for row in self.data
        )
        return Table(*chain([headers],rows))

    def join(self, other_table, join, left, right):
        l_pos = self.headers.index(left)
        r_pos = other_table.headers.index(right)
        headers = self.headers[:]
        headers.append(join)
        rows = (
            chain(
                row,
                [other_table[lambda x: x[r_pos] == row[l_pos]]]
            ) for row in self.data
        )
        return Table(*chain([headers],rows))
