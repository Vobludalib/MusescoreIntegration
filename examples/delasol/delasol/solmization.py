# -*- coding: utf-8 -*-
# -------------------------------------------------------------------
# Author: Bas Cornelissen
# Copyright © 2024 Bas Cornelissen
# -------------------------------------------------------------------
from typing import Union, Callable, Any
from collections.abc import Iterable
from collections import Counter
from copy import deepcopy
from music21.spanner import Line
from music21.stream import Stream
from music21.pitch import Pitch
from music21.note import Note
from music21.tie import Tie
from music21.clef import Clef

# Local imports
from .parse_graph import GamutParseGraph, Segment
from .gamut_graph import GamutGraph, get_gamut, GamutGraphNode, HexachordGraph
from .utils import (
    set_lyrics_color,
    annotate_note,
    num_lyrics,
    extract_lyrics,
)


def evaluator(syllable: str, target: str) -> str:
    """
    Evaluate a note based on the target lyrics.
    """
    if target is not None:
        if target.startswith("["):
            target = target.replace("[", "").replace("]", "")
        elif target.startswith("("):
            target = target.replace("(", "").replace(")", "")
        if "*" in target:
            target = target.split("*")[1]

    if target == syllable:
        return "correct"
    elif target == "?":
        return "missing"
    elif target == "" and syllable != "":
        return "insertion"
    elif target != "" and syllable == "":
        return "deletion"
    else:
        return "incorrect"


EVALUATION_STATUS = ["correct", "missing", "insertion", "deletion", "incorrect"]

EVALUATION_COLORS = dict(
    correct="green", missing="blue", insertion="red", deletion="red", incorrect="red"
)


SolmizationInput = Union[Iterable[Pitch], Iterable[Note], Iterable[str]]
GamutInput = Union[GamutGraph, str]
OutputStyle = Union[str, Iterable[str], Callable[[int, int, Pitch], str]]

SUBSCRIPTS = "₀₁₂₃₄₅₆₇₈₉"
SYLLABLES = ["ut", "re", "mi", "fa", "sol", "la", "fa"]
STATE_NAMES = ["ut", "re", "mi", "fa", "sol", "la", "fi"]


def format_syllable_subscript(degree: int, hexachord: HexachordGraph, **kwargs):
    syllable = SYLLABLES[degree - 1]
    subscript = SUBSCRIPTS[hexachord.number]
    return f"{syllable}{subscript}"


def format_state(degree: int, hexachord: HexachordGraph, **kwargs):
    state = STATE_NAMES[degree - 1]
    return f"{state}{hexachord.number}"


def format_state_subscript(degree: int, hexachord: HexachordGraph, **kwargs):
    name = STATE_NAMES[degree - 1]
    subscript = SUBSCRIPTS[hexachord.number]
    return f"{name}{subscript}"


def by_degree(degree_names: list[str]) -> Callable[[Any], str]:
    if not len(degree_names) == 7:
        raise ValueError(
            "You should pass exactly 7 names for the different degrees in a hexachord"
        )

    def func(degree: int, *args, **kwargs):
        return degree_names[degree - 1]

    return func


def format_davantes(
    hexachord: HexachordGraph,
    pitch: Pitch,
    note: Note = None,
    solmization: Any = None,
    **kwargs,
) -> str:
    clef = solmization.clef
    num = pitch.diatonicNoteNum - clef.lowestLine + 2
    dur = note.duration.quarterLength
    if dur > 4:
        dur = 4
    marks = {
        "soft": {2: ".", 4: "!"},
        "hard": {2: ".", 4: "!"},
        "natural": {2: "", 4: "'"},
    }
    mark = marks[hexachord.type][dur]
    if hexachord.type == "soft":
        symbol = f"{mark}{num}"
    else:
        symbol = f"{num}{mark}"
    return symbol


FORMATTERS = {
    "syllable": by_degree(SYLLABLES),
    "syllable-subscript": format_state_subscript,
    "state": format_state,
    "state-subscript": format_state_subscript,
    "state-syllable": by_degree(["ut", "re", "mi", "fa", "sol", "la", "fi"]),
    "do-ti": by_degree(["do", "re", "mi", "fa", "sol", "la", "ti"]),
    "do-si": by_degree(["do", "re", "mi", "fa", "sol", "la", "si"]),
    "davantes": format_davantes,
}


