#!/usr/bin/env python3

import sys
import os
import argparse
import uuid
import json
from gfftk.gff import gff2dict, dict2gff3
from gfftk.stats import annotation_stats
from .__init__ import __version__
from .help_formatter import MyParser, MyHelpFormatter
from .log import startLogging, system_info, finishLogging
from .hdf5 import HelixerFastaToH5Controller
from .hybrid_model import HybridModel
from .utilities import preds2gff3, download


def main():
    args = parse_args(sys.argv[1:])
    logger = startLogging(logfile=f"{args.out.rsplit('.', 1)[0]}.log")
    system_info(logger.info)
    config = {
        "fungi": {
            "url": "https://zenodo.org/records/10836346/files/fungi_v0.3_a_0100.h5?download=1",
            "name": "fungi_v0.3_a_0100.h5",
            "length": 21384,
            "offset": 10692,
            "core": 16038,
        },
        "land_plants": {
            "url": "https://zenodo.org/records/10836346/files/land_plant_v0.3_a_0080.h5?download=1",
            "name": "and_plant_v0.3_a_0080.h5",
            "length": 54152,
            "offset": 32076,
            "core": 48114,
        },
        "vertebrate": {
            "url": "https://zenodo.org/records/10836346/files/vertebrate_v0.3_a_0200.h5?download=1",
            "name": "vertebrate_v0.3_a_0200.h5",
            "length": 213840,
            "offset": 106920,
            "core": 160380,
        },
        "invertebrate": {
            "url": "https://zenodo.org/records/10836346/files/invertebrate_v0.3_a_0300.h5?download=1",
            "name": "invertebrate_v0.3_a_0300.h5",
            "length": 213840,
            "offset": 106920,
            "core": 160380,
        },
    }
    lineage_config = config.get(args.lineage)
    # check if model exists
    global_model = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "model_files",
        lineage_config["name"],
    )
    if not os.path.isfile(global_model):
        if os.access(os.path.dirname(global_model), os.W_OK):
            model_path = global_model
        else:  # cannot write there, so put in working directory
            logger.info(
                f"User does not appear to have write access to {os.path.dirname(global_model)}, will download model to current directory."
            )
            model_path = lineage_config["name"]
    else:
        logger.info(f"Helixer model already exists: {global_model}")
        model_path = global_model

    if not os.path.isfile(model_path):
        logger.info(f"Downloading Helixer model: {model_path}")
        download(lineage_config["url"], model_path)
    # convert genome to hd5
    slug = str(uuid.uuid4())[:8]
    logger.info(
        f"Converting genome assembly to HDF5 format. Using settings for {args.lineage}: --subsequence-length {lineage_config['length']}"
    )
    fasta2hdf5(
        args.fasta, f"{slug}.h5", species=slug, subseqlen=lineage_config["length"]
    )
    # train with hybrid model
    # build cli options
    # --load-model-path fungi_v0.3_a_0100.h5 --test-data 5f616493-e12d-4090-aace-df674baaafe3.h5 --overlap --val-test-batch-size 32
    logger.info(f"Running helixer HybridModel using model={lineage_config['name']}")
    logger.info(
        f'Using settings for {args.lineage}: --overlap-offset {lineage_config["offset"]} --core-length {lineage_config["core"]}'
    )
    model = HybridModel(
        [
            "--load-model-path",
            model_path,
            "--test-data",
            f"{slug}.h5",
            "--overlap-offset",
            str(lineage_config["offset"]),
            "--core-length",
            str(lineage_config["core"]),
            "--overlap",
            "--val-test-batch-size",
            "32",
            "--prediction-output-path",
            f"{slug}.predictions.h5",
            "--cpus",
            str(args.cpus),
        ]
    )
    model.run()

    # convert to GFF3
    logger.info("Converting predictions.h5 to GFF3 with helixerpost")
    preds2gff3(
        f"{slug}.h5",
        f"{slug}.predictions.h5",
        f"{slug}.gff3",
        peak_threshold=float(args.peak),
        min_coding_length=args.minprotlen,
    )
    # clean/reformat gff
    logger.info("Cleaning GFF3 output with GFFtk")
    Genes = gff2dict(f"{slug}.gff3", args.fasta)
    stats = annotation_stats(Genes)
    dict2gff3(Genes, output=args.out)
    logger.info(f"Annotation stats:\n{json.dumps(stats, indent=2)}")

    # clean up
    for f in [f"{slug}.h5", f"{slug}.predictions.h5", f"{slug}.gff3"]:
        if os.path.isfile(f):
            os.remove(f)
    # finish
    finishLogging(logger.info, vars(sys.modules[__name__])["__name__"])


def parse_args(args):
    description = "helixerlite: simplified helixer de novo genome annotation"
    parser = MyParser(
        description=description, formatter_class=MyHelpFormatter, add_help=False
    )
    required = parser.add_argument_group("Required arguments")
    optional = parser.add_argument_group("Optional arguments")

    required.add_argument(
        "-f",
        "--fasta",
        required=True,
        metavar="",
        help="Input sequence file in FASTA format",
    )
    required.add_argument(
        "-o",
        "--out",
        required=True,
        metavar="",
        help="GFF3 output",
    )
    required.add_argument(
        "-l",
        "--lineage",
        required=True,
        metavar="",
        choices=["fungi", "land_plant", "vertebrate", "invertebrate"],
        help="Specify which model to use for prediction [fungi,land_plant,vertebrate,invertebrate]",
    )
    optional.add_argument(
        "-c",
        "--cpus",
        required=False,
        type=int,
        default=1,
        metavar="",
        help="Specify the number (N=integer) of threads/cores to use.",
    )
    optional.add_argument(
        "-p",
        "--peak-threshold",
        dest="peak",
        required=False,
        default=0.8,
        metavar="",
        help="Minimum peak genic score to call a gene model. [< 1]",
    )
    optional.add_argument(
        "-m",
        "--min-protein-length",
        dest="minprotlen",
        required=False,
        default=60,
        metavar="",
        help="Minimum length protein coding gene [amino acids]",
    )
    help_args = parser.add_argument_group("Help")
    help_args.add_argument(
        "-h",
        "--help",
        action="help",
        default=argparse.SUPPRESS,
        help="Show this help message and exit",
    )
    help_args.add_argument(
        "--version",
        action="version",
        version="{} v{}".format(
            os.path.basename(os.path.dirname(os.path.realpath(__file__))), __version__
        ),
        help="show program's version number and exit",
    )

    # If no arguments were used, print the base-level help which lists possible commands.
    if len(args) == 0:
        parser.print_help(file=sys.stderr)
        raise SystemExit(1)

    return parser.parse_args(args)


def fasta2hdf5(fasta, hdout, subseqlen=21384, species=str(uuid.uuid4())):
    controller = HelixerFastaToH5Controller(fasta, hdout)
    controller.export_fasta_to_h5(
        chunk_size=subseqlen,
        compression="gzip",
        multiprocess=True,
        species=species,
        write_by=20_000_000,
    )


if __name__ == "__main__":
    main()
