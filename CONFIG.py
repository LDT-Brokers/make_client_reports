from pathlib import Path

def check_path(path_str):
    path = Path(path_str)
    if not path.exists():
        print(f"Path {path} does not exist")
    else:
        return path

BASE_LOCATION_PATH = check_path(r'\\10.10.88.21\RecursoCompartido\ArchivosOficina\Desarrollo')
DB_PATH=check_path(r"C:\Users\feder\PycharmProjects\Precio Promedio de Compra\outputs\my_database.db")
INPUTS_PATH =check_path(BASE_LOCATION_PATH.joinpath('inputs'))
ASSETS_PATH =check_path(BASE_LOCATION_PATH.joinpath('assets'))
OUTPUT_REPORTS_PATH=check_path(r"C:\Users\feder\Downloads\reportes")
