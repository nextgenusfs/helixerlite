import time
import h5py
import pyfastx
import datetime
from .numerify import CoordNumerifier


class HelixerExportControllerBase(object):
    def __init__(self, input_path, output_path, match_existing=False):
        self.input_path = input_path
        self.output_path = output_path
        self.match_existing = match_existing

    @staticmethod
    def calc_n_chunks(coord_len, chunk_size):
        """calculates the number of chunks resulting from a coord len and chunk size"""
        n_chunks = coord_len // chunk_size
        if coord_len % chunk_size:
            n_chunks += 1  # bc pad to size
        n_chunks *= 2  # for + & - strand
        return n_chunks

    @staticmethod
    def _create_dataset(
        h5_file, key, matrix, dtype, compression="gzip", create_empty=True
    ):
        shape = list(matrix.shape)
        shuffle = len(shape) > 1
        if create_empty:
            shape[0] = 0  # create w/o size
        h5_file.create_dataset(
            key,
            shape=shape,
            maxshape=tuple([None] + shape[1:]),
            chunks=tuple([1] + shape[1:]),
            dtype=dtype,
            compression=compression,
            shuffle=shuffle,
        )  # only for the compression

    def _create_or_expand_datasets(
        self, h5_group, flat_data, n_chunks, compression="gzip"
    ):
        if h5_group not in self.h5 or len(self.h5[h5_group].keys()) == 0:
            for mat_info in flat_data:
                self._create_dataset(
                    self.h5,
                    h5_group + mat_info.key,
                    mat_info.matrix,
                    mat_info.dtype,
                    compression,
                )

        old_len = self.h5[h5_group + flat_data[0].key].shape[0]
        self.h5_coord_offset = old_len
        for mat_info in flat_data:
            self.h5[h5_group + mat_info.key].resize(old_len + n_chunks, axis=0)

    def _save_data(
        self,
        flat_data,
        h5_coords,
        n_chunks,
        first_round_for_coordinate,
        compression="gzip",
        h5_group="/data/",
    ):
        assert (
            len(set(mat_info.matrix.shape[0] for mat_info in flat_data)) == 1
        ), "unequal data lengths"

        if first_round_for_coordinate:
            self._create_or_expand_datasets(h5_group, flat_data, n_chunks, compression)

        # h5_coords are relative for the coordinate/chromosome, so offset by previous length
        old_len = self.h5_coord_offset
        start = old_len + h5_coords[0]
        end = old_len + h5_coords[1]

        # writing to the h5 file
        for mat_info in flat_data:
            self.h5[h5_group + mat_info.key][start:end] = mat_info.matrix
        self.h5.flush()

    def _add_data_attrs(self):
        attrs = {
            "timestamp": str(datetime.datetime.now()),
            "input_path": self.input_path,
        }
        # insert attrs into .h5 file
        for key, value in attrs.items():
            self.h5.attrs[key] = value


class HelixerFastaToH5Controller(HelixerExportControllerBase):
    class CoordinateSurrogate(object):
        """Mimics some functionality of the Coordinate orm class, so we can go directly from FASTA to H5"""

        def __init__(self, seqid, seq):
            self.seqid = seqid
            self.sequence = seq
            self.length = len(seq)

        def __repr__(self):
            return f"Fasta only Coordinate (seqid: {self.seqid}, len: {self.length})"

    def export_fasta_to_h5(
        self, chunk_size, compression, multiprocess, species, write_by
    ):
        assert write_by >= chunk_size, (
            "when specifying '--write-by' it needs to be larger than "
            "or equal to '--subsequence-length'"
        )
        self.h5 = h5py.File(self.output_path, "w")

        for i, (seqid, seq) in enumerate(
            pyfastx.Fasta(self.input_path, build_index=False)
        ):
            coord = HelixerFastaToH5Controller.CoordinateSurrogate(seqid, seq)
            n_chunks = HelixerExportControllerBase.calc_n_chunks(
                coord.length, chunk_size
            )
            data_gen = CoordNumerifier.numerify_only_fasta(
                coord,
                chunk_size,
                species,
                use_multiprocess=multiprocess,
                write_by=write_by,
            )
            for j, strand_res in enumerate(data_gen):
                data, h5_coords = strand_res
                self._save_data(
                    data,
                    h5_coords=h5_coords,
                    n_chunks=n_chunks,
                    first_round_for_coordinate=(j == 0),
                    compression=compression,
                )
        self._add_data_attrs()
        self.h5.close()
