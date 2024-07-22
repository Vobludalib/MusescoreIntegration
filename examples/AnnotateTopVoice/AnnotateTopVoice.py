import os
import music21 as m21
import sys
import argparse
from pathlib import Path

# Gets path of temp MXL file and returns path of new temp MXL file
def annotate_top_voice(path: str, everyOther: bool = False, color: str = 'red') -> str:
    score = m21.converter.parse(str(path))
    i = -1
    for elem in score.flatten().notes:
        i += 1
        if (not (not everyOther and i % 2 == 1)):
            elem.notes[-1].style.color = str.upper(color)
        

    score.write("musicxml", fp=(str(os.path.dirname(path)) + "\\tempColoured.musicxml"))
    return str(os.path.dirname(path)) + "\\tempColoured.musicxml"

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--tempPath', type=Path, help='Path to temporary file')
    parser.add_argument('--everyOther', action='store_true', help='Option to only every other top note')
    parser.add_argument('--color', type=str, help='Color in hex format')
    p = parser.parse_args()

    outputPath = annotate_top_voice(p.tempPath, everyOther = p.everyOther, color = p.color)
    print(outputPath, file=sys.stdout)