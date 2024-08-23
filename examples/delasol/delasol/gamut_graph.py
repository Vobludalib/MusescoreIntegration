# -*- coding: utf-8 -*-
# -------------------------------------------------------------------
# Author: Bas Cornelissen
# Copyright © 2024 Bas Cornelissen
# -------------------------------------------------------------------
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from typing import Union, Iterable, Optional
from music21.pitch import Pitch
from music21.scale import ConcreteScale, Direction
from music21.key import KeySignature

# Local imports
from .utils import draw_graph, as_pitch

# Custom types
HexachordGraphNode = Pitch
GamutGraphNode = tuple[int, Pitch]

# Number all possible hexachords within some bounds (in practice we only need 0-6)
_hexachordTonicsScale = ConcreteScale(pitches=["F2", "G2", "C3"])
HEXACHORD_TONICS = {}
for i in range(-5, 20):
    direction = Direction.DESCENDING if i < 0 else Direction.ASCENDING
    pitch = _hexachordTonicsScale.nextPitch(
        _hexachordTonicsScale.tonic, direction=direction, stepSize=abs(i)
    )
    if i == 0:
        pitch = _hexachordTonicsScale.tonic
    HEXACHORD_TONICS[pitch] = i
HEXACHORD_TYPES = dict(C="natural", F="soft", G="hard")
STATE_NAMES = ["ut", "re", "mi", "fa", "sol", "la", "fi"]

# Mutations
CONTINENTAL_MUTATIONS = {
    "natural": {
        "up": {
            "hard": [(5, 2)],
            "soft": [(4, 2)],
        },
        "down": {
            "hard": [(4, 6)],
            "soft": [(3, 6)],
        },
    },
    "hard": {
        "up": {
            "natural": [(4, 2)],
        },
        "down": {
            "natural": [(3, 6)],
        },
    },
    "soft": {
        "up": {
            "natural": [(5, 2)],
        },
        "down": {
            "natural": [(4, 6)],
        },
    },
}

ENGLISH_MUTATIONS = {
    "natural": {
        "up": {
            "hard": [(6, 3)],
            "soft": [(6, 4)],
        },
        "down": {
            "hard": [(4, 6)],
            "soft": [(3, 6)],
        },
    },
    "hard": {
        "up": {
            "natural": [(6, 4)],
        },
        "down": {
            "natural": [(3, 6)],
        },
    },
    "soft": {
        "up": {
            "natural": [(6, 3)],
        },
        "down": {
            "natural": [(4, 6)],
        },
    },
}


class HexachordGraph(nx.DiGraph):

    def __init__(
        self,
        tonic: Union[str, Pitch],
        fa_super_la: bool = True,
        **kwargs,
    ):
        super().__init__()
        self._names = None

        # Tonic, number and type
        self.tonic = as_pitch(tonic)
        if self.tonic not in HEXACHORD_TONICS:
            raise ValueError("Invalid tonic: must be a C, F, or G")
        self.number = HEXACHORD_TONICS.get(self.tonic, None)
        self.type = HEXACHORD_TYPES.get(self.tonic.name, "nonstandard")

        # Build the graph
        intervals = ["M2", "M2", "m2", "M2", "M2"]
        if fa_super_la:
            intervals.append("m2")
        self.pitches = [self.tonic]
        for interval in intervals:
            self.pitches.append(self.pitches[-1].transpose(interval))
        self.build(**kwargs)

    def __repr__(self):
        return f"<HexachordGraph {self.number} on {self.tonic.nameWithOctave}>"

    @property
    def names(self):
        if self._names is None:
            self._names = {self.nodes[node]["name"]: node for node in self.nodes}
        return self._names

    def build(
        self,
        step_weight: float = 1,
        loop_weight: float = 0.5,
        fa_super_la_weight: float = 1.5,
        weights: np.ndarray = None,
    ):
        if weights is None:
            N = len(self.pitches)
            weights = np.eye(N) * loop_weight
            np.fill_diagonal(weights[1:], step_weight)
            np.fill_diagonal(weights.T[1:], step_weight)
            weights[N - 1, N - 2] = fa_super_la_weight
            weights[N - 2, N - 1] = fa_super_la_weight

        for i, pitch in enumerate(self.pitches):
            self.add_node(
                pitch,
                degree=i + 1,
                name=f"{STATE_NAMES[i]}{self.number}",
                position=(pitch.diatonicNoteNum, 0),
            )

        for i, pitch1 in enumerate(self.pitches):
            for j, pitch2 in enumerate(self.pitches):
                if weights[i, j] > 0:
                    self.add_edge(pitch1, pitch2, weight=weights[i, j])

    def solmize(self, node: HexachordGraphNode) -> str:
        self.nodes[node]["syllable"]

    def draw(self, show_loops=True, fig=None, **kws):
        if fig is None:
            plt.figure(figsize=(len(self), 1))
        draw_graph(self, show_loops=show_loops, **kws)
        plt.axis("off")
        plt.ylim(-0.5, 0.5)


