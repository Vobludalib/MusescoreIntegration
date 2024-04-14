import music21 as m21

class VoicingGenerator:

    @staticmethod
    def createClosedVoicing(baseChord: m21.chord.Chord, leadNote: m21.note.Note, numberOfNonDoubledNonLeadParts: int = 3, double8vb: bool = True, double8va: bool = False) -> m21.chord.Chord:
        baseChordPitchClasses = baseChord.pitchClasses
        baseChordPitchClasses.sort()

        notesInVoicing = [leadNote]
        currBaseChordIndex = 0
        # find pitch class at which to start iterating downwards from
        foundOneLower = False
        for i in range(0, len(baseChordPitchClasses)):
            if baseChordPitchClasses[i] < leadNote.pitch.pitchClass:
                currBaseChordIndex = i
                currOctave = leadNote.octave
                foundOneLower = True

        if not foundOneLower:
            currBaseChordIndex = -1
            currOctave = leadNote.octave - 1

        for i in range(0, numberOfNonDoubledNonLeadParts):
            appendNote = m21.note.Note('c').transpose(baseChordPitchClasses[currBaseChordIndex])
            appendNote.octave = currOctave
            notesInVoicing.append(appendNote)

            if (currBaseChordIndex % len(baseChordPitchClasses) == 0): currOctave -= 1
            currBaseChordIndex -= 1
            
        if double8va:
            notesInVoicing.append(leadNote.transpose(12))
            
        if double8vb:
            notesInVoicing.append(leadNote.transpose(-12))

        leadNote.notehead = 'diamond'
        leadNote.style.color = 'yellow'
        
        return m21.chord.Chord(notesInVoicing)

    @staticmethod
    def createDrop2Voicing(baseChord: m21.chord.Chord, leadNote: m21.note.Note, numberOfNonDoubledNonLeadParts: int = 3, double8vb: bool = True, double8va: bool = False) -> m21.chord.Chord:
        closedVoicing = VoicingGenerator.createClosedVoicing(baseChord, leadNote, numberOfNonDoubledNonLeadParts, double8va=False, double8vb=False)
        pitches = list(closedVoicing.pitches)
        pitches.sort(key = lambda pitch: pitch.midi)
        pitches[-2].octave -= 1

        if double8va:
            pitches.append(leadNote.transpose(12))
            
        if double8vb:
            pitches.append(leadNote.transpose(-12))

        return m21.chord.Chord(pitches)
    
    def createDrop24Voicing(baseChord: m21.chord.Chord, leadNote: m21.note.Note, numberOfNonDoubledNonLeadParts: int = 3, double8vb: bool = True, double8va: bool = False) -> m21.chord.Chord:
        closedVoicing = VoicingGenerator.createClosedVoicing(baseChord, leadNote, numberOfNonDoubledNonLeadParts, double8va=False, double8vb=False)
        pitches = list(closedVoicing.pitches)
        pitches.sort(key = lambda pitch: pitch.midi)
        pitches[-2].octave -= 1
        pitches[-4].octave -= 1

        if double8va:
            pitches.append(leadNote.transpose(12))
            
        if double8vb:
            pitches.append(leadNote.transpose(-12))

        return m21.chord.Chord(pitches)
    
    def createDrop3Voicing(baseChord: m21.chord.Chord, leadNote: m21.note.Note, numberOfNonDoubledNonLeadParts: int = 3, double8vb: bool = True, double8va: bool = False) -> m21.chord.Chord:
        closedVoicing = VoicingGenerator.createClosedVoicing(baseChord, leadNote, numberOfNonDoubledNonLeadParts, double8va=False, double8vb=False)
        pitches = list(closedVoicing.pitches)
        pitches.sort(key = lambda pitch: pitch.midi)
        pitches[-3].octave -= 1

        if double8va:
            pitches.append(leadNote.transpose(12))
            
        if double8vb:
            pitches.append(leadNote.transpose(-12))

        return m21.chord.Chord(pitches)
    
    # Spread voicings require knowledge of harmonic tensions and chord tones - TODO