class Solmization:

    def __init__(
        self,
        input: SolmizationInput = None,
        gamut: GamutInput = None,
        mismatch_penalty: float = 2,
        prune_parse: bool = True,
        gamut_kws: dict = {},
        parse_graph_kws: dict = {},
    ):
        if isinstance(gamut, str):
            gamut = get_gamut(gamut, **gamut_kws)
        if not isinstance(gamut, GamutGraph):
            raise ValueError("No gamut was specified.")
        if isinstance(input, Stream):
            raise ValueError("Use StreamSolmation for stream inputs")
        elif isinstance(input, Iterable):
            if isinstance(input[0], Pitch):
                pitches = [Pitch(p) for p in input]
            elif isinstance(input[0], Note):
                pitches = [Pitch(n.pitch) for n in input]
            elif isinstance(input[0], str):
                pitches = [Pitch(p) for p in input]
            else:
                raise ValueError(
                    "Unsupported input type: you can pass an iterable of pitches, notes or pitch strings"
                )
        else:
            raise ValueError("You must pass an input.")

        self._path = None
        self.gamut = gamut
        self.pitches = pitches
        self.parse = GamutParseGraph(
            self.gamut,
            self.pitches,
            mismatch_penalty=mismatch_penalty,
            prune=prune_parse,
            **parse_graph_kws,
        )

    @property
    def path(self):
        """Return the solmization path, defaults to the best solmization path."""
        if self._path is None:
            self.select("best")
        return self._path

    def select(
        self, path: Union[str, Iterable[int], Callable[[int, Segment], int]] = "best"
    ) -> None:
        """Select a solmization path"""
        if path == "best":
            self._path = list(self.parse.iter_best_path(input_only=True))
        elif path == "worst":
            self._path = self.parse.iter_nth_path(
                99,
                input_only=True,
            )
        elif isinstance(path, Iterable) and isinstance(path[0], int):
            path = lambda index, segment: path[index]

        if callable(path):
            self._path = []
            for node in self.parse.iter_selected_paths(
                path,
                input_only=True,
            ):
                self.path.append(node)

    def match(
        self, targets: Iterable[str], style: OutputStyle = "syllable"
    ) -> list[GamutGraphNode]:
        # TODO
        raise NotImplemented()

    def output(
        self,
        nodes: Iterable[GamutGraphNode] = None,
        style: OutputStyle = "syllable",
        **kwargs,
    ) -> list[str]:
        """Output labels for a given list of nodes."""
        if nodes is None:
            nodes = self.path
        if callable(style):
            formatter = style
        elif style in FORMATTERS:
            formatter = FORMATTERS[style]
        elif isinstance(style, Iterable):
            formatter = by_degree(style)
        else:
            raise ValueError(f"Invalid style input")

        output = []
        for hex, pitch in nodes:
            degree = self.gamut.nodes[(hex, pitch)]["degree"]
            output.append(
                formatter(
                    degree=degree,
                    pitch=pitch,
                    hexachord=self.gamut.hexachords[hex],
                    solmization=self,
                    **kwargs,
                )
            )
        return output

    def evaluate(
        self,
        targets: Iterable[str],
        predictions: Iterable[str] = None,
        nodes: Iterable[GamutGraphNode] = None,
        style: OutputStyle = None,
        return_counts: bool = True,
        evaluator: Callable[[str, str], str] = evaluator,
    ):
        if style is None:
            style = "syllable"
        if nodes is None:
            nodes = self.path
        if predictions is None:
            predictions = self.output(nodes, style=style)
        evaluation = [evaluator(pred, targ) for pred, targ in zip(predictions, targets)]
        if return_counts:
            return dict(Counter(evaluation))
        else:
            return evaluation