class GamutGraph(nx.DiGraph):
    def __init__(
        self,
        hexachords: Optional[Iterable[HexachordGraph]] = None,
        mutations: Optional[dict] = None,
        mutation_weight: float = 2,
    ):
        super().__init__()
        self.hexachords = {}
        self._names = None
        self._overlapping_hexachords = None
        self._pitches = None

        if hexachords is not None:
            for hexachord in hexachords:
                self.add_hexachord(hexachord)
        if mutations:
            self.add_mutations(mutations, weight=mutation_weight)

    @property
    def names(self) -> dict[str, GamutGraphNode]:
        if self._names is None:
            self._names = {self.nodes[node]["name"]: node for node in self.nodes}
        return self._names

    @property
    def pitches(self) -> dict[Pitch, list[GamutGraphNode]]:
        if self._pitches is None:
            self._pitches = {}
            for hex, pitch in self.nodes:
                if pitch not in self._pitches:
                    self._pitches[pitch] = []
                self._pitches[pitch].append((hex, pitch))
        return self._pitches

    @property
    def lowest(self) -> GamutGraphNode:
        lowest_hex = min(self.hexachords.keys())
        lowest_pitch = self.hexachords[lowest_hex].pitches[0]
        return (lowest_hex, lowest_pitch)

    @property
    def highest(self) -> GamutGraphNode:
        highest_hex = max(self.hexachords.keys())
        highest_pitch = self.hexachords[highest_hex].pitches[-1]
        return (highest_hex, highest_pitch)

    @property
    def overlapping_hexachords(self) -> dict[HexachordGraph, list[HexachordGraph]]:
        if self._overlapping_hexachords is None:
            hexachords = list(self.hexachords.values())
            neighbors = {hex: [] for hex in hexachords}
            for i in range(len(hexachords)):
                for j in range(i + 1, len(hexachords)):
                    hex1 = hexachords[i]
                    hex2 = hexachords[j]
                    if any(p in hex1.pitches for p in hex2.pitches):
                        neighbors[hex1].append(hex2)
                        neighbors[hex2].append(hex1)
            self._overlapping_hexachords = neighbors
        return self._overlapping_hexachords

    def add_hexachord(self, hexachord: HexachordGraph):
        num = hexachord.number
        if num in self.hexachords:
            raise ValueError(f"Hexachord {num} already exists")
        self.hexachords[num] = hexachord
        for node in hexachord.nodes:
            attrs = dict(**hexachord.nodes[node])
            attrs["position"] = (node.ps, num)
            self.add_node((num, node), **attrs)
        weights = nx.get_edge_attributes(hexachord, "weight")
        weighted_edges = [
            ((num, u), (num, v), weight) for (u, v), weight in weights.items()
        ]
        self.add_weighted_edges_from(weighted_edges)

    def add_mutations(self, mutations: dict, weight: float = 2):
        """Add mutations between hexachords to the graph using a mutation dictionary.
        The dictionary describes the degrees at which you can mutate from each type of
        hexachord to each other type, in both ascending and descending direction. The
        dictionary should have the following structure:"""
        for hexachord in self.hexachords.values():
            for neighbor in self.overlapping_hexachords[hexachord]:
                direction = "up" if neighbor.number > hexachord.number else "down"
                moves = mutations[hexachord.type][direction].get(neighbor.type, [])
                for move in moves:
                    source_node = (hexachord.number, hexachord.pitches[move[0] - 1])
                    target_node = (neighbor.number, neighbor.pitches[move[1] - 1])
                    edge_weight = weight if len(move) == 2 else move[2]
                    self.add_edge(source_node, target_node, weight=edge_weight)

    def add_edges_by_names(self, edges: list[tuple], weight: float = 1):
        """Add edges using names of nodes instead of nodes themselves. You can either pass
        a list of tuples (source, target) or a list of tuples (source, target, weight).
        For example:

        >>> [H1, H2] = [HexachordGraph(p) for p in "G2 C3".split(" ")]
        >>> G = GamutGraph(hexachords=[H1, H2])
        >>> G.add_edges_by_names([("fa1", "re2"), ("fa2", "la1", 1.5)])
        """
        for edge in edges:
            edge_weight = weight if len(edge) == 2 else edge[2]
            self.add_edge(self.names[edge[0]], self.names[edge[1]], weight=edge_weight)

    def solmize(self, node: GamutGraphNode):
        """Return the solmization of a pitch in the gamut graph"""
        return self.nodes[node]["syllable"]

    def draw(self, show_axes: bool = True, fig=None, diatonic: bool = True, **kws):
        if fig is None:
            plt.figure(figsize=(len(self) * 0.4, len(self.hexachords)))
        if diatonic:
            positions = {
                node: (node[1].diatonicNoteNum, node[0]) for node in self.nodes
            }
        draw_graph(self, pos=positions, **kws)
        if show_axes:
            ax = plt.gca()
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.set_axis_on()
            ax.xaxis.grid(color=".9")
            ax.tick_params(left=True, bottom=True, labelleft=True, labelbottom=True)
            if diatonic:
                ticks, ticklabels = [], []
                for p in self.pitches.keys():
                    ticks.append(p.diatonicNoteNum)
                    nodes = self.pitches[p]
                    parts = set([node[1].unicodeNameWithOctave for node in nodes])
                    ticklabels.append("/".join(parts))
                    # pitch = self.pitches[p][0][1]
                    # if pitch.name == "C":
                    #     ticklabels.append(f"{p} ({pitch.unicodeNameWithOctave})")
                    # else:
                    #     ticklabels.append(p)
            else:
                ticks = [p.ps for p in self.pitches.keys()]
                ticklabels = [p.unicodeNameWithOctave for p in self.pitches.keys()]
            ax.set_xticks(ticks)
            ax.set_xticklabels(ticklabels)
            plt.ylabel("hexachord number")
            # plt.xlim(self.lowest[1].ps - 1, self.highest[1].ps + 1)
        else:
            plt.axis("off")


