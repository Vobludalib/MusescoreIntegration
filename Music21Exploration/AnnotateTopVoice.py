import music21 as m21
import sys
import argparse
from pathlib import Path

m21.environment.UserSettings()['musescoreDirectPNGPath'] = "C:\\Program Files\\MuseScore 3\\bin\\Musescore3.exe"

# Gets path of temp MXL file and returns path of new temp MXL file
def annotate_top_voice(path: str) -> str:
    score = m21.converter.parse(str(path))
    for elem in score.flatten().notes:
        elem.notes[-1].style.color = 'red'

    score.write("musicxml", fp="C:\\Users\\simon\\OneDrive\\Desktop\\Coding Projects\\MusescoreIntegration\\temp\\tempColoured.mxl")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("file_path", type=Path)
    p = parser.parse_args()
    print(p.file_path, type(p.file_path), p.file_path.exists())
    annotate_top_voice(p.file_path)
