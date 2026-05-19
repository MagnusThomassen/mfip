"""Exception hierarchy for the Bloomberg parser.

Three exception types, in order of specificity. Callers that want to
distinguish use the specific classes; callers that only want 'parser
failed somehow' catch BloombergParserError.
"""

from mfip.ingestion.bloomberg.validator import ValidationReport


class BloombergParserError(Exception):
    """Base class for all parser errors. Catch this for 'parser failed' semantics."""


class WorkbookValidationError(BloombergParserError):
    """Validator returned FAIL; STRICT policy refuses to proceed.

    Carries the full ValidationReport so callers can render the
    failure cause without re-running the validator.
    """

    def __init__(self, report: ValidationReport):
        self.report = report
        super().__init__(
            f"Workbook validation failed: {len(report.findings)} findings"
        )


class WorkbookExtractionError(BloombergParserError):
    """The validator passed but extraction failed anyway.

    Typically indicates a contract drift the validator didn't catch
    (e.g. a cell type that should be numeric is text). Raise sparingly
    — every instance is a signal that the validator should grow a
    new check.
    """

    def __init__(self, sheet: str, detail: str):
        self.sheet = sheet
        self.detail = detail
        super().__init__(f"Extraction failed in sheet {sheet!r}: {detail}")