class HardContinentalGamut(GamutGraph):
    def __init__(
        self,
        hexachords: Optional[list[HexachordGraph]] = None,
        mutations: Optional[dict] = CONTINENTAL_MUTATIONS,
        hexachord_kws: Optional[dict] = {},
        **kwargs,
    ):
        if hexachords is None:
            hexachords = [
                HexachordGraph("G2", **hexachord_kws),
                HexachordGraph("C3", **hexachord_kws),
                HexachordGraph("G3", **hexachord_kws),
                HexachordGraph("C4", **hexachord_kws),
                HexachordGraph("G4", **hexachord_kws),
                HexachordGraph("C5", **hexachord_kws),
            ]
        super().__init__(hexachords=hexachords, mutations=mutations, **kwargs)


class SoftContinentalGamut(GamutGraph):
    def __init__(
        self,
        hexachords: Optional[list[HexachordGraph]] = None,
        mutations: Optional[dict] = CONTINENTAL_MUTATIONS,
        extend_below: bool = True,
        hexachord_kws: Optional[dict] = {},
        **kwargs,
    ):
        if hexachords is None:
            hexachords = [
                HexachordGraph("C3", **hexachord_kws),
                HexachordGraph("F3", **hexachord_kws),
                HexachordGraph("C4", **hexachord_kws),
                HexachordGraph("F4", **hexachord_kws),
            ]
        if extend_below:
            hexachords = [HexachordGraph("F2", **hexachord_kws)] + hexachords
        super().__init__(hexachords=hexachords, mutations=mutations, **kwargs)


