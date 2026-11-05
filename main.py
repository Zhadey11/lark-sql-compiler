import argparse
import sys
from pathlib import Path

from compiler import MsqlError, compile_source


def main():
    cli = argparse.ArgumentParser(
        description="Compila archivos .msql (pseudolenguaje) a SQL de PostgreSQL."
    )
    cli.add_argument("archivos", nargs="+", help="uno o mas archivos .msql")
    cli.add_argument(
        "-o", "--salida", default="output", help="carpeta donde se guardan los .sql (por defecto: output)"
    )
    args = cli.parse_args()

    output_dir = Path(args.salida)
    failed = False

    for name in args.archivos:
        source_path = Path(name)
        try:
            sql = compile_source(source_path.read_text(encoding="utf-8"))
        except OSError as error:
            print(f"{name}: no se pudo leer el archivo ({error.strerror})", file=sys.stderr)
            failed = True
            continue
        except MsqlError as error:
            print(f"{name}\n{error}", file=sys.stderr)
            failed = True
            continue

        output_dir.mkdir(parents=True, exist_ok=True)
        target = output_dir / (source_path.stem + ".sql")
        target.write_text(sql, encoding="utf-8")
        print(f"{name} -> {target}")

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()