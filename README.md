<picture align="left">
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/JasonSteving99/Natty/refs/heads/main/images/Natty%20Logo.png" width=500>
  <img src="https://raw.githubusercontent.com/JasonSteving99/Natty/refs/heads/main/images/Natty%20Logo.png" width=500 height=500>
</picture>

## What is Natty?

Natty is a Bazel-integrated framework that uses LLMs to generate entire programs from natural language descriptions of its components. Describe what you want a component to do in plain English, and Natty will translate it into a working program.

## Why Natty?

Natty enables a more architectural approach to LLM-based code generation:

- **Component-Focused Architecture**: Break down your system into well-defined components with clear boundaries, allowing the LLM to focus on one specific problem at a time
- **Dependency-Aware Generation**: Explicitly define dependencies between components, giving the LLM precise context about what it can use
- **Constrained Problem Scope**: By focusing on smaller, well-defined units of work, the LLM produces higher quality, more reliable code
- **Bazel-Powered Caching**: Leverages Bazel's dependency resolution capabilities to cache generated components, avoiding unnecessary regeneration when dependencies haven't changed
- **Iterative Refinement**: Easily refine your natural language descriptions to get exactly the implementation you need

## Installation

### Prerequisites

- Bazel
- A Gemini API key (environment variable: `LLM_API_KEY`)

### Setup

For now, simply clone the Natty repository:

```bash
git clone https://github.com/JasonSteving99/Natty.git
```

All Python dependencies are handled automatically through the `natty_library` and `natty_binary` rules.

## Usage

### Basic Usage

1. Create a markdown or text file with a natural language description of what you want your code to do:

```markdown
# my_function.md
A Python function that calculates the factorial of a number recursively.
```

2. Create a BUILD file with a `natty_library` rule:

```python
load("@natty//rules_natty:defs.bzl", "natty_library")

natty_library(
    name = "factorial",
    src = "my_function.md",
)
```

3. Build and use your generated code:

```bash
bazel build :factorial --action_env=LLM_API_KEY=<your_gemini_api_key>
```

### Creating Executable Programs

Use `natty_binary` to create executable Python programs:

```python
load("@natty//rules_natty:defs.bzl", "natty_binary")

natty_binary(
    name = "factorial_app",
    src = "my_app.md",
    deps = [":factorial"],
)
```

Then run it with:

```bash
bazel run :factorial_app --action_env=LLM_API_KEY=<your_gemini_api_key>
```

## Examples

### Pretty Printer CLI Example

Natty handles dependencies between generated components, as shown in this example:

```python
# examples/pretty_printer_cli/BUILD
load("//rules_natty:defs.bzl", "natty_binary", "natty_library")

natty_library(
    name = "pretty_print",
    src = "pretty_print.md",
)

natty_binary(
    name = "cli_printer",
    src = "cli_printer.md",
    deps = [":pretty_print"],
)
```

Where:
- `pretty_print.md` contains: "A simple python function that prints the given string inside a box."
- `cli_printer.md` contains: "This is going to be a simple command line app that will just act like a REPL that takes in any text from the user and then pretty prints it using its dependency."

The generated code for `cli_printer` will properly import and use the code from `pretty_print`.

Run it with:

```bash
bazel run examples/pretty_printer_cli:cli_printer --action_env=LLM_API_KEY=<your_gemini_api_key>
```

## Advanced Configuration

You can customize the LLM model and parameters:

```python
natty_library(
    name = "complex_algorithm",
    src = "complex_algorithm.md",
    llm_model = "models/gemini-2.5-pro",  # Use a more powerful model
    temperature = "0.7",  # Increase creativity (0.0 to 2.0)
    max_output_tokens = 16384,  # Increase token limit for complex generations
)
```

## How It Works

1. You write natural language descriptions in markdown or text files
2. Natty sends these descriptions to the Gemini API
3. The LLM generates appropriate Python code with:
   - Proper type hints
   - Docstrings
   - Error handling
   - Best practices
4. The generated code is integrated into your Bazel build system
5. Dependencies between components are maintained

## Limitations

- Currently supports Python code generation only
- Requires network access for code generation (affects caching/remote execution)

- Currently limited to Gemini API (support for additional LLM providers coming soon)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
