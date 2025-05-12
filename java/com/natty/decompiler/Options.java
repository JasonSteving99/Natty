package com.natty.decompiler;

import com.google.devtools.common.options.Option;
import com.google.devtools.common.options.OptionsBase;
import com.google.devtools.common.options.OptionsParser;

import java.util.List;

public class Options extends OptionsBase {
  @Option(
      name = "input-jar",
      abbrev = 'i',
      help = "The input JAR file to be decompiled.",
      defaultValue = ""
  )
  public String inputJar;

  @Option(
      name = "classname",
      abbrev = 'c',
      help = "The fully qualified classname to be decompiled.",
      defaultValue = ""
  )
  public String className;

  @Option(
      name = "outfile",
      abbrev = 'o',
      help = "Path to the output file for the decompiled .java file to be written to.",
      defaultValue = ""
  )
  public String finalOutputFile;

  static Options parseCLIOptions(String... args) {
    OptionsParser parser = OptionsParser.newOptionsParser(Options.class);
    parser.parseAndExitUponError(args);
    return parser.getOptions(Options.class);
  }
}