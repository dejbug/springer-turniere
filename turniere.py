import sys, os, re, csv, io, datetime, traceback, math

import lib.fs
import lib.filetype

from lib.MonatsTurnierFilepath import MonatsTurnierFilepath
from lib.TurnierFile import TurnierFile

class Error(Exception): pass
class InvalidFormatError(Error): pass
class InvalidPointsFieldError(Error): pass
class MissingNamesError(Error): pass

SYNONYMS = {
	'[anto]' : 'Anton',
	'[brun]' : 'Brunner',
	'[budi]' : 'Budimir',
	'[hent]' : 'Hentzner',
	'[heus]' : 'Heusel',
	'[hoff]' : 'Hoffmann',
	'[horn]' : 'Hornig',
	'[hüge]' : 'Hügelschäfer',
	'[iwan]' : 'Iwanicki',
	'[meie]' : 'Meier',
	'[mess]' : 'Messer',
	'[ochs]' : 'Ochs',
	'[pete]' : 'Petersen',
	'[pfei]' : 'Pfeiffer',
	'[rein]' : 'Reinhold',
	'[saue]' : 'Sauer',
	'[schm]' : 'Schmidt',
	'[schu]' : 'Schupp',
	'[wenz]' : 'Wenzel',
	'[sebb]' : 'Bechtold S',

	'Daniel' : '[anto]',
	'Anton' : '[anto]',
	'Daniel Anton' : '[anto]',

	'Ben' : '[brun]',
	'Benedikt': '[brun]',
	'Brunner' : '[brun]',
	'Ben Brunner': '[brun]',
	'Benedikt Brunner': '[brun]',

	'Dejan' : '[budi]',
	'Budimir' : '[budi]',
	'Dejan Budimir' : '[budi]',

	'Patrick' : '[hüge]',
	'Patty' : '[hüge]',
	'Hügelschäfer' : '[hüge]',
	'Patrick Hügelschäfer' : '[hüge]',

	'Heusel' : '[heus]',
	'Bernd' : '[heus]',
	'Bernd Heusel' : '[heus]',

	'Iwanicki' : '[iwan]',
	'Marcel' : '[iwan]',
	'Marcel Iwanicki' : '[iwan]',

	'Reiner' : '[mess]',
	'Messer' : '[mess]',
	'Reiner Messer' : '[mess]',

	'Manuel' : '[rein]',
	'Reinhold' : '[rein]',
	'Manuel Reinhold' : '[rein]',

	'Reinhold Schupp' : '[schu]',
	'Schupp' : '[schu]',

	'Willi' : '[pfei]',
	'Willy' : '[pfei]',
	'Pfeiffer' : '[pfei]',
	'Willi Pfeiffer' : '[pfei]',

	'Hein' : '[pete]',
	'Heinrich' : '[pete]',
	'Petersen' : '[pete]',
	'Heinrich Petersen' : '[pete]',
	'Hein Petersen' : '[pete]',

	'Donald' : '[wenz]',
	'Wenzel' : '[wenz]',
	'Donald Wenzel' : '[wenz]',

	'Gabriel' : '[horn]',
	'Hornig' : '[horn]',
	'Gabriel Hornig' : '[horn]',

	'Rudolf' : '[schm]',
	'Schmidt' : '[schm]',
	'Rudolf Schmidt' : '[schm]',

	'Talin' : '[hoff]',
	'Hoffmann' : '[hoff]',
	'Talin Hoffmann' : '[hoff]',

	'Bruno' : '[saue]',
	'Sauer' : '[saue]',
	'Bruno Sauer' : '[saue]',

	'Meier' : '[meie]',

	'Ochs' : '[ochs]',
	'Viktoria' : '[ochs]',
	'Viktoria Ochs' : '[ochs]',

	'Bernd Hentzner' : '[hent]',
	'Hentzner' : '[hent]',

	'Sebastian B' : '[sebb]',
	'Sebastian Bechtold' : '[sebb]',
	'Bechtold S' : '[sebb]',
}

