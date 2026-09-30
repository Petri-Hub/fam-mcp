from fastmcp import FastMCP

mcp = None
client = None

def initialize_mcp() -> None:
    mcp = FastMCP()

def main() -> None:
    print("Hello from fam-mcp!")
