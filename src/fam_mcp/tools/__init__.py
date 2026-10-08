import importlib
import pkgutil

# Every module in this package registers its tool on import.
for module in pkgutil.iter_modules(__path__):
  importlib.import_module(f"{__name__}.{module.name}")
