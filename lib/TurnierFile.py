import re, csv, os

import lib.filetype

class TurnierFile:
	class Error(Exception): pass
	class ArgError(Error): pass
	class NotFoundError(Error): pass

	def __init__(self, path = None):
		self.path = path
		self._header = None
		self._rows = None

	@classmethod
	def check(cls, path):
		if not path: raise cls.ArgError
		if not os.path.isfile(path): raise cls.NotFoundError
		return True

	@property
	def header(self):
		self.check(self.path)
		if not self._header:
			with open(self.path, "r", encoding="utf8") as file:
				self._header = file.readline().strip()
		return self._header

	@property
	def rows(self):
		self.check(self.path)
		if not self._rows:
			with open(self.path, "r", encoding="utf8") as file:
				self._header = file.readline().strip()
				t = lib.filetype.type(self._header)
				if not t:
					raise Exception("unknown CSV type")
				elif t.startswith("t/"):
					reader = csv.reader(self.tabs2comma(line.strip()) for line in file)
					self._rows = [line for line in reader]
				else:
					reader = csv.reader(line.strip() for line in file)
					self._rows = [line for line in reader]
			for i in range(len(self._rows)):
				self._rows[i] = [cell.strip() for cell in self._rows[i]]
		return self._rows

	@property
	def type(self):
		return lib.filetype.type(self.header)

	@classmethod
	def tabs2comma(self, text):
		return re.sub(r"\t+", ",", text)

	@property
	def points_column_index(self):
		# TODO: Add more types!
		t = self.type
		if t.endswith("#NP"): return -1
		if t.endswith("#NPR"): return 2
		if t.endswith("#NGSRVPBS"): return -3
		raise Exception("score column not found: unknown table")

	@property
	def tiebreaks_column_index(self):
		if self.type.endswith("#NGSRVPBS"): return [-2, -1]
		return []

	def ranks(self, contiguous = False, roworder = True):
		#~ pscores = self.pscores()
		#~ pscores = sorted(pscores, reverse = True)
		#~ lut = range(len(pscores))
		#~ lut = sorted(lut, reverse = True, key = lambda i: pscores[i])
		#~ print(lut)

		ranks = ((i, s) for i, s in enumerate(self.pscores(tiebreaks = True), start = 1))
		ranks = sorted(ranks, reverse = True, key = lambda x: x[1])
		#~ print("ranks (sorted)   ", ranks)

		rank = 0
		last = None
		for index, rowindex_score in enumerate(ranks):
			rowindex, score = rowindex_score
			if score != last:
				last = score
				rank = rank + 1 if contiguous else index + 1
			else:
				rank = index
			ranks[index] = (rowindex, rank)

		if roworder:
			ranks = sorted(ranks, reverse = False, key = lambda x: x[0])
			#~ print("ranks (de-sorted)", ranks)

		#~ print(self.path, ranks)
		return ranks

	def pscores(self, tiebreaks = False, shift = 100):
		i = self.points_column_index
		ss = [float(row[i]) for row in self.rows]
		if tiebreaks:
			ii = self.tiebreaks_column_index
			if ii:
				ss = [[s] for s in ss]
				for j, row in enumerate(self.rows):
					for i in ii:
						ss[j].append(float(row[i]))
				if shift:
					ss = [p * shift * shift + bu * shift + so * shift for p, bu, so in ss]
		return ss

	def rscores(self, contiguous = False, roworder = True):
		ranks = self.ranks(contiguous = contiguous, roworder = roworder)
		if roworder:
			ranks = sorted(ranks, key = lambda r: r[1])

		if len(ranks) == 0: return None
		if len(ranks) == 1: return 10.0
		topscore = 9.0 if ranks[0][1] == ranks[1][1] else 10.0
		ranks = [(i, topscore if r == 1 else max(0.0, 10.0 - r)) for i, r in ranks]

		if roworder:
			ranks = sorted(ranks, key = lambda r: r[0])
		ranks = [r for i, r in ranks]
		return ranks

	def rank(self, seed, contiguous = False):
		ranks = self.ranks(contiguous = contiguous, roworder = True)
		return ranks[seed - 1][1]
		# for i, r in ranks:
		# 	if i == seed:
		# 		return r

	def pscore(self, seed):
		i = self.points_column_index
		return float(self.rows[seed - 1][i])

	def rscore(self, seed, contiguous = False):
		return self.rscores(contiguous = contiguous)[seed - 1]

	@property
	def players(self):
		t = self.type
		t = t.lstrip("t/")
		#~ print(t)
		if t.startswith("#N"):
			for seed, row in enumerate(self.rows, start = 1):
				# yield int(row[0]), row[1]
				yield seed, row[1]
		#~ elif t.startswith("RWSE"):
			#~ d = set()
			#~ for row in self.rows:
				#~ d.add(row[1])
				#~ d.add(row[2])
			#~ for i, n in enumerate(sorted(d), start=1):
				#~ yield i, n

	def player(self, seed):
		# return list(self.players)[rid][1]
		for seed_, name in self.players:
			if seed == seed_:
				return name
