# //tools/rules_vibe/llm_caller.py
import json
import logging
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Literal, cast

import asyncclick as click

# Import the new Google Gen AI SDK
from pydantic import BaseModel, Field

from python.nattyc.llm import call_llm


@dataclass
class ValidationResult:
    """Data class to hold validation result."""

    is_valid: bool
    error_message: str | None = None


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
    resource_files: list[Path] = [],
    target_type: Literal["library", "binary"] = "library",
) -> str:
    """Constructs the system prompt for the LLM.

    Args:
        language: The target programming language
        dep_files_contents: Dictionary mapping dependency names to their code contents
        dep_doc_contents: Dictionary mapping documentation names to their contents
        output_file: The output file path, needed for Java to enforce class naming conventions
        package: The package that can be used for importing the generated file
        resource_files: List of resource files that will be available to the generated program
        target_type: Whether this is a "library" or "binary" target

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

    resource_files_section = ""
    if resource_files:
        resource_files_section += """

The following resource files will be available to the generated program:

"""
        for resource_path in resource_files:
            resource_name = resource_path.name
            resource_files_section += f"# Resource file: {resource_name}\n"

    # Choose language-specific requirements
    if language == Language.PYTHON:
        lang_intro = "You are a helpful assistant that translates English descriptions into Python code."

        resource_instruction = ""
        if resource_files:
            resource_instruction = """
CRITICAL: When accessing resource files, you should read them using appropriate file handling methods.
The following resource files are available:

"""
            for resource_path in resource_files:
                resource_instruction += f"- {str(resource_path)}\n"

        # Add specific instructions based on target type
        binary_instruction = ""
        if target_type == "binary":
            binary_instruction = """
CRITICAL: You MUST create an executable Python program with a `if __name__ == "__main__":` block.
"""

        requirements = f"""
Requirements for the generated code:
1. Add proper type hints to all functions and variables
2. Use Python 3.10+ syntax (e.g., use `list[str]` instead of `List[str]`)
3. Use union syntax in Python types (e.g., `str | None` instead of `Optional[str]`)
4. Include docstrings for all functions and classes
5. Add appropriate error handling
6. Ensure the code is well-structured and follows best practices{resource_instruction}{binary_instruction}

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

        resource_instruction = ""
        if resource_files:
            resource_instruction = """
CRITICAL: When accessing resource files, you MUST use the following method to load each resource as an InputStream:

"""
            for resource_path in resource_files:
                resource_instruction += f"For resource '{str(resource_path)}', use:\nInputStream is = {class_name}.class.getResourceAsStream(\"/{str(resource_path)}\");\n\n"

        # Add specific instructions based on target type
        binary_instruction = ""
        if target_type == "binary":
            binary_instruction = f"""
CRITICAL: This is a Java executable. Your code MUST include a `public static void main(String[] args)` method in the {class_name} class.
The main method should serve as the entry point for the program and provide complete functionality for a standalone application.
"""

        requirements = f"""
Requirements for the generated code:
1. Use Java 8 features when appropriate
2. Include proper exception handling
3. Add JavaDoc comments for all classes, methods, and fields
4. Follow Java naming conventions (camelCase for variables/methods, PascalCase for classes){class_instruction}{package_instruction}
5. Ensure imports come after the package declaration
6. Ensure the code is well-structured and follows best practices{resource_instruction}{binary_instruction}

Generate Java code for the natural language description the user will provide.
"""
    else:
        raise ValueError(f"Unsupported language: {language}")

    return f"{lang_intro}{dependencies_section}{documentation_section}{resource_files_section}{requirements}"


