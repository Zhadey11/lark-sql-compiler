# Compilador de pseudolenguaje a PostgreSQL con Lark

Compilador hecho en Python con [Lark](https://github.com/lark-parser/lark). Lee archivos `.msql` (un pseudolenguaje de una instrucción por línea) y genera el SQL de PostgreSQL equivalente en archivos `.sql`.

## Requisitos

- Python 3.8 o más nuevo
- Lark (se instala con `requirements.txt`)

## Instalación

```
sudo apt install python3 python3-venv python3-pip
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Uso

```
python3 main.py archivo.msql              # genera output/archivo.sql
python3 main.py examples/*.msql           # compila todos los ejemplos
python3 main.py examples/*.msql -o salida # guarda los .sql en otra carpeta
```

Cada archivo `.msql` genera un archivo `.sql` con el mismo nombre. Si un archivo tiene un error, se muestra la línea y la columna y no se genera su `.sql`.

## Lenguaje

Una instrucción por línea, sin `;`. Las palabras clave no distinguen mayúsculas de minúsculas.

| Instrucción | Ejemplo | SQL |
|---|---|---|
| `MAKE` | `MAKE users (id id, name text, email text!)` | `CREATE TABLE` |
| `GET` | `GET name FROM users WHERE active = true SORT name DESC TOP 5` | `SELECT ... WHERE ... ORDER BY ... LIMIT` |
| `GET ALL` | `GET ALL FROM users` | `SELECT *` |
| `PUT` sin `WHERE` | `PUT users (name = 'Alex')` | `INSERT INTO` |
| `PUT` con `WHERE` | `PUT users (name = 'Alex') WHERE id = 1` | `UPDATE ... SET` |
| `DROP` con `WHERE` | `DROP users WHERE active = false` | `DELETE FROM` |
| `DROP` sin `WHERE` | `DROP users` | `DROP TABLE` |

Condiciones: `=`, `!=`, `<>`, `>`, `<`, `>=`, `<=`, unidas con `AND` y `OR`.
Valores: texto con comillas simples o dobles, números (también negativos) y `true` / `false`.

### Tipos

| Pseudolenguaje | PostgreSQL |
|---|---|
| `id` | `BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY` |
| `num` | `NUMERIC` |
| `text` | `TEXT` |
| `bool` | `BOOLEAN DEFAULT FALSE` |
| `time` | `TIMESTAMPTZ DEFAULT NOW()` |

Un `!` al final del tipo agrega `NOT NULL` (por ejemplo `text!` es `TEXT NOT NULL` y `bool!` es `BOOLEAN NOT NULL DEFAULT FALSE`).

## Cómo funciona

| Archivo | Qué hace |
|---|---|
| `grammar.lark` | La gramática del pseudolenguaje (reglas y terminales) |
| `compiler.py` | Crea el analizador LALR de Lark y un `Transformer` que convierte cada nodo del árbol en SQL; también arma los mensajes de error |
| `main.py` | Línea de comandos: lee los `.msql` y escribe los `.sql` |
| `examples/` | Ejemplos de entrada (`.msql`) |
| `output/` | SQL generado a partir de los ejemplos |

## Ejemplo

Entrada (`examples/queries.msql`):

```
GET email, display_name FROM users WHERE active = true SORT created_at DESC TOP 20
```

Salida (`output/queries.sql`):

```sql
SELECT email, display_name
FROM users
WHERE active = TRUE
ORDER BY created_at DESC
LIMIT 20;
```