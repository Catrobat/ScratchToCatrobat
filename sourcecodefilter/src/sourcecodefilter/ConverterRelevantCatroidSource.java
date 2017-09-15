/*
 * ScratchToCatrobat: A tool for converting Scratch projects into Catrobat programs.
 * Copyright (C) 2013-2016 The Catrobat Team
 * (http://developer.catrobat.org/credits)
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as
 * published by the Free Software Foundation, either version 3 of the
 * License, or (at your option) any later version.
 *
 * An additional term exception under section 7 of the GNU Affero
 * General Public License, version 3, is available at
 * http://developer.catrobat.org/license_additional_term
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program.  If not, see http://www.gnu.org/licenses/.
 */

package sourcecodefilter;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Hashtable;
import java.util.List;
import java.util.Map;
import java.util.Set;

import org.apache.commons.io.FileUtils;
import org.eclipse.jdt.core.JavaCore;
import org.eclipse.jdt.core.dom.AST;
import org.eclipse.jdt.core.dom.ASTParser;
import org.eclipse.jdt.core.dom.CompilationUnit;
import org.eclipse.jface.text.BadLocationException;
import org.eclipse.jface.text.Document;
import org.eclipse.text.edits.MalformedTreeException;
import org.eclipse.text.edits.TextEdit;

import com.google.common.base.Joiner;
import com.google.common.io.Files;

public class ConverterRelevantCatroidSource {

    private File sourcePath;
    private final FilteringProject project;
    private Set<String> fieldsToPreserve;
    private Set<String> fieldsToRemove;
    private Set<String> methodsToPreserve;
    private Set<String> methodsToRemove;
    private CompilationUnit sourceAst;
    private Boolean isSerializationClass;
    private Document internalSource;
    private String qualifiedClassName;

    public String getQualifiedClassName() {
		return qualifiedClassName;
	}

    public String getPackageName() {
    	final int indexOfLastDotOccurence = qualifiedClassName.lastIndexOf(".");
		return qualifiedClassName.substring(0, indexOfLastDotOccurence);
	}

	static class FilteringProject {
        private File projectInputDir;
        private File projectOutputDir;
        private Map<String, ConverterRelevantCatroidSource> relevantCatroidSources = new HashMap<>();

        public FilteringProject(File projectInputDir, File projectOutputDir) {
            this.projectInputDir = projectInputDir;
            this.projectOutputDir = projectOutputDir;
        }

        private void addClass(ConverterRelevantCatroidSource catroidSource) {
            this.relevantCatroidSources.put(catroidSource.qualifiedClassName, catroidSource);
        }

        boolean isRelevantClass(String className) {
            if (this.relevantCatroidSources.containsKey(className)) {
                return true;
            } else {
                for (String relevantClassName : this.relevantCatroidSources.keySet()) {
                    if (className.startsWith(relevantClassName)) {
                        return true;
                    }
                }
            }
            return false;
        }

        public File toOutputPath(File sourcePath) {
            return new File(projectOutputDir, sourcePath.getAbsolutePath().replace(projectInputDir.getAbsolutePath(), ""));
        }
    }

    @SuppressWarnings("deprecation")
	private static ASTParser astParser = ASTParser.newParser(AST.JLS4);
    static {
        astParser.setKind(ASTParser.K_COMPILATION_UNIT);
    }

    private ConverterRelevantCatroidSource(
    		File sourcePath,
    		FilteringProject project,
    		boolean isSerializationClass,
            Set<String> fieldsToPreserve,
            Set<String> fieldsToRemove,
            Set<String> methodsToPreserve,
            Set<String> methodsToRemove) {
        this.sourcePath = sourcePath;
        if (fieldsToPreserve == null) {
            fieldsToPreserve = new HashSet<String>();
        }
        if (fieldsToRemove == null) {
        	fieldsToRemove = new HashSet<String>();
        }
        if (methodsToPreserve == null) {
            methodsToPreserve = new HashSet<String>();
        }
        if (methodsToRemove == null) {
        	methodsToRemove = new HashSet<String>();
        }
        this.fieldsToPreserve = fieldsToPreserve;
        this.fieldsToRemove = fieldsToRemove;
        this.methodsToPreserve = methodsToPreserve;
        this.methodsToRemove = methodsToRemove;
        this.sourceAst = null;
        this.internalSource = null;
        this.isSerializationClass = isSerializationClass;
        initializeAst();
        // NOTE: Java class name convention expected
        this.qualifiedClassName = sourceAst.getPackage().getName().getFullyQualifiedName()
        		+ "." + Files.getNameWithoutExtension(sourcePath.getName());
        this.project = project;
    }

    public boolean isSerializationClass() {
        return isSerializationClass;
    }

    public CompilationUnit getSourceAst() {
        return sourceAst;
    }

    public boolean isPreservedField(String fieldName) {
        return fieldsToPreserve.contains(fieldName);
    }

    public boolean isRemovedField(String fieldName) {
    	return fieldsToRemove.contains(fieldName);
    }

    public boolean isPreservedMethod(String methodName) {
        return methodsToPreserve.contains(methodName);
    }

