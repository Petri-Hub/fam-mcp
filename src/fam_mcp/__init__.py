from enum import Enum

import fastmcp
import os
import httpx
import dotenv

dotenv.load_dotenv()

FAM_MCP_NAME = os.getenv("FAM_MCP_NAME")
FAM_URL = os.getenv("FAM_URL")
FAM_USERNAME = os.getenv("FAM_USERNAME")
FAM_PASSWORD = os.getenv("FAM_PASSWORD")

mcp = fastmcp.FastMCP(name=FAM_MCP_NAME)
client = httpx.Client(base_url=FAM_URL, follow_redirects=True)

def main() -> None:
  response = client.post(url="fam/validacao.php", data={
    "user": FAM_USERNAME,
    "senha": FAM_PASSWORD
  })

  successfull = "Petri" in str(response.content) # true, agora cade a porra do cookie?

