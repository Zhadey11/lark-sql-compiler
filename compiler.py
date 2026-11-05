from pathlib import Path

from lark import Lark, Transformer, v_args
from lark.exceptions import UnexpectedCharacters, UnexpectedEOF, UnexpectedInput, UnexpectedToken

# 1. La gramatica vive en su propio archivo; Lark construye el analizador LALR
GRAMMAR_FILE = Path(__file__).with_name("grammar.lark")
parser = Lark.open(str(GRAMMAR_FILE), parser="lalr")

# Tipo del pseudolenguaje -> (tipo de PostgreSQL, resto de la definicion)
TYPES = {
    "id": ("BIGINT", "GENERATED ALWAYS AS IDENTITY PRIMARY KEY"),
    "num": ("NUMERIC", ""),
    "text": ("TEXT", ""),
    "bool": ("BOOLEAN", "DEFAULT FALSE"),
    "time": ("TIMESTAMPTZ", "DEFAULT NOW()"),
}


# 2. El Transformer recorre el arbol de Lark y va armando el SQL de cada nodo
@v_args(inline=True)
class ToPostgres(Transformer):
    def start(self, *statements):
        statements = [s for s in statements if s is not None]
        return "\n".join(statements) + "\n" if statements else ""

    # MAKE -> CREATE TABLE
    def field_def(self, name, type_token):
        text = str(type_token).lower()
        required = text.endswith("!")
        base, extra = TYPES[text.rstrip("!")]
        definition = base
        if required:
            definition += " NOT NULL"
        if extra:
            definition += " " + extra
        return f"  {name} {definition}"

    def make(self, name, *fields):
        return f"CREATE TABLE {name} (\n" + ",\n".join(fields) + "\n);"

    # GET -> SELECT
    def columns(self, *items):
        if len(items) == 1 and items[0].type == "ALL":
            return "*"
        return ", ".join(str(item) for item in items)

    def get(self, columns, table, where, sort, top):
        lines = [f"SELECT {columns}", f"FROM {table}"]
        for part in (where, sort, top):
            if part is not None:
                lines.append(part)
        return "\n".join(lines) + ";"

    def sort(self, name, direction):
        text = f"ORDER BY {name}"
        if direction is not None:
            text += " " + str(direction).upper()
        return text

    def top(self, number):
        return f"LIMIT {number}"

    # PUT -> INSERT (sin WHERE) o UPDATE (con WHERE)
    def assignment(self, name, value):
        return (str(name), value)

    def put(self, table, *rest):
        where = rest[-1]
        assignments = rest[:-1]
        if where is None:
            names = ", ".join(name for name, _ in assignments)
            values = ", ".join(value for _, value in assignments)
            return f"INSERT INTO {table} ({names})\nVALUES ({values});"
        sets = ", ".join(f"{name} = {value}" for name, value in assignments)
        return f"UPDATE {table}\nSET {sets}\n{where};"

    # DROP -> DELETE (con WHERE) o DROP TABLE (sin WHERE)
    def drop(self, table, where):
        if where is None:
            return f"DROP TABLE {table};"
        return f"DELETE FROM {table} {where};"

    # WHERE
    def where(self, condition):
        return f"WHERE {condition}"

    def condition(self, *parts):
        return " OR ".join(parts)

    def and_condition(self, *parts):
        return " AND ".join(parts)

    def comparison(self, name, operator, value):
        return f"{name} {operator} {value}"

    # Valores
    def STRING(self, token):
        text = str(token)
        if text.startswith('"'):  # "texto" -> 'texto'
            return "'" + text[1:-1].replace("'", "''") + "'"
        return text

    def BOOL(self, token):
        return str(token).upper()

    def NUMBER(self, token):
        return str(token)

    def INT(self, token):
        return str(token)


class MsqlError(Exception):
    """Error de sintaxis en el codigo fuente, con linea y columna."""


# Nombres de los terminales, para decirle al usuario que se esperaba
EXPECTED_NAMES = {
    "NAME": "un nombre",
    "TYPE": "un tipo (id, num, text, bool, time)",
    "STRING": "un texto entre comillas",
    "NUMBER": "un numero",
    "INT": "un numero entero",
    "BOOL": "true o false",
    "COMP_OP": "un operador (=, !=, <>, >, <, >=, <=)",
    "DIRECTION": "ASC o DESC",
    "LPAR": "'('",
    "RPAR": "')'",
    "COMMA": "','",
    "EQUAL": "'='",
    "_NL": "el fin de la linea",
    "$END": "el fin del archivo",
}


def _describe(expected):
    expected = set(expected)
    # al inicio de una instruccion, las lineas en blanco no son lo importante
    if expected & {"MAKE", "GET", "PUT", "DROP"}:
        expected -= {"_NL", "$END"}
    names = sorted(EXPECTED_NAMES.get(name, name) for name in expected)
    return ", ".join(names)


def _syntax_error(error, source):
    line = getattr(error, "line", 1)
    column = getattr(error, "column", 1)

    if isinstance(error, UnexpectedToken):
        found = f"'{error.token}'"
        if error.token.type in ("_NL", "$END"):
            found = EXPECTED_NAMES[error.token.type]
        message = f"se encontro {found} y se esperaba: {_describe(error.expected)}"
    elif isinstance(error, UnexpectedCharacters):
        message = f"caracter inesperado '{error.char}'"
        if error.allowed:
            message += f", se esperaba: {_describe(error.allowed)}"
    elif isinstance(error, UnexpectedEOF):
        message = f"el codigo termina antes de tiempo, se esperaba: {_describe(error.expected)}"
    else:
        message = str(error)

    lines = source.splitlines() or [""]
    code = lines[min(line, len(lines)) - 1]
    return MsqlError(
        f"Error de sintaxis [linea {line}, columna {column}]: {message}\n"
        f"  {code}\n  {' ' * (column - 1)}^"
    )


def compile_source(source):
    """Convierte codigo del pseudolenguaje en SQL de PostgreSQL."""
    try:
        tree = parser.parse(source)
    except UnexpectedInput as error:
        raise _syntax_error(error, source) from None
    return ToPostgres().transform(tree)