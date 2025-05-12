/** 
 * Vendored from: https://github.com/windup/windup/blob/43f25011eb8e01ee666fd4027aba9091ae2c0022/decompiler/api/src/test/java/org/jboss/windup/decompiler/util/ClassNameFilter.java 
 * */
package com.natty.decompiler;

import org.jboss.windup.decompiler.util.Filter;

import java.util.zip.ZipEntry;

/**
 * ZipEntry Filter which accepts only one class and its inner classes.
 *
 * @author <a href="mailto:ozizka@redhat.com">Ondrej Zizka</a>
 */
public class ClassNameFilter implements Filter<ZipEntry> {

    private final String cls;

    public ClassNameFilter(String cls) {
        this.cls = cls.replace('.', '/');
    }

    @Override
    public Result decide(ZipEntry what) {
        if (what.isDirectory())
            return Result.REJECT;
        if (!what.getName().startsWith(cls))
            return Result.REJECT;

        final String end = what.getName().substring(cls.length());
        if (end.equals(".class"))
            return Result.ACCEPT;
        if (end.charAt(0) == '$' && end.endsWith(".class"))
            return Result.ACCEPT;

        return Filter.Result.REJECT;
    }

}