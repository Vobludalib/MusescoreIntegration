from music21 import converter
import argparse
from delasol import solmize
import random
import string
import os
import sys

def run_solmization(bestOnly: bool, showWeights: bool, style:str, path):
    score = converter.parse(path)

    for part in score.parts:
        solmization = solmize(part, style=style)
        solmization.annotate(
            # All these are optional:
            # Only annotate the best solmization
            best_only=bestOnly,
            # Hide the weights
            show_weights=showWeights, 
            # Only syllables, no hexachord subscripts
            output_style='syllable', 
            # Gray out the lyrics on line 1
            grey_lyrics_num=1
        )

    outputPath = os.path.join(str(os.path.dirname(path)), generate_random_string() + '.musicxml')
    
    score.write('musicxml', outputPath)
    return os.path.abspath(outputPath)

def generate_random_string(len=10):
    letters = string.ascii_lowercase + "".join([str(i) for i in range (0, 9)])
    return ''.join(random.choice(letters) for i in range(len))

if __name__ == '__main__':
    bestOnly = True
    showWeights = False
    style = "continental"

    parser = argparse.ArgumentParser()
    parser.add_argument('--showNonBest', action='store_true', help='Output more than just the best estimate')
    parser.add_argument('--showWeights', action='store_true', help='Should show estimation weights')
    parser.add_argument('--style', help='What style of solmization to use')
    parser.add_argument('--tempPath', help='Where to read the mxl file from')
    args, leftovers = parser.parse_known_args()
    
    bestOnly = not args.showNonBest
    showWeights = args.showWeights
    if args.style is not None:
        style = args.style

    output_path = run_solmization(bestOnly=bestOnly, showWeights=showWeights, style=style, path=args.tempPath)
    print(output_path)
