import json
import os
import re

import boto3
from botocore.exceptions import BotoCoreError, ClientError


# ============================================================
# CONFIGURATION
# ============================================================

AWS_REGION = os.getenv(
    "AWS_REGION",
    "us-east-1",
)

BEDROCK_MODEL_ID = os.getenv(
    "BEDROCK_MODEL_ID",
    "amazon.nova-lite-v1:0",
)


# ============================================================
# BEDROCK CLIENT
# ============================================================

bedrock = boto3.client(
    "bedrock-runtime",
    region_name=AWS_REGION,
)


# ============================================================
# FALLBACK RESULT
# ============================================================

def error_result(
    title,
    summary,
    root_cause,
    remediation,
):
    """
    Return a predictable result when Bedrock analysis fails.
    """

    return {
        "severity": "UNKNOWN",
        "title": title,
        "summary": summary,
        "root_cause": root_cause,
        "evidence": [],
        "remediation": remediation,
        "impact": "AI analysis unavailable.",
        "confidence": 0.0,
    }


# ============================================================
# JSON EXTRACTION
# ============================================================

def extract_json(text):
    """
    Extract a JSON object from an LLM response.

    Handles:

        {"severity": "HIGH"}

    Markdown:

        ```json
        {"severity": "HIGH"}
        ```

    And responses containing explanatory text:

        Here is the analysis:
        {"severity": "HIGH"}
    """

    if text is None:
        raise ValueError(
            "Bedrock returned no text."
        )

    text = str(text).strip()

    if not text:
        raise ValueError(
            "Bedrock returned an empty response."
        )

    # --------------------------------------------------------
    # Remove Markdown code fences
    # --------------------------------------------------------

    text = re.sub(
        r"^\s*```(?:json)?\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"\s*```\s*$",
        "",
        text,
    )

    text = text.strip()

    # --------------------------------------------------------
    # Attempt 1:
    # Entire response is JSON
    # --------------------------------------------------------

    try:
        return json.loads(text)

    except json.JSONDecodeError:
        pass

    # --------------------------------------------------------
    # Attempt 2:
    # Locate JSON object inside response
    # --------------------------------------------------------

    start = text.find("{")

    if start == -1:
        raise ValueError(
            "No JSON object found in Bedrock response."
        )

    depth = 0
    in_string = False
    escape = False

    for index in range(
        start,
        len(text),
    ):

        char = text[index]

        if in_string:

            if escape:
                escape = False

            elif char == "\\":
                escape = True

            elif char == '"':
                in_string = False

            continue

        if char == '"':
            in_string = True

        elif char == "{":
            depth += 1

        elif char == "}":

            depth -= 1

            if depth == 0:

                candidate = text[
                    start:index + 1
                ]

                try:

                    return json.loads(
                        candidate
                    )

                except json.JSONDecodeError as exc:

                    raise ValueError(
                        "A JSON object was found in "
                        "the Bedrock response, but it "
                        "could not be parsed."
                    ) from exc

    raise ValueError(
        "Bedrock returned an incomplete JSON object."
    )


# ============================================================
# RESPONSE VALIDATION
# ============================================================

def validate_analysis(data):
    """
    Validate and normalize the structure returned
    by Amazon Bedrock.
    """

    if not isinstance(
        data,
        dict,
    ):
        raise ValueError(
            "Bedrock response must be a JSON object."
        )

    # --------------------------------------------------------
    # Required fields
    # --------------------------------------------------------

    required_fields = [
        "severity",
        "title",
        "summary",
        "root_cause",
        "evidence",
        "remediation",
        "impact",
        "confidence",
    ]

    for field in required_fields:

        if field not in data:
            data[field] = ""

    # --------------------------------------------------------
    # Severity
    # --------------------------------------------------------

    severity = str(
        data.get(
            "severity",
            "UNKNOWN",
        )
    ).upper().strip()

    allowed_severities = {
        "CRITICAL",
        "HIGH",
        "MEDIUM",
        "LOW",
        "INFO",
        "UNKNOWN",
    }

    if severity not in allowed_severities:
        severity = "UNKNOWN"

    data["severity"] = severity

    # --------------------------------------------------------
    # Numeric confidence
    #
    # Expected range:
    #
    #     0.0 <= confidence <= 1.0
    # --------------------------------------------------------

    confidence = data.get(
        "confidence"
    )

    if isinstance(
        confidence,
        bool,
    ):

        confidence = 0.0

    elif isinstance(
        confidence,
        (int, float),
    ):

        confidence = float(
            confidence
        )

    elif isinstance(
        confidence,
        str,
    ):

        try:

            confidence = float(
                confidence.strip()
            )

        except ValueError:

            confidence = 0.0

    else:

        confidence = 0.0

    # --------------------------------------------------------
    # Clamp invalid values.
    #
    # The validator in ai_validator.py will also check this,
    # but normalizing here keeps the agent output predictable.
    # --------------------------------------------------------

    if confidence < 0:
        confidence = 0.0

    if confidence > 1:
        confidence = 1.0

    data["confidence"] = confidence

    # --------------------------------------------------------
    # Evidence
    # --------------------------------------------------------

    if data["evidence"] is None:

        data["evidence"] = []

    elif isinstance(
        data["evidence"],
        str,
    ):

        data["evidence"] = [
            data["evidence"]
        ]

    elif not isinstance(
        data["evidence"],
        list,
    ):

        data["evidence"] = [
            str(data["evidence"])
        ]

    # --------------------------------------------------------
    # Remediation
    # --------------------------------------------------------

    if data["remediation"] is None:

        data["remediation"] = []

    elif isinstance(
        data["remediation"],
        str,
    ):

        data["remediation"] = [
            data["remediation"]
        ]

    elif not isinstance(
        data["remediation"],
        list,
    ):

        data["remediation"] = [
            str(data["remediation"])
        ]

    # --------------------------------------------------------
    # String fields
    # --------------------------------------------------------

    for field in [
        "title",
        "summary",
        "root_cause",
        "impact",
    ]:

        if data[field] is None:

            data[field] = ""

        elif not isinstance(
            data[field],
            str,
        ):

            data[field] = str(
                data[field]
            )

    return data


# ============================================================
# MODEL RESPONSE EXTRACTION
# ============================================================

def extract_model_text(response_body):
    """
    Extract generated text from the Bedrock response.

    Supports Amazon Nova / Converse-style responses
    and several common Bedrock response structures.
    """

    if not isinstance(
        response_body,
        dict,
    ):
        raise ValueError(
            "Bedrock response body is not a JSON object."
        )

    # --------------------------------------------------------
    # Amazon Nova / Converse format
    # --------------------------------------------------------

    output = response_body.get(
        "output"
    )

    if isinstance(
        output,
        dict,
    ):

        message = output.get(
            "message"
        )

        if isinstance(
            message,
            dict,
        ):

            content = message.get(
                "content",
                [],
            )

            if isinstance(
                content,
                list,
            ):

                text_parts = []

                for item in content:

                    if not isinstance(
                        item,
                        dict,
                    ):
                        continue

                    text = item.get(
                        "text"
                    )

                    if text is not None:

                        text_parts.append(
                            str(text)
                        )

                if text_parts:

                    return "\n".join(
                        text_parts
                    )

    # --------------------------------------------------------
    # Generic content format
    # --------------------------------------------------------

    content = response_body.get(
        "content"
    )

    if isinstance(
        content,
        list,
    ):

        text_parts = []

        for item in content:

            if not isinstance(
                item,
                dict,
            ):
                continue

            text = item.get(
                "text"
            )

            if text is not None:

                text_parts.append(
                    str(text)
                )

        if text_parts:

            return "\n".join(
                text_parts
            )

    # --------------------------------------------------------
    # Generic completion format
    # --------------------------------------------------------

    completion = response_body.get(
        "completion"
    )

    if completion is not None:
        return str(
            completion
        )

    # --------------------------------------------------------
    # Generic string output
    # --------------------------------------------------------

    if isinstance(
        output,
        str,
    ):
        return output

    # --------------------------------------------------------
    # Other common formats
    # --------------------------------------------------------

    for key in [
        "text",
        "generation",
        "generated_text",
    ]:

        value = response_body.get(
            key
        )

        if isinstance(
            value,
            str,
        ):

            return value

    raise ValueError(
        "Could not find generated text in "
        "the Bedrock response."
    )


# ============================================================
# BEDROCK INVOCATION
# ============================================================

def call_bedrock(ai_input):
    """
    Send Kubernetes/SRE information to Amazon Bedrock
    and return structured analysis.
    """

    prompt = f"""
You are a senior Site Reliability Engineer (SRE)
and Kubernetes troubleshooting expert.

Analyze the supplied Kubernetes incident data.

Determine:

1. Severity
2. Incident title
3. Short summary
4. Root cause
5. Evidence from the supplied data
6. Recommended remediation steps
7. Potential impact
8. Numeric confidence between 0.0 and 1.0

IMPORTANT RULES:

- Return ONLY valid JSON.
- Do NOT use Markdown.
- Do NOT use ```json.
- Do NOT add explanations before the JSON.
- Do NOT add explanations after the JSON.
- Do NOT invent Kubernetes or AWS evidence.
- Base the analysis only on the supplied data.
- Distinguish confirmed facts from hypotheses.
- Do not claim an underlying root cause unless it is
  directly supported by the supplied evidence.
- If the evidence only proves that kubelet stopped
  reporting node status, state that the underlying
  reason is "not yet confirmed".
- A high confidence value means high confidence in
  the conclusion supported by the evidence, not that
  every underlying cause is known.
- confidence MUST be a numeric value between 0.0 and 1.0.

Return exactly this JSON structure:

{{
  "severity": "CRITICAL|HIGH|MEDIUM|LOW|INFO",
  "title": "short incident title",
  "summary": "short incident summary",
  "root_cause": "confirmed cause or explicitly state that the underlying cause is not yet confirmed",
  "evidence": [
    "evidence item 1",
    "evidence item 2"
  ],
  "remediation": [
    "remediation step 1",
    "remediation step 2"
  ],
  "impact": "potential system or user impact",
  "confidence": 0.0
}}

Kubernetes incident data:

{json.dumps(
    ai_input,
    indent=2,
    default=str,
)}
"""

    request_body = {
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "text": prompt,
                    }
                ],
            }
        ],
        "inferenceConfig": {
            "maxTokens": 2000,
            "temperature": 0.1,
        },
    }

    # ========================================================
    # CALL BEDROCK
    # ========================================================

    try:

        print(
            "\nCalling Amazon Bedrock..."
        )

        response = bedrock.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            body=json.dumps(
                request_body
            ),
            contentType="application/json",
            accept="application/json",
        )

    except (
        BotoCoreError,
        ClientError,
    ) as exc:

        print(
            "\nERROR: Amazon Bedrock invocation failed"
        )

        print(
            str(exc)
        )

        return error_result(
            title="Bedrock invocation failed",
            summary=(
                "The AI troubleshooting analysis "
                "could not be completed."
            ),
            root_cause=(
                "The AI analysis could not be performed."
            ),
            remediation=[
                "Check AWS credentials.",
                "Check the configured Bedrock model.",
                "Check IAM permission "
                "bedrock:InvokeModel.",
                "Check AWS region configuration.",
            ],
        )

    # ========================================================
    # READ BEDROCK RESPONSE
    # ========================================================

    try:

        raw_body = response[
            "body"
        ].read()

        response_body = json.loads(
            raw_body
        )

    except Exception as exc:

        print(
            "\nERROR: Could not decode "
            "Bedrock response"
        )

        print(
            str(exc)
        )

        return error_result(
            title="Invalid Bedrock response",
            summary=(
                "Bedrock returned a response "
                "that could not be decoded."
            ),
            root_cause=(
                "The underlying cause is not yet confirmed "
                "because the Bedrock response could not "
                "be decoded."
            ),
            remediation=[
                "Inspect the Bedrock response.",
                "Verify the selected model API format.",
            ],
        )

    # ========================================================
    # EXTRACT MODEL TEXT
    # ========================================================

    try:

        model_text = extract_model_text(
            response_body
        )

    except Exception as exc:

        print(
            "\nERROR: Could not extract "
            "model response"
        )

        print(
            str(exc)
        )

        print(
            "\nBedrock response:"
        )

        print(
            json.dumps(
                response_body,
                indent=2,
                default=str,
            )
        )

        return error_result(
            title="Invalid AI response",
            summary=(
                "The Bedrock response did not "
                "contain usable model text."
            ),
            root_cause=(
                "The underlying cause is not yet confirmed "
                "because the AI response was unavailable."
            ),
            remediation=[
                "Inspect the Bedrock response structure.",
                "Verify the selected model API format.",
            ],
        )

    # ========================================================
    # PARSE AND VALIDATE JSON
    # ========================================================

    try:

        analysis = extract_json(
            model_text
        )

        analysis = validate_analysis(
            analysis
        )

        return analysis

    except Exception as exc:

        print(
            "\nERROR: Bedrock returned malformed JSON"
        )

        print(
            str(exc)
        )

        print(
            "\nRaw model response:"
        )

        print(
            model_text
        )

        return error_result(
            title="AI returned malformed JSON",
            summary=(
                "Kubernetes data was collected "
                "successfully, but the AI response "
                "could not be parsed."
            ),
            root_cause=(
                "The underlying cause is not yet confirmed "
                "because the AI response was malformed."
            ),
            remediation=[
                "Retry the analysis.",
                "Inspect the raw Bedrock response.",
                "Verify the configured model.",
                "Verify the Bedrock request format.",
            ],
        )


# ============================================================
# PUBLIC API
# ============================================================

def analyze(ai_input):
    """
    Public entry point used by main.py.
    """

    if not isinstance(
        ai_input,
        dict,
    ):

        raise ValueError(
            "ai_input must be a dictionary."
        )

    return call_bedrock(
        ai_input
    )