# p = lib.fs.path('springer-turniere', 'tables/blitz-23-01.csv')
#
# def iterParsableTournamentFiles():
# 	root = fs.path('turniere', 'tables')
# 	for n in os.listdir(root):
# 		p = os.path.join(root, n)
# 		pt = fs.ptype(p)
# 		if not pt:
# 			print(f'* unknown ptype: "{p}"')
# 			continue
# 		ft = fs.ftype(p)
# 		yield p, pt, ft
#
# for p, pt, ft in sorted(iterParsableTournamentFiles(), key = lambda x: (x[1].year, x[1].month, x[1].type)):
# 	if pt.type[0] not in 'bs': continue
# 	print(f'{pt.year:02}-{pt.month:02} ({pt.type[0]}) {ft}')
#
# p = fs.path('turniere', '23-10-s.csv')
# print(fs.ftype(p))

def test1():
	# FIXME: Liest 23-02-s.csv falsch. (Es war ein doble-round-robin!)

	root = lib.fs.root('springer-turniere')

	# for t in sorted(iterMonthlyTournaments(23, root)):
	# 	print(t)

	for t in sorted(MonatsTurnierFilepath.iter(root)):
		print()
		print(t)

		f = TurnierFile(t.path)
		# print(dir(f))
		# print(f.ranks())
		# print(f.pscores())
		# print(f.rscores(roworder = True))
		# print(f.rank(3))
		# print(list(f.players()))

		# for rid, name in f.players():
		# 	print(f'{rid:>2} {name.split()[-1]:12} {f.pscore(rid):>4}   {f.rscore(rid):>5}')

		for rid, rank in f.ranks(roworder = False):
			name = f.player(rid).split()[-1]
			print(f'{rid:>2} {rank:>2} {name:12} {f.pscore(rid):>4}   {f.rscore(rid):>5}')


class Record:
	def __init__(self, path):
		self.path = path
		self.type, self.rows = self.load(path)

	def __repr__(self):
		return type(self).__name__ + str(self.__dict__)

	@property
	def table(self):
		return self.type

	@property
	def pcount(self):
		return len(self.rows) - 1

	def name(self, pid):
		return self.rows[pid][1]

	def lastname(self, pid):
		return self.rows[pid][1].split()[-1]

	@classmethod
	def load(cls, path, encoding = 'utf8'):
		lines = []
		header = None
		type = None
		with open(path, encoding = encoding) as file:
			for i, line in enumerate(file):
				line = line.strip()
				if i == 0:
					header = line
					type = lib.filetype.type(header)
					if not type:
						raise InvalidFormatError('invalid file header')
				lines.append(line)

			# signature = lib.filetype.signature(lines)

			if type.startswith('t/'):
				reader = csv.reader(re.sub(r'\t+', ',', line.strip()) for line in lines)
				rows = [line for line in reader]
			else:
				reader = csv.reader(line.strip() for line in lines)
				rows = [line for line in reader]

			for i in range(len(rows)):
				rows[i] = [cell.strip() for cell in rows[i]]

			return type, rows
'''
	@classmethod
	def load(cls, path):
		with open(path, "r", encoding="utf8") as file:
			lines = [line.strip() for line in file]

		type = CsvFileType.fromLines(lines)

		if type.istabbed:
			reader = csv.reader(re.sub(r"\t+", ",", line) for line in lines)
			rows = [line for line in reader]
		else:
			reader = csv.reader(line.strip() for line in lines)
			rows = [line for line in reader]

		for i in range(len(rows)):
			rows[i] = [cell.strip() for cell in rows[i]]

		header = rows[0]
		rows = rows[1:]

		return type, header, rows
'''

# test1(); exit()

def test2():
	root = lib.fs.root('springer-turniere')
	for i, t in enumerate(sorted(MonatsTurnierFilepath.iter(root))):
		if i >= 3: break
		if t.year != 23: continue
		print(t)
		# f = TurnierFile(t.path)
		# print(f.type)
		# with open(f.path) as file:
		# 	print(lib.filetype.signature(file.read().split('\n')))
		r = Record(t.path)
		print(r.table)
		for pid in range(1, r.pcount + 1):
			print(r.lastname(pid))
		print()


