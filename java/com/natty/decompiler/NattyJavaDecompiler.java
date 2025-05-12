package com.natty.decompiler;

import java.io.File;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.util.List;

import org.jboss.windup.decompiler.api.DecompilationListener;
import org.jboss.windup.decompiler.api.DecompilationResult;
import org.jboss.windup.decompiler.fernflower.FernflowerDecompiler;
import org.jboss.windup.decompiler.util.Filter;
import java.util.zip.ZipEntry;

public class NattyJavaDecompiler {
    public static void main(String[] args) {
        if (args.length < 6) {
            System.out.println("Usage: java NattyJavaDecompiler --input-jar <input-jar> --classname <fully.qualified.ClassName> --outfile <output-file.java>");
            System.exit(1);
        }

        Options options = Options.parseCLIOptions(args);
        Path inputJar = Paths.get(options.inputJar);
        Path finalOutputFile = Paths.get(options.finalOutputFile);

        // Create a temporary directory for the initial decompilation
        Path tempOutputDir;
        try {
            tempOutputDir = Files.createTempDirectory("decompiler-temp");
            tempOutputDir.toFile().deleteOnExit();
        } catch (Exception e) {
            System.err.println("Could not create temp directory: " + e.getMessage());
            return;
        }

        // Create the decompiler instance
        FernflowerDecompiler decompiler = new FernflowerDecompiler();

        // Keep track of the decompiled file path
        final Path[] decompiledFilePath = new Path[1];

        try {
            // Create a filter that only accepts the requested class
            Filter<ZipEntry> filter = new ClassNameFilter(options.className);

            // Create a listener to track the decompiled file
            DecompilationListener listener = new DecompilationListener() {
                @Override
                public void fileDecompiled(List<String> sourceClassPaths, String outputPath) {
                    // Save the output path so we can move it later
                    decompiledFilePath[0] = Paths.get(outputPath);
                    System.out.println("Decompiled: " + outputPath);
                }

                @Override
                public void decompilationFailed(List<String> sourceClassPaths, String message) {
                    System.err.println("Failed to decompile: " + sourceClassPaths + " - " + message);
                }

                @Override
                public void decompilationProcessComplete() {
                    System.out.println("Decompilation process complete!");
                }

                @Override
                public boolean isCancelled() {
                    return false;
                }
            };

            // Decompile the archive with our filter
            DecompilationResult result = decompiler.decompileArchive(inputJar, tempOutputDir, filter, listener);

            // Check if we found and decompiled the requested class
            if (decompiledFilePath[0] != null && Files.exists(decompiledFilePath[0])) {
                // Move the file to the requested output location
                Files.createDirectories(finalOutputFile.getParent());
                Files.move(decompiledFilePath[0], finalOutputFile, StandardCopyOption.REPLACE_EXISTING);
                System.out.println("Decompiled file written to: " + finalOutputFile);
            } else {
                System.err.println("Class " + options.className + " not found in the JAR or decompilation failed.");
                if (result.getFailures().size() > 0) {
                    System.err.println("Failures: " + result.getFailures().size());
                }
            }

        } catch (Exception e) {
            System.err.println("Error: " + e.getMessage());
            e.printStackTrace();
        } finally {
            // Clean up
            decompiler.close();
            deleteDirectory(tempOutputDir.toFile());
        }
    }

    // Utility method to recursively delete a directory
    private static void deleteDirectory(File dir) {
        if (dir.isDirectory()) {
            File[] files = dir.listFiles();
            if (files != null) {
                for (File file : files) {
                    deleteDirectory(file);
                }
            }
        }
        dir.delete();
    }
}