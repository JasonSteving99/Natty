java_binary(
    name = "decompiler",
    srcs = [
        "ClassNameFilter.java",
        "NattyJavaDecompiler.java",
        "Options.java",
    ],
    main_class = "com.natty.decompiler.NattyJavaDecompiler",
    deps = [
        "//:fernflower",
        "//:fernflower_windup_decompiler_api_forge_addon",
        "//:google-options",
    ],
)