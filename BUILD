load("@rules_uv//uv:pip.bzl", "pip_compile")
load("@rules_uv//uv:venv.bzl", "create_venv", "sync_venv")

################################################################################
# BEGIN: UV Setup
#
# These targets enable us to use UV to generate the requirements.txt and venv
# using UV for extra speed beyond what's available out of the box in 
# rules_python.
#
# Usage:
#   When you want to add a new pypi dep, you'll simple add it to the 
#   //:requirements.in file, and run `bazel run //:generate_requirements_txt.
#   As the name implies this will generate the //:requirements.txt file.
#   This file then gets used by the `//:(create|sync)_env` targets to create
#   and sync the virtualenv generated at //:.venv to enable IDEs to accurately
#   reflect the deps when they get used in python files throughout the repo.
################################################################################
pip_compile(
    name = "generate_requirements_txt",
    requirements_in = "//:requirements.in", # default
    requirements_txt = "//:requirements.txt", # default
)

create_venv(
    name = "create_venv",
    destination_folder = ".venv",
    requirements_txt = "//:requirements.txt", # default
    site_packages_extra_files = [
        "site_packages_extra/sitecustomize.py",
    ],
)

sync_venv(
    name = "sync_venv",
    destination_folder = ".venv",
    requirements_txt = "//:requirements.txt", # default
    site_packages_extra_files = [
        "site_packages_extra/sitecustomize.py",
    ],
)
################################################################################
# END: UV Setup
################################################################################

################################################################################
# BEGIN: Aliases for Maven Deps
################################################################################
alias(
    name = "fernflower",
    actual = "@maven//:org_jboss_windup_decompiler_decompiler_fernflower",
    visibility = ["//visibility:public"],
)
alias(
    name = "fernflower_windup_decompiler_api_forge_addon",
    actual = "@maven//:org_jboss_windup_decompiler_decompiler_api_forge_addon",
    visibility = ["//visibility:public"],
)
alias(
    name = "google-options",
    actual = "@maven//:com_github_pcj_google_options",
    visibility = ["//visibility:public"],
)
################################################################################
# END: Aliases for Maven Deps
################################################################################