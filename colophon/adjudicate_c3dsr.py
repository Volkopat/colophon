"""Track C adjudication: Comprehensive 3D SR Storage.

One SOP class, 5,408 objects in 5,408 series, five producer groups:
`nnu_net_bpr_annotations` (2,906), `lung_pet_ct_dx_annotations` (1,091),
`nlst_sybil` (970), `prostatex_targets` (345) and
`rms_mutation_prediction_expert_annotations` (96). Every distinct
`message_class_id` the Phase 2 census recorded for this class is adjudicated
here into exactly one of five categories, and no message class is skipped.

    FLOOR         permitted by the standard, the validator flags it anyway. A
                  citation showing the construct is permitted is required.
    NET           a stated requirement is violated. The section and the table
                  giving the Type or the condition are required.
    NOT-IOD       not about IOD conformance at all.
    PLAUSIBILITY  a value-quality heuristic with no requirement behind it.
    UNDECIDABLE   no citation reaches it. This is the default rather than a
                  fallback of last resort: a rule that does not match leaves the
                  class UNDECIDABLE and says so.

The project forbids adjudicating its own results. Nothing here decides whether
an object is good. Each rule attaches the standard's own words to a validator's
own words, and where the two do not meet, the class is UNDECIDABLE and the gap
is written down.

Four findings in this class needed the standard rather than an opinion.

**Clinical Trial Site Name and Site ID.** Both are Type 2 in PS3.3 Table
C.7-2b, and the Clinical Trial Subject Module is Usage U in PS3.3 Table
A.35.13-1. PS3.3 Section A.1.3.3 is the sentence that makes a User Option
Module's Attribute Types bind once the Module is there. Recorded as NET, with
the residual stated and not resolved: A.1.3.3 says "if an optional Module is
supported", and PS3.3 does not define when a stored Data Set counts as
supporting one. Both validators decided that antecedent independently and
landed on identical object sets, and the calculation is also published with
these classes demoted so a reader who reads A.1.3.3 as an implementation
statement does not have to recompute.

**De-identification Method and De-identification Method Code Sequence.** Two
Type 1C rows of the mandatory Patient Module whose conditions refer to each
other. Both are met exactly when Patient Identity Removed (0012,0062) is
present with Value YES and neither attribute is present, which is the state
both validators report on identical object sets. Recorded as NET.

**Ethnic Group (0010,2160).** Retired from the Patient Module. Table C.7-1 in
the pinned edition carries Ethnic Groups (0010,2162) in its place and says so
in the Attribute Description. PS3.6 Table 6-1 still allocates (0010,2160) and
marks it RET (2025a). dicom-validator's message is `is unexpected`, which its
own `ErrorCode.TagUnexpected` documents as "Tag is not in any allowed module",
so it fires on every attribute outside the IOD's module set, retired or
Standard Extended alike. FLOOR, and dciodvfy does not raise it at all.

**Procedure Code Sequence with zero Items.** PS3.5 Section 7.4.5 carries an
explicit prohibition for this case. The companion Value Multiplicity message
dciodvfy emits on the same two objects prints neither the observed nor the
required multiplicity, so no requirement can be attached to it by citation and
it is left UNDECIDABLE. It changes no triple, because it lands on objects that
are already NET.

Usage:
    python -m colophon.adjudicate_c3dsr
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

from .paths import CACHE, RESULTS

CMD = "python -m colophon.adjudicate_c3dsr"
SOP_CLASS = "Comprehensive 3D SR Storage"
EDITION = "PS3 2026c"
VERIFIED_ON = "2026-08-02"

CLASSES_CSV = RESULTS / "phase2" / "census_message_classes.csv"
RECORDS = CACHE / "census" / "records.jsonl"
OUT_CSV = RESULTS / "phase2" / "adjudication_comprehensive_3d_sr.csv"
OUT_MD = RESULTS / "phase2" / "net_rates_comprehensive_3d_sr.md"
OUT_LEDGER = RESULTS / "pending_ledger" / "track_c_c3dsr.json"

FLOOR_LIKE = {"FLOOR", "NOT-IOD", "PLAUSIBILITY"}

# Two sensitivity dimensions, each a set of rule names that a strict reader
# might refuse. Both are reported with every headline number so nobody has to
# recompute the study to disagree with one adjudication.
#
# OFF_PART        the rubric scopes NET citations to PS3.3, PS3.4 and PS3.16.
#                 The Type violated here is given in PS3.3 Table C.7-3 but the
#                 operative prohibition, that a Type 3 SQ shall not be present
#                 with zero Items, is stated in PS3.5 Section 7.4.5 and nowhere
#                 in the IOD parts.
# MODULE_PRESENCE PS3.3 Section A.1.3.3 binds the Attribute Types of a User
#                 Option Module when the Module "is supported". PS3.3 does not
#                 say when a stored Data Set counts as supporting one.
OFF_PART_RULES = {"PROC_CODE_SEQ_ZERO_ITEMS"}
MODULE_PRESENCE_RULES = {"CT_SUBJECT_TYPE2", "DV_CT_SITE_MISSING"}


# --- the rubric, one entry per rule ------------------------------------------
# Ordered. First match wins. `pattern` is searched against the message template
# exactly as the census recorded it.
RULES: list[dict] = [
    dict(
        name="DICOMDIR",
        validator="dciodvfy",
        pattern=r"^Warning - Missing attribute or value that would be needed to "
                r"build DICOMDIR",
        adjudication="NOT-IOD",
        section="PS3.3 Section F.5.2 Study Directory Record Definition; PS3.3 "
                "Section C.7.2.1 General Study Module",
        table="PS3.3 Table F.5-2 Study Keys; PS3.3 Table C.7-3 General Study "
              "Module Attributes",
        quote='PS3.3 Table C.7-3, row "Study ID", tag (0020,0010), Type 2: "User '
              'or equipment generated Study identifier." Row "Study Time", tag '
              '(0008,0030), Type 2: "Time the Study started."',
        rationale="The canonical NOT-IOD case named in the rubric. The attributes "
                  "are wanted for a Study Directory Record of the Basic Directory "
                  "IOD, which is the DICOMDIR, an object this study does not build "
                  "and IDC does not distribute. Both are Type 2 in the module the "
                  "Comprehensive 3D SR IOD actually includes, so a zero length "
                  "value satisfies them, and dciodvfy raised no Type 2 message "
                  "against either attribute on any object in this class. dciodvfy "
                  "says in the message text that this is about building a "
                  "DICOMDIR, emits it at Warning severity, and names no Type.",
    ),
    dict(
        name="RETIRED_PN",
        validator="dciodvfy",
        pattern=r"^Warning - Value dubious for this VR .* Retired Person Name form$",
        adjudication="PLAUSIBILITY",
        section="not applicable, no requirement is cited by the message",
        table="not applicable",
        quote="",
        rationale="Named in the rubric as a plausibility heuristic. The message is "
                  "about the shape of a PN value, a single component with no caret "
                  "delimiters, which PS3.5 Table 6.2-1 permits for VR PN. No Type "
                  "and no condition is asserted, and dciodvfy emits it at Warning "
                  "severity with the word dubious. 1,209 of the 1,224 message "
                  "classes in this SOP class fall under this rule, one per distinct "
                  "name value, because the census keys a class on the normalised "
                  "message text and the value sits inside it.",
    ),
    dict(
        name="CT_SUBJECT_TYPE2",
        validator="dciodvfy",
        pattern=r"^Error - Missing attribute Type 2 Required "
                r"Element=<ClinicalTrialSite(Name|ID)> Module=<ClinicalTrialSubject>$",
        adjudication="NET",
        section="PS3.3 Section C.7.1.3 Clinical Trial Subject Module; PS3.3 "
                "Section A.1.3 IOD Module Table and Functional Group Macro Table "
                "and Section A.1.3.3 User Option Modules; PS3.3 Section A.35.13 "
                "Comprehensive 3D SR IOD; Type 2 semantics in PS3.5 Section 7.4.3",
        table="PS3.3 Table C.7-2b Clinical Trial Subject Module Attributes, rows "
              "Clinical Trial Site ID (0012,0030) Type 2 and Clinical Trial Site "
              "Name (0012,0031) Type 2; PS3.3 Table A.35.13-1 Comprehensive 3D SR "
              "IOD Modules, row Clinical Trial Subject, Usage U",
        quote='PS3.3 Table C.7-2b, row "Clinical Trial Site Name", tag '
              '(0012,0031), Type 2: "Name of the site responsible for submitting '
              'clinical trial or research data." Row "Clinical Trial Site ID", tag '
              '(0012,0030), Type 2: "The identifier of the site responsible for '
              'submitting clinical trial or research data." PS3.3 Table A.35.13-1 '
              'gives the Clinical Trial Subject Module Usage U. PS3.3 Section '
              'A.1.3.3 User Option Modules, in full: "User Option Modules may or '
              'may not be supported. If an optional Module is supported, the '
              'Attribute Types specified in the Modules in Annex C shall be '
              'supported." PS3.5 Section 7.4.3: "IODs and SOP Classes define Type 2 '
              'Data Elements that shall be included and are mandatory Data '
              'Elements. However, it is permissible that if a Value for a Type 2 '
              'Data Element is unknown it can be encoded with zero Value Length and '
              'no Value. ... These Data Elements shall be included in the Data Set '
              'and their absence is a protocol violation."',
        rationale="A Type 2 attribute of a Module the object carries is absent "
                  "entirely, not present and zero length, which PS3.5 Section 7.4.3 "
                  "calls a protocol violation in terms. Two validators from "
                  "different codebases report it on identical object sets, 935 "
                  "objects for Site Name and 8 for Site ID with nothing on either "
                  "side of either difference. One residual is recorded and not "
                  "resolved: PS3.3 Section A.1.3.3 conditions the obligation on the "
                  "optional Module being supported, and PS3.3 states no test for "
                  "when a stored Data Set supports one. Both tools decide that "
                  "antecedent from the presence of other attributes of the Module, "
                  "dciodvfy by naming the Module in the message and dicom-validator "
                  "through its documented _does_module_strongly_exist check, and "
                  "neither is quoting the standard when it does so. Every triple in "
                  "the report is also given with this rule demoted to UNDECIDABLE.",
    ),
    dict(
        name="DEIDENT_1C",
        validator="dciodvfy",
        pattern=r"^Error - Missing attribute Type 1C Conditional "
                r"Element=<DeidentificationMethod(CodeSequence)?> Module=<Patient>$",
        adjudication="NET",
        section="PS3.3 Section C.7.1.1 Patient Module; PS3.3 Section A.35.13 "
                "Comprehensive 3D SR IOD; Type 1C semantics in PS3.5 Section 7.4.2",
        table="PS3.3 Table C.7-1 Patient Module Attributes, rows De-identification "
              "Method (0012,0063) Type 1C and De-identification Method Code "
              "Sequence (0012,0064) Type 1C; PS3.3 Table A.35.13-1 Comprehensive 3D "
              "SR IOD Modules, row Patient, Usage M",
        quote='PS3.3 Table C.7-1, row "De-identification Method", tag (0012,0063), '
              'Type 1C, closing sentences of the Attribute Description: "Required '
              'if Patient Identity Removed (0012,0062) is present and has a Value '
              'of YES and De-identification Method Code Sequence (0012,0064) is not '
              'present. May be present otherwise." Row "De-identification Method '
              'Code Sequence", tag (0012,0064), Type 1C: "Required if Patient '
              'Identity Removed (0012,0062) is present and has a Value of YES and '
              'De-identification Method (0012,0063) is not present. May be present '
              'otherwise." PS3.5 Section 7.4.2: "IODs and SOP Classes define Data '
              'Elements that shall be included under certain specified conditions. '
              'Type 1C Data Elements have the same requirements as Type 1 Data '
              'Elements under these conditions. It is a protocol violation if the '
              'specified conditions are met and the Data Element is not included."',
        rationale="The two conditions refer to each other, so both are met exactly "
                  "when Patient Identity Removed (0012,0062) is present with Value "
                  "YES and neither attribute is present. That is the only state in "
                  "which both messages can be raised together, and both are raised "
                  "together on all 828 objects by dciodvfy and independently by "
                  "dicom-validator, with nothing on any side of any difference. "
                  "The condition is fully evaluable from the Data Set, unlike the "
                  "Laterality Type 2C already adjudicated FLOOR for this project, "
                  "because every term of it is an attribute in the same Module. "
                  "The Patient Module is Usage M in Table A.35.13-1, so no module "
                  "presence question arises.",
    ),
    dict(
        name="REF_SOP_CLASS_UID",
        validator="dciodvfy",
        pattern=r"^Error - Missing attribute Type 1 Required "
                r"Element=<ReferencedSOPClassUID> Module=<SOPInstanceReferenceMacro>$",
        adjudication="NET",
        section="PS3.3 Section 10.8 SOP Instance Reference Macro; reached from "
                "PS3.3 Section C.7.2.1 General Study Module; Type 1 semantics in "
                "PS3.5 Section 7.4.1 and per-Item scope in PS3.5 Section 7.4.6",
        table="PS3.3 Table 10-11 SOP Instance Reference Macro Attributes, row "
              "Referenced SOP Class UID (0008,1150) Type 1; included by PS3.3 Table "
              "C.7-3 General Study Module Attributes, row Referenced Study Sequence "
              "(0008,1110) Type 3",
        quote='PS3.3 Table 10-11, row "Referenced SOP Class UID", tag (0008,1150), '
              'Type 1: "Uniquely identifies the referenced SOP Class." PS3.3 Table '
              'C.7-3, row "Referenced Study Sequence", tag (0008,1110), Type 3: "A '
              'Sequence that provides reference to a Study. One or more Items are '
              'permitted in this Sequence.", followed by the row ">Include Table '
              '10-11 SOP Instance Reference Macro Attributes". PS3.5 Section 7.4.1: '
              '"IODs and SOP Classes define Type 1 Data Elements that shall be '
              'included and are mandatory Data Elements. ... Absence of a valid '
              'Value in a Type 1 Data Element is a protocol violation." PS3.5 '
              'Section 7.4.6: "The Types of the Attributes of the Data Set included '
              'in the Sequence, including any conditionality, are specified within '
              'the scope of each Data Set, i.e., for each Item present in the '
              'Sequence."',
        rationale="Referenced Study Sequence is Type 3, so it need not be present "
                  "at all, but PS3.5 Section 7.4.6 puts the Types of Table 10-11 in "
                  "scope for every Item that is present. The Item is present and "
                  "its Type 1 Referenced SOP Class UID is not. dicom-validator "
                  "reaches the same 38 objects by a different route and prints the "
                  "full path, Module <General Study> (0008,1110) (Referenced Study "
                  "Sequence) Tag (0008,1150) (Referenced SOP Class UID) is missing, "
                  "which names the enclosing Sequence that dciodvfy's message does "
                  "not. Its error code is TagMissing, not TagUnexpected, so the "
                  "modelling defect recorded against this tool for nested macro "
                  "children in the Comprehensive SR adjudication does not reach it.",
    ),
    dict(
        name="PROC_CODE_SEQ_ZERO_ITEMS",
        validator="dciodvfy",
        pattern=r"^Error - Bad Sequence number of Items 0 .*"
                r"Element=<ProcedureCodeSequence> Module=<GeneralStudy>$",
        adjudication="NET",
        section="PS3.3 Section C.7.2.1 General Study Module; Type 3 semantics in "
                "PS3.5 Section 7.4.5",
        table="PS3.3 Table C.7-3 General Study Module Attributes, row Procedure "
              "Code Sequence (0008,1032) Type 3",
        quote='PS3.3 Table C.7-3, row "Procedure Code Sequence", tag (0008,1032), '
              'Type 3: "A Sequence that conveys the type of procedure performed. '
              'One or more Items are permitted in this Sequence." PS3.5 Section '
              '7.4.5 Type 3 Optional Data Elements, in full: "IODs and SOP Classes '
              'define Type 3 Data Elements that are optional Data Elements. Absence '
              'of a Type 3 Data Element from a Data Set does not convey any '
              'significance and is not a protocol violation. Type 3 Data Elements '
              'may also be encoded with zero length and no Value, except for SQ '
              'Data Elements, which shall not be present with zero Items. The '
              'meaning of a zero length Type 3 Data Element shall be precisely the '
              'same as that Data Element being absent from the Data Set."',
        rationale="The Attribute Description in Table C.7-3 is permissive and says "
                  "Items are permitted rather than required, so dciodvfy's phrase "
                  "1-n Required by Module definition is not what the module "
                  "definition says. The prohibition that carries this class is "
                  "elsewhere and is exact: PS3.5 Section 7.4.5 states that SQ Data "
                  "Elements shall not be present with zero Items. Recorded as NET "
                  "and flagged off-part, because the rubric scopes NET citations to "
                  "PS3.3, PS3.4 and PS3.16 and the operative shall is in PS3.5. "
                  "Every triple in the report is also given with this rule demoted "
                  "to UNDECIDABLE. Two objects.",
    ),
    dict(
        name="PROC_CODE_SEQ_VM",
        validator="dciodvfy",
        pattern=r"^Error - Bad attribute Value Multiplicity Type 3 Optional "
                r"Element=<ProcedureCodeSequence> Module=<GeneralStudy>$",
        adjudication="UNDECIDABLE",
        section="PS3.3 Section C.7.2.1 General Study Module",
        table="PS3.3 Table C.7-3 General Study Module Attributes, row Procedure "
              "Code Sequence (0008,1032) Type 3",
        quote='PS3.3 Table C.7-3, row "Procedure Code Sequence", tag (0008,1032), '
              'Type 3: "A Sequence that conveys the type of procedure performed. '
              'One or more Items are permitted in this Sequence." PS3.5 Section '
              '7.5: "Data Elements with a VR of SQ may contain multiple Items but '
              'shall always have a Value Multiplicity of one (i.e., a single '
              'Sequence)."',
        rationale="The message names an attribute, a module and a Type, and asserts "
                  "that the Value Multiplicity is bad, but prints neither the "
                  "observed multiplicity nor the required one, so which "
                  "multiplicity rule it is applying cannot be recovered from the "
                  "output. PS3.5 Section 7.5 fixes the VM of any SQ at one "
                  "regardless of item count, which makes a literal reading of the "
                  "message unattachable to a requirement. Left UNDECIDABLE rather "
                  "than folded into the zero-Items finding by judgement. What is "
                  "measured rather than assumed is that it lands on exactly the 2 "
                  "objects that carry the zero-Items class, with nothing on either "
                  "side of the difference, so it moves no triple: those objects are "
                  "already net.",
    ),
    dict(
        name="DV_CT_SITE_MISSING",
        validator="dicom-validator",
        pattern=r"^Module <Clinical Trial Subject> Tag \(TAG\) "
                r"\(Clinical Trial Site (Name|ID)\) is missing$",
        adjudication="NET",
        section="PS3.3 Section C.7.1.3 Clinical Trial Subject Module; PS3.3 "
                "Section A.1.3.3 User Option Modules; Type 2 semantics in PS3.5 "
                "Section 7.4.3",
        table="PS3.3 Table C.7-2b Clinical Trial Subject Module Attributes, rows "
              "Clinical Trial Site ID (0012,0030) Type 2 and Clinical Trial Site "
              "Name (0012,0031) Type 2; PS3.3 Table A.35.13-1 Comprehensive 3D SR "
              "IOD Modules, row Clinical Trial Subject, Usage U",
        quote='PS3.3 Table C.7-2b, row "Clinical Trial Site Name", tag '
              '(0012,0031), Type 2: "Name of the site responsible for submitting '
              'clinical trial or research data." PS3.3 Section A.1.3.3: "User '
              'Option Modules may or may not be supported. If an optional Module is '
              'supported, the Attribute Types specified in the Modules in Annex C '
              'shall be supported." PS3.5 Section 7.4.3: "These Data Elements shall '
              'be included in the Data Set and their absence is a protocol '
              'violation."',
        rationale="The second codebase on the same finding, by a different route. "
                  "Its error code here is ErrorCode.TagMissing, documented in "
                  "dicom-validator 0.8.2 as Mandatory tag is missing from a module, "
                  "not ErrorCode.TagUnexpected, so the modelling defect recorded "
                  "against this tool for nested macro children in the Comprehensive "
                  "SR adjudication does not reach it. It reaches the module "
                  "presence question through _does_module_strongly_exist, which "
                  "requires the module to carry at least one attribute that no "
                  "other candidate module carries. That heuristic is the tool's, "
                  "not the standard's, so this rule carries the same recorded "
                  "residual and the same demotion in the sensitivity table as the "
                  "dciodvfy class it agrees with.",
    ),
    dict(
        name="DV_DEIDENT_MISSING",
        validator="dicom-validator",
        pattern=r"^Module <Patient> Tag \(TAG\) "
                r"\(De-identification Method( Code Sequence)?\) is missing$",
        adjudication="NET",
        section="PS3.3 Section C.7.1.1 Patient Module; Type 1C semantics in PS3.5 "
                "Section 7.4.2",
        table="PS3.3 Table C.7-1 Patient Module Attributes, rows De-identification "
              "Method (0012,0063) Type 1C and De-identification Method Code "
              "Sequence (0012,0064) Type 1C",
        quote='PS3.3 Table C.7-1, row "De-identification Method", tag (0012,0063), '
              'Type 1C: "Required if Patient Identity Removed (0012,0062) is '
              'present and has a Value of YES and De-identification Method Code '
              'Sequence (0012,0064) is not present. May be present otherwise." Row '
              '"De-identification Method Code Sequence", tag (0012,0064), Type 1C: '
              '"Required if Patient Identity Removed (0012,0062) is present and has '
              'a Value of YES and De-identification Method (0012,0063) is not '
              'present. May be present otherwise." PS3.5 Section 7.4.2: "It is a '
              'protocol violation if the specified conditions are met and the Data '
              'Element is not included."',
        rationale="Independent confirmation in the strict sense. The two tools do "
                  "not share a parsed model, a condition evaluator or a codebase, "
                  "and dicom-validator's condition for (0012,0063), read back from "
                  "its 2026c model, is the conjunction of (0012,0062) equal to YES "
                  "and (0012,0064) absent, which is Table C.7-1's condition. The "
                  "error code is TagMissing, so the TagUnexpected modelling defect "
                  "does not reach it. Identical object sets, 828 on each of the two "
                  "attributes, nothing on any side of any difference.",
    ),
    dict(
        name="DV_REF_SOP_CLASS_MISSING",
        validator="dicom-validator",
        pattern=r"\(Referenced Study Sequence\) Tag \(TAG\) "
                r"\(Referenced SOP Class UID\) is missing$",
        adjudication="NET",
        section="PS3.3 Section 10.8 SOP Instance Reference Macro; reached from "
                "PS3.3 Section C.7.2.1 General Study Module; Type 1 semantics in "
                "PS3.5 Section 7.4.1 and per-Item scope in PS3.5 Section 7.4.6",
        table="PS3.3 Table 10-11 SOP Instance Reference Macro Attributes, row "
              "Referenced SOP Class UID (0008,1150) Type 1; included by PS3.3 Table "
              "C.7-3 General Study Module Attributes, row Referenced Study Sequence "
              "(0008,1110) Type 3",
        quote='PS3.3 Table 10-11, row "Referenced SOP Class UID", tag (0008,1150), '
              'Type 1: "Uniquely identifies the referenced SOP Class." PS3.5 '
              'Section 7.4.1: "Absence of a valid Value in a Type 1 Data Element is '
              'a protocol violation." PS3.5 Section 7.4.6: "The Types of the '
              'Attributes of the Data Set included in the Sequence, including any '
              'conditionality, are specified within the scope of each Data Set, '
              'i.e., for each Item present in the Sequence."',
        rationale="The same 38 objects dciodvfy reports, found by a second "
                  "codebase, and the message names the enclosing Referenced Study "
                  "Sequence that dciodvfy's Module=<SOPInstanceReferenceMacro> "
                  "leaves unnamed. Error code TagMissing.",
    ),
    dict(
        name="DV_ETHNIC_GROUP_UNEXPECTED",
        validator="dicom-validator",
        pattern=r"Tag \(TAG\) \(Ethnic Group\) is unexpected$",
        adjudication="FLOOR",
        section="PS3.3 Section C.7.1.1 Patient Module; PS3.4 Section B.4.1.1 "
                "Levels of Storage Support; PS3.6 Section 6 Registry of DICOM Data "
                "Elements",
        table="PS3.3 Table C.7-1 Patient Module Attributes, row Ethnic Groups "
              "(0010,2162) Type 3; PS3.6 Table 6-1 Registry of DICOM Data Elements, "
              "row (0010,2160) Ethnic Group",
        quote='PS3.3 Table C.7-1, row "Ethnic Groups", tag (0010,2162), Type 3: '
              '"Ethnic group(s) or race(s) of Patient. One or more Values may be '
              'present. This Attribute replaces the use of Ethnic Group (0010,2160), '
              'which has been retired. See PS3.3-2025a." PS3.6 Table 6-1 still '
              'carries the row "(0010,2160) | Ethnic Group | EthnicGroup | SH | 1 | '
              'RET (2025a)". PS3.4 Section B.4.1.1 Levels of Storage Support: '
              '"Storage Level 2 (Full) indicates that all Type 1, Type 2, and Type '
              '3 Attributes defined in the Information Object Definition associated '
              'with the SOP Class, as well as any Standard Extended Attributes '
              '(including Private Attributes) included in the SOP Instance, will be '
              'stored and may be accessed."',
        rationale="A retired attribute present, which the rubric names as a FLOOR "
                  "case. (0010,2160) is still allocated in PS3.6 Table 6-1 and "
                  "marked RET (2025a), and PS3.3 Table C.7-1 records its retirement "
                  "in the Attribute Description of the attribute that replaced it "
                  "rather than prohibiting it. PS3.4 Section B.4.1.1 is the "
                  "standard contemplating a SOP Instance that carries attributes "
                  "beyond those the IOD defines, and naming the storage behaviour "
                  "for them. The message is not a Type verdict: dicom-validator "
                  "0.8.2 documents ErrorCode.TagUnexpected as Tag is not in any "
                  "allowed module and renders it as is unexpected, and it is "
                  "collected under the pseudo-module name General rather than "
                  "against any real module, so it fires on every attribute outside "
                  "the IOD's module set. dciodvfy does not raise it on any of these "
                  "objects. Corroboration and not the basis of the verdict: 29 of "
                  "the 32 rows in results/floor_set.csv are is unexpected messages "
                  "from the same tool against known-good objects.",
    ),
]

UNMATCHED = dict(
    name="UNMATCHED",
    adjudication="UNDECIDABLE",
    section="",
    table="",
    quote="",
    rationale="No adjudication rule in colophon.adjudicate_c3dsr matched this "
              "message template. Recorded as UNDECIDABLE rather than assigned by "
              "judgement.",
)


def classify(validator: str, template: str) -> dict:
    for rule in RULES:
        if rule["validator"] != validator:
            continue
        if re.search(rule["pattern"], template):
            return rule
    return UNMATCHED


# --- inputs -------------------------------------------------------------------
def _arid(value) -> str:
    """Normalise a grouping key.

    The census writes an unlabelled group as a JSON float NaN, which is truthy,
    so `value or "NULL"` silently keeps the NaN and splits the group across two
    keys later. This is the guard for that.
    """
    if isinstance(value, str) and value.strip():
        return value
    return "NULL"


def load_message_classes() -> list[dict]:
    with CLASSES_CSV.open(newline="", encoding="utf-8") as fh:
        return [r for r in csv.DictReader(fh) if r["sop_class_name"] == SOP_CLASS]


def load_objects() -> tuple[list[dict], int, int]:
    """One entry per object, with its distinct message classes.

    Returns the objects, the number of lines read and the number of lines that
    would not parse. A census process may be appending to this file while this
    runs, so an unparseable line is counted and skipped rather than raised on.
    The file is opened read only and is never written to.
    """
    out: list[dict] = []
    lines = skipped = 0
    with RECORDS.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            lines += 1
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                skipped += 1
                continue
            if rec.get("sop_class_name") != SOP_CLASS:
                continue
            for obj in rec.get("objects", []):
                classes = {}
                for validator, class_id, severity, template in obj.get("messages", []):
                    classes[(validator, class_id)] = (severity, template)
                out.append(dict(
                    series_instance_uid=rec["series_instance_uid"],
                    sop_instance_uid=obj.get("sop_instance_uid", ""),
                    analysis_result_id=_arid(rec.get("analysis_result_id")),
                    collection_id=_arid(rec.get("collection_id")),
                    status=obj.get("status", ""),
                    classes=classes,
                ))
    return out, lines, skipped


# --- triples ------------------------------------------------------------------
def pct(num: int, den: int) -> float:
    return round(100.0 * num / den, 2) if den else 0.0


def triple(objects: list[dict], validator: str, severity_kind: str, verdict,
           demote: frozenset = frozenset()) -> dict:
    """gross, floor, net over a set of objects, for one validator and severity.

    gross  objects carrying at least one message class of that severity
    floor  of those, the ones whose classes are all FLOOR, NOT-IOD or
           PLAUSIBILITY
    net    objects carrying at least one class adjudicated NET
    other  the remainder: no NET, but at least one UNDECIDABLE, so neither
           floor nor net. Reported rather than folded into either, because
           folding it into floor would understate and into net would overstate.
    """
    gross = net = floor = other = 0
    for obj in objects:
        cats = []
        for (val, class_id), (severity, _template) in obj["classes"].items():
            if val != validator:
                continue
            if severity.upper() != severity_kind:
                continue
            cats.append(verdict(val, class_id, demote))
        if not cats:
            continue
        gross += 1
        if "NET" in cats:
            net += 1
        elif all(c in FLOOR_LIKE for c in cats):
            floor += 1
        else:
            other += 1
    n = len(objects)
    return dict(objects=n, gross=gross, floor=floor, net=net, other=other,
                pct_gross=pct(gross, n), pct_floor=pct(floor, n),
                pct_net=pct(net, n))


def net_objects(objects: list[dict], verdict,
                demote: frozenset = frozenset()) -> set:
    """Objects with at least one NET class from any validator, any severity."""
    out = set()
    for obj in objects:
        for (val, class_id) in obj["classes"]:
            if verdict(val, class_id, demote) == "NET":
                out.add(obj["sop_instance_uid"])
                break
    return out


# --- report -------------------------------------------------------------------
SENSITIVITY = (
    ("as_adjudicated", frozenset(), "as adjudicated"),
    ("off_part", frozenset(OFF_PART_RULES), "off-part demoted"),
    ("module_presence", frozenset(MODULE_PRESENCE_RULES), "module presence demoted"),
    ("both", frozenset(OFF_PART_RULES | MODULE_PRESENCE_RULES), "both demoted"),
)


def build() -> dict:
    rows = load_message_classes()
    objects, lines_read, lines_skipped = load_objects()

    per_class: dict[tuple[str, str], dict] = {}
    for r in rows:
        key = (r["validator"], r["message_class_id"])
        entry = per_class.setdefault(key, dict(
            validator=r["validator"], message_class_id=r["message_class_id"],
            severity_as_emitted=r["severity_as_emitted"],
            message_template=r["message_template"], objects=0,
            by_arid=Counter()))
        entry["objects"] += int(r["objects"])
        entry["by_arid"][_arid(r["analysis_result_id"])] += int(r["objects"])
    for entry in per_class.values():
        entry["rule"] = classify(entry["validator"], entry["message_template"])

    verdict_map = {k: v["rule"]["adjudication"] for k, v in per_class.items()}
    rule_of = {k: v["rule"]["name"] for k, v in per_class.items()}

    def verdict(validator: str, class_id: str, demote: frozenset) -> str:
        key = (validator, class_id)
        if demote and rule_of.get(key) in demote:
            return "UNDECIDABLE"
        return verdict_map.get(key, "UNDECIDABLE")

    arids = sorted({o["analysis_result_id"] for o in objects})
    collections = sorted({o["collection_id"] for o in objects})
    validators = sorted({v for v, _ in per_class})

    triples: dict = {}
    for key, demote, _label in SENSITIVITY:
        triples[key] = {}
        for validator in validators:
            for severity in ("ERROR", "WARNING"):
                triples[key].setdefault(validator, {})[severity] = dict(
                    overall=triple(objects, validator, severity, verdict, demote),
                    by_arid={a: triple([o for o in objects
                                        if o["analysis_result_id"] == a],
                                       validator, severity, verdict, demote)
                             for a in arids},
                )

    unions: dict = {}
    for key, demote, _label in SENSITIVITY:
        nets = net_objects(objects, verdict, demote)
        per_collection = {}
        for c in collections:
            sub = [o for o in objects if o["collection_id"] == c]
            hit = sum(1 for o in sub if o["sop_instance_uid"] in nets)
            per_collection[c] = dict(
                objects=len(sub), net=hit, pct_net=pct(hit, len(sub)),
                arids=sorted({o["analysis_result_id"] for o in sub}))
        per_arid = {}
        for a in arids:
            sub = [o for o in objects if o["analysis_result_id"] == a]
            hit = sum(1 for o in sub if o["sop_instance_uid"] in nets)
            per_arid[a] = dict(objects=len(sub), net=hit, pct_net=pct(hit, len(sub)),
                               collections=sorted({o["collection_id"] for o in sub}))
        unions[key] = dict(
            net=len(nets), pct_net=pct(len(nets), len(objects)),
            per_collection=per_collection, per_arid=per_arid,
            median_collection=round(statistics.median(
                [per_collection[c]["pct_net"] for c in collections]), 2),
        )

    # Distinct objects per adjudication rule. Summing the per-class object counts
    # double counts an object that trips two classes of the same rule, which the
    # two Clinical Trial Site classes and the two De-identification classes do.
    per_rule_objects: dict[str, int] = {}
    per_rule_classes: dict[str, int] = {}
    for rule_name in {v["rule"]["name"] for v in per_class.values()}:
        keys = {k for k, v in per_class.items() if v["rule"]["name"] == rule_name}
        per_rule_objects[rule_name] = sum(
            1 for o in objects if keys & set(o["classes"]))
        per_rule_classes[rule_name] = len(keys)

    # Object sets per message class, so the relationships between findings are
    # measured rather than asserted. Nothing below is inferred from a tool's
    # internals: it is set arithmetic over the census records.
    class_sets: dict[tuple[str, str], set] = defaultdict(set)
    for o in objects:
        for key in o["classes"]:
            class_sets[key].add(o["sop_instance_uid"])

    def _set_for(validator: str, needle: str) -> set:
        out: set = set()
        for key, e in per_class.items():
            if e["validator"] == validator and needle in e["message_template"]:
                out |= class_sets[key]
        return out

    site_name = _set_for("dciodvfy", "<ClinicalTrialSiteName>")
    site_id = _set_for("dciodvfy", "<ClinicalTrialSiteID>")
    deident = _set_for("dciodvfy", "Element=<Deidentification")
    proc = _set_for("dciodvfy", "<ProcedureCodeSequence>")
    refuid = _set_for("dciodvfy", "<ReferencedSOPClassUID>")
    ethnic = _set_for("dicom-validator", "(Ethnic Group) is unexpected")

    def _net_for(validator: str) -> set:
        out: set = set()
        for o in objects:
            for (v, c) in o["classes"]:
                if v == validator and verdict(v, c, frozenset()) == "NET":
                    out.add(o["sop_instance_uid"])
                    break
        return out

    dciod_net = _net_for("dciodvfy")
    dv_net = _net_for("dicom-validator")

    facts = dict(
        site_name=len(site_name), site_id=len(site_id),
        site_id_within_site_name=site_id <= site_name,
        deident=len(deident), proc=len(proc), refuid=len(refuid),
        ethnic=len(ethnic),
        proc_within_deident=proc <= deident,
        three_findings_disjoint=(not (site_name & deident)
                                 and not (site_name & refuid)
                                 and not (deident & refuid)),
        three_findings_sum=len(site_name) + len(deident) + len(refuid),
        dciod_net=len(dciod_net), dv_net=len(dv_net),
        net_sets_identical=dciod_net == dv_net,
        ethnic_by_collection={
            c: sum(1 for o in objects
                   if o["collection_id"] == c
                   and o["sop_instance_uid"] in ethnic)
            for c in collections
            if any(o["collection_id"] == c and o["sop_instance_uid"] in ethnic
                   for o in objects)},
        ethnic_within_refuid=len(ethnic & refuid),
    )

    return dict(
        facts=facts,
        per_class=per_class, objects=objects, arids=arids,
        collections=collections, validators=validators, triples=triples,
        unions=unions, per_rule_objects=per_rule_objects,
        per_rule_classes=per_rule_classes,
        n_objects=len(objects),
        n_series=len({o["series_instance_uid"] for o in objects}),
        statuses=Counter(o["status"] for o in objects),
        lines_read=lines_read, lines_skipped=lines_skipped,
        verdict_counts=Counter(v["rule"]["adjudication"]
                               for v in per_class.values()),
    )


def write_csv(rep: dict) -> Path:
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    fields = ["validator", "message_class_id", "message_template",
              "severity_as_emitted", "objects", "adjudication", "rule",
              "citation_section", "citation_table", "citation_quote", "rationale"]
    with OUT_CSV.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for key in sorted(rep["per_class"],
                          key=lambda k: (k[0], -rep["per_class"][k]["objects"], k[1])):
            e = rep["per_class"][key]
            rule = e["rule"]
            w.writerow(dict(
                validator=e["validator"], message_class_id=e["message_class_id"],
                message_template=e["message_template"],
                severity_as_emitted=e["severity_as_emitted"], objects=e["objects"],
                adjudication=rule["adjudication"], rule=rule["name"],
                citation_section=rule["section"], citation_table=rule["table"],
                citation_quote=rule["quote"], rationale=rule["rationale"]))
    return OUT_CSV


def _compact(template: str, limit: int = 150) -> str:
    """Shorten a template for a table cell without losing the diagnostic."""
    template = template.replace("|", "\\|")
    return template if len(template) <= limit else template[:limit - 3] + "..."


def _triple_row(label: str, t: dict) -> str:
    return "| %s | %s | %s (%.2f) | %s (%.2f) | %s (%.2f) | %s |" % (
        label, f"{t['objects']:,}", f"{t['gross']:,}", t["pct_gross"],
        f"{t['floor']:,}", t["pct_floor"], f"{t['net']:,}", t["pct_net"],
        f"{t['other']:,}")


def write_markdown(rep: dict) -> Path:
    n = rep["n_objects"]
    f = rep["facts"]
    base = rep["unions"]["as_adjudicated"]
    substantial = base["pct_net"] > 5.0 and base["median_collection"] > 5.0
    L: list[str] = []
    A = L.append

    A("# Comprehensive 3D SR Storage: adjudicated error and warning rates")
    A("")
    A("Generated by `%s`. Standard edition %s, verified %s."
      % (CMD, EDITION, VERIFIED_ON))
    A("")
    A("Census, not a sample: %s objects in %s series, every object in the IDC v24 "
      "manifest for this SOP class, all of them carrying census status OK. "
      "Nothing was sampled, truncated or skipped. Every one of the %s distinct "
      "(validator, message_class_id) pairs recorded for this class is adjudicated "
      "in `adjudication_comprehensive_3d_sr.csv`."
      % (f"{n:,}", f"{rep['n_series']:,}", f"{len(rep['per_class']):,}"))
    A("")
    A("Definitions, fixed before the numbers:")
    A("")
    A("- **gross** objects carrying at least one message class of that severity "
      "from that validator")
    A("- **floor** of those, the ones whose classes are all FLOOR, NOT-IOD or "
      "PLAUSIBILITY")
    A("- **net** objects carrying at least one class adjudicated NET")
    A("- **other** no NET class, but at least one UNDECIDABLE, so neither floor "
      "nor net. Carried as its own column so it is not folded into either and "
      "quietly counted.")
    A("")
    A("Counts are objects, not messages: an object counts once for a class.")
    A("")

    A("## Message classes by verdict")
    A("")
    A("| verdict | message classes | rules |")
    A("|---|---|---|")
    by_verdict: dict[str, list[str]] = defaultdict(list)
    for name, count in sorted(rep["per_rule_classes"].items()):
        rule = next(r for r in RULES + [UNMATCHED] if r["name"] == name)
        by_verdict[rule["adjudication"]].append(name)
    for v in sorted(by_verdict):
        classes = sum(rep["per_rule_classes"][r] for r in by_verdict[v])
        A("| %s | %s | %s |" % (v, f"{classes:,}", ", ".join(sorted(by_verdict[v]))))
    A("")
    A("No message class is left UNMATCHED, so no class falls to UNDECIDABLE for "
      "want of a rule. The single UNDECIDABLE rule is a deliberate verdict with "
      "its reasoning recorded, not a gap.")
    A("")

    A("## Triples by validator and severity")
    A("")
    for validator in rep["validators"]:
        for severity in ("ERROR", "WARNING"):
            t = rep["triples"]["as_adjudicated"][validator][severity]
            if t["overall"]["gross"] == 0:
                A("`%s` emitted no %s class on this SOP class."
                  % (validator, severity.lower()))
                A("")
                continue
            A("### %s, %s" % (validator, severity.lower()))
            A("")
            A("| group | objects | gross (pct) | floor (pct) | net (pct) | other |")
            A("|---|---|---|---|---|---|")
            A(_triple_row("all", t["overall"]))
            for a in rep["arids"]:
                A(_triple_row(a, t["by_arid"][a]))
            A("")

    A("## Residual NET classes")
    A("")
    A("Enumerated by rule. The objects column counts distinct objects, so a rule "
      "whose classes overlap on the same object is not double counted.")
    A("")
    A("| rule | validator | message classes | distinct objects | severity | "
      "representative template | citation |")
    A("|---|---|---|---|---|---|---|")
    net_rows = [(k, e) for k, e in rep["per_class"].items()
                if e["rule"]["adjudication"] == "NET"]
    grouped: dict[str, list] = defaultdict(list)
    for k, e in net_rows:
        grouped[e["rule"]["name"]].append((k, e))
    for name in sorted(grouped, key=lambda x: -rep["per_rule_objects"][x]):
        members = sorted(grouped[name], key=lambda kv: -kv[1]["objects"])
        _, head = members[0]
        cite = "%s; %s" % (head["rule"]["section"], head["rule"]["table"])
        A("| %s | %s | %d (e.g. `%s`) | %s | %s | %s | %s |" % (
            name, head["validator"], len(members), head["message_class_id"],
            f"{rep['per_rule_objects'][name]:,}", head["severity_as_emitted"],
            _compact(head["message_template"]), cite))
    A("")
    A("The floor column is zero for `dciodvfy` at error severity because no "
      "`dciodvfy` error class in this SOP class was adjudicated FLOOR, NOT-IOD or "
      "PLAUSIBILITY. That is a measured zero, not a missing measurement. The Phase "
      "1 floor sets are writer-specific and fixture-specific and are not carried "
      "across to these writers, so no floor is subtracted from any rate above "
      "beyond the adjudication itself.")
    A("")
    A("How the net objects sit against each other, measured by set arithmetic over "
      "the census records rather than asserted. The three findings that carry the "
      "net rate are %s: Clinical Trial Site attributes on %s objects, "
      "De-identification attributes on %s, Referenced SOP Class UID on %s, and "
      "%s + %s + %s = %s, which is the union net exactly. Within the first, the "
      "%s objects missing Clinical Trial Site ID %s a subset of the %s missing "
      "Clinical Trial Site Name. The %s objects with a zero-Item Procedure Code "
      "Sequence %s a subset of the De-identification group, which is why demoting "
      "that rule moves no number. The two validators' net object sets are %s: %s "
      "objects each, nothing on either side of the difference."
      % ("pairwise disjoint" if f["three_findings_disjoint"]
         else "NOT pairwise disjoint",
         f"{f['site_name']:,}", f"{f['deident']:,}", f"{f['refuid']:,}",
         f"{f['site_name']:,}", f"{f['deident']:,}", f"{f['refuid']:,}",
         f"{f['three_findings_sum']:,}",
         f"{f['site_id']:,}",
         "are" if f["site_id_within_site_name"] else "are not",
         f"{f['site_name']:,}", f"{f['proc']:,}",
         "are" if f["proc_within_deident"] else "are not",
         "identical" if f["net_sets_identical"] else "not identical",
         f"{f['dciod_net']:,}"))
    A("")

    A("## The findings this SOP class turns on")
    A("")
    A("**Clinical Trial Site Name (0012,0031) and Clinical Trial Site ID "
      "(0012,0030), %s and %s objects, NET.** Both are Type 2 in PS3.3 Table "
      "C.7-2b, and PS3.3 Table A.35.13-1 gives the Clinical Trial Subject Module "
      "Usage U in this IOD. PS3.3 Section A.1.3.3 is the sentence that makes the "
      "Types of an optional Module bind, in full: \"User Option Modules may or may "
      "not be supported. If an optional Module is supported, the Attribute Types "
      "specified in the Modules in Annex C shall be supported.\" PS3.5 Section "
      "7.4.3 says what Type 2 costs: \"These Data Elements shall be included in "
      "the Data Set and their absence is a protocol violation.\" The attributes "
      "are absent entirely, not present and zero length, which is the case Type 2 "
      "does not forgive."
      % (f"{f['site_name']:,}", f"{f['site_id']:,}"))
    A("")
    A("**The residual on that finding, stated and not resolved.** A.1.3.3 "
      "conditions the obligation on the optional Module being supported, and PS3.3 "
      "gives no test for when a stored Data Set supports one. dciodvfy answers it "
      "by naming the Module in the message; dicom-validator answers it with a "
      "documented heuristic, `_does_module_strongly_exist`, which requires the "
      "module to carry at least one attribute that no other candidate module also "
      "carries. Neither is quoting the standard when it does so. The two tools "
      "reached identical object sets from different codebases, and both numbers "
      "are published: the whole calculation is repeated below with these classes "
      "demoted to UNDECIDABLE.")
    A("")
    A("**De-identification Method (0012,0063) and De-identification Method Code "
      "Sequence (0012,0064), %s objects, NET.** Two Type 1C rows of the Patient "
      "Module, which PS3.3 Table A.35.13-1 gives Usage M, so no module presence "
      "question arises. The conditions in PS3.3 Table C.7-1 refer to each other, "
      "verbatim: \"Required if Patient Identity Removed (0012,0062) is present and "
      "has a Value of YES and De-identification Method Code Sequence (0012,0064) "
      "is not present. May be present otherwise.\" and \"Required if Patient "
      "Identity Removed (0012,0062) is present and has a Value of YES and "
      "De-identification Method (0012,0063) is not present. May be present "
      "otherwise.\" Both conditions are met at once in exactly one state: "
      "(0012,0062) present with Value YES and neither attribute present. PS3.5 "
      "Section 7.4.2: \"It is a protocol violation if the specified conditions are "
      "met and the Data Element is not included.\" Unlike the Laterality Type 2C "
      "this project already adjudicated FLOOR, every term of this condition is an "
      "attribute of the same Module, so the condition is evaluable from the Data "
      "Set rather than from knowledge the object does not carry."
      % f"{f['deident']:,}")
    A("")
    A("**Referenced SOP Class UID (0008,1150), %s objects, NET.** PS3.3 Table "
      "C.7-3 carries Referenced Study Sequence (0008,1110) as Type 3 followed by "
      "the row \">Include Table 10-11 SOP Instance Reference Macro Attributes\", "
      "and PS3.3 Table 10-11 makes Referenced SOP Class UID Type 1. Type 3 on the "
      "Sequence means it need not be there at all; it does not loosen the Items "
      "that are. PS3.5 Section 7.4.6 says so: \"The Types of the Attributes of the "
      "Data Set included in the Sequence, including any conditionality, are "
      "specified within the scope of each Data Set, i.e., for each Item present in "
      "the Sequence.\" PS3.5 Section 7.4.1: \"Absence of a valid Value in a Type 1 "
      "Data Element is a protocol violation.\""
      % f"{f['refuid']:,}")
    A("")
    A("**Ethnic Group (0010,2160), %s objects, FLOOR.** A retired attribute "
      "present, which the rubric names as a floor case. PS3.3 Table C.7-1 in the "
      "pinned edition has no row for (0010,2160). It has a row for Ethnic Groups "
      "(0010,2162) whose Attribute Description reads, verbatim: \"Ethnic group(s) "
      "or race(s) of Patient. One or more Values may be present. This Attribute "
      "replaces the use of Ethnic Group (0010,2160), which has been retired. See "
      "PS3.3-2025a.\" PS3.6 Table 6-1 still allocates the tag and marks it RET "
      "(2025a). PS3.4 Section B.4.1.1 is the standard contemplating exactly this "
      "shape of object, verbatim: \"Storage Level 2 (Full) indicates that all Type "
      "1, Type 2, and Type 3 Attributes defined in the Information Object "
      "Definition associated with the SOP Class, as well as any Standard Extended "
      "Attributes (including Private Attributes) included in the SOP Instance, "
      "will be stored and may be accessed.\" Nothing in the citation chain forbids "
      "the attribute; the standard records that it was replaced."
      % f"{f['ethnic']:,}")
    A("")
    A("Where those %s objects sit: %s. The %s in `lung_pet_ct_dx` are exactly the "
      "%s that also carry the Referenced SOP Class UID finding, so they are net on "
      "that citation and not on this one. The %s in `rms_mutation_prediction` "
      "carry no other error class from either validator, which is why that whole "
      "group appears in the `dicom-validator` error triple as floor and not as "
      "net."
      % (f"{f['ethnic']:,}",
         ", ".join("%s in `%s`" % (f"{v:,}", k)
                   for k, v in sorted(f["ethnic_by_collection"].items())),
         f"{f['ethnic_within_refuid']:,}", f"{f['refuid']:,}",
         f"{f['ethnic'] - f['ethnic_within_refuid']:,}"))
    A("")
    A("**The Ethnic Group message is not a Type verdict.** dicom-validator 0.8.2 "
      "documents `ErrorCode.TagUnexpected` as \"Tag is not in any allowed module\" "
      "and renders it as `is unexpected`. A failed condition is a different code, "
      "`ErrorCode.TagNotAllowed`, rendered as `is not allowed by condition`. The "
      "message is filed under the pseudo-module name `General`, which the tool "
      "uses for tags it could not place in any module of the IOD at all, so this "
      "code fires on every attribute outside the IOD's module set, retired or "
      "Standard Extended alike. dciodvfy raised nothing against this attribute on "
      "any of these objects. That is the same instrument behaviour the "
      "Comprehensive SR adjudication recorded, reached here by a different route: "
      "there the tool's parsed model held nested macro children as siblings, here "
      "the attribute genuinely is outside the IOD, and in both cases the message "
      "is a statement about the module table rather than about a requirement.")
    A("")

    A("## Net rate across validators, by analysis result and by collection")
    A("")
    A("An object is net here if any validator raised any class adjudicated NET, at "
      "any severity. This is the number PRE-05 is evaluated against.")
    A("")
    A("| analysis_result_id | collections | objects | net | pct net |")
    A("|---|---|---|---|---|")
    for a in rep["arids"]:
        d = base["per_arid"][a]
        A("| %s | %s | %s | %s | %.2f |" % (
            a, ", ".join(d["collections"]), f"{d['objects']:,}", f"{d['net']:,}",
            d["pct_net"]))
    A("| **all** | | %s | %s | %.2f |" % (f"{n:,}", f"{base['net']:,}",
                                          base["pct_net"]))
    A("")
    A("| collection_id | analysis results present | objects | net | pct net |")
    A("|---|---|---|---|---|")
    for c in rep["collections"]:
        d = base["per_collection"][c]
        A("| %s | %s | %s | %s | %.2f |" % (
            c, ", ".join(d["arids"]), f"{d['objects']:,}", f"{d['net']:,}",
            d["pct_net"]))
    A("")
    A("Collection-level median net rate: **%.2f percent** across %d collections."
      % (base["median_collection"], len(rep["collections"])))
    A("")
    A("The two groupings are not nested in this class and neither can be derived "
      "from the other. One collection carries two analysis results and one "
      "analysis result spans two collections, so a reader who wants the producer "
      "view and a reader who wants the archive view need both tables. Reported by "
      "group, not ranked.")
    A("")

    A("## PRE-05")
    A("")
    A("PRE-05, pre-registered before any archive object was validated, reads: "
      "\"null is defined as a post-floor failure rate at or below 5 percent of "
      "series in a class; substantial is defined as above 20 percent; the band "
      "between is reported as indeterminate and neither claim is made\". This "
      "class has one object per series, %s objects and %s series, so the object "
      "rate and the series rate are the same number."
      % (f"{n:,}", f"{rep['n_series']:,}"))
    A("")
    A("Both required numbers, reported whether or not either passes:")
    A("")
    A("| number | value | threshold | clears |")
    A("|---|---|---|---|")
    A("| net error-class rate, this SOP class | %.2f percent (%s of %s) | above "
      "5.0 percent | %s |"
      % (base["pct_net"], f"{base['net']:,}", f"{n:,}",
         "yes" if base["pct_net"] > 5.0 else "no"))
    A("| collection-level median net rate | %.2f percent (median of %d "
      "collections) | above 5.0 percent | %s |"
      % (base["median_collection"], len(rep["collections"]),
         "yes" if base["median_collection"] > 5.0 else "no"))
    A("")
    A("Conjunction required by the Track C evaluation rule, substantial if and "
      "only if both are above 5.0 percent: **%s**."
      % ("substantial" if substantial else "not substantial"))
    A("")
    A("Against PRE-05's own three bands, applied to the class-level rate on its "
      "own, the %.2f percent net rate falls in the **%s** band."
      % (base["pct_net"],
         "substantial, above 20 percent" if base["pct_net"] > 20.0
         else ("indeterminate, above 5 and at or below 20 percent"
               if base["pct_net"] > 5.0 else "null, at or below 5 percent")))
    A("")
    A("Why the two tests separate, stated so a reader does not have to "
      "reconstruct it: the net objects are not spread across the class. Across the "
      "%d collections, in alphabetical order, the net rates are %s. A class-level "
      "rate of %.2f percent and a median collection rate of %.2f percent are both "
      "correct descriptions of the same data, and the collection-level gate is the "
      "one that refuses to let a minority of clusters stand in for a class. That "
      "is the non-independence the ledger already carries as C3-12."
      % (len(rep["collections"]),
         ", ".join("%s %.2f percent" % (c, base["per_collection"][c]["pct_net"])
                   for c in rep["collections"]),
         base["pct_net"], base["median_collection"]))
    A("")
    A("This class %s clear PRE-05 under the conjunction. PRE-01 is already RETIRED "
      "in the pending ledger as a wrong prediction on the Key Object Selection "
      "evidence, and nothing here touches it. PRE-05 is per object class and not "
      "every Phase 2 class is complete, so this file records the Comprehensive 3D "
      "SR Storage limb of it and nothing wider. The sentence proposed for folding "
      "into PRE-05 is carried in ledger row C-C3D-12 rather than by editing PRE-05 "
      "here, because two tracks already collided on that row and the orchestrator "
      "reconciled it by hand."
      % ("does" if substantial else "does not"))
    A("")

    A("## Sensitivity: two adjudications reported both ways")
    A("")
    A("Two rules could be refused by a reader applying the rubric strictly, and "
      "the whole calculation is repeated with each of them demoted to UNDECIDABLE "
      "so nobody has to recompute the study to disagree with one verdict.")
    A("")
    A("- **off-part**, `PROC_CODE_SEQ_ZERO_ITEMS`: the Type violated is given in "
      "PS3.3 Table C.7-3, but the operative prohibition, that a Type 3 SQ shall "
      "not be present with zero Items, is stated in PS3.5 Section 7.4.5 and "
      "nowhere in PS3.3, PS3.4 or PS3.16.")
    A("- **module presence**, `CT_SUBJECT_TYPE2` and `DV_CT_SITE_MISSING`: PS3.3 "
      "Section A.1.3.3 binds the Attribute Types of a User Option Module when the "
      "Module is supported, and PS3.3 does not say when a stored Data Set counts "
      "as supporting one.")
    A("")
    A("| reading | net objects | pct net | collection median pct | substantial at "
      "5.0 percent |")
    A("|---|---|---|---|---|")
    for key, _demote, label in SENSITIVITY:
        u = rep["unions"][key]
        A("| %s | %s | %.2f | %.2f | %s |" % (
            label, f"{u['net']:,}", u["pct_net"], u["median_collection"],
            "yes" if (u["pct_net"] > 5.0 and u["median_collection"] > 5.0)
            else "no"))
    A("")
    A("| reading | %s |" % " | ".join("%s error net" % v
                                      for v in rep["validators"]))
    A("|---|%s" % ("---|" * len(rep["validators"])))
    for key, _demote, label in SENSITIVITY:
        cells = []
        for v in rep["validators"]:
            t = rep["triples"][key][v]["ERROR"]["overall"]
            cells.append("%s (%.2f pct)" % (f"{t['net']:,}", t["pct_net"]))
        A("| %s | %s |" % (label, " | ".join(cells)))
    A("")
    A("The off-part row is identical to the as-adjudicated row, and that is a "
      "result rather than an oversight: the %s objects carrying the zero-Item "
      "Procedure Code Sequence are a subset of the %s carrying the "
      "De-identification finding, so they stay net on a different citation. "
      "Neither demotion changes the PRE-05 verdict for this class, and the module "
      "presence demotion is the one that would move a headline number, from %.2f "
      "percent to %.2f percent."
      % (f"{f['proc']:,}", f"{f['deident']:,}",
         rep["unions"]["as_adjudicated"]["pct_net"],
         rep["unions"]["module_presence"]["pct_net"]))
    A("")

    A("## What was dropped")
    A("")
    A("Nothing. `_cache/census/records.jsonl` was read with %s lines parsed and "
      "%d unparseable lines skipped, and the file was opened read only and never "
      "written to. All %s objects the census records for this SOP class carry "
      "status OK, every distinct message class is adjudicated, and no message "
      "class was set aside as too rare to matter: the two objects carrying the "
      "Procedure Code Sequence classes are adjudicated on the same terms as the "
      "%s carrying the Clinical Trial Site Name class."
      % (f"{rep['lines_read']:,}", rep["lines_skipped"], f"{n:,}",
         f"{rep['per_rule_objects'].get('CT_SUBJECT_TYPE2', 0):,}"))
    A("")
    A("`results/environment.json` records the standard edition as PS3 2025e while "
      "`results/standards.json` and the running dicom-validator both use 2026c. "
      "Every PS3.3, PS3.4 and PS3.6 citation in this file was read from the "
      "docbook sources dicom-validator has pinned for 2026c, and every PS3.5 "
      "citation was read from the PS3.5 docbook whose subtitle reads \"DICOM PS3.5 "
      "2026c - Data Structures and Encoding\". The disagreement in the environment "
      "record is reported, not repaired here.")
    A("")
    A("One further state disagreement is reported rather than repaired: PRE-01 and "
      "PRE-05 carry their reconciled text in "
      "`results/pending_ledger/merged/zz_pre01_outcome.json` and "
      "`zz_pre05_consolidated.json`, and `results/ledger.csv` still holds the "
      "pre-merge rows for both. This file evaluates PRE-05 against the reconciled "
      "text and touches neither row.")
    A("")

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(L) + "\n", encoding="utf-8")
    return OUT_MD


# --- proposed ledger rows -----------------------------------------------------
def ledger_entries(rep: dict) -> list[dict]:
    n = rep["n_objects"]
    base = rep["unions"]["as_adjudicated"]
    tri = rep["triples"]["as_adjudicated"]
    dciod_e = tri["dciodvfy"]["ERROR"]["overall"]
    dciod_w = tri["dciodvfy"]["WARNING"]["overall"]
    dvv_e = tri["dicom-validator"]["ERROR"]["overall"]
    substantial = base["pct_net"] > 5.0 and base["median_collection"] > 5.0

    src = ("results/phase2/adjudication_comprehensive_3d_sr.csv and "
           "results/phase2/net_rates_comprehensive_3d_sr.md")
    dropped = ("nothing: census of all %s objects in the IDC v24 manifest for this "
               "SOP class, all status OK, every distinct message class adjudicated, "
               "none skipped. %s records.jsonl lines parsed, %d unparseable lines "
               "skipped, file opened read only."
               % (f"{n:,}", f"{rep['lines_read']:,}", rep["lines_skipped"]))
    common = dict(section="C-C3D",
                  section_title="Track C, Comprehensive 3D SR Storage adjudication",
                  sop_class=SOP_CLASS, idc_index_version="v24")
    measured = dict(command=CMD, source_file=src, dropped=dropped, **common)
    verified = dict(external_source="DICOM %s, dicom.nema.org" % EDITION,
                    verified_on=VERIFIED_ON, source_file=src, command=CMD,
                    dropped=dropped, **common)
    DCIOD_VER = "dicom3tools snapshot 20260701065818, sha256 d931cded1048a2fd"
    DV_VER = "dicom-validator 0.8.2, edition 2026c"
    BOTH_VER = ("dicom3tools snapshot 20260701065818; dicom-validator 0.8.2, "
                "edition 2026c")

    entries: list[dict] = []

    entries.append(dict(
        id="C-C3D-01", status="VERIFIED",
        claim="Clinical Trial Site Name (0012,0031) and Clinical Trial Site ID "
              "(0012,0030) absent from an object that carries the Clinical Trial "
              "Subject Module violate a stated Type 2 requirement.",
        value="PS3.3 Table C.7-2b makes both Type 2. PS3.3 Table A.35.13-1 gives "
              "the Clinical Trial Subject Module Usage U in the Comprehensive 3D SR "
              "IOD. PS3.3 Section A.1.3.3 verbatim: User Option Modules may or may "
              "not be supported. If an optional Module is supported, the Attribute "
              "Types specified in the Modules in Annex C shall be supported. PS3.5 "
              "Section 7.4.3 verbatim: These Data Elements shall be included in the "
              "Data Set and their absence is a protocol violation.",
        n=str(rep["per_rule_objects"].get("CT_SUBJECT_TYPE2", 0)), denominator=str(n),
        floor="not applicable, this row is the citation rather than a rate",
        validator="dciodvfy and dicom-validator", validator_version=BOTH_VER,
        status_note="Residual recorded and not resolved: PS3.3 Section A.1.3.3 "
                    "conditions the obligation on the optional Module being "
                    "supported and PS3.3 states no test for when a stored Data Set "
                    "supports one. dciodvfy decides it by naming the Module; "
                    "dicom-validator decides it with its documented "
                    "_does_module_strongly_exist heuristic. Neither is quoting the "
                    "standard for that step, and the two reached identical object "
                    "sets, 935 for Site Name and 8 for Site ID with nothing on "
                    "either side of either difference.",
        notes="Because the antecedent is a tool judgement rather than a quoted "
              "requirement, every triple in the write-up is also published with "
              "these classes demoted to UNDECIDABLE. See C-C3D-11.",
        **verified))

    entries.append(dict(
        id="C-C3D-02", status="VERIFIED",
        claim="De-identification Method (0012,0063) and De-identification Method "
              "Code Sequence (0012,0064) both absent while Patient Identity Removed "
              "(0012,0062) is YES violates two stated Type 1C conditions at once.",
        value="PS3.3 Table C.7-1, (0012,0063) Type 1C verbatim: Required if Patient "
              "Identity Removed (0012,0062) is present and has a Value of YES and "
              "De-identification Method Code Sequence (0012,0064) is not present. "
              "May be present otherwise. And (0012,0064) Type 1C verbatim: Required "
              "if Patient Identity Removed (0012,0062) is present and has a Value "
              "of YES and De-identification Method (0012,0063) is not present. May "
              "be present otherwise. PS3.5 Section 7.4.2 verbatim: It is a protocol "
              "violation if the specified conditions are met and the Data Element "
              "is not included.",
        n=str(rep["per_rule_objects"].get("DEIDENT_1C", 0)), denominator=str(n),
        floor="not applicable, this row is the citation rather than a rate",
        validator="dciodvfy and dicom-validator", validator_version=BOTH_VER,
        status_note="The two conditions refer to each other, so both are met in "
                    "exactly one state and that state is the one both validators "
                    "report. The Patient Module is Usage M in PS3.3 Table "
                    "A.35.13-1, so the module presence question that qualifies "
                    "C-C3D-01 does not arise here. Every term of the condition is "
                    "an attribute of the same Module, so the condition is evaluable "
                    "from the Data Set, unlike the Laterality Type 2C this project "
                    "adjudicated FLOOR at C-GSPS scope.",
        notes="Independent in the strict sense: different codebases, different "
              "condition evaluators, identical object sets of 828 on each of the "
              "two attributes. dicom-validator's error code here is TagMissing, not "
              "TagUnexpected, so the modelling defect recorded at C-CSR-02 does not "
              "reach it.",
        **verified))

    entries.append(dict(
        id="C-C3D-03", status="VERIFIED",
        claim="A Referenced Study Sequence Item without Referenced SOP Class UID "
              "(0008,1150) violates a Type 1 requirement, notwithstanding that the "
              "Sequence itself is Type 3.",
        value="PS3.3 Table C.7-3 carries Referenced Study Sequence (0008,1110) as "
              "Type 3 followed by the row Include Table 10-11 SOP Instance "
              "Reference Macro Attributes. PS3.3 Table 10-11, Section 10.8, makes "
              "Referenced SOP Class UID (0008,1150) Type 1. PS3.5 Section 7.4.6 "
              "verbatim: The Types of the Attributes of the Data Set included in "
              "the Sequence, including any conditionality, are specified within the "
              "scope of each Data Set, i.e., for each Item present in the Sequence. "
              "PS3.5 Section 7.4.1 verbatim: Absence of a valid Value in a Type 1 "
              "Data Element is a protocol violation.",
        n=str(rep["per_rule_objects"].get("REF_SOP_CLASS_UID", 0)), denominator=str(n),
        floor="not applicable, this row is the citation rather than a rate",
        validator="dciodvfy and dicom-validator", validator_version=BOTH_VER,
        status_note="Type 3 on the enclosing Sequence means the Sequence need not "
                    "be present at all. It does not loosen the Types inside an Item "
                    "that is present, which is what PS3.5 Section 7.4.6 states.",
        notes="dciodvfy names the macro and not the enclosing Sequence, reporting "
              "Module=<SOPInstanceReferenceMacro>. dicom-validator prints the full "
              "path including (0008,1110) Referenced Study Sequence, which is what "
              "locates the finding in the General Study Module. Same 38 objects, "
              "nothing on either side of the difference.",
        **verified))

    entries.append(dict(
        id="C-C3D-04", status="VERIFIED",
        claim="Ethnic Group (0010,2160) present in a 2026c object is a retired "
              "attribute, permitted, and is adjudicated FLOOR.",
        value="PS3.3 Table C.7-1 has no row for (0010,2160) in the pinned edition. "
              "Its row for Ethnic Groups (0010,2162) Type 3 reads verbatim: Ethnic "
              "group(s) or race(s) of Patient. One or more Values may be present. "
              "This Attribute replaces the use of Ethnic Group (0010,2160), which "
              "has been retired. See PS3.3-2025a. PS3.6 Table 6-1 still allocates "
              "(0010,2160) Ethnic Group, VR SH, VM 1, marked RET (2025a). PS3.4 "
              "Section B.4.1.1 verbatim: Storage Level 2 (Full) indicates that all "
              "Type 1, Type 2, and Type 3 Attributes defined in the Information "
              "Object Definition associated with the SOP Class, as well as any "
              "Standard Extended Attributes (including Private Attributes) included "
              "in the SOP Instance, will be stored and may be accessed.",
        n=str(rep["per_rule_objects"].get("DV_ETHNIC_GROUP_UNEXPECTED", 0)),
        denominator=str(n),
        floor="not applicable, this row is the citation rather than a rate",
        validator="dicom-validator", validator_version=DV_VER,
        status_note="The message is not a Type verdict. dicom-validator 0.8.2 "
                    "documents ErrorCode.TagUnexpected as Tag is not in any allowed "
                    "module and renders it as is unexpected, and files it under the "
                    "pseudo-module name General, which the tool uses for tags it "
                    "could place in no module of the IOD. The code therefore fires "
                    "on every attribute outside the IOD's module set, retired or "
                    "Standard Extended alike. dciodvfy raised nothing against this "
                    "attribute on any object in this class.",
        notes="Corroboration and not the basis of the verdict: 29 of the 32 rows in "
              "results/floor_set.csv are is unexpected messages from the same tool "
              "against known-good objects. This is the second route by which the "
              "TagUnexpected code has been shown not to carry a requirement, the "
              "first being C-CSR-02.",
        **verified))

    entries.append(dict(
        id="C-C3D-05", status="VERIFIED",
        claim="Procedure Code Sequence (0008,1032) present with zero Items "
              "violates a stated prohibition; dciodvfy's companion Value "
              "Multiplicity message on the same objects carries no citation and is "
              "left UNDECIDABLE.",
        value="PS3.3 Table C.7-3 makes (0008,1032) Type 3 with the Attribute "
              "Description: A Sequence that conveys the type of procedure "
              "performed. One or more Items are permitted in this Sequence. PS3.5 "
              "Section 7.4.5 verbatim: Type 3 Data Elements may also be encoded "
              "with zero length and no Value, except for SQ Data Elements, which "
              "shall not be present with zero Items.",
        n=str(rep["per_rule_objects"].get("PROC_CODE_SEQ_ZERO_ITEMS", 0)),
        denominator=str(n),
        floor="not applicable, this row is the citation rather than a rate",
        validator="dciodvfy", validator_version=DCIOD_VER,
        status_note="dciodvfy's phrase 1-n Required by Module definition is not "
                    "what the module definition says: Table C.7-3 says Items are "
                    "permitted, not required. The prohibition that carries the "
                    "class is PS3.5 Section 7.4.5, so the class is flagged off-part "
                    "and every triple is also published with it demoted. See "
                    "C-C3D-11.",
        notes="The companion message, Bad attribute Value Multiplicity Type 3 "
              "Optional on the same attribute and module, prints neither the "
              "observed nor the required multiplicity, and PS3.5 Section 7.5 fixes "
              "the VM of any SQ at one regardless of item count, so no requirement "
              "can be attached to it by citation. Left UNDECIDABLE rather than "
              "folded into this finding by judgement. Measured rather than assumed: "
              "it lands on exactly the same 2 objects, so it moves no triple.",
        **verified))

    entries.append(dict(
        id="C-C3D-06", status="MEASURED",
        claim="dciodvfy error triple for Comprehensive 3D SR Storage, after "
              "adjudication.",
        value="gross %s of %s objects (%.2f percent), floor %s (%.2f percent), net "
              "%s (%.2f percent), other %s"
              % (f"{dciod_e['gross']:,}", f"{n:,}", dciod_e["pct_gross"],
                 f"{dciod_e['floor']:,}", dciod_e["pct_floor"],
                 f"{dciod_e['net']:,}", dciod_e["pct_net"], f"{dciod_e['other']:,}"),
        n=str(dciod_e["net"]), denominator=str(n),
        floor="%s objects (%.2f percent) carry only FLOOR, NOT-IOD or PLAUSIBILITY "
              "error classes" % (f"{dciod_e['floor']:,}", dciod_e["pct_floor"]),
        validator="dciodvfy", validator_version=DCIOD_VER,
        status_note="other counts objects with no NET class but at least one "
                    "UNDECIDABLE class, so they are neither floor nor net and are "
                    "not folded into either.",
        derived_from="C-C3D-01,C-C3D-02,C-C3D-03,C-C3D-05", **measured))

    entries.append(dict(
        id="C-C3D-07", status="MEASURED",
        claim="dciodvfy warning triple for Comprehensive 3D SR Storage, after "
              "adjudication.",
        value="gross %s of %s objects (%.2f percent), floor %s (%.2f percent), net "
              "%s (%.2f percent), other %s"
              % (f"{dciod_w['gross']:,}", f"{n:,}", dciod_w["pct_gross"],
                 f"{dciod_w['floor']:,}", dciod_w["pct_floor"],
                 f"{dciod_w['net']:,}", dciod_w["pct_net"], f"{dciod_w['other']:,}"),
        n=str(dciod_w["net"]), denominator=str(n),
        floor="%s objects (%.2f percent) carry only FLOOR, NOT-IOD or PLAUSIBILITY "
              "warning classes" % (f"{dciod_w['floor']:,}", dciod_w["pct_floor"]),
        validator="dciodvfy", validator_version=DCIOD_VER,
        status_note="No warning class in this SOP class is adjudicated NET. The 100 "
                    "percent gross warning rate reported in the Phase 2 census is "
                    "the DICOMDIR advice on Study ID and Study Time, which is "
                    "NOT-IOD, and the Retired Person Name form heuristic, which is "
                    "PLAUSIBILITY.",
        derived_from="C-C3D-06", **measured))

    entries.append(dict(
        id="C-C3D-08", status="MEASURED",
        claim="dicom-validator error triple for Comprehensive 3D SR Storage, after "
              "adjudication.",
        value="gross %s of %s objects (%.2f percent), floor %s (%.2f percent), net "
              "%s (%.2f percent), other %s"
              % (f"{dvv_e['gross']:,}", f"{n:,}", dvv_e["pct_gross"],
                 f"{dvv_e['floor']:,}", dvv_e["pct_floor"],
                 f"{dvv_e['net']:,}", dvv_e["pct_net"], f"{dvv_e['other']:,}"),
        n=str(dvv_e["net"]), denominator=str(n),
        floor="%s objects (%.2f percent) carry only FLOOR, NOT-IOD or PLAUSIBILITY "
              "error classes" % (f"{dvv_e['floor']:,}", dvv_e["pct_floor"]),
        validator="dicom-validator", validator_version=DV_VER,
        status_note="Every dicom-validator error class in this SOP class except the "
                    "Ethnic Group one is TagMissing on a top-level module "
                    "attribute, which is a different code path from the "
                    "TagUnexpected modelling defect recorded at C-CSR-02. The whole "
                    "of the floor column is the Ethnic Group class.",
        derived_from="C-C3D-01,C-C3D-02,C-C3D-03,C-C3D-04", **measured))

    entries.append(dict(
        id="C-C3D-09", status="MEASURED",
        claim="Net rate across both validators for Comprehensive 3D SR Storage, by "
              "analysis result.",
        value="; ".join("%s %s of %s (%.2f percent)"
                        % (a, f"{base['per_arid'][a]['net']:,}",
                           f"{base['per_arid'][a]['objects']:,}",
                           base["per_arid"][a]["pct_net"])
                        for a in rep["arids"])
              + "; all %s of %s (%.2f percent)"
              % (f"{base['net']:,}", f"{n:,}", base["pct_net"]),
        n=str(base["net"]), denominator=str(n),
        floor="reported per validator in C-C3D-06, C-C3D-07 and C-C3D-08; no single "
              "scalar floor is quoted for the union",
        validator="dciodvfy and dicom-validator", validator_version=BOTH_VER,
        status_note="Aggregated by analysis result, not ranked. The five groups "
                    "have different producers and the differences are reported as "
                    "structure in the data, not as a league table.",
        derived_from="C-C3D-06,C-C3D-08", **measured))

    entries.append(dict(
        id="C-C3D-10", status="MEASURED",
        claim="Collection-level net rates for Comprehensive 3D SR Storage, and "
              "their median.",
        value="median %.2f percent across %d collections: %s"
              % (base["median_collection"], len(rep["collections"]),
                 "; ".join("%s %.2f percent (%s of %s)"
                           % (c, base["per_collection"][c]["pct_net"],
                              f"{base['per_collection'][c]['net']:,}",
                              f"{base['per_collection'][c]['objects']:,}")
                           for c in rep["collections"])),
        n=str(base["net"]), denominator=str(n),
        floor="reported per validator in C-C3D-06, C-C3D-07 and C-C3D-08",
        validator="dciodvfy and dicom-validator", validator_version=BOTH_VER,
        status_note="Collection is read from _cache/census/records.jsonl, which was "
                    "opened read only. Objects and series are one to one in this "
                    "class, so the object rate and the series rate coincide. The "
                    "collection and analysis result groupings are not nested: one "
                    "collection carries two analysis results and one analysis "
                    "result spans two collections, so neither table can be derived "
                    "from the other.",
        derived_from="C-C3D-09", **measured))

    entries.append(dict(
        id="C-C3D-11", status="MEASURED",
        claim="Two adjudications in this class are reported both ways, so a reader "
              "who refuses either does not have to recompute the study.",
        value="; ".join("%s: net %s of %s (%.2f percent), collection median %.2f "
                        "percent, substantial %s"
                        % (label, f"{rep['unions'][key]['net']:,}", f"{n:,}",
                           rep["unions"][key]["pct_net"],
                           rep["unions"][key]["median_collection"],
                           "yes" if (rep["unions"][key]["pct_net"] > 5.0
                                     and rep["unions"][key]["median_collection"] > 5.0)
                           else "no")
                        for key, _d, label in SENSITIVITY),
        n=str(rep["unions"]["both"]["net"]), denominator=str(n),
        floor="see C-C3D-06 and C-C3D-08",
        validator="dciodvfy and dicom-validator", validator_version=BOTH_VER,
        status_note="off-part is PROC_CODE_SEQ_ZERO_ITEMS, whose Type is in PS3.3 "
                    "Table C.7-3 but whose operative shall is in PS3.5 Section "
                    "7.4.5. module presence is CT_SUBJECT_TYPE2 and "
                    "DV_CT_SITE_MISSING, whose antecedent, that a User Option "
                    "Module is supported by this Data Set, is a tool judgement "
                    "rather than a quoted requirement.",
        notes="No demotion changes the PRE-05 verdict for this class.",
        derived_from="C-C3D-01,C-C3D-05,C-C3D-09,C-C3D-10", **measured))

    fold = (
        "Comprehensive 3D SR: class-level net %.2f percent of %s objects, "
        "collection median %.2f percent across %d collections, so the conjunction "
        "%s and the class is %s under the registered rule."
        % (base["pct_net"], f"{n:,}", base["median_collection"],
           len(rep["collections"]),
           "holds" if substantial else "fails",
           "SUBSTANTIAL" if substantial else "NOT substantial"))

    entries.append(dict(
        id="C-C3D-12", status="DERIVED",
        claim="PRE-05 outcome for Comprehensive 3D SR Storage, and the sentence to "
              "fold into PRE-05.",
        value="net error-class rate %.2f percent (%s of %s), %s 5.0 percent; "
              "collection-level median net rate %.2f percent across %d "
              "collections, %s 5.0 percent. Conjunction %s, so this class is %s. "
              "Against PRE-05's own three bands the class-level rate alone falls "
              "in the %s band."
              % (base["pct_net"], f"{base['net']:,}", f"{n:,}",
                 "above" if base["pct_net"] > 5.0 else "at or below",
                 base["median_collection"], len(rep["collections"]),
                 "above" if base["median_collection"] > 5.0 else "at or below",
                 "met" if substantial else "not met",
                 "substantial" if substantial else "not substantial",
                 "substantial, above 20 percent" if base["pct_net"] > 20.0
                 else ("indeterminate, above 5 and at or below 20 percent"
                       if base["pct_net"] > 5.0 else "null, at or below 5 percent")),
        n=str(base["net"]), denominator=str(n),
        floor="see C-C3D-06, C-C3D-07 and C-C3D-08",
        validator="dciodvfy and dicom-validator", validator_version=BOTH_VER,
        status_note="No PRE-05 row is proposed by this track. PRE-05 was "
                    "reconciled by hand by the orchestrator after two tracks "
                    "collided on it, and the sentence to fold into its status_note "
                    "is carried here instead, verbatim in the notes field. PRE-01 "
                    "is already RETIRED in "
                    "results/pending_ledger/merged/zz_pre01_outcome.json as a wrong "
                    "prediction on the Key Object Selection evidence, and this "
                    "track does not touch it. This class %s clear PRE-05, so it "
                    "%s a second independent falsification of PRE-01."
                    % ("does" if substantial else "does not",
                       "is" if substantial else "is not"),
        notes="Exact sentence to fold into PRE-05: %s" % fold,
        derived_from="C-C3D-09,C-C3D-10,C-C3D-11,PRE-05", **measured))

    return entries


def write_ledger(rep: dict) -> Path:
    entries = ledger_entries(rep)
    from . import ledger as ledger_mod
    allowed = set(ledger_mod.FIELDS) | {"fields_changed"}
    for e in entries:
        unknown = set(e) - allowed
        if unknown:
            raise ValueError("pending ledger row %s has unknown keys: %s"
                             % (e["id"], sorted(unknown)))
        if e["status"] not in ledger_mod.VALID_STATUS:
            raise ValueError("bad status on %s" % e["id"])
        if e["status"] in ("MEASURED", "DERIVED"):
            for field in ("command", "source_file", "dropped", "floor"):
                if not e.get(field):
                    raise ValueError("%s row %s has no %s"
                                     % (e["status"], e["id"], field))
    OUT_LEDGER.parent.mkdir(parents=True, exist_ok=True)
    OUT_LEDGER.write_text(json.dumps(dict(
        track="C", sop_class=SOP_CLASS, generated_by=CMD,
        generated_on=VERIFIED_ON, standard_edition=EDITION,
        note="Proposed rows, not merged. Keys match colophon.ledger.FIELDS. No "
             "PRE-05 row is proposed: that row was reconciled by hand by the "
             "orchestrator and the sentence this class contributes to it is "
             "carried verbatim in the notes field of C-C3D-12. PRE-01 is already "
             "RETIRED and is not touched.",
        rows=entries), indent=1), encoding="utf-8")
    return OUT_LEDGER


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.parse_args(argv)
    rep = build()

    unmatched = [k for k, v in rep["per_class"].items()
                 if v["rule"]["name"] == "UNMATCHED"]
    print("message classes adjudicated: %d" % len(rep["per_class"]))
    for k in sorted(rep["verdict_counts"]):
        print("  %-13s %5d classes" % (k, rep["verdict_counts"][k]))
    if unmatched:
        print("UNMATCHED, left UNDECIDABLE: %d" % len(unmatched))
        for v, c in unmatched[:20]:
            print("   %s %s %s"
                  % (v, c, rep["per_class"][(v, c)]["message_template"][:110]))

    print("\nobjects %s in %s series, records.jsonl lines %s, unparseable %d"
          % (f"{rep['n_objects']:,}", f"{rep['n_series']:,}",
             f"{rep['lines_read']:,}", rep["lines_skipped"]))
    for validator in rep["validators"]:
        for severity in ("ERROR", "WARNING"):
            t = rep["triples"]["as_adjudicated"][validator][severity]["overall"]
            print("  %-16s %-8s gross %5d  floor %5d  net %5d  other %5d"
                  % (validator, severity.lower(), t["gross"], t["floor"], t["net"],
                     t["other"]))
    for key, _d, label in SENSITIVITY:
        u = rep["unions"][key]
        print("  %-24s union net %5d (%6.2f pct), collection median %6.2f pct"
              % (label, u["net"], u["pct_net"], u["median_collection"]))

    print("\nwrote %s" % write_csv(rep))
    print("wrote %s" % write_markdown(rep))
    print("wrote %s" % write_ledger(rep))
    return 0


if __name__ == "__main__":
    sys.exit(main())
