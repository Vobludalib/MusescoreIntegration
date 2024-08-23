# -*- coding: utf-8 -*-
# -------------------------------------------------------------------
# Author: Bas Cornelissen
# Copyright © 2024 Bas Cornelissen
# -------------------------------------------------------------------
import networkx as nx
import numpy as np
import matplotlib.cm as cm
from collections.abc import Iterable
from music21.pitch import Pitch
from music21.stream import Stream
from music21.note import Note


def as_stream(pitch_string: str, sep: str = " ") -> Stream:
    pitches = [Pitch(p) for p in pitch_string.split(sep)]
    notes = [Note(p) for p in pitches]
    return Stream(notes)


def as_pitch(pitch):
    if isinstance(pitch, str):
        pitch = Pitch(pitch)
    return pitch


def extract_lyrics(notes: Iterable[Note], number: int) -> list[str]:
    """Extract the lyrics at a given line number from an iterable of notes"""
    extracted = []
    for note in notes:
        lyrics = {lyric.number: lyric for lyric in note.lyrics}
        if number in lyrics:
            extracted.append(lyrics[number].text)
        else:
            extracted.append(None)
    return extracted


def num_lyrics(stream: Stream) -> int:
    """Returns the maximum number of lyrics in a stream"""
    num_lyrics = 0
    for note in stream.flat.notes:
        numbers = [lyric.number for lyric in note.lyrics]
        if len(numbers) > 0:
            num_lyrics = max(max(numbers), num_lyrics)
    return num_lyrics


def annotate_note(
    note: Note, text: str = None, color: str = None, number: int = 1
) -> None:
    """Add lyrics to a note and set its color"""
    if text is not None:
        note.addLyric(text, lyricNumber=number)
    lyrics = {lyric.number: lyric for lyric in note.lyrics}
    if color is not None:
        if number in lyrics:
            lyrics[number].style.color = color


def set_lyrics_color(
    notes: Iterable[Note], number: int, color: str = "#000000"
) -> None:
    """Set the color of a lyric in a list of notes."""
    for note in notes:
        annotate_note(note, color=color, number=number)


def find_first_difference(sequence, value, offset: int = 0):
    """Find the index of the first element in the sequence that is different from the value.

    >>> find_first_difference([1, 1, 2, 1], 1)
    2
    """
    for i in range(offset, len(sequence) - 1):
        if sequence[i] != value:
            return i
    return None


def find_first_repeat(sequence, value, offset: int = 0):
    """Find the index where a given value is first repeated in the sequence.

    >>> find_first_repeat([1, 2, 1, 1, 1, 1], 1)
    2
    """
    for i in range(offset, len(sequence) - 1):
        if sequence[i] == value and sequence[i + 1] == value:
            return i
    return None


def segment_deviations(sequence, value):
    """Segment a sequence into parts that are constant and parts that are not. If possible,
    the deviating parts are surrounded by constant values. The function returns a sequence of
    tuples `(first, last)` indicating the index of the first and last element of the segment.

    In this example, the sequence  `[1, 2, 1, 1, 1, 1]` is divided into two segments:
    `[1, 2, 1]` and `[1, 1, 1]`:

    >>> segment_deviations([1, 2, 1, 1, 1, 1], 1)
    [(0, 2), (3, 5)]
    """
    start = 0
    segments = []
    while start < len(sequence):
        diff = find_first_difference(sequence[start:], value)
        if diff is None:
            segments.append((start, len(sequence) - 1))
            break
        else:
            end = find_first_repeat(sequence[start:], value, offset=max(0, diff - 2))
            if end is None:
                segments.append((start, len(sequence) - 1))
                break
            else:
                if start == 0:
                    segment = (0, end)
                else:
                    segment = (start, start + end)
                segments.append(segment)
                start += end + 1

    return segments


def draw_graph(
    graph,
    labels=None,
    pos=None,
    weights=None,
    show_loops=False,
    label_kws={},
    edge_kws={},
    color_mapper=lambda w: cm.Reds(0.9 * w + 0.1),
):
    """
    Draw a networkx graph with specific attributes for nodes and edges."""
    # Nodes
    if pos is None:
        pos = nx.get_node_attributes(graph, "position")
    if labels is None:
        labels = nx.get_node_attributes(graph, "name")
    kws = dict(
        font_size=9,
        bbox=dict(
            facecolor="white",
            linewidth=0.5,
            boxstyle="round,pad=.5,rounding_size=1",
        ),
    )
    kws.update(**label_kws)
    nx.draw_networkx_labels(graph, labels=labels, pos=pos, **kws)

    # Edges
    if show_loops:
        edges = graph.edges
    else:
        edges = [e for e in graph.edges if e[0] != e[1]]
    if weights is None:
        weights = np.array([graph.edges[e]["weight"] for e in edges])
        weights = weights / weights.max()
    kws = dict(
        width=1,
        min_target_margin=10,
        arrowsize=7,
        node_size=500,
        connectionstyle="arc3,rad=-.2",
    )
    kws.update(**edge_kws)
    nx.draw_networkx_edges(
        graph,
        pos=pos,
        edgelist=edges,
        edge_color=[color_mapper(w) for w in weights],
        **kws
    )