def load(path, encoding = 'utf8'):
	lines = []
	header = None
	type = None
	loader = None
	with open(path, encoding = encoding) as file:
		for i, line in enumerate(file):
			line = line.strip()
			if i == 0:
				header = line
				type = lib.filetype.type(header)
				if not type:
					raise InvalidFormatError('invalid file header')
			lines.append(line)

		# signature = lib.filetype.signature(lines)

		tabbed = type.startswith('t/')
		if tabbed:
			type = type[2:]

		if tabbed:
			reader = csv.reader(re.sub(r'\t+', ',', line) for line in lines)
			rows = [line for line in reader]
		else:
			reader = csv.reader(line for line in lines)
			rows = [line for line in reader]

		for i in range(len(rows)):
			rows[i] = [cell.strip() for cell in rows[i]]

		if type.startswith('#NGSR'):
			loader = loadWinDrawTable
		elif type.startswith('#NPR'):
			loader = loadRoundsTable
		elif type.startswith('#N'):
			loader = loadCrossTable

		return rows, loader

def loadCrossTable(rows):
	pc = len(rows) - 1	# player count
	cc = len(rows[0])	# column count
	assert cc >= pc + 2
	ec = cc - 2 - pc	# extra columns count
	# print(pc, cc, ec)
	for pid, row in enumerate(rows[1:], start = 1):
		assert len(row) >= cc
		seed = row[0]
		name = row[1]
		results = parseResults(pid, row[2 : 2 + pc])
		points = None
		if cc > 2 + pc:
			points = parseFloat(row[2 + pc])
		place = None
		if cc > 2 + pc + 1:
			place = row[2 + pc + 1]
		print(f'{seed:>2} {name:>12}', results, f'{points:4}', place)

def loadWinDrawTable(rows):
	pass

def loadRoundsTable(rows):
	pass

def parseFloat(text):
	try: return float(text)
	except:
		return text

def parseResults(pid, cols):
	cols[pid - 1] = None
	for i in range(len(cols)):
		cols[i] = Result.parse(cols[i])
	return cols

class Result:
	def __init__(self, first, firstWhite = True, second = None, secondWhite = None):
		self.first = first
		self.firstWhite = firstWhite
		self.second = second
		self.secondWhite = secondWhite

	def __repr__(self):
		def resulToString(value, white):
			if value is None: return '--'
			elif value == .5: value = '='
			else: value = str(value)
			return value + ('w' if white else 'b')

		left = resulToString(self.first, self.firstWhite)
		if self.second is None:
			return f'{left}'
		right = resulToString(self.second, self.secondWhite)
		return f'{left}/{right}'

	@classmethod
	def parse(cls, text):
		if text is None or text == '\'':
			return cls(None, True, None, True)
		m = re.match(r'(0?\.5|[01+-=])(\*?)(?:/(0?\.5|[01+-=])(\*?))?', text)
		if not m:
			raise ValueError(f'invalid result: "{text}"')
		first, firstStar, second, secondStar = m.groups()
		first = translateResultValue(first)
		second = translateResultValue(second)
		firstWhite = not firstStar
		secondWhite = not secondStar
		return cls(first, firstWhite, second, secondWhite)

def translateResultValue(text):
	if text is None: return None
	if text == '+' or text == '1': return 1
	if text == '-' or text == '0': return 0
	if text == '=' or text == '0.5' or text == '.5': return 0.5
	raise ValueError(f'could not translate result: "{text}"')

def test3():
	root = lib.fs.root('springer-turniere')
	for i, t in enumerate(sorted(MonatsTurnierFilepath.iter(root))):
			# if i >= 3: break
			if t.year != 23: continue
			print()
			print(t)
			rows, loader = load(t.path)

			# for row in rows: print(row)

			if not loader:
				raise InvalidFormatError('unable to load table')
			r = loader(rows)
			print(r)


