load("@rules_python//python:defs.bzl", "py_binary", "py_library") # Creating a py_library wrapper
load("@rules_java//java:defs.bzl", "JavaInfo")

"""Provider for Natty library information."""
NattyInfo = provider(
    fields = {
        "generated_source": "The File object representing the generated source code.",
        "language": "The programming language of the generated source code.",
    },
    doc = "Provides information about a Natty-generated library.",
)

"""Provider for Natty Header information."""
NattyHeaderInfo = provider(
    fields = {
        "decompiled_header_source": "The File object representing the decompiled source code of the Turbine-generated hjar.",
    },
    doc = "Provides information about the Header for a Natty-generated library.",
)

def _natty_library_impl(ctx):
    """Implementation of the natty_library rule."""

    language = ctx.attr.language
    extension = ".java" if language == "java" else ".py"
    output_file = ctx.actions.declare_file(ctx.label.name + extension)
    input_txt = ctx.file.src  # Assuming allow_single_file=True

    # Collect generated source files from direct dependencies
    dep_files = []
    for dep in ctx.attr.deps:
        if NattyHeaderInfo in dep:
            dep_files.append(dep[NattyHeaderInfo].decompiled_header_source)

    # Prepare arguments for the LLM caller script
    args = ctx.actions.args()
    args.add("--input_txt", input_txt.path)
    args.add("--output_file", output_file.path)
    args.add("--language", language)
    args.add("--package", ctx.attr.package)
    # Add target_type to indicate if this is a binary or library
    args.add("--target_type", ctx.attr.target_type)
    for f in dep_files:
        args.add("--dep_file", f.path)
    for f in ctx.files.docs:
        args.add("--dep_doc", f.path)
    # Add resource files
    for f in ctx.files.resources:
        args.add("--resource_file", f.short_path)
    # Add any other necessary args: API endpoint, model name, maybe API key path?
    # SECURITY WARNING: Avoid passing API keys directly on the command line.
    # Use environment variables via ctx.actions.run(..., environments = ...)
    # or have the script read from a secure location/config.
    args.add("--llm_model", ctx.attr.llm_model)
    args.add("--temperature", ctx.attr.temperature)
    args.add("--max_output_tokens", ctx.attr.max_output_tokens)
    
    # If the language is Java, pass Java dependency jars for compilation
    if language == "java":
        # Collect paths to the jar files of dependencies
        java_dep_jars = []
        for dep in ctx.attr.java_deps:
            if JavaInfo in dep:
                for jar in dep[JavaInfo].transitive_compile_time_jars.to_list():
                    args.add("--java_dep_jar", jar.path)
                    java_dep_jars.append(jar)

    # Define the inputs for the action
    inputs = [input_txt] + dep_files + ctx.files.docs + ctx.files.resources + [ctx.executable._nattyc]
    
    # If we're dealing with Java, add jar files to inputs
    if language == "java":
        inputs.extend([jar for dep in ctx.attr.java_deps if JavaInfo in dep for jar in dep[JavaInfo].compile_jars.to_list()])
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
        # Also allows the javac command installed on the machine to be used rather than Bazel's
        # builtin javac toolchain. TODO! Make this use the hermetic javac toolchain.
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
        "target_type": attr.string(
            default = "library",
            values = ["library", "binary"],
            doc = "Whether this target is a library or a binary executable.",
        ),
        "deps": attr.label_list(
            providers = [[NattyHeaderInfo]], # Dependents must provide NattyHeaderInfo
            doc = "List of other natty_library targets this target depends on.",
        ),
        "java_deps": attr.label_list(
            doc = "List of Java library dependencies (jar files) used for Java compilation.",
        ),
        "docs": attr.label_list(
            allow_files=True,
            doc = "Paths to documentation files to be fed to the LLM to aid codegen.",
        ),
        "resources": attr.label_list(
            allow_files=True,
            doc = "Resource files that will be available to the generated program.",
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

def _natty_header_impl(ctx):
    # Get the rule name and output file
    name = ctx.label.name
    raw_header_output_file = ctx.actions.declare_file(name + "_raw.java")

    # Prepare arguments for NattyJavaDecompiler.
    args = ctx.actions.args()
    # Find the Turbine-generated hjar of the given java_library() target src.
    hjar = None
    for jar in ctx.attr.src[JavaInfo].transitive_compile_time_jars.to_list():
        hjar_name = "lib{0}-hjar.jar".format(ctx.attr.src.label.name)
        if jar.basename.startswith(hjar_name) and jar.basename.endswith(hjar_name):
            hjar = jar
            args.add("--input-jar", hjar)
            break  # There's only one of these, done looking now.
    if not hjar:
        fail("Failed to find hjar for {0}".format(ctx.attr.src.label.name))

    args.add("--classname", ctx.attr.classname)
    args.add("--outfile", raw_header_output_file)
    
    # Generate the raw header itself. This is technically going to be under-specified for
    # consumption in isolation since it doesn't have any parameter names or javadoc.
    ctx.actions.run(
        executable = ctx.executable._natty_decompiler,
        arguments = [args],
        inputs = depset([hjar]),  # Use depset for efficiency
        outputs = [raw_header_output_file],
        progress_message = "Generating Natty header for {0}".format(ctx.label),
        mnemonic = "NattyJavaDecompiler",
    )

    # Now generate the additional usage context necessary to fill in the gaps in the raw
    # header above.
    output_file = ctx.actions.declare_file(name + ".java")
    natty_src = ctx.attr.natty_src[NattyInfo].generated_source
    args = ctx.actions.args()
    args.add("--source_file", natty_src.path)
    args.add("--raw_header_file", raw_header_output_file.path)
    args.add("--output_file", output_file.path)
    # Add any other necessary args: API endpoint, model name, maybe API key path?
    # SECURITY WARNING: Avoid passing API keys directly on the command line.
    # Use environment variables via ctx.actions.run(..., environments = ...)
    # or have the script read from a secure location/config.
    args.add("--llm_model", ctx.attr.llm_model)
    args.add("--temperature", ctx.attr.temperature)
    args.add("--max_output_tokens", ctx.attr.max_output_tokens)

    # This is generating the usage description and prepending it as a file-level javadoc comment
    # on the raw header generated above so that we can try providing the LLM consumer the 
    # additional necessary context to understand this component's usage via its under-specified 
    # raw header alone.
    ctx.actions.run(
        executable = ctx.executable._natty_usage_description_generator,
        arguments = [args],
        inputs = depset([natty_src, raw_header_output_file]),  # Use depset for efficiency
        outputs = [output_file],
        progress_message = "Generating Natty usage description for {0}".format(ctx.label),
        mnemonic = "NattyUsageDescriptionGenerator",
        # Enable LLM_API_KEY env var to be passed along to nattyc via --action_env=LLM_API_KEY=foo
        # Also allows the javac command installed on the machine to be used rather than Bazel's
        # builtin javac toolchain. TODO! Make this use the hermetic javac toolchain.
        use_default_shell_env = True,
    )
    
    return [
        DefaultInfo(files = depset([raw_header_output_file, output_file])),
        NattyHeaderInfo(decompiled_header_source = output_file),
    ]

_natty_header = rule(
    implementation = _natty_header_impl,
    attrs = {
        "src": attr.label(
            providers = [JavaInfo],
            mandatory = True,
            doc = "Java dep providing JavaInfo so the hjar can be decompiled.",
        ),
        "classname": attr.string(
            mandatory = True,
            doc = "Fully qualified name of the class to decompile.",
        ),
        "natty_src": attr.label(
            providers = [NattyInfo],
            mandatory = True,
            doc = "Natty library source that's having its header generated.",
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
            default = 1024,
            doc = "Maximum output tokens for usage description generation.",
        ),
        "_natty_decompiler": attr.label(
            default = Label("//java/com/natty/decompiler:decompiler"), 
            cfg = "exec", # Runs in the execution configuration
            executable = True,
            allow_files = True,
        ),
        "_natty_usage_description_generator": attr.label(
            default = Label("//python/nattyc:generate_usage_description"), 
            cfg = "exec", # Runs in the execution configuration
            executable = True,
            allow_files = True,
        ),
    },
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
    name, src, deps = [], py_deps = [], docs = [], resources = [], llm_model = None, temperature = None, visibility = None, tags = [],
):
    """
    User-facing macro to generate a Python library from English text.

    Args:
      name: The name of the target.
      src: The single .txt or .md file with the English description.
      deps: List of other natty_library targets this depends on.
      py_deps: Additional Python library dependencies.
      docs: Documentation files to provide to the LLM for context.
      resources: Resource files that will be available to the generated program.
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
        target_type = "library",  # This is a library target
        deps = [dep + "_codegen" for dep in deps],
        docs = docs,
        resources = resources,
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
    name, src, deps = [], py_deps = [], docs = [], resources = [], llm_model = None, temperature = None, visibility = None, tags = [],
):
    """
    User-facing macro to generate a Python binary executable from English text.

    Args:
      name: The name of the target.
      src: The single .txt or .md file with the English description.
      deps: List of other natty_library targets this depends on.
      py_deps: Additional Python library dependencies.
      docs: Documentation files to provide to the LLM for context.
      resources: Resource files that will be available to the generated program.
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
        target_type = "binary",  # This is a binary executable
        deps = [dep + "_codegen" for dep in deps],
        docs = docs,
        resources = resources,
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
    name, src, deps = [], java_deps = [], docs = [], resources = [], max_output_tokens = None, llm_model = None, temperature = None, visibility = None, tags = [],
):
    """
    User-facing macro to generate a Java library from English text.

    Args:
      name: The name of the target.
      src: The single .txt or .md file with the English description.
      deps: List of other natty_java_library targets this depends on.
      java_deps: Additional Java library dependencies.
      docs: Documentation files to provide to the LLM for context.
      resources: Resource files that will be available to the generated program.
      max_output_tokens: Optional; maximum output tokens to generate.
      llm_model: Optional; overrides the default LLM model.
      temperature: Optional; overrides the default sampling temperature.
      visibility: Standard Bazel visibility.
      tags: Standard Bazel tags.
    """

    # Call the internal rule to perform the code generation
    _natty_library_rule(
        name = name,
        src = src,
        language = "java",  # Fixed to Java for this macro
        package = _get_import_str(name, "java"),
        target_type = "library",  # This is a library target
        # Use the simplified headers for codegen instead of the full source.
        deps = [dep + "_natty_header" for dep in deps],
        java_deps = [dep + "_java_lib" for dep in deps] + java_deps,  # Pass Java dependencies for compilation
        docs = docs,
        resources = resources,
        max_output_tokens = max_output_tokens,
        llm_model = llm_model, # Pass through optional model override
        temperature = temperature,
        tags = tags + ["natty_codegen_internal"], # Add internal tag if desired
        visibility = visibility,
    )

    # Wrap the output in a standard java_library
    native.java_library(
        name = name + "_java_lib",
        srcs = [":" + name], # Use the output of the codegen rule
        deps = [dep + "_java_lib" for dep in deps] + java_deps,
        # For the sake of avoiding needing to constrain the LLM generated code to somehow know that 
        # it shouldn't be importing anything it sees in the dependency impls that it's shown, just
        # make sure that everything it could possibly see is importable.
        exports = [dep + "_java_lib" for dep in deps] + java_deps,
        resources = resources,
        # Disable ErrorProne for now unless/until I'm able to run ErrorProne during the codegen verification loop.
        javacopts = ["-XepDisableAllChecks"],
        visibility = visibility,
        tags = tags,
    )

    # Now, this executes the NattyJavaDecompiler to produce a dramatically simpler view of the Java
    # class generated by Natty above. Dependents on this Natty component should then depend on this
    # simplified artifact to feed the LLM dependency context.
    _natty_header(
        name = name + "_natty_header",
        src = ":" + name + "_java_lib",
        classname = _get_import_str(name, "java") + "." + name,
        natty_src = ":" + name,
        max_output_tokens = max_output_tokens,
        llm_model = llm_model, # Pass through optional model override
        temperature = temperature,
        visibility = visibility,
        tags = tags,
    )

