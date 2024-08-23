# -*- coding: utf-8 -*-
# -------------------------------------------------------------------
# Author: Bas Cornelissen
# Copyright © 2024 Bas Cornelissen
# -------------------------------------------------------------------
import glob
import os
import subprocess
import yaml
from datetime import datetime
from typing import Union, Iterable, Optional
import pandas as pd
import seaborn as sns
import music21
from music21.metadata import Metadata
from tqdm.auto import tqdm

from .solmization import solmize, EVALUATION_STATUS

MSCORE_EXECUTABLE = "/Applications/MuseScore 4.app/Contents/MacOS/mscore"
CUR_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.abspath(os.path.join(CUR_DIR, os.pardir))


class Corpus:
    _lyric_number = None
    _metadata = None
    _works = None
    formats = {
        "musescore": "mscz",
        "musicxml": "musicxml",
        "pdf": "pdf",
    }

    def __init__(
        self,
        name: str = None,
        directory: str = None,
        metafile: str = "corpus.yaml",
        mscore_executable: str = MSCORE_EXECUTABLE,
    ):
        if name is None and directory is None:
            raise ValueError("Either 'name' or 'directory' must be provided")
        elif name is None:
            self.dir = directory
            self.name = os.path.basename(directory)
        elif directory is None:
            self.name = name
            self.dir = os.path.join(ROOT_DIR, "corpora", self.name)
        if not os.path.exists(self.dir):
            raise FileExistsError(
                f"Corpus directory not found (corpus={self.name}): {self.dir}"
            )

        # Set MuseScore executable. Only test if it exists when needed.
        self.mscore_exec = mscore_executable

        # Save directory structure
        self.dirs = dict(output=os.path.join(self.dir, "output"))
        for format in self.formats.keys():
            dir = os.path.join(self.dir, format)
            self.dirs[format] = dir
        for dir in self.dirs.values():
            os.makedirs(dir, exist_ok=True)

        # Load metadata file
        self.metafile = os.path.join(self.dir, metafile)
        if not os.path.exists(self.metafile):
            raise Exception("Metadata file not found: {self.metafile}")

    def __len__(self):
        return len(self.works)

    def __repr__(self):
        return f"<Corpus {self.name}>"

    @property
    def metadata(self):
        if self._metadata is None:
            with open(self.metafile, "r") as file:
                self._metadata = yaml.safe_load(file)
            works = {}
            for work in self.metadata["works"]:
                id = work["id"]
                for format, extension in self.formats.items():
                    work[f"_{format}"] = os.path.join(
                        self.dirs[format], f"{id}.{extension}"
                    )
                works[id] = work
            self._metadata["works"] = works
            if not "name" in self._metadata:
                self._metadata["name"] = self.name
            if not "solmization_style" in self._metadata:
                self._metadata["solmization_style"] = "continental"
        return self._metadata

    @property
    def works(self):
        return self.metadata["works"]

    @property
    def ids(self):
        return sorted([k for k in self.works.keys()])

    @property
    def lyric_number(self):
        if self._lyric_number is None:
            self._lyric_number = {
                type: line + 1 for line, type in enumerate(self.metadata["lyric_lines"])
            }
        return self._lyric_number

    def files(self, format="musicxml"):
        if not format in self.formats:
            raise ValueError(f'Unsupported format "{format}"')
        return {id: work[f"_{format}"] for id, work in self.works.items()}

    def mscore(self, *args):
        if not os.path.exists(self.mscore_exec):
            raise FileNotFoundError(
                f"MuseScore executable not found: {self.mscore_exec}"
            )
        return subprocess.run([self.mscore_exec, *args])

    def convert_musescore_work(self, id, to: str, refresh: bool = False):
        work = self.works[id]
        source = work["_musescore"]
        if not os.path.exists(source):
            raise FileNotFoundError(
                f"MuseScore file not found (work id={work['id']}): {source}"
            )
        target = work[f"_{to}"]
        if not os.path.exists(target) or refresh:
            result = self.mscore("-o", target, source)
            if result.returncode != 0:
                raise Exception(f"Error converting {source} to {to}: {result.stderr}")

    def convert_musescore_files(
        self,
        to: Iterable[str] = ["musicxml", "pdf"],
        refresh: bool = False,
        ids: list[str] = None,
    ):
        """Convert musescore files to another format using the MuseScore executable"""
        if ids is None:
            ids = self.works.keys()
        for id in tqdm(ids):
            for format in to:
                self.convert_musescore_work(id, to=format, refresh=refresh)

    def load_score(self, id, **kwargs):
        work = self.works[id]
        return music21.converter.parse(work["_musicxml"], **kwargs)

    def report_evaluation(self, evaluation):
        # Make sure all fields are present
        for key in EVALUATION_STATUS:
            evaluation[key] = evaluation.get(key, 0)

        # Don't count missing syllables as a mistake
        evaluation["num_notes"] = sum(evaluation.values())
        evaluation["num_syllables"] = evaluation["num_notes"] - evaluation["missing"]
        evaluation["accuracy"] = evaluation["correct"] / evaluation["num_syllables"]
        report = f"Accuracy best solmization: {evaluation['accuracy']:.0%}"
        errors = [
            f"{evaluation[k]} {k}"
            for k in ["incorrect", "missing", "insertion", "deletion"]
            if evaluation[k] > 0
        ]
        if len(errors) > 0:
            report += f' ({", ".join(errors)})'
        return report

    def evaluate_work(
        self,
        id,
        target_lyrics: str,
        solmization_style: str = None,
        style: str = None,
        force_source: bool = False,
        solmization_kws: dict = {},
        **kwargs,
    ):
        # Determine options
        if target_lyrics is None or target_lyrics not in self.lyric_number:
            raise ValueError(f"Invalid target_lyrics: {target_lyrics}")
        target_lyrics_num = self.lyric_number[target_lyrics]
        if solmization_style is None:
            solmization_style = self.metadata["solmization_style"]

        # Load stream, solmize and evaluate
        work = self.works[id]
        score = music21.converter.parse(work["_musicxml"], forceSource=force_source)
        solmization = solmize(score, style=solmization_style, **solmization_kws)
        evaluation = solmization.evaluate(target_lyrics=target_lyrics_num, style=style)
        report = self.report_evaluation(evaluation)

        # Annotate the evaluated score
        solmization.annotate(
            target_lyrics=target_lyrics_num, test_style=style, **kwargs
        )
        now = datetime.now().strftime("%d-%m-%Y")
        metadata = dict(title=id, composer=f"Generated on {now}")
        score.metadata = Metadata(lyricist=report, **metadata)

        return score, evaluation

    def evaluate(
        self,
        ids: Iterable[str] = None,
        target_lyrics: str = "syllables",
        write_output: bool = False,
        output_dir: str = None,
        refresh: bool = False,
        remove_musicxml: bool = True,
        write_log: bool = True,
        **kwargs,
    ):
        start = datetime.now()
        if ids is None:
            ids = self.ids
        if write_output is False:
            write_log = False
        if write_output:
            if output_dir is None:
                output_dir = f"output-{start.strftime('%Y_%m_%d-%H_%M')}"
            output_dir = os.path.join(self.dirs["output"], output_dir)
            log_fn = os.path.join(output_dir, "log.yaml")
            if os.path.exists(output_dir) and refresh:
                os.remove(log_fn)
            else:
                os.makedirs(output_dir, exist_ok=True)

        # A basic log
        log = {}
        log["time_start"] = start
        log["num_works"] = len(ids)
        log["works"] = {}
        log["errors"] = {}

        iterator = tqdm(ids) if write_output else ids
        for id in iterator:
            work = dict(id=id)
            if write_output:
                xml_fn = os.path.join(output_dir, f"{id}.musicxml")
                pdf_fn = os.path.join(output_dir, f"{id}.pdf")
            if refresh or not write_output or not os.path.exists(pdf_fn):
                try:
                    score, evaluation = self.evaluate_work(
                        id, target_lyrics=target_lyrics, **kwargs
                    )
                    if write_output:
                        score.write("musicxml.pdf", pdf_fn)
                        if remove_musicxml:
                            os.remove(xml_fn)
                    work["status"] = "success"
                    work["evaluation"] = evaluation

                except Exception as e:
                    work["status"] = "error"
                    log["errors"][id] = str(e)
            else:
                work["status"] = "skipped"

            log["works"][id] = work

        # Finish up logging
        log["time_stop"] = datetime.now()
        log["num_errors"] = len(log["errors"])
        if write_log:
            with open(log_fn, "w") as file:
                yaml.dump(log, file)

        return self._log_to_df(log)

    def _log_to_df(self, log) -> pd.DataFrame:
        data = {}
        for id, work in log["works"].items():
            data[id] = work.get("evaluation", {})
            data[id]["status"] = work["status"]
        df = pd.DataFrame(data).T
        if "incorrect" in df and "num_notes" in df:
            df["perc_incorrect"] = df["incorrect"] / df["num_notes"]
        if "missing" in df and "num_notes" in df:
            df["perc_missing"] = df["missing"] / df["num_notes"]
        return df

    def load_evaluation(self, output_dir: str = None) -> pd.DataFrame:
        if output_dir is None:
            subdirs = sorted(os.listdir(self.dirs["output"]))
            output_dir = os.path.join(self.dirs["output"], subdirs[-1])

        log_fn = os.path.join(output_dir, "log.yaml")
        with open(log_fn, "r") as file:
            log = yaml.safe_load(file)

        return self._log_to_df(log)
