# ============================================================
# COMPACT SRE REPORT
# ============================================================


def _truncate(text, length=42):
    """
    Keep terminal output readable.
    """

    text = str(text)

    if len(text) <= length:
        return text

    return text[:length - 3] + "..."


# ============================================================
# CONFIDENCE
# ============================================================

def _confidence_percent(confidence):
    """
    Convert numeric 0.0-1.0 confidence to percentage.
    """

    if isinstance(
        confidence,
        (int, float),
    ):

        confidence = max(
            0.0,
            min(
                1.0,
                float(confidence),
            ),
        )

        return f"{round(confidence * 100)}%"

    return "N/A"


# ============================================================
# LIST NORMALIZATION
# ============================================================

def _as_list(value):
    """
    Normalize a value into a list.

    Examples:

        "something"
            -> ["something"]

        ["one", "two"]
            -> ["one", "two"]

        None
            -> []
    """

    if value is None:
        return []

    if isinstance(
        value,
        list,
    ):
        return value

    if isinstance(
        value,
        tuple,
    ):
        return list(value)

    if isinstance(
        value,
        str,
    ):

        if value.strip():
            return [value]

        return []

    return [str(value)]


# ============================================================
# OBSERVED FACTS
# ============================================================

def _get_observed_facts(ai_result):
    """
    Extract confirmed facts.

    Current schema:
        evidence

    Backward-compatible schema:
        confirmed_facts
    """

    facts = ai_result.get(
        "evidence"
    )

    if not facts:

        facts = ai_result.get(
            "confirmed_facts",
            [],
        )

    facts = _as_list(
        facts
    )

    return [
        str(item)
        for item in facts[:4]
    ]


# ============================================================
# IMPACT
# ============================================================

def _get_impact(ai_result):
    """
    Extract concise impact information.

    Current schema:
        impact

    Supports both string and list values.
    """

    impact = ai_result.get(
        "impact",
        [],
    )

    impact = _as_list(
        impact
    )

    return [
        str(item)
        for item in impact[:2]
    ]


# ============================================================
# NEXT INVESTIGATION
# ============================================================

def _get_next_investigation(ai_result):
    """
    Extract investigation/remediation actions.

    Current schema:
        remediation

    Backward-compatible schema:
        next_investigation
    """

    actions = ai_result.get(
        "next_investigation"
    )

    if not actions:

        actions = ai_result.get(
            "remediation",
            [],
        )

    actions = _as_list(
        actions
    )

    return [
        str(item)
        for item in actions[:3]
    ]


# ============================================================
# LIKELY CAUSE
# ============================================================

def _get_likely_cause(ai_result):
    """
    Return a likely cause when the AI provides
    explicit hypotheses.

    If no hypotheses are available, use the
    root-cause assessment as the displayed cause.
    """

    hypotheses = ai_result.get(
        "alternative_hypotheses",
        [],
    )

    if isinstance(
        hypotheses,
        list,
    ):

        # ----------------------------------------------------
        # Prefer HIGH likelihood hypothesis
        # ----------------------------------------------------

        for item in hypotheses:

            if not isinstance(
                item,
                dict,
            ):
                continue

            if str(
                item.get(
                    "likelihood",
                    "",
                )
            ).upper() == "HIGH":

                return str(
                    item.get(
                        "hypothesis",
                        "Likely cause not specified.",
                    )
                )

        # ----------------------------------------------------
        # Then MEDIUM likelihood
        # ----------------------------------------------------

        for item in hypotheses:

            if not isinstance(
                item,
                dict,
            ):
                continue

            if str(
                item.get(
                    "likelihood",
                    "",
                )
            ).upper() == "MEDIUM":

                return str(
                    item.get(
                        "hypothesis",
                        "Possible cause not specified.",
                    )
                )

    # --------------------------------------------------------
    # Current schema fallback
    # --------------------------------------------------------

    root_cause = ai_result.get(
        "root_cause",
        "",
    )

    if root_cause:

        return str(
            root_cause
        )

    return "No likely cause identified."


# ============================================================
# VALIDATION
# ============================================================

def _get_validation(ai_result):
    """
    Extract validation information.
    """

    validation = ai_result.get(
        "validation",
        {},
    )

    if not isinstance(
        validation,
        dict,
    ):

        return {
            "valid": False,
            "errors": [
                "Validation result is malformed."
            ],
            "warnings": [],
        }

    return validation


# ============================================================
# PRINT SRE REPORT
# ============================================================

