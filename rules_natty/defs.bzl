load("@rules_python//python:defs.bzl", "py_binary", "py_library") # Creating a py_library wrapper

"""Provider for Natty library information."""
NattyInfo = provider(
    fields = {
        "generated_py_source": "The File object representing the generated Python source code.",
    },
    doc = "Provides information about a Natty-generated library.",
)

# //tools/rules_vibe/defs.bzl (continued)

def _natty_library_impl(ctx):
    """Implementation of the natty_library rule."""

    output_py = ctx.actions.declare_file(ctx.label.name + ".py")
    input_txt = ctx.file.src  # Assuming allow_single_file=True

    # Collect generated Python sources from direct dependencies
    dep_py_files = []
    for dep in ctx.attr.deps:
        if NattyInfo in dep:
            dep_py_files.append(dep[NattyInfo].generated_py_source)

    # Prepare arguments for the LLM caller script
    args = ctx.actions.args()
    args.add("--input_txt", input_txt.path)
    args.add("--output_py", output_py.path)
    args.add_all("--dep_py", [f.path for f in dep_py_files])
    # Add any other necessary args: API endpoint, model name, maybe API key path?
    # SECURITY WARNING: Avoid passing API keys directly on the command line.
    # Use environment variables via ctx.actions.run(..., environments = ...)
    # or have the script read from a secure location/config.
    args.add("--llm_model", ctx.attr.llm_model)
    args.add("--temperature", ctx.attr.temperature)
    args.add("--max_output_tokens", ctx.attr.max_output_tokens)

    # Define the inputs for the action
    inputs = [input_txt] + dep_py_files + [ctx.executable._nattyc]
    # If the caller script needs other files (e.g., config), add them too.

    # Define the action to run the LLM caller script
    ctx.actions.run(
        executable = ctx.executable._nattyc,
        arguments = [args],
        inputs = depset(inputs), # Use depset for efficiency
        outputs = [output_py],
        progress_message = "Generating Python code for %s using Natty" % ctx.label,
        mnemonic = "Natty",
        # WARNING: requires-network can disable sandboxing & affect caching/remote execution.
        execution_requirements = {"requires-network": "True"},
        # Enable LLM_API_KEY env var to be passed along to nattyc via --action_env=LLM_API_KEY=foo
        use_default_shell_env = True,
    )

    # Return providers:
    # - DefaultInfo: Makes the generated .py file the default output.
    # - NattyInfo: Passes the generated source file to dependents.
    # - PyInfo: (Optional but recommended) Makes this behave like a standard py_library
    #           for other Bazel Python rules. Creating PyInfo correctly can be complex,
    #           involving transitive sources, deps, etc. Start simple first.
    return [
        DefaultInfo(files = depset([output_py])),
        NattyInfo(generated_py_source = output_py),
        # Simple PyInfo example (might need adjustment based on actual needs):
        # PyInfo(
        #     transitive_sources = depset([output_py], transitive = [dep[PyInfo].transitive_sources for dep in ctx.attr.deps if PyInfo in dep]),
        #     # Forward deps if necessary, or handle imports within generated code.
        # ),
    ]

_natty_library_rule = rule(
    implementation = _natty_library_impl,
    attrs = {
        "src": attr.label(
            allow_single_file= [".txt", ".md"],
            mandatory = True,
            doc = "The single textual file containing English behavior description.",
        ),
        "deps": attr.label_list(
            providers = [[NattyInfo]], # Dependents must provide VibeInfo
            doc = "List of other natty_library targets this target depends on.",
        ),
        "llm_model": attr.string(
            default = "models/gemini-2.5-flash-preview-04-17",
            doc = "Identifier for the LLM model to use. Currently supports Gemini models only.",
        ),
        "temperature": attr.string(
            default = "0.2",
            doc = "A floating point number in the range [0.0, 2.0] for the temperature to pass to the LLM. Lower number implies less creativity by way of less randomness in sampling next token."
        ),
        "max_output_tokens": attr.int(
            default = 8192,
            doc = "Maximum output tokens",
        ),
        "_nattyc": attr.label(
            default = Label("//python/nattyc:main"), # Path to your script
            cfg = "exec", # Runs in the execution configuration
            executable = True,
            allow_files = True,
            doc = "Internal: The tool used to call the LLM for code generation.",
        ),
    },
    outputs = {
        # This isn't strictly needed if declared in the implementation,
        # but can be good practice. Bazel infers it from declare_file.
        # "py_output": "%{name}.py"
    },
    doc = "Generates a Python library from Natural Language text using an LLM.",
)


def natty_library(name, src, deps = [], llm_model = None, visibility = None, tags = []):
    """
    User-facing macro to generate a Python library from English text.

    Args:
      name: The name of the target.
      src: The single .txt file with the English description.
      deps: List of other vibe_library targets this depends on.
      llm_model: Optional; overrides the default LLM model.
      visibility: Standard Bazel visibility.
      tags: Standard Bazel tags.
    """

    # Define the name for the internal code generation rule
    codegen_rule_name = name + "_codegen"

    # Call the internal rule to perform the code generation
    _natty_library_rule(
        name = codegen_rule_name,
        src = src,
        deps = [dep + "_codegen" for dep in deps],
        llm_model = llm_model, # Pass through optional model override
        tags = tags + ["natty_codegen_internal"], # Add internal tag if desired
        visibility = visibility,
    )

    # Wrap the output in a standard py_library (better integration)
    # This makes `:my_vibe_lib` directly consumable as a Python dependency.
    py_library(
        name = name,
        srcs = [":" + codegen_rule_name], # Use the output of the codegen rule
        # How should deps be handled?
        # Simple case: Assume py_library deps mirror vibe_library deps.
        # Complex case: You might need a separate `py_deps` attribute.
        deps = deps,
        visibility = visibility,
        tags = tags,
    )

def natty_binary(name, src, deps = [], llm_model = None, visibility = None, tags = []):
    """
    User-facing macro to generate a Python library from English text.

    Args:
      name: The name of the target.
      src: The single .txt file with the English description.
      deps: List of other vibe_library targets this depends on.
      llm_model: Optional; overrides the default LLM model.
      visibility: Standard Bazel visibility.
      tags: Standard Bazel tags.
    """

    # Define the name for the internal code generation rule
    codegen_rule_name = name + "_codegen"

    # Call the internal rule to perform the code generation
    _natty_library_rule(
        name = codegen_rule_name,
        src = src,
        deps = [dep + "_codegen" for dep in deps],
        llm_model = llm_model, # Pass through optional model override
        tags = tags + ["natty_codegen_internal"], # Add internal tag if desired
        visibility = visibility,
    )

    # Wrap the output in a standard py_library (better integration)
    # This makes `:my_vibe_lib` directly consumable as a Python dependency.
    py_binary(
        name = name,
        srcs = [":" + codegen_rule_name], # Use the output of the codegen rule
        main = ":" + codegen_rule_name + ".py",
        # How should deps be handled?
        # Simple case: Assume py_library deps mirror vibe_library deps.
        # Complex case: You might need a separate `py_deps` attribute.
        deps = deps,
        visibility = visibility,
        tags = tags,
    )