    public boolean isRemovedMethod(String methodName) {
    	return methodsToRemove.contains(methodName);
    }

    public void writeModifications(File outputProjectDir) {
        assert outputProjectDir.isDirectory();
        TextEdit edits = sourceAst.rewrite(internalSource, null);
        try {
            edits.apply(internalSource);
        } catch (MalformedTreeException e) {
            e.printStackTrace();
            System.exit(ExitCode.FAILURE);
        } catch (BadLocationException e) {
            e.printStackTrace();
            System.exit(ExitCode.FAILURE);
        }
        //        File targetFile = new File(outputProjectDir, sourcePath.getAbsolutePath().replace(project.projectInputDir.getAbsolutePath(), ""));
        File targetFile = project.toOutputPath(this.sourcePath);
        if (! (targetFile.exists())) {
            System.out.println("writing filtered file: " + targetFile.getName() + " (" + targetFile.getParent() + ")");
            try {
            	// replace text
            	String generatedCode = internalSource.get();
                FileUtils.write(targetFile, generatedCode);
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
        //        else {
        //            //            String currentFilteredSource = new String(java.nio.file.Files.readAllBytes(Paths.get(targetFile.toURI())));
        //            //            for (Diff diff : diff_lineMode(filteredSource, currentFilteredSource)) {
        //            //                System.out.println(diff.toString());
        //            //            }
        //            File fileCmp = new File(targetFile.getAbsolutePath() + ".cmp");
        //            FileUtils.write(fileCmp, filteredSource);
        //            throw new FileAlreadyExistsException(targetFile.getAbsolutePath());
        //        }
        //        assert false;
    }

    interface IProgressMonitor {
    }

    private void initializeAst() {
        try {
            this.internalSource = new Document(FileUtils.readFileToString(sourcePath));
        } catch (IOException e) {
            e.printStackTrace();
            System.exit(ExitCode.FAILURE);
        }
        @SuppressWarnings("unchecked")
        Hashtable<String, String> options = JavaCore.getOptions();
        // enable Enum support
        options.put(JavaCore.COMPILER_COMPLIANCE, JavaCore.VERSION_1_5);
        options.put(JavaCore.COMPILER_CODEGEN_TARGET_PLATFORM, JavaCore.VERSION_1_5);
        options.put(JavaCore.COMPILER_SOURCE, JavaCore.VERSION_1_5);
        astParser.setCompilerOptions(options);
        astParser.setSource(internalSource.get().toCharArray());
        sourceAst = (CompilationUnit) astParser.createAST(null);
        sourceAst.recordModifications();
    }

    public static List<ConverterRelevantCatroidSource> converterRelevantSources(FilteringProject project) {
        // TODO: consolidate with project class
        final File catroidProjectDir = project.projectInputDir;
        assert catroidProjectDir.isDirectory();
        List<ConverterRelevantCatroidSource> relevantSources = new ArrayList<ConverterRelevantCatroidSource>();
        Set<String> serializationTargetClassNames = SourceCodeFilter.parseSerializationRelevantClassNames(catroidProjectDir);
        List<String> existingSources = new ArrayList<String>();
        for (File sourcePath : FileUtils.listFiles(catroidProjectDir, new String[] { "java" }, true)) {
            if (! (project.toOutputPath(sourcePath).exists())) {
                String className = Files.getNameWithoutExtension(sourcePath.getName());
                boolean isSerializationSource = serializationTargetClassNames.contains(className);
                boolean isHelperSource = SourceCodeFilter.ADDITIONAL_HELPER_CLASSES.contains(className);
                boolean isRemovedClass = SourceCodeFilter.REMOVE_CLASSES.contains(className);

                //boolean isClassOfRemovedPackage = SourceCodeFilter.packagesToBeRemoved.contains(className);
                if ((! isRemovedClass) && (isSerializationSource || isHelperSource)) {
                    ConverterRelevantCatroidSource catroidSource = new ConverterRelevantCatroidSource(
                        sourcePath,
                        project,
                        isSerializationSource,
                        // TODO: move into project class?
                        SourceCodeFilter.classToPreservedFieldsMapping.get(className),
                        SourceCodeFilter.removeFieldsMapping.get(className),
                        SourceCodeFilter.classToPreservedMethodsMapping.get(className),
                        SourceCodeFilter.removeMethodsMapping.get(className)
                    );

                    if (isInRemovedPackage(catroidSource)) {
                    	continue;
                    }

                    project.addClass(catroidSource);
                    relevantSources.add(catroidSource);
                }
            } else {
                existingSources.add(sourcePath.getAbsolutePath());
            }
        }
        if (!(existingSources.isEmpty())) {
            System.out.println("Skipped already existing files: (" + existingSources.size() + ")");
            System.out.println(Joiner.on(", ").join(existingSources));
            System.out.println();
        }
        return relevantSources;
    }

    private static boolean isInRemovedPackage(ConverterRelevantCatroidSource catroidSource) {
        for (String packageToBeRemoved : SourceCodeFilter.PACKAGES_TO_BE_REMOVED) {
        	if (catroidSource.getPackageName().startsWith(packageToBeRemoved)) {
        		return true;
        	}
        }
        return false;
    }
}
