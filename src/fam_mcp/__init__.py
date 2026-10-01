from .server import authenticate, serve
from . import tools  # registers the tools

def main() -> None:
  authenticate()
  serve()
