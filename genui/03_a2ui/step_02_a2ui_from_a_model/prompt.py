"""The a2ui-agent-sdk side: a system prompt built from the Basic Catalog, a
streaming parser that yields messages while the model is still writing, and
a full parser that repairs and validates the finished reply.

pip install a2ui-agent-sdk   (0.6.0; pulls a2ui-core, which holds the schemas)
"""

from a2ui.basic_catalog import BasicCatalog
from a2ui.inference_formats.direct_json import DirectJsonFormat, DirectJsonStreamParser
from a2ui.core import A2uiParseError
from a2ui.parser.errors import A2uiCompilationError

SPEC_VERSION = "0.9.1"

ROLE = """You are a UI agent. Answer every request with A2UI messages, nothing else.
Always send, in this order: one createSurface with surfaceId "main", one
updateComponents, one updateDataModel that sets the initial values of every
bound path under /form.
Rules for the surface:
- Bind every input to a data model path under /form (for example /form/email).
- End the form with a Text component bound to the path /status. It starts empty;
  the server writes confirmations there.
- The submit Button's action is an event named "submit" whose context carries
  every bound field, for example {"email": {"path": "/form/email"}}.
- Use a Card with a Column inside as the root; label every field."""

_format = None


def inference_format():
    """Loads the bundled v0.9.1 schemas and the Basic Catalog once."""
    global _format
    if _format is None:
        _format = DirectJsonFormat(version=SPEC_VERSION, catalogs=[BasicCatalog.get_config(SPEC_VERSION)])
    return _format


def catalog_id():
    """The id the SDK tells the model to use; note it says v0_9, not v0_9_1."""
    return inference_format().supported_catalog_ids[0]


def system_prompt():
    """Role text, the SDK's workflow rules, then the full JSON schema of the catalog."""
    return inference_format().prompt_generator.generate(role_description=ROLE, include_schema=True)


def stream_parser():
    """Feed model text chunks in; get A2UI messages out as soon as they are usable."""
    return DirectJsonStreamParser(inference_format()._supported_catalogs[0])


def parse_reply(text):
    """The finished reply: repaired (trailing commas and the like), validated
    against the catalog, split into prose and messages.

    Returns (messages, prose). Raises ValueError with the validator's text
    when the reply cannot be made valid; the caller sends that back to the model.
    """
    try:
        parts = inference_format().parser.parse_response(text)
    except (A2uiCompilationError, A2uiParseError) as error:
        raise ValueError(str(error)) from error
    messages, prose = [], []
    for part in parts:  # a part holds the prose before a block and the block's messages
        if part.text and part.text.strip():
            prose.append(part.text.strip())
        messages.extend(part.a2ui_json or [])
    return messages, prose
