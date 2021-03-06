# emacs: -*- mode: python-mode; py-indent-offset: 4; tab-width: 4; indent-tabs-mode: nil; coding: utf-8 -*-
# ex: set sts=4 ts=4 sw=4 noet:
# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See COPYING file distributed along with the datalad package for the
#   copyright and license terms.
#
# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
"""Test all extractors at a basic level"""

from pkg_resources import iter_entry_points
from inspect import isgenerator
from datalad.api import Dataset
from datalad.utils import on_osx
from datalad.tests.utils import with_tree
from datalad.tests.utils import ok_clean_git
from datalad.tests.utils import known_failure_direct_mode

from nose import SkipTest
from nose.tools import assert_equal


@with_tree(tree={'file.dat': ''})
def check_api(no_annex, path):
    ds = Dataset(path).create(force=True, no_annex=no_annex)
    ds.add('.')
    ok_clean_git(ds.path)
    processed_extractors = []

    skip = []
    for extractor_ep in iter_entry_points('datalad.metadata.extractors'):
        processed_extractors.append(extractor_ep.name)
        # we need to be able to query for metadata, even if there is none
        # from any extractor
        try:
            extractor_cls = extractor_ep.load()
        except Exception as exc:
            exc_ = str(exc)
            #if 'Exempi library not found.' in exc_ or \
            #   'which was built for Mac OS X 10' in exc_:
            # known problems on OSX
            if on_osx:
                skip += [exc_]
                continue
            raise
        extractor = extractor_cls(
            ds, paths=['file.dat'])
        meta = extractor.get_metadata(
            dataset=True,
            content=True)
        # we also get something for the dataset and something for the content
        # even if any of the two is empty
        assert_equal(len(meta), 2)
        dsmeta, contentmeta = meta
        assert (isinstance(dsmeta, dict))
        assert hasattr(contentmeta, '__len__') or isgenerator(contentmeta)
        # verify that generator does not blow and has an entry for our
        # precious file
        cm = dict(contentmeta)
        # datalad_core does provide some (not really) information about our
        # precious file
        if extractor_ep.name == 'datalad_core':
            assert 'file.dat' in cm
    assert "datalad_core" in processed_extractors, \
        "Should have managed to find at least the core extractor extractor"
    if skip:
        raise SkipTest(
            "Not fully tested/succeded since some extractors failed"
            " to load:\n%s" % ("\n".join(skip)))


def test_api_git():
    # should tollerate both pure git and annex repos
    yield check_api, True


@known_failure_direct_mode
def test_api_annex():
    yield check_api, False
