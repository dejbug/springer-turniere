import os, re

class MonatsTurnierFilepath:
	def __init__(self, path):
		self.path = path
		self.year, self.month, self.mode = self.parse(self.path)

	def __lt__(self, other):
		if self.year < other.year:
			return True
		elif self.year == other.year:
			if self.month < other.month:
				return True
			elif self.month == other.month:
				return self.mode < other.mode

	def __str__(self):
		return f'{self.year:02}-{self.month:02} ({self.mode}) {self.path}'

	@classmethod
	def parse(cls, path):
		m = re.match(r'.*?(\d+)-(\d+)-(.)\.csv', path)
		if not m: return 0, 0, ''
		return int(m.group(1)), int(m.group(2)), m.group(3)

	@classmethod
	def iter(cls, root = '.'):
		for filename in os.listdir(root):
			m = re.match(r'(\d+)-(\d+)-(.).csv', filename)
			if m:
				y, m, t = m.groups()
				filepath = os.path.join(root, filename)
				yield cls(filepath)