class HardEnglishGamut(GamutGraph):
    def __init__(
        self,
        hexachords=None,
        mutations=ENGLISH_MUTATIONS,
        mutation_weight=0.75,
        hexachord_kws={},
        **kwargs,
    ):
        kws = dict(
            fa_super_la=False,
            loop_weight=0.5,
            step_weight=1,
            fa_super_la_weight=1,
        )
        kws.update(**hexachord_kws)
        if hexachords is None:
            hexachords = [
                HexachordGraph("G2", **kws),
                HexachordGraph("C3", **kws),
                HexachordGraph("G3", **kws),
                HexachordGraph("C4", **kws),
                HexachordGraph("G4", **kws),
            ]
        super().__init__(
            hexachords=hexachords,
            mutations=mutations,
            mutation_weight=mutation_weight,
            **kwargs,
        )


class SoftEnglishGamut(GamutGraph):
    def __init__(
        self,
        hexachords=None,
        mutations=ENGLISH_MUTATIONS,
        mutation_weight=0.75,
        hexachord_kws={},
        **kwargs,
    ):
        kws = dict(
            fa_super_la=False,
            loop_weight=0.5,
            step_weight=1,
            fa_super_la_weight=1,
        )
        kws.update(**hexachord_kws)
        if hexachords is None:
            hexachords = [
                HexachordGraph("C3", **kws),
                HexachordGraph("F3", **kws),
                HexachordGraph("C4", **kws),
                HexachordGraph("F4", **kws),
            ]
        super().__init__(
            hexachords=hexachords,
            mutations=mutations,
            mutation_weight=mutation_weight,
            **kwargs,
        )


GAMUTS = {
    "hard-continental": HardContinentalGamut,
    "soft-continental": SoftContinentalGamut,
    "hard-english": HardEnglishGamut,
    "soft-english": SoftEnglishGamut,
}

SHARPS_TO_GAMUT_NAME = {
    "continental": {
        0: "hard-continental",
        -1: "soft-continental",
    },
    "english": {
        0: "hard-english",
        -1: "soft-english",
    },
}


def get_gamut(
    name: str = None,
    style: str = None,
    sharps: int = None,
    key: KeySignature = None,
    **kws,
) -> GamutGraph:
    """Returns a gamut by its name, the style or the number of sharps"""
    if key is not None:
        sharps = key.sharps

    if sharps is not None:
        if style is None:
            raise ValueError(
                "No solmization style specified. This is required if you provide a key signature or the number of sharps"
            )
        if style not in SHARPS_TO_GAMUT_NAME:
            raise ValueError("Invalid style {style}")
        if sharps not in SHARPS_TO_GAMUT_NAME[style]:
            raise ValueError(
                f"Number of sharps ({sharps}) is not supported for style {style}."
            )
        name = SHARPS_TO_GAMUT_NAME[style][sharps]

    if name not in GAMUTS:
        raise ValueError(
            f"Invalid gamut name '{name}'. Suppored names are: {', '.join(GAMUTS.keys())}"
        )
    else:
        return GAMUTS[name](**kws)
