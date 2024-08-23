# -*- coding: utf-8 -*-
# -------------------------------------------------------------------
# Author: Bas Cornelissen
# Copyright © 2024 Bas Cornelissen
# -------------------------------------------------------------------
import matplotlib.pyplot as plt
import numpy as np
import networkx as nx
from music21.pitch import Pitch
from typing import Callable, Iterable, Any

from .utils import segment_deviations, draw_graph
from .gamut_graph import GamutGraph

OrigGraphNode = Any
ParseGraphNode = tuple[int, OrigGraphNode]
SequenceItem = Any
Path = list[ParseGraphNode]


def match_fn(node: OrigGraphNode, target: SequenceItem) -> bool:
    return node[1] == target


class Segment:
    def __init__(self, graph, start: int, end: int):
        if not isinstance(graph, ParseGraph):
            raise Exception("Only segments of parse graphs are currently supported.")
        if len(graph.positions[start]) > 1 or len(graph.positions[end]) > 1:
            raise ValueError("Segments must have a unique end and starting node")

        self.graph = graph
        self.start = start
        self.end = end
        self.start_node = self.graph.positions[start][0]
        self.end_node = self.graph.positions[end][0]
        if self.start_node == self.end_node:
            paths = [[self.start_node]]
            weights = [0]
        else:
            paths = list(
                nx.all_simple_paths(self.graph, self.start_node, self.end_node)
            )
            weights = [nx.path_weight(self.graph, path, "weight") for path in paths]

        self.ranking = np.argsort(weights)
        self.paths = [paths[i] for i in self.ranking]
        self.weights = [weights[i] for i in self.ranking]

    def __repr__(self):
        return f"<Segment {self.start}–{self.end} of {repr(self.graph)}>"

    def __len__(self):
        return self.end - self.start

    def __iter__(self):
        for pos in range(self.start, self.end + 1):
            yield self[pos]

    def __getitem__(self, index):
        index = index - self.start
        return dict(
            nodes=[path[index] for path in self.paths],
            weights=self.weights,
            pos_in_segment=index,
        )


class SegmentedGraph(nx.DiGraph):
    _pos_to_segment = None
    _positions = None
    _segments = []

    @property
    def length(self):
        return len(self._positions)

    @property
    def positions(self) -> dict[int, list[ParseGraphNode]]:
        if self._positions is None:
            self._positions = {}
            for node in self.nodes:
                pos, _ = node
                if pos not in self._positions:
                    self._positions[pos] = []
                self._positions[pos].append(node)
        return self._positions

    @property
    def width(self) -> np.ndarray:
        """A numpy array with the number of nodes at each position."""
        if self._width is None:
            self._width = np.zeros(len(self))
            for pos, _ in self.nodes:
                self._width[pos] += 1
        return self._width

    @property
    def segments(self) -> list[Segment]:
        if self._segments is None:
            self._segments = []
            positions = segment_deviations(self.width, value=1)
            for start, end in positions:
                segment = Segment(self, start, end)
                self._segments.append(segment)
        return self._segments

    @property
    def pos_to_segment(self):
        if self._pos_to_segment is None:
            self._pos_to_segment = {}
            for segment in self.segments:
                for pos in range(segment.start, segment.end + 1):
                    self._pos_to_segment[pos] = segment
        return self._pos_to_segment

    def step(self, position: int):
        segment = self.pos_to_segment[position]
        return segment[position]

    def iter_steps(
        self, positions: Iterable[int] = None, return_orig_node: bool = True
    ):
        last_segment = None
        for position in positions:
            segment = self.pos_to_segment[position]
            step = segment[position]
            if return_orig_node:
                step["nodes"] = [n[1] for n in step["nodes"]]
            step["is_first"] = segment != last_segment
            last_segment = segment
            yield step

    def iter_selected_paths(
        self,
        selector: Callable[[Segment], int],
        positions: Iterable[int] = None,
        return_orig_node: bool = True,
    ):
        for index, segment in enumerate(self.segments):
            index = selector(index, segment)
            for i, step in enumerate(segment):
                pos = segment.start + i
                if positions is None or pos in positions:
                    node = step["nodes"][index]
                    yield node[1] if return_orig_node else node

    def iter_nth_path(self, n: int = 0, **kwargs):
        selector = lambda index, segment: min(n, len(segment.paths))
        return self.iter_selected_paths(selector, **kwargs)

    def iter_best_path(self, **kwargs):
        return self.iter_nth_path(0, **kwargs)


