load("@rules_python//python:py_binary.bzl", "py_binary")
load("@rules_python//python:py_library.bzl", "py_library")
load("@pypi//:requirements.bzl", "requirement")


py_binary(
  name = "main",
  srcs = ["main.py"],
  deps = [
    ":llm",
    requirement("asyncclick"),
    requirement("pydantic"),
  ],
  visibility = ["//visibility:public"],
)

py_binary(
  name = "generate_usage_description",
  srcs = ["generate_usage_description.py"],
  deps = [
    ":llm",
    requirement("asyncclick"),
    requirement("pydantic"),
  ],
  visibility = ["//visibility:public"],
)

py_library(
  name = "llm",
  srcs = ["llm.py"],
  deps = [
    requirement("google-genai"),
    requirement("pydantic"),
  ],
)
