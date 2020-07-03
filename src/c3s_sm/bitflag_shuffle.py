# -*- coding: utf-8 -*-
"""
Independent implementation of C3S bitflag creation, similar to the c3s metadata
Necessary as the image metadata cannot be transferred directly to time series.
Allows more sophisticated reading of data...
"""

from collections import Iterable, OrderedDict
import itertools
import pandas as pd
import numpy as np

def combinations(iterable, n, must_include=None):
    """
    Create possible combinations of an input iterable.
    Parameters
    ---------
    iterable: Iterable
        Elements from this iterable are combined.
    n : int
        Number of elements per combination.
    must_include : Iterable, optional (default: None)
        One or more element(s) of iterable that MUST be in each combination.

    Returns:
    ---------
    combs: iterable
        The possible combinations of n elements.
    """
    if must_include:
        if (not isinstance(must_include, Iterable)) or isinstance(must_include, str):
            must_include = [must_include]

    combs = list(itertools.combinations(iterable, n))
    if must_include:
        combs_filtered = []
        for comb in combs:
            if all([i in comb for i in must_include]):
                combs_filtered.append(comb)
        combs = combs_filtered
    return combs

class BitFlagShuffler():
    """ Class to generate bitflags and create flag names from a list of named bits """

    def __init__(self, unflagged, bit0_meaning, *other_bits_meanings):
        """
        Create Bit Flags, combinations of flags and conversion to int.

        Parameters
        ----------
        unflagged : str
            Value when a point is not flagged at all, i.e. all bit flags are 0
            2b000000 = int0 = no bits set = e.g. "good"
        bit0_meaning : str
            Meaning when bit0 is active, i.e. for 2b000001 = int1 = e.g. "frozen soil"
        other_bits_meanings : str
            Like bit0_meaning, for subsequent bits.
            e.g for bit1, i.e. for 2b000010 = int2 = e.g. "dense vegetation"
        """
        self.bits_flags = OrderedDict([(None, unflagged), (2**0, bit0_meaning)])

        for b, meaning in enumerate(other_bits_meanings, start=1):
            self.bits_flags[2**b] = meaning

        self.bits = list(self.bits_flags.keys())[1:]
        self.n_bits = len(self.bits)
        self.bitflag_template = '0b' + ''.join(['{b' + f'{2**b}' + '}'
                                                for b in reversed(range(self.n_bits))])

        self.template = {f'b{b}' : 0 for b in self.bits}
        self.df = self.build() # initial build with default args

    @staticmethod
    def bitflag2int(bitflag:str):
        return int(bitflag, 2)

    @staticmethod
    def int2bitflag(flag:int):
        return bin(flag)

    def _combi2bitflag(self, combi, num=True, pref='', sep='_', postf='') -> (str, str, int):
        """ Create combinatory bitflag (numbers from bit meanings) and description """
        kwargs = self.template.copy()
        for c in combi:
            kwargs[f'b{c}'] = 1

        if len(combi) == 0:
            meaning = self.bits_flags[None]
        elif len(combi) == 1:
            meaning = self.bits_flags[combi[0]]
        else:
            if num:
                flags = [str(int(f)) for f in combi]
            else:
                flags = [str(self.bits_flags[f]) for f in combi]
            meaning = pref + sep.join(flags) + postf

        bitflag = self.bitflag_template.format(**kwargs)

        return bitflag, meaning, self.bitflag2int(bitflag)

    def build(self, combis_ref_num=True, combis_prefix='combination_of_flag_values_',
              combis_sep='_and_', combis_postfix=''):
        """
        Create combinations of certain flags. If None are passed, all are used.

        Parameters
        ----------
        combis_ref_num : bool, optional (default: True)
            When creating the meanings for combined flags, refer to the single
            flags with their bit. If this is set to false, flags are referred
            to by their name instead of their number.
        combis_prefix : str (default: 'combination_of_flag_values_')
            Prefix for flag meaning when combining multiple flags
        combis_sep: str, optional (default: '_and_')
            Separator for flag meaning when combining multiple flags
        combis_postfix : str, optional (default: '')
            Postfix that is added to the flag meaning

        Returns
        -------
        self.df : pd.DataFrame
            DataFrame containing all the flags
        """

        bitflags, meanings, intflags, flags = [], [], [], []
        for bs in range(self.n_bits + 1):
            combis = combinations(self.bits, bs)
            for c in combis:
                bitflag, meaning, intflag = self._combi2bitflag(
                    c, combis_ref_num, combis_prefix, combis_sep, combis_postfix)
                bitflags.append(bitflag)
                meanings.append(meaning)
                intflags.append(intflag)
                flags.append(c)

        df = pd.DataFrame(index=intflags,
                          data={'bitflag':bitflags, 'meaning': meanings,
                                '_flags': flags}).sort_index()

        for b in self.bits:
            df[f'b{b}'] = False

        for ind, col in df['_flags'].iteritems():
            df.loc[ind, [f'b{b}' for b in col]] = True

        df.drop(columns=['_flags'], inplace=True)

        self.df = df
        return self.df

    def _idx4bit(self, bit) -> np.array:
        # find the indices in df where a bit is active
        return self.df[self.df[f'b{bit}'] == True].index.values

    def df4bit(self, include_bits:{int,list}=None,
               exclude_bits:{int,list}=None) -> pd.DataFrame:
        """
        Filter df for rows of flags for a certain bit

        Parameters
        ----------
        include_bits : int or list, optional (default: None)
            Bits (as in self.bits) which are included from self.df
            If None are passed, all are included
        exclude_bits : int or list, optional (default: None)
            Bits (as in self.bits) for which are excluded from self.df
            If None are passed, None are excluded

        Returns
        -------
        df : pd.DataFrame
            The filtered data
        """

        if include_bits is None:
            include_bits = self.bits
        if exclude_bits is None:
            exclude_bits = []

        if not isinstance(include_bits, Iterable):
            include_bits = [include_bits]
        if not isinstance(exclude_bits, Iterable):
            exclude_bits = [exclude_bits]

        for bit in include_bits + exclude_bits:
            if bit not in self.bits:
                raise ValueError(bit, f'Bit must be one of {self.bits}, {bit} is not.')

        indices_incl = []
        for bit in include_bits:
            indices_incl += self.df[self.df[f'b{bit}']==True].index.values.tolist()
        indices_incl = np.unique(np.array(indices_incl))

        indices_excl = []
        for bit in exclude_bits:
            indices_excl += self._idx4bit(bit).tolist()
        indices_excl = np.unique(np.array(indices_excl))

        idx = indices_incl[~np.in1d(indices_incl, indices_excl)]
        df = self.df.loc[idx].copy()

        return df
