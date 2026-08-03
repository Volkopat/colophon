"""Pin deviations: the exposure has to stay measured, not asserted."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from colophon import deviations


def test_the_three_changelog_entries_are_the_whole_difference():
    """If the difference between the two dicom3tools builds is ever restated as
    something other than these three entries, the exposure measurement below
    stops bounding anything."""
    entries = {c["entry"] for c in deviations.CHANGELOG_DIFF}
    assert entries == {"231003", "241003", "241114"}
    conditions = {c["condition"] for c in deviations.CHANGELOG_DIFF}
    assert conditions == {"TILED_FULL", "LABELMAP"}


def test_pin_exposure_is_measured():
    frame, summary = deviations.dicom3tools_exposure()
    assert summary["measured_objects"] > 0
    # The two conditions are counted apart, never as one number.
    assert "LABELMAP_objects" in summary and "TILED_FULL_objects" in summary
    assert summary["exposed_objects"] == (summary["LABELMAP_objects"]
                                          + summary["TILED_FULL_objects"])
    # What was not captured has to travel with the number.
    assert summary["unmeasured"]["class"] == "Parametric Map Storage"
    assert summary["unmeasured"]["objects"] >= 0


def test_exposure_is_reported_per_class_and_analysis_result():
    frame, _ = deviations.dicom3tools_exposure()
    if len(frame):
        for column in ("sop_class_name", "analysis_result_id", "condition",
                       "objects", "pct_of_cell"):
            assert column in frame.columns


def test_highdicom_is_not_in_the_measurement_path():
    """The whole DEV-02 argument. If a measurement module ever starts calling a
    highdicom reader, the pin stops being inconsequential."""
    hd = deviations.highdicom_exposure()
    for module, flags in hd["imported_by_measurement_modules"].items():
        assert not flags["used_as_an_instrument"], module
    assert hd["corpus_objects_written_by_a_pinned_version"] == 0, (
        "an object written by 0.28.0 or 0.28.1 would put the pin back in scope")


def test_the_deviation_does_not_edit_the_registration():
    """A pin never satisfied is declared. A pin edited after seeing results is
    the thing pre-registration exists to prevent."""
    source = Path(deviations.__file__).read_text(encoding="utf-8")
    assert "1.00~20240118131615-1" in source
    assert "neither registration is edited" in source
    from colophon import floor
    assert floor.tool_versions()["dciodvfy"]["registered_pin"] == "1.00~20240118131615-1"


def test_the_direction_of_the_difference_is_stated():
    """The registered build is the stricter one. Reporting exposure without the
    direction would leave a reader unable to tell which way a rate could move."""
    source = Path(deviations.__file__).read_text(encoding="utf-8")
    assert "stricter" in source
    assert "lower bound" in source