class Table:
	def __init__(self, pathOrFile, encoding = 'utf8'):
		if isinstance(pathOrFile, MonatsTurnierFilepath):
			self.file = pathOrFile
			self.path = self.file.path
		else:
			self.file = None
			self.path = pathOrFile
		self.type, self.lines = self.load(self.path, encoding)

	@classmethod
	def loadLines(cls, path, encoding = 'utf8'):
		lines = []
		type = None
		with open(path, encoding = encoding) as file:
			for i, line in enumerate(file):
				line = line.strip()
				if not line: continue
				if i == 0:
					type = lib.filetype.type(line)
					if not type:
						raise InvalidFormatError('invalid file header')
				lines.append(line)
		return type, lines

	@classmethod
	def chopLines(cls, type, lines):
		tabbed = type.startswith('t/')
		if tabbed:
			type = type[2:]
			reader = csv.reader(re.sub(r'\t+', ',', line) for line in lines)
			lines = [line for line in reader]
		else:
			reader = csv.reader(line for line in lines)
			lines = [line for line in reader]
		for i in range(len(lines)):
			lines[i] = [cell.strip() for cell in lines[i]]
		return type, lines

	@classmethod
	def substituteIdentityChar(cls, type, lines, char = 'X'):
		if type != '#NPR' and not type.startswith('#NGSR'):
			for pid in range(1, len(lines)):
				lines[pid][1 + pid] = char
		return type, lines

	@classmethod
	def load(cls, path, encoding = 'utf8'):
		type, lines = cls.loadLines(path, encoding)
		# signature = lib.filetype.signature(lines)
		type, lines = cls.chopLines(type, lines)
		type, lines = cls.substituteIdentityChar(type, lines)

		# loader = None
		# if type.startswith('#NGSR'):
		# 	loader = loadWinDrawTable
		# elif type.startswith('#NPR'):
		# 	loader = loadRoundsTable
		# elif type.startswith('#N'):
		# 	loader = loadCrossTable

		return type, lines

	@property
	def pcount(self):
		return len(self.lines) - 1

	@property
	def ccount(self):
		return len(self.lines[0])

	def name(self, pid):
		return self.lines[pid][1]

	def print(self):
		for line in self.lines:
			print(f'{line[0]:>2} {line[1]:>20}', end = '  ')
			for col in line[2:]:
				print(col, end = '\t')
			print()


class Table2(Table):
	def __init__(self, path, encoding = 'utf8'):
		super().__init__(path, encoding)

	def getInt(self, row, col):
		return int(self.lines[row][col])

	def getFloat(self, row, col):
		return float(self.lines[row][col])

	@classmethod
	def parseSingleResult(cls, text):
		mark = text.find('*') > -1
		text = text.strip('*')
		if text == '1' or text == '+': return 1, mark
		if text == '0' or text == '-': return 0, mark
		if text == '.5' or text == '0.5' or text == '=': return .5, mark
		return None, mark

	@classmethod
	def parseResult(cls, text):
		rr = []
		for r in text.split('/'):
			rr.append(cls.parseSingleResult(r))
		return rr

	def result(self, pid, oid):
		if pid == oid:
			return None
		if self.type == '#NP':
			text = self.lines[pid][1 + oid]
			return (pid, oid, self.parseResult(text))

	def results(self, pid):
		rr = []
		if self.type == '#NP':
			for oid, text in enumerate(self.lines[pid][2 : 2 + self.pcount], start = 1):
				if pid != oid:
					r = pid, oid, self.parseResult(text)
					rr.append(r)
			return rr
		elif self.type == '#NPR':
			for text in self.lines[pid][3:]:
				m = re.match(r'(\d+)([wsb])(0?\.5|[10+-=])', text)
				if m:
					oid, color, score = m.groups()
					r = pid, int(oid), [(float(score), color in 'sb')]
					rr.append(r)
			return rr

	def pointsField(self, pid):
		if self.type == '#NP':
			# return self.lines[pid][2 + self.pcount]
			return self.getFloat(pid, 2 + self.pcount)
		elif self.type == '#NPR':
			return self.getFloat(pid, 2)
		elif self.type == '#NGSRVPBS':
			return self.getFloat(pid, 2 + 4)

	def points(self, pid):
		if self.type == '#NGSRVPBS':
			return self.getInt(pid, 3) + self.getInt(pid, 4) * .5
		else:
			results = self.results(pid)
			points = 0.0
			if results:
				for pid, oid, scores in results:
					points += sum(r[0] or 0 for r in scores)
				return points

	def checkPoints(self):
		for pid in range(1, 1 + self.pcount):
			if self.pointsField(pid) != self.points(pid):
				raise InvalidPointsFieldError(f'{self.pointsField(pid)} != {self.points(pid)} [{self.path}]')