def validate_generated_code(
    code: str,
    language: Language,
    output_file: Path | None = None,
    java_dep_jars: list[Path] = [],
) -> ValidationResult:
    """Basic validation of generated code.

    Args:
        code: The generated code to validate
        language: The programming language of the code
        output_file: The path where the code has been written for Java compilation
        java_dep_jars: List of jar files needed for Java compilation

    Returns:
        ValidationResult containing validity and any error message
    """
    # Check if the code is empty
    if not code.strip():
        return ValidationResult(
            is_valid=False, error_message="Generated code is empty."
        )

    if language == Language.PYTHON:
        # Check if Python code compiles
        try:
            compile(code, "<string>", "exec")
            return ValidationResult(is_valid=True)
        except SyntaxError as e:
            return ValidationResult(
                is_valid=False, error_message=f"Python syntax error: {str(e)}"
            )
    elif language == Language.JAVA:
        # First, basic validation to catch obvious issues
        if not ("class " in code or "interface " in code or "enum " in code):
            return ValidationResult(
                is_valid=False,
                error_message="Java code must contain at least one class, interface, or enum.",
            )

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

                # If compilation failed, capture the errors
                if result.returncode != 0:
                    error_message = "Java compilation failed:\n"
                    if result.stdout:
                        error_message += f"Compiler stdout: {result.stdout}\n"
                    if result.stderr:
                        error_message += f"Compiler stderr: {result.stderr}"

                    logging.error(
                        f"Java compilation failed with exit code {result.returncode}"
                    )
                    logging.error(f"Compilation command: {' '.join(cmd)}")
                    logging.error(error_message)

                    return ValidationResult(is_valid=False, error_message=error_message)

                return ValidationResult(is_valid=True)
            except Exception as e:
                # If any exception occurs during compilation, log it and return with error
                error_message = f"Error during Java compilation: {str(e)}"
                logging.error(error_message)
                return ValidationResult(is_valid=False, error_message=error_message)
        else:
            # Fallback to basic validation if no output file is provided
            if "class " in code or "interface " in code or "enum " in code:
                return ValidationResult(is_valid=True)
            else:
                return ValidationResult(
                    is_valid=False,
                    error_message="Java code must contain at least one class, interface, or enum.",
                )
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
    "--target_type",
    type=click.Choice(["library", "binary"]),
    default="library",
    help="Whether this target is a library or a binary executable",
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
    "--resource_file",
    multiple=True,
    type=click.Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
        path_type=Path,
        readable=True,
    ),
    default=[],
    help="Paths to resource files that will be available to the generated program.",
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
    target_type: Literal["library", "binary"],
    package: str,
    dep_file: list[Path],
    dep_doc: list[Path],
    java_dep_jar: list[Path],
    resource_file: list[Path],
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
            resource_files=resource_file,
            target_type=target_type,
        )

        # Get API Key
        api_key = os.environ.get(api_key_env_var)
        if not api_key:
            logger.error(f"Error: {api_key_env_var} environment variable not set.")
            sys.exit(1)

        # Initialize variables for retry loop
        max_retries = 5
        retries = 0
        success = False
        validation_result = None
        response = None

        while retries <= max_retries:
            # Call the LLM
            response = await call_llm(
                system_prompt=system_prompt,
                english_description=english_text,
                model_name=llm_model,
                api_key=api_key,
                response_schema=GeneratedCode,
                temperature=temperature,
                max_output_tokens=max_output_tokens,
            )
            generated_code = cast(GeneratedCode, response.parsed).generated_code

            # Write the output with appropriate language-specific header
            # This ensures the file exists for Java compilation validation
            with open(output_file, "w") as f:
                if language == Language.PYTHON:
                    f.write("# Usage: Import from this package using the following:\n")
                    f.write(f"# from {package} import <name to import>\n\n")
                # For Java, the package declaration should already be in the code
                f.write(generated_code)

            # Validate the generated code
            if language == Language.JAVA:
                # For Java, pass the output file and jar dependencies for proper compilation
                validation_result = validate_generated_code(
                    generated_code, language, output_file, java_dep_jar
                )
            else:
                # For Python, we can validate without the file
                validation_result = validate_generated_code(generated_code, language)

            # If validation passed, mark as success and break out of the retry loop
            if validation_result.is_valid:
                success = True
                break

            # Increment retry counter and log retry attempt
            retries += 1
            logger.info(f"Validation failed. Retry {retries}/{max_retries}...")

            # If we still have retries left, update the system prompt with error feedback
            if retries < max_retries:
                error_feedback = f"""

IMPORTANT: Your previous attempt at generating code failed validation with the following error:

{validation_result.error_message}

Here is your previous code that needs to be fixed:

```
{generated_code}
```

Please fix the issues and provide a COMPLETE implementation of the code, not just the changes.
Make sure your code handles the errors mentioned above.
"""
                # Update system prompt with error feedback for retry
                system_prompt = system_prompt + error_feedback

        # After the loop, check if we succeeded or exhausted all retries
        if success:
            # Log success message with usage stats
            logger.info(f"Successfully generated {output_file}")
            if response:
                logger.info(f"Usage stats: {json.dumps(response.usage)}")
        else:
            # Log the final error and exit with failure
            if validation_result:
                logger.error(
                    f"Generated code failed validation after {max_retries} attempts. Last error: {validation_result.error_message}"
                )
            sys.exit(1)

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