class StreamSolmization(Solmization):
    def __init__(
        self,
        stream: Stream,
        style: str = "continental",
        gamut: GamutInput = None,
        in_place: bool = True,
        **kwargs,
    ):
        self.stream = stream if in_place else deepcopy(stream)
        if self.stream.hasPartLikeStreams():
            if len(self.stream.parts) >= 2:
                print(
                    f"Warning: found {len(self.stream.parts)} parts, but only the first part of the stream will be used"
                )
                self.stream = self.stream.parts[0]
        self.style = style
        self.clef = self.stream.flat.clef
        if gamut is None:
            key = self.stream.flat.keySignature
            gamut = get_gamut(style=self.style, key=key)
        self.notes = [
            note for note in self.stream.flat.notes if note.tie != Tie("stop")
        ]
        super().__init__(self.notes, gamut=gamut, **kwargs)

    def evaluate(
        self,
        target_lyrics: int = None,
        targets: Iterable[str] = None,
        style: OutputStyle = None,
        **kwargs,
    ):
        if style is None:
            style = "syllable"
        if "nodes" in kwargs:
            del kwargs["nodes"]
        if targets is None:
            if target_lyrics is None:
                raise ValueError(
                    "Please specify target_lyrics: the lyric number containing the target syllables"
                )
            targets = extract_lyrics(self.notes, target_lyrics)

        predictions = []
        for note, node in zip(self.notes, self.path):
            pred = self.output([node], style=style, note=note)[0]
            predictions.append(pred)

        return super().evaluate(targets, predictions=predictions, **kwargs)

    def annotate(
        self,
        test_style: str = None,
        output_style: str = None,
        targets: Iterable[str] = None,
        target_lyrics: int = None,
        offset: int = None,
        best_only: bool = False,
        max_num_paths: int = 4,
        show_more_paths: bool = True,
        show_weights: bool = True,
        show_segments: bool = True,
        show_all_segments: bool = True,
        grey_lyrics_num: int = None,
        evaluator: Callable = evaluator,
        colors: dict[str, str] = EVALUATION_COLORS,
    ):
        """Annotate a stream with solmization syllables."""
        if test_style is None:
            test_style = "syllable"
        if output_style is None:
            output_style = "state-subscript"
        if best_only:
            max_num_paths = 1
            show_segments = False
            show_more_paths = False
            show_weights = False
        if offset is None:
            offset = num_lyrics(self.stream)
        notes = self.notes
        if target_lyrics is not None:
            targets = extract_lyrics(notes, target_lyrics)

        # Local helper function to overline segments
        def overline_segment(segment_notes, n_paths):
            if (
                show_segments
                and len(segment_notes) > 1
                and (show_all_segments or n_paths > 1)
            ):
                line = Line(segment_notes)
                line.lineType = "dotted"
                self.stream.insert(0, line)

        segment_notes = []
        for pos, (step, note) in enumerate(zip(self.parse.iter_steps(), notes)):
            n_paths = len(step["nodes"])
            kwargs = dict(note=note)
            predictions = self.output(step["nodes"], style=test_style, **kwargs)
            annotations = self.output(step["nodes"], style=output_style, **kwargs)
            for rank in range(min(max_num_paths, n_paths)):

                # Annotate the note
                annot = annotations[rank]
                pred = predictions[rank]
                if show_weights and step["is_first"]:
                    annot = f"[w={step['weights'][rank]:.1f}] {annot}"
                opts = dict(number=rank + offset + 1)
                if targets is not None:
                    result = evaluator(pred, targets[pos])
                    opts["color"] = colors.get(result, "black")
                annotate_note(note, annot, **opts)

            # Show the number of hidden paths and overline segments
            if step["is_first"]:
                if show_more_paths and n_paths > max_num_paths:
                    note.addLyric(f"({n_paths - max_num_paths} more paths)")
                overline_segment(segment_notes, n_paths)
                segment_notes = []

            # Add next notes to segment
            segment_notes.append(note)

        # Overline possible final segment and gray out lyrics if needed
        overline_segment(segment_notes, n_paths)
        if grey_lyrics_num is not None:
            set_lyrics_color(notes, grey_lyrics_num, "#999999")


def solmize(
    input,
    style: str = None,
    gamut: GamutInput = None,
    prune_parse: bool = True,
    mismatch_penalty: float = None,
    mutation_weight: float = None,
    loop_weight: float = None,
    fa_super_la: bool = None,
    fa_super_la_weight: float = None,
    step_weight: float = None,
    hexachord_weights=None,
    in_place: bool = True,
) -> Solmization:
    """A convenience function that creates a Solmization object depending on the input type."""
    opts = {}

    gamut_kws = {}
    if mutation_weight is not None:
        gamut_kws["mutation_weight"] = mutation_weight
    opts["gamut_kws"] = gamut_kws

    hex_kws = {}
    if loop_weight is not None:
        hex_kws["loop_weight"] = loop_weight
    if fa_super_la is not None:
        hex_kws["fa_super_la"] = fa_super_la
    if fa_super_la_weight is not None:
        hex_kws["fa_super_la_weight"] = fa_super_la_weight
    if step_weight is not None:
        hex_kws["step_weight"] = step_weight
    if hexachord_weights is not None:
        hex_kws["weights"] = hexachord_weights
    opts["gamut_kws"]["hexachord_kws"] = hex_kws

    if mismatch_penalty is not None:
        opts["mismatch_penalty"] = mismatch_penalty
    if prune_parse is not None:
        opts["prune_parse"] = prune_parse

    if isinstance(input, Stream):
        solmization = StreamSolmization(
            input, style=style, gamut=gamut, in_place=in_place, **opts
        )
    else:
        solmization = Solmization(input, gamut=gamut, **opts)
    return solmization