class Table3(Table2):
	def __init__(self, path, encoding = 'utf8'):
		super().__init__(path, encoding)

	def sonneborn(self, pid):
		if self.type == '#NGSRVPBS':
			return self.getFloat(pid, -1)
		else:
			value = 0
			for pid, oid, scores in self.results(pid):
				opt = self.points(oid)
				for score, black in scores:
					if score: # is not None:
						value += score * opt
			return value

	def buchholz(self, pid):
		if self.type == '#NGSRVPBS':
			return self.getFloat(pid, -2)
		else:
			value = 0
			for pid, oid, scores in self.results(pid):
				opt = self.points(oid)
				value += opt
			return value

	def ranking(self):
		if self.type.startswith('#N'):
			rr = []
			for pid in range(1, 1 + self.pcount):
				name = self.lines[pid][1]
				points = self.points(pid)
				so = self.sonneborn(pid)
				bu = self.buchholz(pid)
				r = Ranking(pid, name, points, so, bu)
				rr.append(r)
				# points = fpad(points, 2, 1)
				# so = fpad(so, 3, 2)
				# bu = fpad(bu, 3, 1)
				# print(f'{pid:>2} {name:>10} {points:<4} {so} {bu}')
			return rr

def fpad(score, ilength, flength, strip = True):
	if not score:
		return "%s0 %s" % (" " * (ilength - 1), " " * flength)
	s = ("%%%d.%df" % (ilength, flength)) % score
	s = ("%%%ds" % (ilength + 1 + flength)) % s
	if strip:
		s = s.rstrip("0")
		s = s.rstrip(".")
	return s + " " * (ilength + 1 + flength - len(s))


def normalizeNames(table, SYNONYMS):
	missing = []
	if table.type.startswith('#N'):
		for line in table.lines[1:]:
			if line[1] in SYNONYMS:
				line[1] = SYNONYMS[line[1]]
			else:
				missing.append(line[1])
	return missing


class Ranking:
	def __init__(self, pid = 0, name = '', points = 0, so = 0, bu = 0):
		self.pid, self.name, self.points, self.so, self.bu = pid, name, points, so, bu

	def __lt__(self, other):
		if self.points < other.points: return True
		elif self.points == other.points:
			if self.so < other.so: return True
			elif self.so == other.so:
				if self.bu < other.bu: return True
				elif self.bu == other.bu:
					if self.name < other.name: return True
					else:
						return self.pid < other.pid

	def __getitem__(self, key):
		if key == 0: return self.pid
		if key == 1: return self.name
		if key == 2: return self.points
		if key == 3: return self.so
		if key == 4: return self.bu

	def __iter__(self):
		yield self.pid
		yield self.name
		yield self.points
		yield self.so
		yield self.bu

def sortRanking(ranking):
	ranking = sorted(ranking, key = lambda r: (r.name, r.pid))
	ranking = sorted(ranking, key = lambda r: (r.points, r.so, r.bu), reverse = True)
	return ranking

def placingFromRanking(ranking, tiebreaks = False):
	if tiebreaks:
		return {r[0] : i for i, r in enumerate(sortRanking(ranking), start = 1)}
	pp = {}
	if ranking:
		ranking = sortRanking(ranking)
		place = 1
		for i in range(len(ranking)):
			if i > 0 and ranking[i].points != ranking[i - 1].points:
				place = i + 1
			pp[ranking[i].pid] = place
	return pp

