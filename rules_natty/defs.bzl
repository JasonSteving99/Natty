load("@rules_python//python:defs.bzl", "py_binary", "py_library") # Creating a py_library wrapper

"""Provider for Natty library information."""
NattyInfo = provider(
    fields = {
        "generated_source": "The File object representing the generated source code.",
        "language": "The programming language of the generated source code.",
    },
    doc = "Provides information about a Natty-generated library.",
)

# //tools/rules_vibe/defs.bzl (continued)

def _natty_library_impl(ctx):
    """Implementation of the natty_library rule."""

    language = ctx.attr.language
    extension = ".java" if language == "java" else ".py"
    output_file = ctx.actions.declare_file(ctx.label.name + extension)
    input_txt = ctx.file.src  # Assuming allow_single_file=True

    # Collect generated source files from direct dependencies
    dep_files = []
    for dep in ctx.attr.deps:
        if NattyInfo in dep:
            dep_files.append(dep[NattyInfo].generated_source)

    # Prepare arguments for the LLM caller script
    args = ctx.actions.args()
    args.add("--input_txt", input_txt.path)
    args.add("--output_file", output_file.path)
    args.add("--language", language)
    args.add("--package", ctx.attr.package)
    for f in dep_files:
        args.add("--dep_file", f.path)
    for f in ctx.files.docs:
        args.add("--dep_doc", f.path)
    # Add any other necessary args: API endpoint, model name, maybe API key path?
    # SECURITY WARNING: Avoid passing API keys directly on the command line.
    # Use environment variables via ctx.actions.run(..., environments = ...)
    # or have the script read from a secure location/config.
    args.add("--llm_model", ctx.attr.llm_model)
    args.add("--temperature", ctx.attr.temperature)
    args.add("--max_output_tokens", ctx.attr.max_output_tokens)

    # Define the inputs for the action
    inputs = [input_txt] + dep_files + ctx.files.docs + [ctx.executable._nattyc]
    # If the caller script needs other files (e.g., config), add them too.

    # Define the action to run the LLM caller script
    ctx.actions.run(
        executable = ctx.executable._nattyc,
        arguments = [args],
        inputs = depset(inputs), # Use depset for efficiency
        outputs = [output_file],
        progress_message = "Generating %s code for %s using Natty" % (language.capitalize(), ctx.label),
        mnemonic = "Natty",
        # WARNING: requires-network can disable sandboxing & affect caching/remote execution.
        execution_requirements = {"requires-network": "True"},
        # Enable LLM_API_KEY env var to be passed along to nattyc via --action_env=LLM_API_KEY=foo
        use_default_shell_env = True,
    )

    # Return providers:
    # - DefaultInfo: Makes the generated source file the default output.
    # - NattyInfo: Passes the generated source file to dependents.
    return [
        DefaultInfo(files = depset([output_file])),
        NattyInfo(generated_source = output_file, language = language),
    ]

