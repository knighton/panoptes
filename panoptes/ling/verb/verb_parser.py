from collections import defaultdict
from itertools import chain
import json
import sys

from base.combinatorics import each_choose_one_from_each, int_from_int_tuple, \
    int_tuple_from_int, collapse_int_tuples_to_wildcards
from ling.verb.conjugation import Conjugator, MAGIC_INTS_LEMMA
from ling.verb.verb import SurfaceVerb


def remove_lemma_specific_word(sss):
    if sss[1]:
        return tuple(sss[0]), tuple(sss[1][:-1])
    else:
        return None


def deverb(sss):
    return tuple(sss[0]), tuple(sss[1][:-1])


def to_ints(sss2vv, options_per_field, num_options_per_field):
    s2nn = {}
    for sss, vv in sss2vv.iteritems():
        s = ' '.join(list(sss[0]) + ['|'] + list(sss[1]))
        nnn = []
        for v in vv:
            nn = v.to_int_tuple(options_per_field)
            nnn.append(nn)
        print 'Collapsing', len(nnn),
        sys.stdout.flush()
        nnn = collapse_int_tuples_to_wildcards(nnn, num_options_per_field)
        print '->', len(nnn)
        ints = []
        for nn in nnn:
            n = int_from_int_tuple(nn, num_options_per_field)
            ints.append(n)
        s2nn[s] = ints
    return s2nn


def save_lookup_tables(be, pro, deverbed, f):
    """
    be, pro, deverbed, f -> None
    """
    verbs_used = ['be', 'see', MAGIC_INTS_LEMMA]
    options_per_field = SurfaceVerb.all_options(verbs_used, [False, True])
    zz = map(len, options_per_field)
    be_s2nn = to_ints(be, options_per_field, zz)
    pro_verb_s2nn = to_ints(pro, options_per_field, zz)
    deverbed_s2nn = to_ints(deverbed, options_per_field, zz)
    d = {
        'options_per_field': options_per_field,
        'be': be_s2nn,
        'pro-verb': pro_verb_s2nn,
        'deverbed': deverbed_s2nn,
    }
    json.dump(d, open(f, 'wb'))


def load_lookup_tables(f):
    """
    f -> be, pro, deverbed
    """

    """
    d = cPickle.load(open(f))
    return d['be'], d['pro-verb'], d['deverbed']
    """

    assert False  # XXX


def construct_one_lookup_table(verb_sayer, lemmas, is_pro_verbs):
    finite_options = SurfaceVerb.finite_options(lemmas, is_pro_verbs)
    nonfinite_options = SurfaceVerb.nonfinite_options(lemmas, is_pro_verbs)
    sss2vv = defaultdict(list)
    for aa in chain(each_choose_one_from_each(finite_options),
                    each_choose_one_from_each(nonfinite_options)):
        v = SurfaceVerb.from_tuple(aa)
        for sss in verb_sayer.get_all_say_options(v):
            sss = (tuple(sss[0]), tuple(sss[1]))
            sss2vv[sss].append(v)
    return sss2vv


def construct_lookup_tables(sayer):
    """
    None -> be, pro, deverbed
    """
    print 'Conjugating forms of "to be"...'
    be = construct_one_lookup_table(sayer, ['be'], [False, True])
    print 'Conjugating pro-verbs...'
    pro = construct_one_lookup_table(sayer, ['see'], [True])
    print 'Conjugating all other verbs...'
    deverbed = construct_one_lookup_table(sayer, [MAGIC_INTS_LEMMA], [False])
    print 'Done conjugating.'
    return be, pro, deverbed


class VerbParser(object):
    def __init__(self, conjugator, be_sss2vv, pro_verb_sss2vv, deverbed_sss2vv):
        self.conjugator = conjugator
        assert isinstance(self.conjugator, Conjugator)

        # (pre words, main words) -> list of SurfaceVerb.
        #
        # The "to be" table.  "To be" conjugates specially.
        self.be_sss2vv = be_sss2vv
        assert isinstance(self.be_sss2vv, defaultdict)

        # (pre words, main words) -> list of SurfaceVerb.
        #
        # Pro-verbs also conjugate specially.
        self.pro_verb_sss2vv = pro_verb_sss2vv
        assert isinstance(self.pro_verb_sss2vv, defaultdict)

        # (pre words, main words with int) -> list of de-lemma'd SurfaceVerb.
        #
        # Table for everything else.  Replace conjugated lemma-specific word
        # with its field index to use.
        self.deverbed_sss2vv = deverbed_sss2vv
        assert isinstance(self.deverbed_sss2vv, defaultdict)

        # Used by main_sss2vv parsing.
        self.deverbed_sss_set = \
            set(filter(bool, map(remove_lemma_specific_word,
                                 self.deverbed_sss2vv)))

    @staticmethod
    def load(conjugator, f):
        be, pro, deverbed = load_lookup_tables(f)
        return VerbParser(conjugator, be, pro, deverbed)

    @staticmethod
    def construct(verb_sayer, f):
        be, pro, deverbed = construct_lookup_tables(verb_sayer)
        save_lookup_tables(be, pro, deverbed, f)
        return VerbParser(verb_sayer.conjugator, be, pro, deverbed)

    @staticmethod
    def load_or_construct(verb_sayer, f):
        try:
            return VerbParser.load(verb_sayer.conjugator, f)
        except:
            return VerbParser.construct(verb_sayer, f)

    def parse_field_index_replacing(self, sss):
        """
        (pre words tuple, main words tuple) -> list of SurfaceVerb
        """
        # It must have main words on the right.
        if not sss[1]:
            return []

        # Lemma-specific conjugated word must be verified to look like a verb,
        # as it isn't implicity checked by the lookup table generation like the
        # others.
        last = sss[1][-1]
        if not last.islower():
            return []

        # The lemma-agnostic remainder of the verb words must be known.
        deverbed_sss = deverb(sss)
        if deverbed_sss not in self.deverbed_sss_set:
            return []

        # Decode what the lemma-specific word means.
        rr = []
        for lemma, field_index in self.conjugator.identify_word(last):
            # Look up the field index-replaced form in the table.
            key = (deverbed_sss[0], tuple(deverbed_sss[1] + [str(field_index)]))
            sub_rr = self.deverbed_sss2vv[key]

            # Put our lemma into the results found.
            for r in sub_rr:
                r.intrinsics.lemma = lemma

            rr += sub_rr
        return rr

    def parse(self, sss):
        """
        (pre words tuple, main words tuple) -> list of SurfaceVerb
        """
        rr = []
        rr += self.be_sss2vv[sss]
        rr += self.pro_verb_sss2vv[sss]
        rr += self.parse_field_index_replacing(sss)
        return rr
