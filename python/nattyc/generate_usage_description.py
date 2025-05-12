# //tools/rules_vibe/generate_usage_description.py
import json
import logging
import os
import sys
from pathlib import Path
from typing import cast

import asyncclick as click
from pydantic import BaseModel, Field

from python.nattyc.llm import call_llm


class UsageDescription(BaseModel):
    reasoning: str = Field(description="Use this field to plan out your solution.")
    usage_description: str = Field(
        description="The generated usage description for the provided code."
    )


def setup_logging(level: int = logging.INFO) -> None:
    """Set up logging configuration.

    Args:
        level: The logging level to use
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stderr)],
    )


def construct_system_prompt(source_code: str) -> str:
    """Constructs the system prompt for the LLM.

    Args:
        source_code: The source code for which to generate a usage description

    Returns:
        A formatted system prompt string for the LLM
    """
    return f"""You are a helpful assistant that generates clear, concise usage descriptions for source code.

Write a concise but effective usage guide for the following given Java file in 300 words or less for consumption by an LLM (not a human).
Start by very briefly describing the purpose and intention of this class.

CRITICAL: Only describe the PUBLIC interface of this class, do not describe any internal details unless they're absolutely essential for correct usage..
CRITICAL: Clarify the semantic interpretation of any primitive arguments to public methods. The LLM should be able to understand what to pass in there, and WON'T HAVE ACCESS TO parameter names when they are given this code.


Here is the source code to describe:

```
{source_code}
```
"""


@click.command(help="Generate usage descriptions for source code files")
@click.option(
    "--source_file",
    type=click.Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
        path_type=Path,
        resolve_path=True,
        readable=True,
    ),
    required=True,
    help="Path to source code file",
)
@click.option(
    "--output_file",
    type=click.Path(
        file_okay=True,
        dir_okay=False,
        path_type=Path,
        resolve_path=True,
        writable=True,
    ),
    required=True,
    help="Path to output the usage description",
)
@click.option(
    "--llm_model", required=True, help="LLM model name (e.g., gemini-2.0-flash-001)"
)
@click.option(
    "--temperature", type=float, default=0.2, help="Sampling temperature (0.0-1.0)"
)
@click.option(
    "--max_output_tokens", type=int, default=2048, help="Maximum output tokens"
)
@click.option(
    "--api_key_env_var",
    default="LLM_API_KEY",
    help="Environment variable name for API key",
)
@click.option(
    "--raw_header_file",
    type=click.Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
        path_type=Path,
        resolve_path=True,
        readable=True,
    ),
    required=True,
    help="Path to raw header file to prepend to the output",
)
async def main(
    source_file: Path,
    output_file: Path,
    llm_model: str,
    temperature: float,
    max_output_tokens: int,
    api_key_env_var: str,
    raw_header_file: Path,
) -> None:
    """Main function to orchestrate the usage description generation process."""
    # Set up logging
    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        # Read source code file
        source_code = source_file.read_text()

        # Construct the prompt
        system_prompt = construct_system_prompt(source_code)

        # Get API Key
        api_key = os.environ.get(api_key_env_var)
        if not api_key:
            logger.error(f"Error: {api_key_env_var} environment variable not set.")
            sys.exit(1)

        # Call the LLM
        response = await call_llm(
            system_prompt=system_prompt,
            english_description="Generate a usage description for the provided source code.",
            model_name=llm_model,
            api_key=api_key,
            response_schema=UsageDescription,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )

        # Extract the usage description
        usage_description = cast(UsageDescription, response.parsed).usage_description

        # Read the raw header file
        raw_header_content = raw_header_file.read_text()

        # Format as a javadoc comment first, then append the raw header content
        javadoc_comment = (
            "/**\n* "
            + usage_description.replace("\n", "\n* ").replace("*/", "* /")
            + "\n*/\n"
        )
        formatted_output = javadoc_comment + raw_header_content

        # Write the output
        with open(output_file, "w") as f:
            f.write(formatted_output)

        # Log success message with usage stats
        logger.info(f"Successfully generated usage description at {output_file}")
        logger.info(f"Usage stats: {json.dumps(response.usage)}")

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
