import os
import sys
import argparse
from pathlib import Path
import json

def create_xml_from_json(path):
    with open(path, "r") as f:
        data = json.load(f)
        title = data.get("title", "")
        subtitle = data.get("subtitle", "")
        composer = data.get("composer", "")
        lyricist = data.get("lyricist", "")
        copyright = data.get("copyright", "")

    with open("template.musicxml", "r") as f:
        text = "".join(f.readlines())
        newText = text.replace("InsertTitle", title).replace("InsertSubtitle", subtitle).replace("InsertComposer", composer).replace("InsertLyricist", lyricist).replace("InsertCopyright", copyright)
    
    with open("output.musicxml", "w") as f:
        f.write(newText)

    return os.path.abspath("output.musicxml")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', type=str, help='Path to json')
    p = parser.parse_args()

    outputPath = create_xml_from_json(p.path)
    print(outputPath, file=sys.stdout)