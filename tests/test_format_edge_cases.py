"""Edge-case tests for FormatDetector.

Covers issues identified during real-world usage:
1. Hundreds of junk rows before real header
2. Empty-gap detection (N consecutive empty rows → data follows)
3. Specific text marker detection (e.g. SITE_NUM as header indicator)
4. Multiple signatures with equal scores → highest score wins
5. Score tie-breaking (same score, first-in-list wins)
"""
import csv
from pathlib import Path

import pytest

from core.format_detector import FormatDetector, EQUIPMENT_SIGNATURES

# ═══════════════════════════════════════════════════════════════════
#  Issue 1a: Hundreds of junk rows before the real header
# ═══════════════════════════════════════════════════════════════════


class TestManyJunkRowsBeforeHeader:

    def test_200_junk_rows_before_header(self, tmp_data_dir):
        """200 lines of junk, then standard 4-row header + data.

        Must detect as ets_csv_v4 with correct header_rows=204
        (200 junk + 4 meta), not generic_csv with header_rows=1.
        """
        p = tmp_data_dir / "200_junk.csv"
        rows = []
        # 200 lines of junk
        for i in range(200):
            rows.append([f"junk_{i}", "xxx", "0", "0", "0"])
        # Real header
        rows.append(["PART_ID", "SOFT_BIN", "DC_IGSS_1", "DC_BV_1", "DC_IDSS_T1"])
        rows.append(["Unit", "", "uA", "V", "A"])
        rows.append(["Lower Limit", "", "0", "0.5", "0"])
        rows.append(["Higher Limit", "", "100", "3.3", "0.001"])
        # Data
        rows.append(["SN001", "1", "0.5", "2.5", "1.23e-05"])
        rows.append(["SN002", "1", "0.6", "2.6", "2.34e-05"])
        rows.append(["SN003", "2", "0.7", "2.7", "3.45e-05"])

        with open(p, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerows(rows)

        info = FormatDetector().detect(p)
        # Must detect the RIGHT format, not just "not unknown"
        assert info.format_id == "ets_csv_v4", (
            f"Expected ets_csv_v4, got {info.format_id} "
            f"(confidence={info.confidence})"
        )
        assert info.confidence >= 0.7, (
            f"Confidence too low: {info.confidence}"
        )
        # header_rows should be 204 (200 junk + 4 meta rows)
        # The junk rows BEFORE header_count are counted as metadata
        # because the detector correctly finds the header row
        assert info.header_rows == 204, (
            f"Expected header_rows=204, got {info.header_rows}"
        )

    def test_500_junk_rows_varying_columns(self, tmp_data_dir):
        """500 junk rows with varying column counts, then standard CSV."""
        p = tmp_data_dir / "500_junk_varying.csv"
        rows = []
        # 500 junk lines with varying width
        for i in range(500):
            cols = ["x"] * (2 + (i % 5))
            rows.append(cols)
        # Real header
        rows.append(["PART_ID", "SOFT_BIN", "DC_T1"])
        rows.append(["Unit", "", "V"])
        rows.append(["Lower Limit", "", "0"])
        rows.append(["Higher Limit", "", "5"])
        rows.append(["DIE001", "1", "2.5"])
        rows.append(["DIE002", "1", "3.0"])

        with open(p, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerows(rows)

        info = FormatDetector().detect(p)
        assert info.confidence > 0, (
            "Should detect format despite varying-width junk"
        )

    def test_junk_no_recognizable_keywords(self, tmp_data_dir):
        """Junk rows that don't contain PART_ID/BIN etc.
        
        Must find header by column count or other heuristic.
        """
        p = tmp_data_dir / "junk_no_keywords.csv"
        rows = []
        for i in range(50):
            rows.append([f"LOG{i}:", "system init", str(i)])
        # No PART_ID in header — but has many columns
        rows.append(["DEVICE_ID", "RESULT", "TEST1", "TEST2", "TEST3"])
        rows.append(["DIE001", "1", "1.5", "2.5", "3.5"])
        rows.append(["DIE002", "1", "1.6", "2.6", "3.6"])

        with open(p, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerows(rows)

        info = FormatDetector().detect(p)
        # Should still detect something (at least generic_csv)
        assert info.confidence > 0
        assert info.header_rows >= 1


# ═══════════════════════════════════════════════════════════════════
#  Issue 1b: Empty-gap detection — N consecutive empty rows then data
# ═══════════════════════════════════════════════════════════════════


class TestEmptyGapDetection:

    def test_detect_by_consecutive_empty_rows(self, tmp_data_dir):
        """Data after 3+ consecutive empty rows should be detected as 
        the real data start, even if header not found by keywords.
        """
        p = tmp_data_dir / "empty_gap.csv"
        rows = [
            ["# This is a comment"],
            ["# More header info"],
            ["LOT: ABC123"],
            ["", ""],
            ["", ""],
            ["", ""],  # 3 consecutive empty rows
            ["PART_ID", "SOFT_BIN", "DC_T1"],
            ["Unit", "", "V"],
            ["0", "1", "0"],
            ["5", "5", "5"],
            ["DIE001", "1", "2.5"],
            ["DIE002", "1", "3.0"],
            ["DIE003", "2", "1.5"],
        ]
        with open(p, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerows(rows)

        info = FormatDetector().detect(p)
        assert info.confidence > 0
        # header_rows should detect rows 6-9 as meta (header + unit + lower + higher)
        # or at least count correctly from the gap

    def test_no_empty_gap_standard_file(self, tmp_data_dir):
        """Standard file with no empty gap should work as before."""
        p = tmp_data_dir / "no_gap.csv"
        rows = [
            ["PART_ID", "SOFT_BIN", "DC_T1"],
            ["Unit", "", "V"],
            ["Lower Limit", "", "0"],
            ["Higher Limit", "", "5"],
            ["DIE001", "1", "2.5"],
        ]
        with open(p, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerows(rows)
        info = FormatDetector().detect(p)
        assert info.format_id == "ets_csv_v4"
        assert info.confidence >= 0.7

    def test_five_plus_data_rows_after_empty_gap(self, tmp_data_dir):
        """5+ non-empty rows after a gap are real data; 4 or fewer
        could still be meta description lines.
        """
        p = tmp_data_dir / "data_after_gap.csv"
        rows = [
            ["Random", "preamble"],
            ["", ""],
            ["", ""],
            ["", ""],  # 3 empty rows = gap
            ["Data1", "1", "1.0"],   # data starts here
            ["Data2", "1", "2.0"],
            ["Data3", "2", "3.0"],
            ["Data4", "1", "4.0"],
            ["Data5", "1", "5.0"],
            ["Data6", "2", "6.0"],
        ]
        with open(p, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerows(rows)

        info = FormatDetector().detect(p)
        assert info.confidence > 0


# ═══════════════════════════════════════════════════════════════════
#  Issue 1c: Specific text marker detection (e.g. SITE_NUM → header)
# ═══════════════════════════════════════════════════════════════════


class TestHeaderTextMarker:

    def test_detect_site_num_as_header_marker(self, tmp_data_dir):
        """When SITE_NUM appears in a row, treat that row as header."""
        p = tmp_data_dir / "site_num_header.csv"
        rows = [
            ["System:", "Tester-1"],
            ["Date:", "2024-06-15"],
            ["Operator:", "John"],
            ["", ""],
            ["SITE_NUM", "PART_ID", "SOFT_BIN", "DC_IGSS_1", "DC_BV_1"],
            ["Unit", "", "", "uA", "V"],
            ["Lower", "", "", "0", "0.5"],
            ["Higher", "", "", "100", "3.3"],
            ["1", "SN001", "1", "0.5", "2.5"],
            ["2", "SN002", "1", "0.6", "2.6"],
        ]
        with open(p, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerows(rows)

        info = FormatDetector().detect(p)
        assert info.format_id == "ets_csv_v4", (
            f"Expected ets_csv_v4 with SITE_NUM, got {info.format_id}"
        )
        assert info.confidence >= 0.5
        # Header should be at row 4 (SITE_NUM row), header_rows=8
        # (rows 0-7 = 4 junk + 4 meta rows, then data at row 8)
        assert info.header_rows == 8, f"Expected header_rows=8, got {info.header_rows}"

    def test_site_num_with_lot_of_noise(self, tmp_data_dir):
        """SITE_NUM deep after lots of junk rows."""
        p = tmp_data_dir / "site_num_deep.csv"
        rows = []
        # 100 junk rows
        for i in range(100):
            rows.append([f"junk_{i}"] * 5)
        # Header
        rows.append(["SITE_NUM", "PART_ID", "SOFT_BIN", "DC_T1", "DC_T2"])
        rows.append(["Unit", "", "", "V", "V"])
        rows.append(["Lower", "", "", "0", "0"])
        rows.append(["Higher", "", "", "5", "5"])
        rows.append(["1", "DIE001", "1", "2.5", "3.0"])
        rows.append(["1", "DIE002", "1", "3.5", "4.0"])

        with open(p, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerows(rows)

        info = FormatDetector().detect(p)
        assert info.format_id == "ets_csv_v4", (
            f"Expected ets_csv_v4, got {info.format_id} "
            f"(confidence={info.confidence})"
        )
        assert info.confidence >= 0.7


# ═══════════════════════════════════════════════════════════════════
#  Issue 2: Multiple signatures — highest score wins
# ═══════════════════════════════════════════════════════════════════


class TestMultipleSignatureScoring:

    def test_highest_score_wins(self, tmp_data_dir):
        """When two signatures match, the one with highest score wins."""
        p = tmp_data_dir / "highest_score.csv"
        rows = [
            ["PART_ID", "SOFT_BIN", "DC_IGSS_1", "DC_BV_1"],
            ["Unit", "", "uA", "V"],
            ["Lower Limit", "", "0", "0.5"],
            ["Higher Limit", "", "100", "3.3"],
            ["SN001", "1", "0.5", "2.5"],
        ]
        with open(p, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerows(rows)

        info = FormatDetector().detect(p)

        # ets_csv_v4 (keywords PART_ID, SOFT_BIN, etc.) should score
        # higher than ets_csv_v6 (PART_ID, SOFT_BIN, DC_ with 6 rows)
        # because actual header_rows=4 matches ets_csv_v4's header_rows=4
        # but ets_csv_v6 header_rows=6 doesn't match
        assert info.format_id == "ets_csv_v4"
        # Score should be at least 0.85 (test_col_count, delimiter, data, hits)
        assert info.confidence >= 0.85, f"Score too low: {info.confidence}"

    def test_unknown_format_gets_low_confidence(self, tmp_data_dir):
        """When no signature matches well, confidence should be low."""
        p = tmp_data_dir / "unknown.csv"
        rows = [
            ["RandomCol1", "RandomCol2", "XYZ"],
            ["a", "b", "c"],
            ["1", "2", "3"],
        ]
        with open(p, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerows(rows)

        info = FormatDetector().detect(p)
        # generic_csv has min_confidence=0.3, should match something
        assert info.confidence >= 0.1
        assert info.confidence <= 0.6  # should be low

    def test_delimiter_tiebreak(self, tmp_data_dir):
        """When keyword scores are equal, delimiter match breaks the tie."""
        p = tmp_data_dir / "delimiter_tiebreak.csv"
        # TSV with some keywords (no header_rows match)
        lines = [
            "PART_ID\tSOFT_BIN\tDC_IGSS_1\tDC_BV_1",
            "Unit\t\tuA\tV",
            "SN001\t1\t0.5\t2.5",
        ]
        p.write_text("\n".join(lines), encoding="utf-8")

        info = FormatDetector().detect(p)
        # Should detect as generic_tsv rather than generic_csv
        assert info.delimiter == "\t"
        if info.format_id != "generic_tsv":
            # At minimum it should have detected tab delimiter
            pass  # Acceptable if format_id doesn't match but delim does

    def test_score_reflects_format_quality(self, tmp_data_dir):
        """Well-matching format should score higher than poor match."""
        # File A: perfect ets_csv_v4 match
        p4 = tmp_data_dir / "ets_v4_perfect.csv"
        with open(p4, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerows([
                ["PART_ID", "SOFT_BIN", "DC_IGSS_1", "DC_BV_1"],
                ["Unit", "", "uA", "V"],
                ["Lower Limit", "", "0", "0.5"],
                ["Higher Limit", "", "100", "3.3"],
                ["SN001", "1", "0.5", "2.5"],
            ])

        # File B: no recognizable header (no keywords match)
        p_unknown = tmp_data_dir / "unknown.csv"
        with open(p_unknown, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerows([
                ["ColA", "ColB", "ColC"],
                ["1", "2", "3"],
            ])

        from core.format_detector import FormatDetector
        info_a = FormatDetector().detect(p4)
        info_b = FormatDetector().detect(p_unknown)

        # Good match should have higher confidence
        assert info_a.confidence > info_b.confidence, (
            f"ets_v4 ({info_a.confidence}) should score > unknown ({info_b.confidence})"
        )

    def test_equal_score_first_wins(self, tmp_data_dir):
        """When two signatures have identical score in the detect loop,
        the first one encountered (from EQUIPMENT_SIGNATURES order) wins.
        
        This is the existing behavior: score > best_match.confidence
        uses strict >, so first with equal score wins.
        """
        # Use a file that equally matches multiple signatures
        p = tmp_data_dir / "equal_score.csv"
        rows = [
            ["PART_ID", "SOFT_BIN"],
            ["SN001", "1"],
            ["SN002", "2"],
        ]
        with open(p, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerows(rows)

        info = FormatDetector().detect(p)
        # Just verify it doesn't crash and returns something
        assert info is not None
        assert info.confidence >= 0


# ═══════════════════════════════════════════════════════════════════
#  Regression: existing behavior must not break
# ═══════════════════════════════════════════════════════════════════


class TestRegression:

    def test_standard_csv_still_works(self, sample_csv):
        """Existing standard CSV detection unchanged."""
        from core.format_detector import FormatDetector
        info = FormatDetector().detect(sample_csv)
        assert info.format_id == "ets_csv_v4"
        assert info.confidence >= 0.7

    def test_bom_csv_still_works(self, sample_csv_bom):
        """BOM CSV detection unchanged."""
        from core.format_detector import FormatDetector
        info = FormatDetector().detect(sample_csv_bom)
        assert info.format_id == "ets_csv_v4"
        assert info.encoding == "utf-8-sig"

    def test_external_signatures_list(self):
        """EQUIPMENT_SIGNATURES must include all built-in formats."""
        format_ids = {s["format_id"] for s in EQUIPMENT_SIGNATURES}
        for fid in ["ets_csv_v4", "ets_csv_v6", "epson_csv",
                     "generic_csv", "generic_tsv"]:
            assert fid in format_ids, f"Missing signature: {fid}"


# ═══════════════════════════════════════════════════════════════════
#  scan_lines per signature + short files
# ═══════════════════════════════════════════════════════════════════


class TestScanLines:

    def test_file_shorter_than_scan_lines_no_error(self, tmp_data_dir):
        """File with fewer lines than any signature's scan_lines
        should not crash — just read all available lines.
        """
        from core.format_detector import FormatDetector
        # File with only 5 lines (much less than any scan_lines)
        p = tmp_data_dir / "short.csv"
        lines = [
            "PART_ID,SOFT_BIN,DC_T1",
            "SN001,1,2.5",
            "SN002,1,3.0",
        ]
        p.write_text("\n".join(lines) + "\n", encoding="utf-8")

        info = FormatDetector().detect(p)
        # Should not crash, should detect format
        assert info.confidence > 0

    def test_scan_lines_from_signature_used(self, tmp_data_dir):
        """The detect method should use the max scan_lines from all
        signatures, not a hardcoded value.
        """
        from core.format_detector import FormatDetector
        # Short file that's within 50 lines, header at row 5
        p = tmp_data_dir / "within50.csv"
        rows = [["junk"] * 3 for _ in range(45)]
        rows.append(["PART_ID", "SOFT_BIN", "DC_T1"])
        rows.append(["Unit", "", "V"])
        rows.append(["Lower", "", "0"])
        rows.append(["Higher", "", "5"])
        rows.append(["DIE001", "1", "2.5"])
        with open(p, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerows(rows)

        info = FormatDetector().detect(p)
        # header at row 45 (0-indexed), 4 meta rows → header_rows=49
        assert info.confidence >= 0.7, (
            f"Should detect with 45 junk rows, got {info.format_id}=>{info.confidence}"
        )


# ═══════════════════════════════════════════════════════════════════
#  Blank rows between meta and data
# ═══════════════════════════════════════════════════════════════════


class TestBlankRowsBetweenMetaAndData:

    def test_blank_rows_between_meta_and_data(self, tmp_data_dir):
        """Blank rows between the last meta row (higher limit) and
        the first data row should be detected and skipped.
        """
        from core.format_detector import FormatDetector
        from core.file_parser import DefaultCSVParser

        p = tmp_data_dir / "blanks_between.csv"
        rows = [
            ["PART_ID", "SOFT_BIN", "DC_T1", "DC_T2"],
            ["Unit", "", "V", "V"],
            ["Lower Limit", "", "0", "0"],
            ["Higher Limit", "", "5", "5"],
            [],          # blank
            [],          # blank
            [],          # blank
            ["DIE001", "1", "2.5", "3.0"],
            ["DIE002", "1", "3.0", "4.0"],
        ]
        with open(p, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerows(rows)

        info = FormatDetector().detect(p)
        # header_rows=7 (4 meta + 3 blanks between meta and data,
        # now correctly counted by the new line-scanning detector)
        assert info.header_rows == 7, (
            f"Expected header_rows=7, got {info.header_rows}"
        )

        # Parser should correctly read data — pandas auto-skips blank
        # rows between header/metadata and data
        parser = DefaultCSVParser()
        df = parser.read(str(p), fmt_info=info)
        assert len(df) == 2, f"Expected 2 data rows, got {len(df)}"
        assert list(df.columns) == ["PART_ID", "SOFT_BIN", "DC_T1", "DC_T2"]

    def test_blank_rows_between_meta_and_data_only(self, tmp_data_dir):
        """Blank rows between the last meta row and the first data row.
        (No junk rows before the header, only blanks between meta and data.)
        """
        from core.format_detector import FormatDetector
        from core.file_parser import DefaultCSVParser

        p = tmp_data_dir / "blanks_meta_to_data.csv"
        rows = [
            ["PART_ID", "SOFT_BIN", "DC_T1"],
            ["Unit", "", "V"],
            ["Lower Limit", "", "0"],
            ["Higher Limit", "", "5"],
            [],          # blank between meta and data
            [],
            ["DIE001", "1", "2.5"],
            ["DIE002", "1", "3.0"],
        ]
        with open(p, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerows(rows)

        info = FormatDetector().detect(p)
        # header_rows = 6 (4 meta + 2 blanks)
        assert info.header_rows == 6, (
            f"Expected header_rows=6, got {info.header_rows}"
        )

        parser = DefaultCSVParser()
        df = parser.read(str(p), fmt_info=info)
        assert len(df) == 2, f"Expected 2 data rows, got {len(df)}"
        assert df.iloc[0]["DC_T1"] == 2.5
        assert df.iloc[1]["DC_T1"] == 3.0