def grandPrixScoreFromPlacing(placing):
	xx = {}
	x = 10
	if len(placing) == 0: return {}
	if len(placing) == 1: return { placing.keys()[0] : x }
	placing = sorted(placing.items(), key = lambda p: p[1])
	if placing[0][1] == placing[1][1]:
		x = 9
	oldplace = None
	for pid, place in placing:
		if oldplace is not None and place != oldplace:
			x = 10 - place
		xx[pid] = x
		oldplace = place
	return xx
	x = 10
	if len(placing) == 0: pass
	elif len(placing) == 1:
		xx[placing[0][0]] = x
	else:
		if placing[0][1] == placing[1][1]:
			x = 9
		for i in range(len(placing)):
			if i > 0 and placing[i][1] != placing[i - 1][1] and x > 0:
				x -= 1
			xx[placing[i][0]] = x
	return xx

def getFullRanking(ranking):
	placing = placingFromRanking(ranking, tiebreaks = False)
	gp = grandPrixScoreFromPlacing(placing)
	return ranking, placing, gp

def printRanking(ranking, sorted = True):
	if ranking:
		if sorted:
			ranking = sortRanking(ranking)
		print(f' # {"Name":>10}|{"Pt":>3}  |{"So":>3}   |{"Bu":>3}  |')
		for pid, name, points, so, bu in ranking:
			points = fpad(points, 2, 1)
			so = fpad(so, 3, 2)
			bu = fpad(bu, 3, 1)
			print(f'{pid:>2} {name:>10}| {points:<4}|{so}|{bu}|')

def printFullRanking(ranking, placing, gp, sorted = True):
	if ranking:
		if sorted:
			ranking = sortRanking(ranking)
		# placing = placingFromRanking(ranking, tiebreaks = False)
		# gp = grandPrixScoreFromPlacing(placing)
		print(f'Pl Gp {"Name":>10}|{"Pt":>3}  |{"So":>3}   |{"Bu":>3}  |')
		for pid, name, points, so, bu in ranking:
			points = fpad(points, 2, 1)
			so = fpad(so, 3, 2)
			bu = fpad(bu, 3, 1)
			print(f'{placing[pid]:>2} {gp[pid]:>2} {name:>10}| {points:<4}|{so}|{bu}|')

def iterTournamentFilesForYear(yy = None):
	ff = []
	if not yy:
		t = datetime.datetime.now()
		yy = t.year % 100
	root = lib.fs.path('springer-turniere', 'tables')
	for i, f in enumerate(sorted(MonatsTurnierFilepath.iter(root))):
		if f.year != yy: continue
		ff.append(f)
	return ff

def iterTablesForTournamentFiles(ff, verbose = True):
	tt = []
	for f in ff:
		try:
			t = Table3(f)
		except InvalidFormatError as e:
			if verbose: print('FAIL  |', f,  '\n')
			traceback.print_exception(e)
			continue
		else:
			if verbose: print('  OK  |', f)
		# print(t.pcount, t.ccount, t.type)
		missing = normalizeNames(t, SYNONYMS)
		if missing:
			raise MissingNamesError(f.path, missing)
		normalizeNames(t, SYNONYMS)
		# t.print()
		# print(t.result(1, 2))
		# print(t.results(1))
		t.checkPoints()
		tt.append(t)
	if verbose: print()
	return tt

def printFullRankings(tt):
	for t in tt:
		ranking = t.ranking()
		print()
		# printRanking(ranking)
		# placing = placingFromRanking(ranking, tiebreaks = True)
		placing = placingFromRanking(ranking)
		gp = grandPrixScoreFromPlacing(placing)
		printFullRanking(ranking, placing, gp)
		print()