_natty_library_rule = rule(
    implementation = _natty_library_impl,
    attrs = {
        "src": attr.label(
            allow_single_file= [".txt", ".md"],
            mandatory = True,
            doc = "The single textual file containing English behavior description.",
        ),
        "language": attr.string(
            default = "python",
            values = ["python", "java"],
            doc = "The target programming language for code generation.",
        ),
        "package": attr.string(
            mandatory = True,
            doc = "The package that can be used to specify importing this generated file.",
        ),
        "deps": attr.label_list(
            providers = [[NattyInfo]], # Dependents must provide NattyInfo
            doc = "List of other natty_library targets this target depends on.",
        ),
        "docs": attr.label_list(
            allow_files=True,
            doc = "Paths to documentation files to be fed to the LLM to aid codegen.",
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
    doc = "Generates code in a specified language from Natural Language text using an LLM.",
)

def _get_import_str(name, language):
    """
    Create a language-appropriate package/module name for the generated code.
    
    Args:
        name: The target name
        language: The target programming language
        
    Returns:
        String representing the package/module name
    """
    # Leveraging Bazel semantics to produce a unique module name from this target's Bazel package.
    # If this target is declared as //src/com/foo/bar:my_module, then the unique_module_name will be set to
    # 'src$com$foo$bar$my_module' which is guaranteed to be a name that's unique across this entire Bazel project.
    package_name = native.package_name()
    
    if language == "python":
        # Convert slashes to dots for Python module naming
        unique_module_name = package_name.replace('/', '.') + '.' + name + "_codegen"
        return unique_module_name
    elif language == "java":
        # Convert slashes to dots and create proper Java package naming
        unique_package_name = package_name.replace('/', '.')
        return unique_package_name
    else:
        fail("Unsupported language: " + language)


def natty_library(
    name, src, deps = [], py_deps = [], docs = [], llm_model = None, temperature = None, visibility = None, tags = [],
):
    """
    User-facing macro to generate a Python library from English text.

    Args:
      name: The name of the target.
      src: The single .txt or .md file with the English description.
      deps: List of other natty_library targets this depends on.
      py_deps: Additional Python library dependencies.
      docs: Documentation files to provide to the LLM for context.
      llm_model: Optional; overrides the default LLM model.
      temperature: Optional; overrides the default sampling temperature.
      visibility: Standard Bazel visibility.
      tags: Standard Bazel tags.
    """

    # Define the name for the internal code generation rule
    codegen_rule_name = name + "_codegen"

    # Call the internal rule to perform the code generation
    _natty_library_rule(
        name = codegen_rule_name,
        src = src,
        language = "python",  # Fixed to Python for this macro
        package = _get_import_str(name, "python"),
        deps = [dep + "_codegen" for dep in deps],
        docs = docs,
        llm_model = llm_model, # Pass through optional model override
        temperature = temperature,
        tags = tags + ["natty_codegen_internal"], # Add internal tag if desired
        visibility = visibility,
    )

    # Wrap the output in a standard py_library (better integration)
    # This makes `:my_vibe_lib` directly consumable as a Python dependency.
    py_library(
        name = name,
        srcs = [":" + codegen_rule_name], # Use the output of the codegen rule
        deps = deps + py_deps,
        visibility = visibility,
        tags = tags,
    )

def natty_binary(
    name, src, deps = [], py_deps = [], docs = [], llm_model = None, temperature = None, visibility = None, tags = [],
):
    """
    User-facing macro to generate a Python binary executable from English text.

    Args:
      name: The name of the target.
      src: The single .txt or .md file with the English description.
      deps: List of other natty_library targets this depends on.
      py_deps: Additional Python library dependencies.
      docs: Documentation files to provide to the LLM for context.
      llm_model: Optional; overrides the default LLM model.
      temperature: Optional; overrides the default sampling temperature.
      visibility: Standard Bazel visibility.
      tags: Standard Bazel tags.
    """

    # Define the name for the internal code generation rule
    codegen_rule_name = name + "_codegen"

    # Call the internal rule to perform the code generation
    _natty_library_rule(
        name = codegen_rule_name,
        src = src,
        language = "python",  # Fixed to Python for this macro
        package = _get_import_str(name, "python"),
        deps = [dep + "_codegen" for dep in deps],
        docs = docs,
        llm_model = llm_model, # Pass through optional model override
        temperature = temperature,
        tags = tags + ["natty_codegen_internal"], # Add internal tag if desired
        visibility = visibility,
    )

    # Wrap the output in a standard py_binary for execution
    py_binary(
        name = name,
        srcs = [":" + codegen_rule_name], # Use the output of the codegen rule
        main = ":" + codegen_rule_name + ".py",
        deps = deps + py_deps,
        visibility = visibility,
        tags = tags,
    )

def natty_java_library(
    name, src, deps = [], java_deps = [], docs = [], llm_model = None, temperature = None, visibility = None, tags = [],
):
    """
    User-facing macro to generate a Java library from English text.

    Args:
      name: The name of the target.
      src: The single .txt or .md file with the English description.
      deps: List of other natty_java_library targets this depends on.
      java_deps: Additional Java library dependencies.
      docs: Documentation files to provide to the LLM for context.
      llm_model: Optional; overrides the default LLM model.
      temperature: Optional; overrides the default sampling temperature.
      visibility: Standard Bazel visibility.
      tags: Standard Bazel tags.
    """

    # Define the name for the internal code generation rule
    codegen_rule_name = name + "_codegen"

    # Call the internal rule to perform the code generation
    _natty_library_rule(
        name = codegen_rule_name,
        src = src,
        language = "java",  # Fixed to Java for this macro
        package = _get_import_str(name, "java"),
        deps = [dep + "_codegen" for dep in deps],
        docs = docs,
        llm_model = llm_model, # Pass through optional model override
        temperature = temperature,
        tags = tags + ["natty_codegen_internal"], # Add internal tag if desired
        visibility = visibility,
    )

    # Wrap the output in a standard java_library
    native.java_library(
        name = name,
        srcs = [":" + codegen_rule_name], # Use the output of the codegen rule
        deps = deps + java_deps,
        visibility = visibility,
        tags = tags,
    )

def natty_java_binary(
    name, src, deps = [], java_deps = [], docs = [], llm_model = None, temperature = None, visibility = None, tags = [],
    main_class = None,
):
    """
    User-facing macro to generate a Java binary executable from English text.

    Args:
      name: The name of the target.
      src: The single .txt or .md file with the English description.
      deps: List of other natty_java_library targets this depends on.
      java_deps: Additional Java library dependencies.
      docs: Documentation files to provide to the LLM for context.
      main_class: The main class to execute (if not specified, will be determined from the generated code).
      llm_model: Optional; overrides the default LLM model.
      temperature: Optional; overrides the default sampling temperature.
      visibility: Standard Bazel visibility.
      tags: Standard Bazel tags.
    """

    # Define the name for the internal code generation rule
    codegen_rule_name = name + "_codegen"

    # Call the internal rule to perform the code generation
    _natty_library_rule(
        name = codegen_rule_name,
        src = src,
        language = "java",  # Fixed to Java for this macro
        package = _get_import_str(name, "java"),
        deps = [dep + "_codegen" for dep in deps],
        docs = docs,
        llm_model = llm_model, # Pass through optional model override
        temperature = temperature,
        tags = tags + ["natty_codegen_internal"], # Add internal tag if desired
        visibility = visibility,
    )

    # Determine main class if not provided
    if main_class == None:
        # Default to package.ClassName format based on natty's naming convention
        java_package = _get_import_str(name, "java")
        # Extract class name from the end of the name (capitalize first letter)
        class_name = name + "_codegen"
        main_class = java_package + "." + class_name

    # Wrap the output in a standard java_binary for execution
    native.java_binary(
        name = name,
        srcs = [":" + codegen_rule_name], # Use the output of the codegen rule
        main_class = main_class,
        deps = deps + java_deps,
        visibility = visibility,
        tags = tags,
    )
