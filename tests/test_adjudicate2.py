"""The second adjudication pass: the rules that keep it honest."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from colophon import adjudicate2 as a2


def test_uncited_is_undecidable():
    """The fence: nothing reaches NET without a cited section, and a family no
    rule matches is undecidable by construction rather than by omission."""
    verdict = a2.adjudicate("a message nothing in the table describes", "dciodvfy")
    assert verdict["adjudication2"] == a2.UNDECIDABLE
    assert verdict["citation_section2"] == ""
    for pattern, v, section, table, rationale in a2.RULES:
        if v == a2.NET:
            assert section, pattern
            assert rationale, pattern


def test_dicom_validator_alone_never_produces_a_net_class():
    """Addendum 02 section 2 registers it as a second opinion on 1C and 2C only,
    never a rate source, because it fails open on unparseable conditions."""
    verdict, section, table, rationale = a2.DICOM_VALIDATOR_DEFAULT
    assert verdict == a2.UNDECIDABLE
    assert "fails open" in rationale


def test_the_crosswalk_between_the_two_vocabularies_is_published():
    assert a2.CROSSWALK["PLAUSIBILITY"] == a2.FLOOR
    assert a2.CROSSWALK["NOT-IOD"] == a2.FLOOR
    assert a2.CROSSWALK["NET"] == a2.NET
    assert a2.CROSSWALK["UNDECIDABLE"] == a2.UNDECIDABLE
    # The strict reading keeps the distinction so a coarse mapping cannot
    # manufacture agreement.
    assert a2.CROSSWALK_STRICT["PLAUSIBILITY"] == "PLAUSIBILITY"
    assert a2.CROSSWALK_STRICT["NOT-IOD"] == "NOT-IOD"


def test_an_unknown_first_pass_term_is_undecidable_not_net():
    assert a2.normalise_verdict("something new") == a2.UNDECIDABLE
    assert a2.normalise_verdict("") == a2.UNDECIDABLE


def test_pre_disclosed_families_are_flagged():
    """MORNING_REPORT.md disclosed several verdicts before this pass ran. A
    blind figure that included them would overstate the check."""
    assert a2.pre_disclosed(
        "Error - Missing attribute Type 2C Conditional Element=<Laterality> "
        "Module=<GeneralSeries>")
    assert a2.pre_disclosed(
        "Error - DisplayedAreaSelectionSequence is internally inconsistent")
    assert not a2.pre_disclosed(
        "Warning - Missing attribute or value that would be needed to build "
        "DICOMDIR - Study ID")


def test_family_keeps_the_attribute_and_collapses_the_value():
    """Too fine a unit adjudicates the same diagnostic 1,608 times. Too coarse
    a unit merges distinct attributes under one verdict."""
    a = a2.family_of("Error - Missing attribute Type 2 Required "
                     "Element=<ClinicalTrialSiteName> Module=<ClinicalTrialSubject>")
    b = a2.family_of("Error - Missing attribute Type 2 Required "
                     "Element=<Manufacturer> Module=<GeneralEquipment>")
    assert a != b, "the attribute must survive the family key"
    c = a2.family_of("Warning - Value dubious for this VR - (TAG) PN Patient's "
                     "Name PN [1] = <TCGA-BT-A42B> - Retired Person Name form")
    d = a2.family_of("Warning - Value dubious for this VR - (TAG) PN Patient's "
                     "Name PN [1] = <RMS2448> - Retired Person Name form")
    assert c == d, "the instance value must not survive the family key"


def test_consensus_only_keeps_agreements():
    frame = pd.DataFrame({
        "adjudication1": [a2.NET, a2.NET, a2.FLOOR, a2.FLOOR],
        "adjudication2": [a2.NET, a2.UNDECIDABLE, a2.FLOOR, a2.NET],
    })
    out = a2.consensus(frame)
    assert list(out["consensus"]) == [a2.NET, a2.UNDECIDABLE, a2.FLOOR,
                                      a2.UNDECIDABLE]
    assert list(out["agreed"]) == [True, False, True, False]


def test_agreement_is_reported_both_ways():
    """Over all classes and over the blind subset, never one alone."""
    path = Path("results/adjudication2/agreement.json")
    if not path.exists():
        pytest.skip("second pass has not been run")
    a = json.loads(path.read_text(encoding="utf-8"))
    for key in ("three_way_all", "three_way_blind", "net_binary_all",
                "net_binary_blind"):
        assert key in a and a[key]["kappa"] is not None
    assert a["three_way_blind"]["n"] < a["three_way_all"]["n"], (
        "the blind subset must exclude the pre-disclosed classes")
    assert a["pre_disclosed_classes"] > 0


def test_consensus_never_exceeds_either_pass():
    """Dropping disagreements to undecidable can only remove classes from the
    numerator, so the consensus rate is a lower bound on both."""
    path = Path("results/adjudication2/net_rates_two_pass.csv")
    if not path.exists():
        pytest.skip("second pass has not been run")
    net = pd.read_csv(path)
    for row in net.itertuples():
        assert row.net_consensus <= row.net_pass1, row.sop_class_name
        assert row.net_consensus <= row.net_pass2, row.sop_class_name


def test_no_first_pass_verdict_was_edited():
    """Both adjudications are published side by side. The first pass's files are
    read and never written."""
    source = Path(a2.__file__).read_text(encoding="utf-8")
    assert "to_csv" not in source, (
        "the adjudicating module must not write over the first pass")
    for path in Path("results/phase2").glob("adjudication_*.csv"):
        columns = pd.read_csv(path, nrows=1).columns
        assert "adjudication" in columns
        assert "adjudication2" not in columns, (
            "%s was overwritten by the second pass" % path.name)
