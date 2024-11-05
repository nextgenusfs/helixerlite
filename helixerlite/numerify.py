"""convert cleaned-db schema to numeric values describing gene structure"""

import time

import numpy as np
import math
import multiprocessing
from abc import ABC, abstractmethod


AMBIGUITY_DECODE = {
    "C": [1.0, 0.0, 0.0, 0.0],
    "A": [0.0, 1.0, 0.0, 0.0],
    "T": [0.0, 0.0, 1.0, 0.0],
    "G": [0.0, 0.0, 0.0, 1.0],
    "Y": [0.5, 0.0, 0.5, 0.0],
    "R": [0.0, 0.5, 0.0, 0.5],
    "W": [0.0, 0.5, 0.5, 0.0],
    "S": [0.5, 0.0, 0.0, 0.5],
    "K": [0.0, 0.0, 0.5, 0.5],
    "M": [0.5, 0.5, 0.0, 0.0],
    "D": [0.0, 0.33, 0.33, 0.33],
    "V": [0.33, 0.33, 0.0, 0.33],
    "H": [0.33, 0.33, 0.33, 0.0],
    "B": [0.33, 0.0, 0.33, 0.33],
    "N": [0.25, 0.25, 0.25, 0.25],
}


class Stepper(object):
    def __init__(self, end, by):
        self.at = 0
        self.end = end
        self.by = by

    def step(self):
        prev = self.at
        if prev + self.by < self.end:
            new = prev + self.by
        else:
            new = self.end
        self.at = new
        return prev, new

    def step_to_end(self):
        while self.at < self.end:
            yield self.step()


class Numerifier(ABC):
    def __init__(self, n_cols, coord, max_len, dtype=np.float32, start=0, end=None):
        if end is None:
            end = coord.length
        assert isinstance(n_cols, int)
        self.n_cols = n_cols
        self.coord = coord
        self.max_len = max_len
        self.dtype = dtype
        self.matrix = None
        self.start = start
        self.end = end
        self.length = self.end - self.start
        # set paired steps
        partitioner = Stepper(end=self.end - self.start, by=self.max_len)
        self.paired_steps = list(partitioner.step_to_end())
        super().__init__()

    @abstractmethod
    def coord_to_matrices(self):
        """Method to be called from outside. Numerifies both strands."""
        pass

    def _slice_matrices(self, is_plus_strand, *argv):
        """Slices (potentially) multiple matrices in the same way according to self.paired_steps"""
        assert len(argv) > 0, "Need a matrix to slice"
        all_slices = [[] for _ in range(len(argv))]
        # reverse steps on minus strand
        steps = self.paired_steps if is_plus_strand else self.paired_steps[::-1]
        for prev, current in steps:
            for matrix, slices in zip(argv, all_slices):
                data_slice = matrix[prev:current]
                if not is_plus_strand:
                    # invert directions
                    data_slice = np.flip(data_slice, axis=0)
                slices.append(data_slice)
        return all_slices

    def _zero_matrix(self):
        self.matrix = np.zeros(
            (
                self.length,
                self.n_cols,
            ),
            self.dtype,
        )


def seq_numerify(seq_part):
    as_list = [AMBIGUITY_DECODE[c.upper()] for c in seq_part]
    return np.array(as_list, np.float16)


