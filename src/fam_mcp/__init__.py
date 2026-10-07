from .server import validate, serve
from . import tools  # registers the tools

def main() -> None:
  validate()
  serve()
