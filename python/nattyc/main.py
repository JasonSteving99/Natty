# //tools/rules_vibe/llm_caller.py
import json
import logging
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, cast

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


class Language(str):
    """Enum-like class for supported programming languages."""

    PYTHON = "python"
    JAVA = "java"


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


def construct_system_prompt(
    language: Language,
    dep_files_contents: dict[str, str],
    dep_doc_contents: dict[str, str],
    output_file: Path,
    package: str,
) -> str:
    """Constructs the system prompt for the LLM.

    Args:
        language: The target programming language
        dep_files_contents: Dictionary mapping dependency names to their code contents
        dep_doc_contents: Dictionary mapping documentation names to their contents
        output_file: The output file path, needed for Java to enforce class naming conventions

    Returns:
        A formatted system prompt string for the LLM
    """
    dependencies_section = ""
    if dep_files_contents:
        if language == Language.PYTHON:
            dependencies_section += """

The following Python code snippets are dependencies that can be used in the generated implementation. 
DO NOT DUPLICATE THE CODE IN THESE DEPENDENCIES. 
Ensure the generated code correctly interacts with them via import statements if necessary:

"""
        elif language == Language.JAVA:
            dependencies_section += """

The following Java code snippets are dependencies that can be used in the generated implementation. 
DO NOT DUPLICATE THE CODE IN THESE DEPENDENCIES. 
Ensure the generated code correctly interacts with them via import statements if necessary:

"""
        for name, content in dep_files_contents.items():
            dependencies_section += f"# Dependency: {name}\n{content}\n---\n"

    documentation_section = ""
    if dep_doc_contents:
        documentation_section += """

The following is collected documentation that should be referenced in planning the approach. This
documentation includes necessary information for correct implementation:

"""
        for name, content in dep_doc_contents.items():
            documentation_section += f"# Documentation: {name}\n{content}\n---\n"

    # Choose language-specific requirements
    if language == Language.PYTHON:
        lang_intro = "You are a helpful assistant that translates English descriptions into Python code."
        requirements = """
Requirements for the generated code:
1. Add proper type hints to all functions and variables
2. Use Python 3.10+ syntax (e.g., use `list[str]` instead of `List[str]`)
3. Use union syntax in Python types (e.g., `str | None` instead of `Optional[str]`)
4. Include docstrings for all functions and classes
5. Add appropriate error handling
6. Ensure the code is well-structured and follows best practices

Generate Python code for the natural language description the user will provide.
"""
    elif language == Language.JAVA:
        lang_intro = "You are a helpful assistant that translates English descriptions into Java code."

        # Extract the base filename without extension for Java class naming
        class_name = output_file.stem
        class_instruction = f"""
CRITICAL: You MUST name the primary public class '{class_name}' to match the output file name. 
This is a strict Java requirement when the class is defined in a file named '{class_name}.java'.
"""

        # Add package instruction - package is the Bazel package path relative to workspace root
        package_instruction = f"""
CRITICAL: The Java code MUST start with 'package {package};' as the first line of the file (after any comments).
This package declaration is required by the Java compiler and must exactly match the Bazel workspace path.
"""

        requirements = f"""
Requirements for the generated code:
1. Use Java 8 features when appropriate
2. Include proper exception handling
3. Add JavaDoc comments for all classes, methods, and fields
4. Follow Java naming conventions (camelCase for variables/methods, PascalCase for classes){class_instruction}{package_instruction}
5. Ensure imports come after the package declaration
6. Ensure the code is well-structured and follows best practices

Generate Java code for the natural language description the user will provide.
"""
    else:
        raise ValueError(f"Unsupported language: {language}")

    return f"{lang_intro}{dependencies_section}{documentation_section}{requirements}"


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
                response_schema=GeneratedCode,
            ),
        )

        # Handle potential content filtering
        if response.candidates and response.candidates[0].finish_reason == "SAFETY":
            raise RuntimeError("Content was filtered due to safety concerns")

        # Extract the text from the response
        text = ""
        if response.parsed:
            # Parse the LLM's response and extract ONLY the generated code - the reasoning was
            # just for the model's own benefit.
            text = cast(GeneratedCode, response.parsed).generated_code

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


