import re
from typing import Set, List, Union

class TagQueryEvaluator:
    def __init__(self, query: str):
        self.tokens = self._tokenize(query)
        self.pos = 0

    def _tokenize(self, query: str) -> List[str]:
        # Tokenize parentheses, pipe, exclusion tags, and standard tags
        token_pattern = r'\(|\)|\||\-[a-zA-Z0-9_:]+|[a-zA-Z0-9_:]+'
        return re.findall(token_pattern, query)

    def parse(self):
        self.pos = 0
        return self._parse_expression()

    def _parse_expression(self):
        # Handles OR expressions
        nodes = [self._parse_term()]
        while self.pos < len(self.tokens) and self.tokens[self.pos] == '|':
            self.pos += 1
            nodes.append(self._parse_term())
        return ('OR', nodes) if len(nodes) > 1 else nodes[0]

    def _parse_term(self):
        # Handles AND (space-separated sequences)
        nodes = []
        while self.pos < len(self.tokens) and self.tokens[self.pos] not in (')', '|'):
            nodes.append(self._parse_factor())
        return ('AND', nodes) if len(nodes) > 1 else (nodes[0] if nodes else None)

    def _parse_factor(self):
        token = self.tokens[self.pos]
        if token == '(':
            self.pos += 1
            node = self._parse_expression()
            if self.pos < len(self.tokens) and self.tokens[self.pos] == ')':
                self.pos += 1
            return node
        elif token.startswith('-'):
            self.pos += 1
            return ('NOT', token[1:].lower())
        else:
            self.pos += 1
            return ('TAG', token.lower())

    @staticmethod
    def evaluate(ast: Union[tuple, str, None], gallery_tags: Set[str]) -> bool:
        if ast is None:
            return True
        node_type = ast[0]

        if node_type == 'TAG':
            return ast[1] in gallery_tags
        elif node_type == 'NOT':
            return ast[1] not in gallery_tags
        elif node_type == 'AND':
            return all(TagQueryEvaluator.evaluate(child, gallery_tags) for child in ast[1])
        elif node_type == 'OR':
            return any(TagQueryEvaluator.evaluate(child, gallery_tags) for child in ast[1])
        return False
