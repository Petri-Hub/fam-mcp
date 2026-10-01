from bs4 import BeautifulSoup

def to_soup(html: str) -> BeautifulSoup:
  return BeautifulSoup(html, 'html.parser')