def natty_java_binary(
    name, src, deps = [], java_deps = [], docs = [], resources = [], max_output_tokens = None, llm_model = None, temperature = None, visibility = None, tags = [],
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
      resources: Resource files that will be available to the generated program.
      max_output_tokens: Optional; maximum output tokens to generate.
      main_class: The main class to execute (if not specified, will be determined from the generated code).
      llm_model: Optional; overrides the default LLM model.
      temperature: Optional; overrides the default sampling temperature.
      visibility: Standard Bazel visibility.
      tags: Standard Bazel tags.
    """

    # Call the internal rule to perform the code generation
    _natty_library_rule(
        name = name,
        src = src,
        language = "java",  # Fixed to Java for this macro
        package = _get_import_str(name, "java"),
        target_type = "binary",  # This is a binary executable
        deps = deps,
        java_deps = [dep + "_java_lib" for dep in deps] + java_deps,  # Pass Java dependencies for compilation
        docs = docs,
        resources = resources,
        max_output_tokens = max_output_tokens,
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
        main_class = java_package + "." + name

    # Wrap the output in a standard java_binary for execution
    native.java_binary(
        name = name + "_java_bin",
        srcs = [":" + name], # Use the output of the codegen rule
        main_class = main_class,
        deps = [dep + "_java_lib" for dep in deps] + java_deps,
        resources = resources,
        # Disable ErrorProne for now unless/until I'm able to run ErrorProne during the codegen verification loop.
        javacopts = ["-XepDisableAllChecks"],
        visibility = visibility,
        tags = tags,
    )