def getHistoryForTournamentTables(tt):
	# history = { '.meta' : {} }
	history = { }
	for t in tt:
		ranking = t.ranking()
		# printRanking(ranking); print()
		# placing = placingFromRanking(ranking, tiebreaks = True)
		placing = placingFromRanking(ranking)
		gp = grandPrixScoreFromPlacing(placing)
		# printFullRanking(ranking, placing, gp); print()
		for pid, score in gp.items():
			name = t.name(pid)
			if name not in history:
				history[name] = [score]
				# history['.meta'][name] = { 'placing' : placing, 'gp' : gp }
			else:
				history[name].append(score)
	# print(history)
	return history

def getTotalsForTournamentHistory(history):
	totals = {}
	for name, scores in history.items():
		# if name == '.meta': continue
		scores = sorted(scores, reverse = True)
		history[name] = sorted(scores, reverse = True)
		totals[name] = sum(scores[:9])
	return totals

def getTitleForTournamentFiles(ff):
	out = io.StringIO()
	yy = ff[0].year
	year = yy + 2000
	ma = ff[0].month
	mz = ff[-1].month
	if mz - ma + 1 < 12:
		mm = ['', 'Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez']
		ma = mm[ma]
		mz = mm[mz]
		# out.write('Schnellschach-Meisterschaft %d\n' % year)
		# out.write('    ( * Zwischenstand %s - %s )' % (ma, mz))
		out.write('Schnellschach-Meisterschaft\n')
		# out.write(f' ----- {year} ----- ({ma}-{mz})')
		out.write(f'         {year}     ({ma}-{mz})')
	else:
		out.write('Schnellschach-Meisterschaft %d' % year)
	return out.getvalue()

def getIntegerStringLength(i):
	return int(math.log(i, 10)) + 1

def getPrintTotalsLengthInfo(history, totals):
	longestHistory = max(len(scores) for scores in history.values())
	info = { 'historyLength' : longestHistory }

	longestScoreLengths = [ 0 for i in range(longestHistory) ]
	for name, total in sorted(totals.items(), key = lambda x: x[1], reverse = True):
		scores = history[name]
		# print(name, total, scores, longestHistory - len(scores))
		scoreLengths = []
		for i, score in enumerate(scores):
			# scoreLengths[i] = len(str(score))
			# scoreLengths.append(int(math.log(score, 10)) + 1)
			scoreLength = getIntegerStringLength(score)
			scoreLengths.append(scoreLength)
			longestScoreLengths[i] = max(longestScoreLengths[i], scoreLength)
		for i in range(len(scores), longestHistory):
			scoreLengths.append(0)
		info[name] = { 'scoreLengths' : scoreLengths, 'totalLength' : getIntegerStringLength(total) }
	info['longestScoreLengths'] = longestScoreLengths

	scoreFormats = []
	for i in range(longestHistory):
		scoreFormats.append(f'%{longestScoreLengths[i]}s')
	info['scoreFormats'] = scoreFormats

	# print(info)
	return info

def printTotals(history, totals, header = True):
	maxNameLength = 0
	for name in totals.keys():
		maxNameLength = max(maxNameLength, len(name))

	longestHistory = max(len(scores) for scores in history.values())

	longestHistoryString = 0
	for score in history.values():
		length = sum(len(str(s)) for s in score)
		longestHistoryString = max(longestHistoryString, length)
		# print(score, length)

	if header:
		print(f'%{maxNameLength}s' % 'Name', f'{"Gp":>3}  | Historie')
		print('-' * (maxNameLength + 1 + 3 + 2) + '+' + '-' * (longestHistoryString + longestHistory))

	info = getPrintTotalsLengthInfo(history, totals)
	scoreFormats = info['scoreFormats']

	colsep = ' '
	spacer = '.'
	for name, total in sorted(totals.items(), key = lambda x: x[1], reverse = True):
		scores = history[name]
		# print(f'{name:>10} {total:>3}  |{"|".join("%2d" % s for s in scores)}|')
		# print(f'{name:>10} {total:>3}  |', end = ' ')
		print(f'%{maxNameLength}s' % name, f'{total:>3}  |', end = ' ')
		for i in range(longestHistory):
			# print(f'{score:>2}', end = '|')
			if i < 9:
				if i < len(scores):
					# print(f'{scores[i]:>2}', end = colsep)
					print(scoreFormats[i] % scores[i], end = colsep)
				else:
					# print(f'{spacer:>2}', end = colsep)
					print(scoreFormats[i] % spacer, end = colsep)
			else:
				if i == 9:
					print(' / ', end = '')
				if i < len(scores):
					# print(f'{scores[i]:>2}', end = colsep)
					print(scoreFormats[i] % scores[i], end = colsep)
				else:
					# print(f'{spacer:>2}', end = colsep)
					print(scoreFormats[i] % spacer, end = colsep)

		# for i in scores[9:]:

		'''
		h = '|'.join(f'{s:>2}' for s in scores[:9]) + '|'
		print(h, end = ' ')
		if scores[9:]:
			print(' ' * (3 * 9 - len(h)), scores[9:])
		else:
			print()
		'''
		print()



