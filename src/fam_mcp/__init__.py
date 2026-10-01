from .server import validate, authenticate, serve
from . import tools  # registers the tools

def main() -> None:
  validate()
  authenticate()
  serve()
