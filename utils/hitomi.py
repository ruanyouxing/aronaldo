import re
from typing import List, Union, Optional, Collection

class BooleanQueryParser:
    def __init__(self, query: str):
        self.tokens = self._tokenize(query)
        self.pos = 0

    def _tokenize(self, query: str) -> List[str]:
        pattern = r'\(|\)|\||\-[\w:]+|[\w:]+'
        return re.findall(pattern, query.strip())

    def parse(self) -> Optional[tuple]:
        self.pos = 0
        if not self.tokens:
            return None
        return self._parse_or()

    def _parse_or(self):
        nodes = [self._parse_and()]
        while self.pos < len(self.tokens) and self.tokens[self.pos] == '|':
            self.pos += 1
            nodes.append(self._parse_and())
        return ('OR', nodes) if len(nodes) > 1 else nodes[0]

    def _parse_and(self):
        nodes = []
        while self.pos < len(self.tokens) and self.tokens[self.pos] not in (')', '|'):
            nodes.append(self._parse_factor())
        return ('AND', nodes) if len(nodes) > 1 else (nodes[0] if nodes else None)

    def _parse_factor(self):
        if self.pos >= len(self.tokens):
            return None

        token = self.tokens[self.pos]
        if token == '(':
            self.pos += 1
            node = self._parse_or()
            if self.pos < len(self.tokens) and self.tokens[self.pos] == ')':
                self.pos += 1
            return node
        elif token.startswith('-'):
            self.pos += 1
            return ('NOT', token[1:].lower())
        else:
            self.pos += 1
            return ('TERM', token.lower())

    @staticmethod
    def evaluate(ast: Optional[tuple], targets: Union[Collection[str], str]) -> bool:
        if ast is None:
            return True

        if targets is None:
            target_set = set()
        elif isinstance(targets, str):
            target_set = {targets.lower().replace(" ", "_")}
        else:
            target_set = {str(item).lower().replace(" ", "_") for item in targets}

        node_type = ast[0]

        if node_type == 'TERM':
            return ast[1] in target_set
        elif node_type == 'NOT':
            return ast[1] not in target_set
        elif node_type == 'AND':
            return all(BooleanQueryParser.evaluate(child, target_set) for child in ast[1] if child is not None)
        elif node_type == 'OR':
            return any(BooleanQueryParser.evaluate(child, target_set) for child in ast[1] if child is not None)
        
        return True


def get_thumbnail_url(gallery_id: int, file_info: dict) -> str:
    hash_val = file_info.get("hash", "")
    if not hash_val:
        return ""

    part1 = hash_val[-1]
    part2 = hash_val[-3:-1]

    return f"https://tn.gold-usergeneratedcontent.net/webpbigtn/{part1}/{part2}/{hash_val}.webp"
