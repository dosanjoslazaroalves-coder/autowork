"""Sistema autocontido de comandos complexos do AUTOWORK."""

from .interpretador_complex import detectar_comando_complexo, interpretar_comando_complexo
from .executor_complexo import ExecutorComplexo, executar_workflow

__all__ = [
    "ExecutorComplexo",
    "detectar_comando_complexo",
    "executar_workflow",
    "interpretar_comando_complexo",
]
