# coding=utf-8
# Copyright 2020 The HuggingFace Datasets Authors and the current dataset script contributor.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import re
import datasets
import glob
from utils import schemas
from utils.configs import BigBioConfig
from utils.constants import Tasks


_DATASETNAME = "ask_a_patient"

_CITATION = """
@inproceedings{limsopatham-collier-2016-normalising,
    title = "Normalising Medical Concepts in Social Media Texts by Learning Semantic Representation",
    author = "Limsopatham, Nut  and
      Collier, Nigel",
    booktitle = "Proceedings of the 54th Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers)",
    month = aug,
    year = "2016",
    address = "Berlin, Germany",
    publisher = "Association for Computational Linguistics",
    url = "https://aclanthology.org/P16-1096",
    doi = "10.18653/v1/P16-1096",
    pages = "1014--1023",
}
"""

_DESCRIPTION = """
The AskAPatient dataset contains medical concepts written on social media \
mapped to how they are formally written in medical ontologies (SNOMED-CT and AMT).
"""

_HOMEPAGE = "https://zenodo.org/record/55013"

_LICENSE = "CC BY 4.0"

_URLs = "https://zenodo.org/record/55013/files/datasets.zip"

_SUPPORTED_TASKS = [Tasks.NAMED_ENTITY_RECOGNITION, Tasks.NAMED_ENTITY_DISAMBIGUATION]
_SOURCE_VERSION = "1.0.0"
_BIGBIO_VERSION = "1.0.0"


class AskAPatient(datasets.GeneratorBasedBuilder):
    """AskAPatient: Dataset for Normalising Medical Concepts in Social Media Text."""

    DEFAULT_CONFIG_NAME = "ask_a_patient_source"
    SOURCE_VERSION = datasets.Version(_SOURCE_VERSION)
    BIGBIO_VERSION = datasets.Version(_BIGBIO_VERSION)

    BUILDER_CONFIGS = [
        BigBioConfig(
            name="ask_a_patient_source",
            version=SOURCE_VERSION,
            description="AskAPatient source schema",
            schema="source",
            subset_id="ask_a_patient",
        ),
        BigBioConfig(
            name="ask_a_patient_bigbio_kb",
            version=BIGBIO_VERSION,
            description="AskAPatient simplified BigBio schema",
            schema="bigbio_kb",
            subset_id="ask_a_patient",
        ),
    ]

    def _info(self):
        if self.config.schema == "source":
            features = datasets.Features(
                {
                    "cui": datasets.Value("string"),
                    "medical_concept": datasets.Value("string"),
                    "social_media_text": datasets.Value("string"),
                }
            )
        elif self.config.schema == "bigbio_kb":
            features = schemas.kb_features
        return datasets.DatasetInfo(
            description=_DESCRIPTION,
            features=features,
            supervised_keys=None,
            homepage=_HOMEPAGE,
            license=_LICENSE,
            citation=_CITATION,
        )

    def _split_generators(self, dl_manager):
        dl_dir = dl_manager.download_and_extract(_URLs)
        dataset_dir = os.path.join(dl_dir, "datasets", "AskAPatient")
        # dataset supports k-folds
        splits = []
        for split_name in [
            datasets.Split.TRAIN,
            datasets.Split.VALIDATION,
            datasets.Split.TEST,
        ]:
            for fold_filepath in glob.glob(
                os.path.join(dataset_dir, f"AskAPatient.fold-*.{split_name}.txt")
            ):
                fold_id = re.search("AskAPatient\.fold-(\d)\.", fold_filepath).group(1)
                split_id = f"{split_name}_{fold_id}"
                splits.append(
                    datasets.SplitGenerator(
                        name=split_id,
                        gen_kwargs={"filepath": fold_filepath, "split_id": split_id},
                    )
                )
        return splits

    def _generate_examples(self, filepath, split_id):
        with open(filepath, "r", encoding="latin-1") as f:
            for i, line in enumerate(f):
                id = f"{split_id}_{i}"
                cui, medical_concept, social_media_text = line.strip().split("\t")
                if self.config.schema == "source":
                    yield id, {
                        "cui": cui,
                        "medical_concept": medical_concept,
                        "social_media_text": social_media_text,
                    }
                elif self.config.schema == "bigbio_kb":
                    text_type = "social_media_text"
                    offset = (0, len(social_media_text))
                    yield id, {
                        "id": id,
                        "document_id": id,
                        "passages": [
                            {
                                "id": f"{id}_passage",
                                "type": text_type,
                                "text": [social_media_text],
                                "offsets": [offset],
                            }
                        ],
                        "entities": [
                            {
                                "id": f"{id}_entity",
                                "type": text_type,
                                "text": [social_media_text],
                                "offsets": [offset],
                                "normalized": [
                                    {"db_name": "SNOMED-CT|AMT", "db_id": cui}
                                ],
                            }
                        ],
                        "events": [],
                        "coreferences": [],
                        "relations": [],
                    }