"""
def main_old():
	root = lib.fs.root('springer-turniere')
	history = {}
	for i, f in enumerate(sorted(MonatsTurnierFilepath.iter(root))):
		# if i >= 3: break
		# if f.year != 23: continue
		if f.year != 24: continue
		print()
		print(f)
		print()
		t = Table3(f.path)
		# print(t.pcount, t.ccount, t.type)
		normalizeNames(t, SYNONYMS)
		normalizeNames(t, SYNONYMS)
		t.print()
		# print(t.result(1, 2))
		# print(t.results(1))
		t.checkPoints()
		ranking = t.ranking()
		print()
		# printRanking(ranking)
		# placing = placingFromRanking(ranking, tiebreaks = True)
		placing = placingFromRanking(ranking)
		gp = grandPrixScoreFromPlacing(placing)
		printFullRanking(ranking, placing, gp)
		print()
		# The September tournament was aborted after 4 rounds.
		if f.year == 24 and f.month == 9:
			continue
		for pid, score in gp.items():
			name = t.name(pid)
			if name not in history:
				history[name] = [score]
			else:
				history[name].append(score)
		# print(history)
	totals = {}
	for name, scores in history.items():
		scores = sorted(scores, reverse = True)
		history[name] = sorted(scores, reverse = True)
		totals[name] = sum(scores[:9])
	print('Schnellschach-Meisterschaft* 2024')
	print('      ( * Zwischenstand)')
	print()
	print(f'{"Name":>10} {"Gp":>3}  | Historie')
	longestHistory = max(len(scores) for scores in history.values())

	colsep = ' '
	spacer = '.'
	for name, total in sorted(totals.items(), key = lambda x: x[1], reverse = True):
		scores = history[name]
		# print(f'{name:>10} {total:>3}  |{"|".join("%2d" % s for s in scores)}|')
		print(f'{name:>10} {total:>3}  |', end = ' ')
		for i in range(longestHistory):
			# print(f'{score:>2}', end = '|')
			if i < 9:
				if i < len(scores):
					print(f'{scores[i]:>2}', end = colsep)
				else:
					print(f'{spacer:>2}', end = colsep)
			else:
				if i == 9:
					print(' / ', end = '')
				if i < len(scores):
					print(f'{scores[i]:>2}', end = colsep)
				else:
					print(f'{spacer:>2}', end = colsep)

		# for i in scores[9:]:

		'''
		h = '|'.join(f'{s:>2}' for s in scores[:9]) + '|'
		print(h, end = ' ')
		if scores[9:]:
			print(' ' * (3 * 9 - len(h)), scores[9:])
		else:
			print()
		'''
		print()
"""



if __name__ == '__main__':
	# main_old()
	ff = iterTournamentFilesForYear()
	tt = iterTablesForTournamentFiles(ff)
	# for t in tt: t.print(); print()
	# printFullRankings(tt)
	history = getHistoryForTournamentTables(tt)
	# print(history)
	totals = getTotalsForTournamentHistory(history)
	# print(totals)
	title = getTitleForTournamentFiles(ff)
	print(title)
	print('\n    * Mai-Resultate fehlen!\n')
	printTotals(history, totals, header = True)
