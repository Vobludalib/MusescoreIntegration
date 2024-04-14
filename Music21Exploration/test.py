import music21 as m21
from voicingGenerator import *

# CRUCIAL FOR RENDERING CHORD SYMBOLS: MS4 IS STILL BUGGY AS HELL WHEN DOING COMMAND LINE DIRECT PNG RENDERING
# m21.environment.UserSettings()['musescoreDirectPNGPath'] = "/Applications/MuseScore 3.app/Contents/MacOS/mscore"
m21.environment.UserSettings()['musescoreDirectPNGPath'] = "C:\\Program Files\\MuseScore 3\\bin\\Musescore3.exe"
# print(m21.environment.UserSettings().getSettingsPath())

sc = m21.converter.parse("./OtherTest.mxl")
piano = sc.parts[0]
notesRests = list(piano.flatten().notesAndRests)
# notesRests = [t for t in notesRests if not isinstance(t, m21.harmony.ChordSymbol)]
notesRests.sort(key = lambda thing: thing.offset)
# print([t.offset for t in notesRests if not isinstance(t, m21.harmony.ChordStepModification)])

# print(notesRests)
chordSymbols = list(piano.flatten().getElementsByClass(m21.harmony.ChordSymbol))
# print([cs.offset for cs in chordSymbols])
displayPart = m21.stream.Stream()

# THIS CAN BE IMPROVED
def findRelevantChordForOffset(offset: float, chordSymbolList: list) -> m21.harmony.ChordSymbol:
    chordSymbolOffsets = [cs.offset for cs in chordSymbolList]
    maxIndex = 0
    found = False
    for i in range(0, len(chordSymbolOffsets)):
        if chordSymbolOffsets[i] <= offset:
            maxIndex = i
            found = True
    
    if not found:
        maxIndex = -1

    return chordSymbolList[maxIndex]


for noteOrRest in notesRests:
    if isinstance(noteOrRest, m21.note.Note):
        ch = findRelevantChordForOffset(noteOrRest.offset, chordSymbols)
        voicing = VoicingGenerator.createClosedVoicing(ch, noteOrRest)
        voicing.offset = noteOrRest.offset
        voicing.duration = noteOrRest.duration
        displayPart.append(voicing)
     
    elif isinstance(noteOrRest, m21.note.Rest):
        displayPart.append(noteOrRest)

    else:
        displayPart.append(noteOrRest)

for cs in chordSymbols:
    element = displayPart.getElementsByOffset(cs.offset)[0]
    element.lyric = cs.findFigure()

# print(m21.environment.UserSettings()['musescoreDirectPNGPath'])
# displayPart.show()
displayPart.write("musicxml.png", fp="test.png")