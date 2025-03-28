from sqlalchemy import String, Numeric, ARRAY
from sqlalchemy.sql.expression import FunctionElement
from sqlalchemy.ext.compiler import compiles


class CaseSensitiveString(String):
    def __init__(self, length=None):
        super(CaseSensitiveString, self).__init__(length)


# Modify how this type is handled for each dialect
@compiles(CaseSensitiveString, "sqlite")
def compile_cs_sqlite(element, compiler, **kw):
    return f"VARCHAR({element.length}) COLLATE BINARY"  # BINARY is case-sensitive in SQLite


@compiles(CaseSensitiveString, "postgresql")
def compile_cs_postgresql(element, compiler, **kw):
    return f'VARCHAR({element.length}) COLLATE "C"'  # "C" collation is case-sensitive


@compiles(CaseSensitiveString, "mysql")
def compile_cs_mysql(element, compiler, **kw):
    return f"VARCHAR({element.length}) COLLATE utf8mb4_bin"  # utf8mb4_bin is case-sensitive


class SQLArray(ARRAY):
    """Custom ARRAY type that compiles to JSON in SQL"""

    def __init__(self, item_type, **kwargs):
        super().__init__(item_type, **kwargs)


@compiles(SQLArray, "sqlite")
def compile_sqlite_array(element, compiler, **kw):
    return "JSON"


@compiles(SQLArray, "postgresql")
def compile_sqlite_array_postgresql(element, compiler, **kw):
    return compiler.visit_ARRAY(element, **kw)


@compiles(SQLArray, "mysql")
def compile_sqlite_array_mysql(element, compiler, **kw):
    return "JSON"


class DaysDiff(FunctionElement):
    type = Numeric()
    name = "days_diff"
    inherit_cache = True


@compiles(DaysDiff, "postgresql")
def compile_days_diff_postgresql(element, compiler, **kw):
    return "EXTRACT(EPOCH FROM (expire - CURRENT_TIMESTAMP)) / 86400"


@compiles(DaysDiff, "mysql")
def compile_days_diff_mysql(element, compiler, **kw):
    return "DATEDIFF(expire, UTC_TIMESTAMP())"


@compiles(DaysDiff, "sqlite")
def compile_days_diff_sqlite(element, compiler, **kw):
    return "(julianday(expire) - julianday('now'))"
