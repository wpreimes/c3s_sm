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

class BitFlagShuffler(object):
    """
    Class to generate bitflags and create flag names from a list of
    named bits
    """

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
        self.bits_flags = OrderedDict([(0, unflagged), (2**0, bit0_meaning)])

        for b, meaning in enumerate(other_bits_meanings, start=1):
            self.bits_flags[2**b] = meaning

        self.bits = list(self.bits_flags.keys())[1:]
        self.n_bits = len(self.bits)
        self.bitflag_template = '0b' + ''.join(['{b' + f'{2**b}' + '}'
                                                for b in reversed(range(self.n_bits))])

        self.template = {f'b{b}' : 0 for b in self.bits}
        self._df = None

    @staticmethod
    def bitflag2int(bitflag:str):
        return int(bitflag, 2)

    @staticmethod
    def int2bitflag(flag:int):
        return bin(flag)

    @property
    def df(self):
        if self._df is None:
            self.build()
        return self._df

    @df.setter
    def df(self, df):
        self._df = df

    def _idx4bit(self, bit) -> np.array:
        # find the indices in _df where a bit is active
        return self.df[self.df[f'b{bit}'] == True].index.values

    def _combi2bitflag(self, combi, num=True, pref='', sep='_', postf='') -> (str, str, int):
        """ Create combinatory bitflag (numbers from bit meanings) and description """
        kwargs = self.template.copy()
        for c in combi:
            kwargs[f'b{c}'] = 1

        if len(combi) == 0:
            meaning = self.bits_flags[0]
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
        self._df : pd.DataFrame
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
        df.index.name = 'intflag'

        for b in self.bits:
            df[f'b{b}'] = False

        for ind, col in df['_flags'].iteritems():
            df.loc[ind, [f'b{b}' for b in col]] = True

        df.drop(columns=['_flags'], inplace=True)

        self.df = df
        return self.df

    def filter_bits(self, include_bits:{int, list}=None,
                    exclude_bits:{int,list}=None, inplace=False) -> pd.DataFrame:
        """
        Filter df for rows of flags for a certain bit

        Parameters
        ----------
        include_bits : int or list, optional (default: None)
            Bits (as in self.bits) which are included from self._df
            If None are passed, all are included
        exclude_bits : int or list, optional (default: None)
            Bits (as in self.bits) for which are excluded from self._df
            If None are passed, None are excluded
        inplace : bool, optional (default: True)
            Replace self._df with the filtered flags. If inplace is False, the
            new df is just returned

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

        if inplace:
            self.df = df

        return df

    def get_flags(self, index='bitflag', as_type='dict', drop_other=False,
                  no_combis=False):
        """
        Get object of currently loaded bit flags and their meaning

        Parameters
        ----------
        flagtype : {'intflag', 'bitflag'}, optional (default: 'bitflag')
            Set bit flag values or intflag values from self.df as the index
        as_type : {'dict', 'pandas'}, optional (default: 'dict')
            Return data in selected format
        drop_other : bool, optional (default: False)
            Drop intflag or bitflag, depending on which one is NOT the index
        no_combis : bool, optional (default: False)
            Only include flags that were passed at definition and not any
            combinations of flags.

        Returns
        -------
        bit_flags : {'dict', 'pandas'}
            Bit flags in the selected  data format
        """

        _types = {'dict', 'pandas'}
        _indices = {'intflag', 'bitflag'}

        index = index.lower()
        if index not in _indices:
            raise ValueError(f"Unexpected index passed, pass one of {_indices}")
        as_type = as_type.lower()
        if as_type not in _types:
            raise ValueError(f"Unexpected type passed, pass one of {_types}")

        df = self.df[['bitflag', 'meaning']]

        if no_combis:
            df = df.loc[[0, *self.bits], :]

        df = df.reset_index().set_index(index)

        if drop_other:
            df.drop(columns=[i for i in _indices if i != index], inplace=True)

        if as_type.lower() == 'pandas':
            return df

        elif as_type.lower() == 'dict':
            if len(df.columns) == 1:
                return df[df.columns[0]].to_dict(into=OrderedDict)
            else:
                return df.to_dict(into=OrderedDict, orient='index')
        else:
            raise ValueError(f"Unexpected type passed to 'as_type', expected on of {_types}")


class ProductBitFlag(BitFlagShuffler):
    def __init__(self, *args, active_bits=None, passive_bits=None):
        """
        Parameters
        ----------
        args :
            Passed to BitFlagShuffler
        active_bits : list, optional (default: None)
            Bit values that are valid for active sensors, or None to use all bits
        passive_bits : list, optional (default: None)
            Bit values that are valid for passive sensors, or None to use all bits
        """
        self.active_bits = active_bits
        self.passive_bits = passive_bits
        super(ProductBitFlag, self).__init__(*args)

    def get_prod_flags(self, sensor_prod, *args, **kwargs):
        """
        Get flags for a product

        Parameters
        ----------
        product : {'combined', 'active', 'passive'}
            Sensor product to get the flags for
        *args, **kwargs:
            Are passed to get_flags()

        Returns
        -------
        flags :
            Flags in the chosen format (default dict)
        """
        if sensor_prod.lower() == 'active':
            return self.get_active(*args, **kwargs)
        elif sensor_prod.lower() == 'passive':
            return self.get_passive(*args, **kwargs)
        elif sensor_prod.lower() == 'combined':
            return self.get_combined(*args, **kwargs)
        else:
            raise ValueError(f'{sensor_prod} is not an allowed product, expected '
                             f'one of: combined, active, passive')

    def get_active(self, *args, **kwargs):
        # get sensor flags for active sensors only (exclude passive from combined)
        self.filter_bits(include_bits=self.active_bits,
                         exclude_bits=self.passive_bits, inplace=True)
        flags = super(ProductBitFlag, self).get_flags(*args, **kwargs)
        self.filter_bits(None) # reset filter

        return flags

    def get_passive(self, *args, **kwargs):
        # get sensor flags for passive sensors only (exclude active from combined)
        self.filter_bits(include_bits=self.passive_bits,
                         exclude_bits=self.active_bits, inplace=True)
        flags = super(ProductBitFlag, self).get_flags(*args, **kwargs)
        self.filter_bits(None)  # reset filter

        return flags

    def get_combined(self, *args, **kwargs):
        # get sensor flag for all sensors
        flags = super(ProductBitFlag, self).get_flags(*args, **kwargs)

        return flags


class ProdVarAttr(object):
    """
    Store/access variable attributes for combined, active, passive separately
    """

    def __init__(self, name:str, active_attrs:dict, combined_attrs:dict,
                 passive_attrs:dict):

        self.name = name
        self.attrs = {'active': active_attrs, 'combined': combined_attrs,
                      'passive': passive_attrs}

    def get_sensor_attrs(self, sensor_prod):
        """
        Get attributes for combined, active or passive sensors

        Parameters
        ----------
        sensor_prod : {'combined', 'active', 'passive'}
            Sensor product

        Returns
        -------
        name : str
            Variable Name
        attrs : OrderedDict
            Variable Attributes
        """
        return self.name, self.attrs[sensor_prod]