def validate_generated_code(
    code: str,
    language: Language,
    output_file: Path | None = None,
    java_dep_jars: list[Path] = [],
) -> bool:
    """Basic validation of generated code.

    Args:
        code: The generated code to validate
        language: The programming language of the code
        output_file: The path where the code has been written for Java compilation
        java_dep_jars: List of jar files needed for Java compilation

    Returns:
        True if validation passes, False otherwise
    """
    # Check if the code is empty
    if not code.strip():
        return False

    if language == Language.PYTHON:
        # Check if Python code compiles
        try:
            compile(code, "<string>", "exec")
            return True
        except SyntaxError:
            return False
    elif language == Language.JAVA:
        # First, basic validation to catch obvious issues
        if not ("class " in code or "interface " in code or "enum " in code):
            return False

        # For proper Java syntax validation, we'll compile the code with javac
        if output_file:
            try:
                # Construct the javac command
                cmd = ["javac", output_file.as_posix()]

                # Add classpath with dependencies if provided
                if java_dep_jars:
                    classpath = ":".join(jar.as_posix() for jar in java_dep_jars)
                    cmd.extend(["-classpath", classpath])

                # Run the javac command
                result = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False,
                    text=True,
                )

                # If compilation failed, log the errors
                if result.returncode != 0:
                    logging.error(
                        f"Java compilation failed with exit code {result.returncode}"
                    )
                    logging.error(f"Compilation command: {' '.join(cmd)}")
                    if result.stdout:
                        logging.error(f"Compiler stdout: {result.stdout}")
                    if result.stderr:
                        logging.error(f"Compiler stderr: {result.stderr}")

                return result.returncode == 0
            except Exception as e:
                # If any exception occurs during compilation, log it and return False
                logging.error(f"Error during Java compilation: {str(e)}")
                return False
        else:
            # Fallback to basic validation if no output file is provided
            return "class " in code or "interface " in code or "enum " in code
    else:
        raise ValueError(f"Unsupported language: {language}")


def read_dependencies(dep_paths: List[Path]) -> Dict[str, str]:
    """Read all dependency files.

    Args:
        dep_paths: List of paths to dependency files

    Returns:
        Dictionary mapping dependency names to their code contents
    """
    dep_contents: Dict[str, str] = {}

    for dep_path in dep_paths:
        dep_name = dep_path.as_posix()
        dep_contents[dep_name] = dep_path.read_text()

    return dep_contents


@click.command(help="Generate code from English descriptions using LLMs")
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
    "--output_file",
    type=click.Path(
        file_okay=True,
        dir_okay=False,
        path_type=Path,
        resolve_path=True,
        writable=True,
    ),
    required=True,
    help="Path to output code file",
)
@click.option(
    "--language",
    type=click.Choice([Language.PYTHON, Language.JAVA]),
    default=Language.PYTHON,
    help="Target programming language",
)
@click.option(
    "--package",
    required=True,
    help="The package that can be used to specify importing this generated file.",
)
@click.option(
    "--dep_file",
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
    help="Paths to dependency code files",
)
@click.option(
    "--dep_doc",
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
    help="Paths to documentation files to be fed to the LLM to aid codegen.",
)
@click.option(
    "--java_dep_jar",
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
    help="Paths to Java dependency jar files needed for compilation.",
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
    output_file: Path,
    language: Language,
    package: str,
    dep_file: list[Path],
    dep_doc: list[Path],
    java_dep_jar: list[Path],
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

        # Read dependency code files
        dep_files_contents = read_dependencies(dep_file)

        # Read docs to seed the LLM with context
        dep_docs_contents = read_dependencies(dep_doc)

        # Construct the prompt
        system_prompt = construct_system_prompt(
            language=language,
            dep_files_contents=dep_files_contents,
            dep_doc_contents=dep_docs_contents,
            output_file=output_file,
            package=package,
        )

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

        # Write the output with appropriate language-specific header first
        # This ensures the file exists for Java compilation validation
        with open(output_file, "w") as f:
            if language == Language.PYTHON:
                f.write("# Usage: Import from this package using the following:\n")
                f.write(f"# from {package} import <name to import>\n\n")
            # For Java, we don't need to add a comment about the package,
            # as the package declaration should already be in the generated code
            f.write(response.text)

        # Now validate the generated code
        if language == Language.JAVA:
            # For Java, pass the output file and jar dependencies for proper compilation
            if not validate_generated_code(
                response.text, language, output_file, java_dep_jar
            ):
                logger.error(
                    f"Generated Java code failed validation/compilation. Generated code:\n\n{response.text}"
                )
                sys.exit(1)
        else:
            # For Python, we can validate without the file
            if not validate_generated_code(response.text, language):
                logger.error(
                    f"Generated code failed validation. Generated code:\n\n{response.text}"
                )
                sys.exit(1)

        # Log success message with usage stats
        logger.info(f"Successfully generated {output_file}")
        logger.info(f"Usage stats: {json.dumps(response.usage)}")

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