class SequenceNumerifier(Numerifier):
    def __init__(self, coord, max_len, start=0, end=None, use_multiprocess=True):
        self.use_multiprocess = use_multiprocess
        super().__init__(
            n_cols=4,
            coord=coord,
            max_len=max_len,
            dtype=np.float16,
            start=start,
            end=end,
        )

    def coord_to_matrices(self):
        """Does not alter the error mask unlike in AnnotationNumerifier"""

        # plus strand, actual numerification of the sequence
        start_time = time.time()
        seq = self.coord.sequence[self.start : self.end]
        seq_len = len(seq)  # can be slow
        if seq_len < int(1e6) or not self.use_multiprocess:
            # numerify short sequences sequentially
            as_list = [AMBIGUITY_DECODE[c.upper()] for c in seq]
            self.matrix = np.array(as_list, self.dtype)

        else:
            # numerify longer sequences in parallel
            # use one less cpu than possible, with minimum 500K chars per process
            n_processes = min(multiprocessing.cpu_count(), seq_len // int(5e5)) - 1
            with multiprocessing.Pool(n_processes) as p:
                max_seq_part_len = int(np.ceil(seq_len / n_processes))
                seq_parts = [
                    seq[offset : offset + max_seq_part_len]
                    for offset in range(0, seq_len, max_seq_part_len)
                ]
                numerified_parts = p.map(seq_numerify, seq_parts)
            assert seq_len == sum([len(p) for p in numerified_parts])
            self.matrix = np.concatenate(numerified_parts)

        # very important to copy here
        data_plus = self._slice_matrices(True, np.copy(self.matrix))[0]

        # minus strand
        self.matrix = np.flip(self.matrix, axis=1)  # complementary base
        # slice matrix will reverse direction
        data_minus = self._slice_matrices(False, self.matrix)[0]

        # put everything together
        data = {"plus": data_plus, "minus": data_minus}
        return data


class MatAndInfo:
    """organizes data and meta info for post-processing and saving a matrix"""

    def __init__(self, key, matrix, dtype):
        self.key = key
        self.matrix = matrix
        self.dtype = dtype

    def __repr__(self):
        return "key: {}, matrix shape: {}, matrix dtype {}: target dtype {}".format(
            self.key, self.matrix.shape, self.matrix.dtype, self.dtype
        )


class CoordNumerifier(object):
    """Combines the different Numerifiers which need to operate on the same Coordinate
    to ensure consistent parameters. Selects all Features of the given Coordinate.
    """

    @staticmethod
    def pad(d, chunk_size):
        n_seqs = len(d)
        # insert all the sequences so that 0-padding is added if needed
        shape = tuple([n_seqs, chunk_size] + list(d[0].shape[1:]))
        padded_d = np.zeros(shape, dtype=d[0].dtype)
        for j in range(n_seqs):
            padded_d[j, : len(d[j])] = d[j]
        return padded_d

    @staticmethod
    def start_ends(numerifier, strand):
        assert isinstance(numerifier, Numerifier)
        if strand == "plus":
            start_ends = numerifier.paired_steps
        else:
            # flip the start ends back for - strand
            start_ends = [(x[1], x[0]) for x in numerifier.paired_steps[::-1]]
        start_ends = np.array(start_ends, dtype=np.int64)
        return start_ends

    @staticmethod
    def seq_matinfos(coord, genome, start_ends, length):
        res = [
            MatAndInfo("species", np.array([genome.encode("ASCII")] * length), "S25"),
            MatAndInfo(
                "seqids", np.array([coord.seqid.encode("ASCII")] * length), "S50"
            ),
            MatAndInfo("start_ends", start_ends, "int64"),
        ]
        return res

    @staticmethod
    def numerify_only_fasta(
        coord, max_len, genome, one_hot=True, use_multiprocess=False, write_by=20000000
    ):
        """export the FASTA sequence only"""
        # passing empty features causes SplitFinder to consider noting more than splitting
        # to max length of write_by and end of sequence handling.
        split_finder = SplitFinder(
            features=(),
            write_by=write_by,
            coord_length=coord.length,
            chunk_size=max_len,
        )
        for _, bp_coord, h5_coord in split_finder.feature_n_coord_gen():
            start, end = bp_coord
            seq_numerifier = SequenceNumerifier(
                coord=coord,
                max_len=max_len,
                start=start,
                end=end,
                use_multiprocess=use_multiprocess,
            )
            xb = seq_numerifier.coord_to_matrices()
            for strand in ["plus", "minus"]:
                x = CoordNumerifier.pad(xb[strand], max_len)
                start_ends = CoordNumerifier.start_ends(seq_numerifier, strand)
                start_ends += start
                out = [MatAndInfo("X", x, "float16")]
                out.extend(
                    CoordNumerifier.seq_matinfos(coord, genome, start_ends, len(x))
                )
                yield tuple(out), h5_coord[strand]

    @staticmethod
    def numerify(
        coord,
        coord_features,
        max_len,
        one_hot=True,
        mode=("X", "y", "anno_meta", "transitions"),
        write_by=5000000,
        use_multiprocess=True,
    ):
        assert isinstance(max_len, int) and max_len > 0, "what is {} of type {}".format(
            max_len, type(max_len)
        )
        coord_features = sorted(
            coord_features, key=lambda f: min(f.start, f.end)
        )  # sort by ~ +strand start
        split_finder = SplitFinder(
            features=coord_features,
            write_by=write_by,
            coord_length=coord.length,
            chunk_size=max_len,
        )
        for f_set, bp_coord, h5_coord in split_finder.feature_n_coord_gen():
            for strand_res in CoordNumerifier._numerify_super_write_chunk(
                f_set,
                bp_coord,
                h5_coord,
                coord,
                max_len,
                one_hot,
                coord_features,
                mode,
                use_multiprocess,
            ):
                yield strand_res


# todo, consider moving to separate splitting file or exporter...?
class SplitFinder:
    def __init__(self, features, write_by, coord_length, chunk_size):
        if write_by % chunk_size:
            old_write_by = write_by
            write_by = chunk_size * (write_by // chunk_size)
        self.features = features
        self.write_by = write_by  # target writing this many bp to the h5 file at once
        self.coord_length = coord_length
        self.chunk_size = chunk_size
        self.splits = tuple(self._find_splits())
        self.relative_h5_coords = tuple(self._get_rel_h5_coords_for_splits())

    @property
    def coords(self):
        starts = [0] + list(self.splits)[:-1]
        return tuple(zip(starts, self.splits))

    def feature_n_coord_gen(self):
        """generator for feature subset, bp coordinates, and h5 coordinates (for +/-)"""
        return zip(self.split_features(), self.coords, self.relative_h5_coords)

    def split_features(self):
        """get all features from start of list that aren't passed _to_"""
        i = 0
        in_split = []
        in_next_split = []
        for end in self.splits:
            feature = self._ith_feature_or_none(i)
            while self._feature_not_past(feature, end):
                in_split.append(feature)
                if self._feature_ends_after(
                    feature, end
                ):  # basically this is 'if overlaps end' in context
                    in_next_split.append(feature)
                i += 1
                feature = self._ith_feature_or_none(i)
            yield in_split
            in_split = in_next_split
            in_next_split = []

    def _ith_feature_or_none(self, i):
        try:
            return self.features[i]
        except IndexError:
            return None

    def _get_rel_h5_coords_for_splits(self):
        """calculates where to write the +/- strand super-chunk splits in the h5 file"""
        # calculate the positive strand first
        postive_h5_ends = []
        postive_h5_starts = [0]
        for end in self.splits:
            p_h5 = end // self.chunk_size
            if end % self.chunk_size:  # end of seq, will be padded to full chunk size
                p_h5 += 1
            else:
                postive_h5_starts.append(p_h5)
            postive_h5_ends.append(p_h5)

        postive_h5s = list(zip(postive_h5_starts, postive_h5_ends))
        # calculate the negative strand as positive strand, but backwards from end
        h5_end = postive_h5_ends[-1] * 2
        negative_h5s = [(h5_end - x[1], h5_end - x[0]) for x in postive_h5s]
        return ({"plus": x[0], "minus": x[1]} for x in zip(postive_h5s, negative_h5s))

    @staticmethod
    def _feature_not_past(feature, to):
        """whether feature is before or overlaps end by any measure"""
        if feature is None:
            return False  # force break of while loop when out of features
        if feature.is_plus_strand:
            return feature.start < to
        else:
            # although the end is exclusive and this gets one position where the feature itself has no overlap;
            # for transitions themselves we potentially want to make sure the feature.end is included
            return feature.end < to

    @staticmethod
    def _feature_ends_after(feature, to):
        """combines with _feature_not_past to define overlaps of trailing edge 'to'"""
        # overlapping features will be saved and numerified with the next write_by split as well
        if feature.is_plus_strand:
            # include as soon as end is after, despite exclusive end, to include the transition just in case
            return feature.end >= to
        else:
            return feature.start >= to

    def _find_splits(self):
        """yields splits of ~write_by size that can be safely split at"""
        tr_mask = self._transition_and_split_cds_mask()
        for i in range(self.write_by, self.coord_length, self.write_by):
            if i not in tr_mask:
                yield i
            else:
                for i_fudge in range(
                    i, min(i + self.write_by, self.coord_length), self.chunk_size
                ):
                    if i_fudge not in tr_mask:
                        yield i_fudge
                        break
        yield self.coord_length

    def _transition_and_split_cds_mask(self):
        """mark all possible splits where there is a transition, so splitting there would change the numerify results"""
        tr_mask = set()
        for feature in self.features:
            # avoid splitting exactly at transitions, as transitions are detected by
            # state change (of binary encoding) and you can't detect state-change
            # if you split at it
            f_start, f_end = self._plus_strand_transitions(feature)
            for tr in (f_start, f_end):
                if not tr % self.chunk_size:
                    tr_mask.add(tr)
            # also avoid splitting in the middle of a CDS, this is necessary to
            # simplify the encoding of phase / avoid painful edge cases
            # this should add all chunk ends with a CDS to the mask
            cs = self.chunk_size
            if feature.type.value == "geenuff_cds":
                round_start = math.ceil(f_start / cs)
                round_end = math.ceil(f_end / cs)
                for chunk_end in range(round_start * cs, round_end * cs, cs):
                    tr_mask.add(chunk_end)

        return tr_mask

    @staticmethod
    def _plus_strand_transitions(feature):
        if feature.is_plus_strand:
            return feature.start, feature.end
        else:
            return feature.end - 1, feature.start - 1