def print_sre_report(ai_result):
    """
    Print a concise human-readable SRE incident report.

    Expected AI fields:

        severity
        title
        summary
        root_cause
        evidence
        remediation
        impact
        confidence
        validation
    """

    if not isinstance(
        ai_result,
        dict,
    ):

        print()
        print(
            "Unable to generate SRE report: "
            "AI result is not a dictionary."
        )

        return

    # ========================================================
    # BASIC INFORMATION
    # ========================================================

    severity = str(
        ai_result.get(
            "severity",
            "UNKNOWN",
        )
    ).upper()

    title = str(
        ai_result.get(
            "title",
            "Unknown incident",
        )
    )

    confidence = _confidence_percent(
        ai_result.get(
            "confidence"
        )
    )

    summary = str(
        ai_result.get(
            "summary",
            "No summary available.",
        )
    )

    root_cause = str(
        ai_result.get(
            "root_cause",
            "Root cause not yet confirmed.",
        )
    )

    likely_cause = _get_likely_cause(
        ai_result
    )

    observed = _get_observed_facts(
        ai_result
    )

    impact = _get_impact(
        ai_result
    )

    next_steps = _get_next_investigation(
        ai_result
    )

    validation = _get_validation(
        ai_result
    )

    validation_errors = _as_list(
        validation.get(
            "errors",
            [],
        )
    )

    validation_warnings = _as_list(
        validation.get(
            "warnings",
            [],
        )
    )

    validation_valid = validation.get(
        "valid",
        False,
    )

    # ========================================================
    # REPORT
    # ========================================================

    print()

    print(
        "┌" + "─" * 58 + "┐"
    )

    print(
        "│" + " SRE INCIDENT REPORT".center(58) + "│"
    )

    print(
        "├" + "─" * 58 + "┤"
    )

    print(
        f"│ Severity   : {_truncate(severity, 43):<43} │"
    )

    print(
        f"│ Incident   : {_truncate(title, 43):<43} │"
    )

    print(
        f"│ Confidence : {confidence:<43} │"
    )

    print(
        "├" + "─" * 58 + "┤"
    )

    # ========================================================
    # SUMMARY
    # ========================================================

    print(
        "│ SUMMARY" + " " * 50 + "│"
    )

    print(
        f"│ {_truncate(summary, 56):<56} │"
    )

    print(
        "├" + "─" * 58 + "┤"
    )

    # ========================================================
    # OBSERVED
    # ========================================================

    print(
        "│ OBSERVED" + " " * 50 + "│"
    )

    if observed:

        for fact in observed:

            print(
                f"│ • {_truncate(fact, 54):<54} │"
            )

    else:

        print(
            "│ • No confirmed evidence available." + " " * 22 + "│"
        )

    print(
        "├" + "─" * 58 + "┤"
    )

    # ========================================================
    # ROOT CAUSE
    # ========================================================

    print(
        "│ ROOT CAUSE ASSESSMENT" + " " * 36 + "│"
    )

    print(
        f"│ {_truncate(root_cause, 56):<56} │"
    )

    print(
        "│" + " " * 58 + "│"
    )

    print(
        f"│ Likely: {_truncate(likely_cause, 49):<49} │"
    )

    print(
        "├" + "─" * 58 + "┤"
    )

    # ========================================================
    # IMPACT
    # ========================================================

    print(
        "│ IMPACT" + " " * 51 + "│"
    )

    if impact:

        for item in impact:

            print(
                f"│ • {_truncate(item, 54):<54} │"
            )

    else:

        print(
            "│ • Impact not identified." + " " * 33 + "│"
        )

    print(
        "├" + "─" * 58 + "┤"
    )

    # ========================================================
    # NEXT INVESTIGATION
    # ========================================================

    print(
        "│ NEXT INVESTIGATION / REMEDIATION" + " " * 24 + "│"
    )

    if next_steps:

        for step in next_steps:

            print(
                f"│ • {_truncate(step, 54):<54} │"
            )

    else:

        print(
            "│ • No remediation actions provided." + " " * 20 + "│"
        )

    print(
        "├" + "─" * 58 + "┤"
    )

    # ========================================================
    # VALIDATION
    # ========================================================

    print(
        "│ VALIDATION" + " " * 47 + "│"
    )

    if validation_valid and not validation_errors:

        print(
            "│ ✓ PASS - No evidence contradictions." + " " * 20 + "│"
        )

    else:

        print(
            f"│ ✗ FAIL - {len(validation_errors)} validation error(s)"
            f"{' ' * 37}│"
        )

        for error in validation_errors:

            print(
                f"│ • {_truncate(error, 54):<54} │"
            )

    # --------------------------------------------------------
    # Warnings
    # --------------------------------------------------------

    if validation_warnings:

        print(
            "│" + " " * 58 + "│"
        )

        print(
            f"│ Warnings: {len(validation_warnings):<47} │"
        )

        for warning in validation_warnings[:3]:

            print(
                f"│ • {_truncate(warning, 54):<54} │"
            )

    print(
        "└" + "─" * 58 + "┘"
    )
