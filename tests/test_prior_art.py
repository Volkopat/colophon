

# --- the two negatives addendum 03 asked to be closed --------------------------
def test_europe_pmc_negative_is_recorded():
    """Ledger PA-10. Two of the three attribute names return zero hits across
    the whole corpus, which is the most auditable negative in the paper."""
    from colophon import ledger
    row = {r["id"]: r for r in ledger.load()}["PA-10"]
    assert row["status"] == "MEASURED"
    assert "SegmentationAlgorithmIdentificationSequence 0 hits" in row["value"]
    assert "ContributingEquipmentSequence 0 hits" in row["value"]
    # Both hits are identified, so the negative cannot hide an unread record.
    assert "41113334" in row["value"] and "39443503" in row["value"]
    assert "europepmc" in row["command"].lower()


def test_cp_negative_covers_the_whole_series():
    """Ledger PA-11. Addendum 03 recorded this as unverified before 2023. The
    full numbered series parses, so the negative no longer needs a window."""
    from colophon import ledger
    row = {r["id"]: r for r in ledger.load()}["PA-11"]
    assert row["status"] == "MEASURED"
    assert "CP-1 to CP-2649" in row["value"]
    assert row["n"] == "0"
    # Title screening only, and that limit travels with the row.
    assert "title screening" in row["dropped"]
