# //tools/rules_vibe/llm_caller.py
import json
import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import asyncclick as click

# Import the new Google Gen AI SDK
from google import genai
from google.genai.types import (
    GenerateContentConfig,
    HarmBlockThreshold,
    HarmCategory,
    SafetySetting,
)
from pydantic import BaseModel, Field


@dataclass
class LlmResponse:
    """Data class to standardize LLM response format."""

    text: str
    model: str
    usage: Dict[str, int]
    finish_reason: str | None


class GeneratedCode(BaseModel):
    reasoning: str = Field(description="Use this field to plan out your solution.")
    generated_code: str = Field(
        description="The generated source code implementation. MUST ONLY INCLUDE THE CODE ITSELF AND NOTHING ELSE."
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


def construct_system_prompt(dep_py_contents: Dict[str, str]) -> str:
    """Constructs the system prompt for the LLM.

    Args:
        dep_py_contents: Dictionary mapping dependency names to their code contents

    Returns:
        A formatted system prompt string for the LLM
    """
    dependencies_section = ""
    if dep_py_contents:
        dependencies_section += """

The following Python code snippets are dependencies that can be used in the generated implementation. 
DO NOT DUPLICATE THE CODE IN THESE DEPENDENCIES. 
Ensure the generated code correctly interacts with them via import statements if necessary:

"""
        for name, content in dep_py_contents.items():
            dependencies_section += f"# Dependency: {name}\n{content}\n---\n"

    # Emphasize quality requirements
    return f"""You are a helpful assistant that translates English descriptions into Python code.{dependencies_section}

Requirements for the generated code:
1. Add proper type hints to all functions and variables
2. Use Python 3.10+ syntax (e.g., use `list[str]` instead of `List[str]`)
3. Use union syntax in Python types (e.g., `str | None` instead of `Optional[str]`)
4. Include docstrings for all functions and classes
5. Add appropriate error handling
6. Ensure the code is well-structured and follows best practices

Generate Python code for the natural language description the user will provide.
"""


async def call_llm(
    *,
    system_prompt: str,
    english_description: str,
    model_name: str,
    api_key: str,
    temperature: float = 0.2,
    max_output_tokens: int = 8192,
) -> LlmResponse:
    """Call the Gemini API to generate code.

    Args:
        prompt: The formatted prompt to send to the LLM
        model_name: The specific Gemini model to use
        api_key: API key for authentication
        temperature: Sampling temperature (lower = more deterministic)
        max_output_tokens: Maximum tokens in the response

    Returns:
        An LlmResponse object containing the generated code and metadata

    Raises:
        ValueError: If required parameters are missing or invalid
        RuntimeError: If the API call fails
    """
    logger = logging.getLogger(__name__)

    logger.debug(f"--- SYSTEM PROMPT for {model_name} ---")
    logger.debug(
        system_prompt
    )  # Use debug to avoid showing the entire prompt in normal operation
    logger.debug("--- END SYSTEM PROMPT ---")

    if not api_key:
        raise ValueError("Error: LLM_API_KEY not set.")

    try:
        # Create a client instance
        client = genai.Client(api_key=api_key)

        # Generate the content
        response = await client.aio.models.generate_content(
            model=model_name,
            contents=english_description,
            config=GenerateContentConfig(
                system_instruction=system_prompt,
                candidate_count=1,
                temperature=temperature,
                max_output_tokens=max_output_tokens,
                # Set up safety settings - allow code generation
                safety_settings=[
                    SafetySetting(
                        category=category,
                        threshold=HarmBlockThreshold.BLOCK_ONLY_HIGH,
                    )
                    for category in HarmCategory
                    if category is not HarmCategory.HARM_CATEGORY_UNSPECIFIED
                ],
                response_mime_type="application/json",
                response_schema=GeneratedCode.model_json_schema(),
            ),
        )

        # Handle potential content filtering
        if response.candidates and response.candidates[0].finish_reason == "SAFETY":
            raise RuntimeError("Content was filtered due to safety concerns")

        # Extract the text from the response
        text = ""
        if response.candidates:
            candidate = response.candidates[0]
            if candidate.content and candidate.content.parts:
                raw_response_text = "".join(
                    part.text for part in candidate.content.parts if part.text
                )
                # Parse the LLM's response and extract ONLY the generated code - the reasoning was
                # just for the model's own benefit.
                text = GeneratedCode.model_validate_json(
                    raw_response_text
                ).generated_code

        # Create usage stats dictionary (estimate, as Gemini might not provide exact counts)
        usage = {
            "input_tokens": (len(system_prompt) + len(english_description))
            // 4,  # Rough estimate
            "completion_tokens": len(text) // 4,  # Rough estimate
            "total_tokens": (len(system_prompt) + len(english_description) + len(text))
            // 4,  # Rough estimate
        }

        # Get finish reason
        finish_reason = None
        if response.candidates:
            finish_reason = response.candidates[0].finish_reason

        return LlmResponse(
            text=text, model=model_name, usage=usage, finish_reason=finish_reason
        )

    except Exception as e:
        logger.error(f"Error calling Gemini API: {str(e)}")
        raise RuntimeError(f"Failed to generate code: {str(e)}")


def validate_generated_code(code: str) -> bool:
    """Basic validation of generated Python code.

    Args:
        code: The generated Python code to validate

    Returns:
        True if validation passes, False otherwise
    """
    # Check if the code is empty
    if not code.strip():
        return False

    # Check if it compiles
    try:
        compile(code, "<string>", "exec")
        return True
    except SyntaxError:
        return False


def read_dependencies(dep_paths: List[Path]) -> Dict[str, str]:
    """Read all dependency Python files.

    Args:
        dep_paths: List of paths to dependency Python files

    Returns:
        Dictionary mapping dependency names to their code contents
    """
    dep_py_contents: Dict[str, str] = {}

    for dep_path in dep_paths:
        dep_name = dep_path.as_posix()
        dep_py_contents[dep_name] = dep_path.read_text()

    return dep_py_contents


@click.command(help="Generate Python code from English descriptions using LLMs")
@click.option(
    "--input_txt",
    type=click.Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
        path_type=Path,
        resolve_path=True,
        readable=True,
    ),
    required=True,
    help="Path to input text description file",
)
@click.option(
    "--output_py",
    type=click.Path(
        file_okay=True,
        dir_okay=False,
        path_type=Path,
        resolve_path=True,
        writable=True,
    ),
    required=True,
    help="Path to output Python file",
)
@click.option(
    "--dep_py",
    multiple=True,
    type=click.Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
        path_type=Path,
        resolve_path=True,
        readable=True,
    ),
    default=[],
    help="Paths to dependency Python files",
)
@click.option(
    "--llm_model", required=True, help="LLM model name (e.g., gemini-2.0-flash-001)"
)
@click.option(
    "--temperature", type=float, default=0.2, help="Sampling temperature (0.0-1.0)"
)
@click.option(
    "--max_output_tokens", type=int, default=8192, help="Maximum output tokens"
)
@click.option(
    "--api_key_env_var",
    default="LLM_API_KEY",
    help="Environment variable name for API key",
)
async def main(
    input_txt: Path,
    output_py: Path,
    dep_py: list[Path],
    llm_model: str,
    temperature: float,
    max_output_tokens: int,
    api_key_env_var: str,
) -> None:
    """Main function to orchestrate the code generation process."""
    # Set up logging
    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        # Read input English text
        english_text = input_txt.read_text()

        # Read dependency Python code
        dep_py_contents = read_dependencies(dep_py)

        # Construct the prompt
        system_prompt = construct_system_prompt(dep_py_contents)

        # Get API Key
        api_key = os.environ.get(api_key_env_var)
        if not api_key:
            logger.error(f"Error: {api_key_env_var} environment variable not set.")
            sys.exit(1)

        # Call the LLM
        response = await call_llm(
            system_prompt=system_prompt,
            english_description=english_text,
            model_name=llm_model,
            api_key=api_key,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )

        # Validate the generated code
        if not validate_generated_code(response.text):
            logger.error(
                f"Generated code failed validation. Generated code:\n\n{response.text}"
            )
            sys.exit(1)

        # Write the output
        with open(output_py, "w") as f:
            f.write(response.text)

        # Log success message with usage stats
        logger.info(f"Successfully generated {output_py}")
        logger.info(f"Usage stats: {json.dumps(response.usage)}")

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