class ParseGraph(SegmentedGraph):
    input_positions = None
    _positions = None
    _shortest_paths = {}

    def __init__(
        self,
        graph: nx.Graph,
        sequence: Iterable[SequenceItem] = None,
        match_fn: Callable[[OrigGraphNode, SequenceItem], bool] = match_fn,
        prune: bool = True,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.orig = graph
        self.match_fn = match_fn
        if sequence is not None:
            self.build(sequence, prune=prune)

    def __repr__(self):
        return f"<ParseGraph of {self.orig.__class__.__name__}>"

    def __len__(self):
        return max(*self.positions.keys()) + 1

    ## Parent search operations

    def search(
        self, target: Any, nodes: Iterable[OrigGraphNode] = None
    ) -> list[tuple[OrigGraphNode, dict]]:
        """Search for nodes matching a certain target value using the match function."""
        if nodes is None:
            nodes = self.orig.nodes
        matches = []
        for node in nodes:
            if not node in self.orig:
                raise ValueError(f"Node {node} is not in the original graph.")
            if self.match_fn(node, target):
                matches.append(node)
        return matches

    def shortest_paths(
        self, source_value: OrigGraphNode, target_value: OrigGraphNode
    ) -> dict[tuple[OrigGraphNode, OrigGraphNode], list[list[OrigGraphNode]]]:
        """Return the shortest paths between two nodes in the original graph. This function memoizes the results."""
        if (source_value, target_value) not in self._shortest_paths:
            source_matches = self.search(source_value)
            target_matches = self.search(target_value)
            all_paths = []
            for source in source_matches:
                for target in target_matches:
                    paths = nx.all_shortest_paths(self.orig, source, target)
                    all_paths.extend(paths)

            # Store the shortest paths
            shortest_length = min([len(path) for path in all_paths])
            all_paths = [path for path in all_paths if len(path) == shortest_length]
            self._shortest_paths[(source_value, target_value)] = all_paths

        return self._shortest_paths[(source_value, target_value)]

    ## Construction

    def _add_node(self, pos: int, orig_node: OrigGraphNode) -> ParseGraphNode:
        """Add a node to the parse graph based on the position and a node in the original graph."""
        node = (pos, orig_node)
        attrs = dict(**self.orig.nodes[orig_node])
        self.add_node(node, **attrs)
        return node

    def _add_path(self, start, path):
        new_nodes = []
        for i, orig_node in enumerate(path):
            pos = start + i
            new_node = (pos, orig_node)
            if new_node not in self.nodes:
                self._add_node(pos, orig_node)
            if i >= 1:
                orig_weight = self.orig[new_nodes[-1][1]][new_node[1]]["weight"]
                self.add_edge(new_nodes[-1], new_node, weight=orig_weight)

            new_nodes.append(new_node)
        return new_nodes

    def prune_branch(self, source: ParseGraphNode):
        """Remove all predecessors of a node that have only one successor. This allows us to
        prune branches that cannot parse the sequence anyway."""
        predecessors = list(self.predecessors(source))
        for predecessor in predecessors:
            if self.out_degree[predecessor] == 1:
                self.prune_branch(predecessor)
                self.remove_node(predecessor)

        if self.out_degree[source] == 0:
            self.remove_node(source)

    def clear(self):
        self._segments = None
        self._width = None
        self._positions = None
        self._shortest_paths = {}
        super().clear()

    def build(self, sequence: Iterable[SequenceItem], prune: bool = True):
        self.clear()
        self.seq = sequence
        self.start = (0, "START")
        self.add_node(self.start, name="START", position=(0, 0))

        # First step: from start to first matching nodes (in the original graph)
        matches = self.search(self.seq[0])
        for orig_node in matches:
            new_node = self._add_node(1, orig_node)
            self.add_edge(self.start, new_node, weight=0)

        pos = 1
        prev_nodes = [node for node in matches]
        self.input_positions = [1]
        for prev_value, next_value in zip(self.seq, self.seq[1:]):
            # Find all paths from prev_value to next_value
            paths = self.shortest_paths(prev_value, next_value)
            paths = [p for p in paths if p[0] in prev_nodes]
            if len(paths) == 0:
                raise Exception("This sequence could not be parsed")

            # Add paths to the next nodes
            next_nodes = []
            for prev_node in prev_nodes:
                for path in paths:
                    if path[0] == prev_node:
                        if prev_value != next_value:
                            path = path[1:]
                        new_nodes = self._add_path(pos + 1, path)
                        orig_weight = self.orig[prev_node][new_nodes[0][1]]["weight"]
                        self.add_edge(
                            (pos, prev_node), new_nodes[0], weight=orig_weight
                        )
                        next_nodes.append(new_nodes[-1][1])

            # Prune paths
            if prune:
                for prev_node in prev_nodes:
                    if self.out_degree[(pos, prev_node)] == 0:
                        self.prune_branch((pos, prev_node))

            pos = new_nodes[-1][0]
            self.input_positions.append(pos)
            prev_nodes = set(next_nodes)

        # Finish up: connect to end node
        self.end = (pos + 1, "END")
        self.add_node(self.end, name="END", position=(pos + 1, 0))
        for prev_node in prev_nodes:
            self.add_edge((pos, prev_node), self.end, weight=0)
        self.set_node_positions()

    ## Iterating segments

    def iter_selected_paths(
        self,
        selector: Callable[[Segment], int],
        input_only=True,
        **kwargs,
    ):
        if input_only:
            kwargs["positions"] = self.input_positions
        return super().iter_selected_paths(selector, **kwargs)

    def iter_steps(self, input_only=True, **kwargs):
        if input_only:
            kwargs["positions"] = self.input_positions
        return super().iter_steps(**kwargs)

    # Drawing

    def set_node_positions(self):
        def orig_y_position(node):
            if node[1] in self.orig.nodes:
                orig_node_attrs = self.orig.nodes[node[1]]
                return orig_node_attrs.get("position", (0, 0))[1]
            return 0

        for pos, nodes in self.positions.items():
            nodes = sorted(nodes, key=orig_y_position)
            for i, node in enumerate(nodes):
                self.nodes[node]["position"] = (pos, i)

    def draw(
        self,
        fig=None,
        show_segments: bool = True,
        show_axes: bool = True,
        width_factor: float = 0.7,
        **kws,
    ):
        if fig is None:
            plt.figure(figsize=((len(self) - 1) * width_factor, self.width.max()))
        if show_segments:
            for segment in self.segments[1:]:
                plt.gca().axvline(
                    segment.start - 0.5, color="k", lw=0.5, linestyle="--"
                )
        draw_graph(self, **kws)
        if show_axes:
            ax = plt.gca()
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.set_axis_on()
            ax.xaxis.grid(color=".9")
            ax.tick_params(left=True, bottom=True, labelleft=True, labelbottom=True)
            ax.set_xticks(range(len(self)))
            xlabels = ["start"] + [f"{i}" for i in range(1, len(self) - 1)] + ["end"]
            for i, pos in enumerate(self.input_positions):
                xlabels[pos] += f"\n{self.seq[i]}"
            ax.set_xticklabels(xlabels)
            ax.set_yticks(np.arange(0, self.width.max()))
            ax.set_yticklabels(np.arange(1, self.width.max() + 1, dtype=int))
            plt.ylabel("width")
            plt.ylim(-0.5, self.width.max() - 0.5)
            plt.xlim(-1, len(self))
        else:
            plt.axis("off")
        plt.tight_layout()


class GamutParseGraph(ParseGraph):
    def __init__(
        self,
        gamut: GamutGraph,
        sequence: Iterable[Pitch] = None,
        mismatch_penalty: float = 0,
        match_fn: Any = None,
        **kwargs,
    ):
        if not isinstance(gamut, GamutGraph):
            raise ValueError("The graph should be a GamutGraph.")
        if sequence is not None and not isinstance(sequence[0], Pitch):
            raise ValueError("The sequence should be a list of pitches.")
        if match_fn is not None:
            raise Warning("The match function is ignored for GamutParseGraph.")

        self.gamut = gamut
        self.mismatch_penalty = mismatch_penalty
        super().__init__(graph=gamut, sequence=sequence, **kwargs)

    def search(
        self, target: Pitch, nodes: Iterable[OrigGraphNode] = None
    ) -> list[tuple[OrigGraphNode, dict]]:
        """Search for nodes with a matching pitch"""
        if nodes is None:
            nodes = self.orig.nodes
        return [n for n in nodes if n[1].diatonicNoteNum == target.diatonicNoteNum]

    def build(self, sequence: Iterable[Pitch], prune: bool = True):
        super().build(sequence, prune=prune)

        # Add a mismatch penalty to all nodes that do not exactly match the target pitch
        for pos, target in zip(self.input_positions, sequence):
            for node in self.positions[pos]:
                _, (_, pitch) = node
                if pitch != target:
                    for predecessor in self.predecessors(node):
                        self[predecessor][node]["weight"] += self.mismatch_penalty
