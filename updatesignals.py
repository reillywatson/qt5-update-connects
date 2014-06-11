import codecs
import re
import sys

class SignalInfo:
	def __init__(self, prefix, sender, signal, receiver, slot, connectionType, fileName, lineNo):
		self.prefix = prefix
		self.sender = sender
		self.signal = signal
		self.receiver = receiver
		self.slot = slot
		self.connectionType = connectionType
		self.fileName = fileName
		self.lineNo = lineNo

def signalsForFile(path, lines):
	signals = []
	for lineNo, line in enumerate(lines):
		pattern = r'^(?P<prefix>.*)connect\((?P<sender>[\w\-\>_]+), (SIGNAL|SLOT)\((?P<signal>\w+)\(.*\), (?P<receiver>[\w\-\>_]+), (SIGNAL|SLOT)\((?P<slot>\w+)\(.*\)(?P<connectiontype>, Qt::\w+)?\);$'
		m = re.search(pattern, line)
		if m:
			signals.append(SignalInfo(m.group('prefix'), m.group('sender'), m.group('signal'), m.group('receiver'), m.group('slot'), m.group('connectiontype'), path, lineNo))
	return signals

def typeInLine(line, varName):
	words = re.split(r'[\W\<\>]+', line)
	if varName in words:
		t = words[words.index(varName) - 1]
		if 'QPointer' in words:
			return 'QPointer:' + t
		return t
	return ''

def inferType(fileName, lines, varName, lineNo):
	potentialTypes = []
	if varName == 'this':
		potentialTypes.append(fileName.split('/')[-1].split('.')[0])
	for i in range(lineNo - 1, -1, -1):
		potentialTypes.append(typeInLine(lines[i], varName))
	if varName != 'this' and not fileName.endswith('.h'):
		try:
			header = ''.join(fileName.split('.')[:-1]) + '.h'
			for line in codecs.open(header, 'r', 'utf-8').read().split('\n'):
				potentialTypes.append(typeInLine(line, varName))
		except:
			pass
	if 'ui->' in varName:
		try:
			ui = ''.join(fileName.split('.')[:-1]) + '.ui'
			search = r'class="(?P<classname>\w+)" name="%s"' % varName.split('->')[-1]
			for line in codecs.open(ui, 'r', 'utf-8').read().split('\n'):
				match = re.search(search, line)
				if match:
					potentialTypes.append(match.group('classname'))
		except:
			pass
	return set([a for a in potentialTypes if len(a) > 0 and a[0].isupper()])

def newStyleConnect(signal, senderTypes, receiverTypes):
	for senderType in senderTypes:
		for receiverType in receiverTypes:
			# TODO: this is gross
			senderSuffix = ''
			if 'QPointer:' in senderType:
				senderSuffix = '.data()'
				senderType = senderType.replace('QPointer:', '')
			receiverSuffix = ''
			if 'QPointer:' in receiverType:
				receiverSuffix = '.data()'
				receiverType = receiverType.replace('QPointer:', '')
			connectType = ''
			if signal.connectionType:
				connectType = signal.connectionType
			yield '%sconnect(%s%s, &%s::%s, %s%s, &%s::%s%s);' % (signal.prefix, signal.sender, senderSuffix, senderType, signal.signal, signal.receiver, receiverSuffix, receiverType, signal.slot, connectType)

def updateConnects(filename):
	import envoy
	lines = codecs.open(filename, 'r', 'utf-8').read().split('\n')
	while lines[-1] == '\n':
		lines = lines[:-1]
	for signal in signalsForFile(filename, lines):
		potentialLines = [a for a in newStyleConnect(signal, inferType(filename, lines, signal.sender, signal.lineNo), inferType(filename, lines, signal.receiver, signal.lineNo))]
		if len(potentialLines) > 0:
			potentialLines.append(lines[signal.lineNo])
		for line in potentialLines:
			print signal.lineNo+1, line
			lines[signal.lineNo] = line
			newfile = codecs.open(filename, 'w', 'utf-8')
			newfile.write('\n'.join(lines))
			newfile.close()
			ret = envoy.run('make -j8')
			if ret.status_code == 0:
				print 'success'
				break
			else:
				print 'failed'

def findFiles(base):
	import os
	if os.path.isfile(base):
		return [base]
	files = []
	for root, dirnames, filenames in os.walk(base):
		for f in filenames:
			files.append(os.path.join(root, f))
	return files

def main():
	if len(sys.argv) < 2:
		print 'Usage: updatesignals <paths>'
		return -1
	for path in sys.argv[1:]:
		for f in findFiles(path):
			print f
			updateConnects(f)

if __name__ == '__main__':
	sys.exit(main())
