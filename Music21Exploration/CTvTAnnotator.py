import music21 as m21

class CTandTAnnotator:
    
    # ADD SUPPORT FOR SLASH CHORDS?
    @staticmethod
    def AnnotateChord(voicing: m21.chord.Chord, underlyingHarmony: m21.harmony.ChordSymbol):
        bassPitch = underlyingHarmony.bass()
        listOfIntervals = []
        listOfAdjustedNotes = []
        for pitch in voicing.pitches:
            newPitch = m21.pitch.Pitch(pitch)
            diff = pitch.midi - bassPitch.midi
            octaveDelta = abs((diff-1)// 12)
            if diff < 0: # Flip from below to just above
                newPitch.octave += octaveDelta
            
            if diff > 21:
                newPitch.octave -= octaveDelta

            listOfAdjustedNotes.append(newPitch)

        adjustedChord = m21.chord.Chord(listOfAdjustedNotes)

        for pitch in adjustedChord.pitches:
            if pitch == bassPitch:
                print(f"{pitch} is bass note")
            else:
                print(f"annotating {pitch}")
            
            interval = m21.interval.Interval(bassPitch, pitch)
            listOfIntervals.append(interval)

        return listOfIntervals

underlying = m21.harmony.chordSymbolFromChord(m21.chord.Chord(["D3", "F#3", "A3", "C4"]))
voicing = m21.chord.Chord(["C3", "D3", "F#3", "A3", "C4", "E6"])
print(CTandTAnnotator.AnnotateChord(voicing, underlying))