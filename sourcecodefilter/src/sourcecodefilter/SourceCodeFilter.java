/*
 * ScratchToCatrobat: A tool for converting Scratch projects into Catrobat programs.
 * Copyright (C) 2013-2015 The Catrobat Team
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
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.net.URL;
import java.nio.channels.Channels;
import java.nio.channels.ReadableByteChannel;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.eclipse.jdt.core.dom.AST;
import org.eclipse.jdt.core.dom.ASTNode;
import org.eclipse.jdt.core.dom.ASTParser;
import org.eclipse.jdt.core.dom.ASTVisitor;
import org.eclipse.jdt.core.dom.AbstractTypeDeclaration;
import org.eclipse.jdt.core.dom.Annotation;
import org.eclipse.jdt.core.dom.Block;
import org.eclipse.jdt.core.dom.BodyDeclaration;
import org.eclipse.jdt.core.dom.CompilationUnit;
import org.eclipse.jdt.core.dom.EnumDeclaration;
import org.eclipse.jdt.core.dom.FieldDeclaration;
import org.eclipse.jdt.core.dom.IExtendedModifier;
import org.eclipse.jdt.core.dom.ImportDeclaration;
import org.eclipse.jdt.core.dom.MethodDeclaration;
import org.eclipse.jdt.core.dom.MethodInvocation;
import org.eclipse.jdt.core.dom.Modifier;
import org.eclipse.jdt.core.dom.SimpleType;
import org.eclipse.jdt.core.dom.Statement;
import org.eclipse.jdt.core.dom.Type;
import org.eclipse.jdt.core.dom.TypeDeclaration;
import org.eclipse.jdt.core.dom.VariableDeclarationFragment;
import org.yaml.snakeyaml.Yaml;

import sourcecodefilter.ConverterRelevantCatroidSource.FilteringProject;

import com.google.common.base.Charsets;
import com.google.common.io.Files;

class ExitCode {
	public static final int FAILURE = 1;
	public static final int SUCCESS = 0;
}

public class SourceCodeFilter {

	public static Set<String> REMOVED_CLASSES = null;
	private static Set<String> REMOVED_METHOD_INVOCATIONS = null;
    private static Set<String> ADDITIONAL_SERIALIZATION_CLASSES = null;
    private static Set<String> PRESERVED_INTERFACES = null;
    public static Set<String> ADDITIONAL_HELPER_CLASSES = null;
    public static Map<String, Set<String>> classToPreservedFieldsMapping = null;
    public static Map<String, Set<String>> classToPreservedMethodsMapping = null;
    public static Map<String, Set<String>> removeFieldsMapping = null;
    public static Map<String, Set<String>> removeMethodsMapping = null;

    @SuppressWarnings("deprecation")
	private static ASTParser astParser = ASTParser.newParser(AST.JLS4);
    static { astParser.setKind(ASTParser.K_COMPILATION_UNIT); }

    @SuppressWarnings("unchecked")
	private static void removeUnsupportedClassHierarchyTypesIn(ConverterRelevantCatroidSource catroidSource) {
        final List<AbstractTypeDeclaration> types = catroidSource.getSourceAst().types();
        List<Type> superInterfaceTypes = null;

        for (AbstractTypeDeclaration abstractTypeDecl : types) {
            if (abstractTypeDecl.getNodeType() == ASTNode.TYPE_DECLARATION) {
                TypeDeclaration typeDecl = (TypeDeclaration) abstractTypeDecl;
                superInterfaceTypes = typeDecl.superInterfaceTypes();
                // Delete inner types
                for (TypeDeclaration innerType : Arrays.asList(typeDecl.getTypes())) {
                    innerType.delete();
                }

            } else if (abstractTypeDecl.getNodeType() == ASTNode.ENUM_DECLARATION) {
                EnumDeclaration enumDecl = (EnumDeclaration) abstractTypeDecl;
                superInterfaceTypes = enumDecl.superInterfaceTypes();

            } else {
                assert false : "Unhandled case: " + abstractTypeDecl.getClass().getName();
            }

            // modify type hierarchy
            for (Iterator<Type> iterator = superInterfaceTypes.iterator(); iterator.hasNext();) {
                Type interfaceType = iterator.next();
                if (interfaceType.getNodeType() == ASTNode.SIMPLE_TYPE) {
                    String interfaceName = ((SimpleType) interfaceType).getName().getFullyQualifiedName();
                    if (! (PRESERVED_INTERFACES.contains(interfaceName))) {
                        iterator.remove();
                    }
                }
            }
        }
    }

    @SuppressWarnings("unchecked")
	private static boolean isOverriding(MethodDeclaration methodDeclaration) {
        for (IExtendedModifier modifier : (List<IExtendedModifier>) methodDeclaration.modifiers()) {
            if (modifier.isAnnotation() && ((Annotation) modifier).getTypeName().equals("Override")) {
                return true;
            }
        }
        return false;
    }

    @SuppressWarnings("unchecked")
	private static boolean isRelatedToTransientFields(final String methodName, Set<FieldDeclaration> transientFields) {
        for (FieldDeclaration fieldDeclaration : transientFields) {
            for (VariableDeclarationFragment varDeclFrgmt : ((List<VariableDeclarationFragment>)fieldDeclaration.fragments())) {
                String fieldName = varDeclFrgmt.getName().getIdentifier();
                String fieldNameFirstUpper = Character.toUpperCase(fieldName.charAt(0)) + fieldName.substring(1);
                //                System.out.println(methodName + " " + fieldNameFirstUpper);
                if (methodName.endsWith(fieldNameFirstUpper)) {
                    return true;
                }
            }
        }
        return false;
    }

    static Set<String> parseSerializationRelevantClassNames(File baseDir) {
        File xstreamConfigurationSourceFile = new File(baseDir, "/org/catrobat/catroid/io/StorageHandler.java");
        if (!(xstreamConfigurationSourceFile.exists())) {
            throw new RuntimeException("Serialization configuration source must exist: " + xstreamConfigurationSourceFile.toString());
        }
        Set<String> classNames = new HashSet<>(ADDITIONAL_SERIALIZATION_CLASSES);
        try {
            String fileContent = Files.toString(xstreamConfigurationSourceFile, Charsets.UTF_8);
            Pattern serializedClassNamePattern = Pattern.compile("(?:xstream\\..*?)(\\w+)(?:\\.class)");
            Matcher matcher = serializedClassNamePattern.matcher(fileContent);
            while (matcher.find()) {
                classNames.add(matcher.group(1));
            }
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
        return classNames;
    }

    private static void removeUnsupportedImportsIn(ConverterRelevantCatroidSource catroidSource, FilteringProject project) {
        for (@SuppressWarnings("unchecked")
		Iterator<ImportDeclaration> iterator = catroidSource.getSourceAst().imports().iterator(); iterator.hasNext();) {
            ImportDeclaration importDecl = iterator.next();
            String importName = importDecl.getName().getFullyQualifiedName();
            if (importName.contains("android") || importName.startsWith("com.") || importName.endsWith(".R")
                    || importName.contains("catroid.ui")) {
                if (!(importName.startsWith("com.thoughtworks"))) {
                    iterator.remove();
                }
            } else if (importName.startsWith("org.catrobat")) {
                if (!(project.isRelevantClass(importName))) {
                    System.out.println("DEBUG:     import to delete: " + importName);
                    iterator.remove();
                } else {
                    System.out.println("DEBUG:     relevant import: " + importName);
                }
            }
        }
    }

    @SuppressWarnings("unchecked")
	private static void removeNonSerializedFieldsAndUnusedMethodsIn(ConverterRelevantCatroidSource source) {
        final List<AbstractTypeDeclaration> types = source.getSourceAst().types();
        assert types.size() > 0;
        // TODO: add abstraction for field and method iteration
        for (AbstractTypeDeclaration abstractTypeDecl : types) {
            Set<FieldDeclaration> nonTransientFields = new HashSet<FieldDeclaration>();
            // using AbstractTypeDeclaration to cover regular Types and Enums
            for (BodyDeclaration bodyDecl : new ArrayList<BodyDeclaration>(abstractTypeDecl.bodyDeclarations())) {
                if (bodyDecl.getNodeType() == ASTNode.FIELD_DECLARATION) {
                    FieldDeclaration fieldDecl = (FieldDeclaration) bodyDecl;
                    assert fieldDecl.fragments().size() == 1 : String.format("Unsupported multi field declaration: '%s'",
                        fieldDecl.toString());
                    String fieldName = ((VariableDeclarationFragment) fieldDecl.fragments().get(0)).getName().getIdentifier();
                    if (source.isRemovedField(fieldName)) {
                        fieldDecl.delete();
                	} else if (Modifier.isTransient(fieldDecl.getModifiers()) && !(source.isPreservedField(fieldName))) {
                        fieldDecl.delete();
                    } else {
                        nonTransientFields.add(fieldDecl);
                    }
                }
            }

            for (BodyDeclaration bodyDecl : new ArrayList<BodyDeclaration>(abstractTypeDecl.bodyDeclarations())) {
                if (bodyDecl.getNodeType() == ASTNode.METHOD_DECLARATION) {
                    MethodDeclaration methodDeclaration = (MethodDeclaration) bodyDecl;
                    if (! methodDeclaration.isConstructor()) {
                        //                            removeOverrideAnnotation(methodDeclaration);
                        final String methodName = methodDeclaration.getName().getIdentifier();
                        if (methodName.equals("init")) {
                            Block body = methodDeclaration.getBody();
                            for (Iterator<Statement> iterator2 = body.statements().iterator(); iterator2.hasNext();) {
                                iterator2.next();
                                iterator2.remove();
                            }
                        } else if (source.isRemovedMethod(methodName)) {
                            methodDeclaration.delete();
                        } else if (!(source.isPreservedMethod(methodName))) {
                            if (!(isRelatedToTransientFields(methodName, nonTransientFields)) || isOverriding(methodDeclaration)) {
                                methodDeclaration.delete();
                            }
                        }
                    }
                }
            }
        }
    }

    private static final ASTVisitor visitor = new ASTVisitor() {
    	/*public boolean visit(SimpleName node) {
    		System.out.println(">>> " + node);
    		return false;
    	}

    	public boolean visit(final PrefixExpression node) {
    		System.out.println(">>> " + node);
			return false;
    	}
    	public boolean visit(final PostfixExpression node) {
    		System.out.println(">>> " + node);
    		return false;
    	}

    	public boolean visit(org.eclipse.jdt.core.dom.StringLiteral node) {
    		System.out.println(">>> " + node);
    		return false;
    	}

    	public boolean visit(QualifiedName node) {
    		System.out.println(">>> " + node);
    		return false;
    	}
    	
    	public boolean visit(LabeledStatement node) {
    		System.out.println(">>> " + node);
    		return false;
    	}

    	public boolean visit(final VariableDeclarationFragment node) {
    		System.out.println(">>> " + node);
    		return false;
    	}

    	public boolean visit(final Assignment node) {
    		System.out.println(">>> " + node);
    		return false;
    	}

    	public boolean visit(EnhancedForStatement node) {
    		System.out.println(">>> " + node);
    		return false;
    	}

    	public boolean visit(final TypeDeclaration node) {
    		System.out.println(">>> " + node);
    		return false;
    	}

    	public boolean visit(PackageDeclaration node) {
    		System.out.println(">>> " + node);
    		return false;
    	}

    	public boolean visit(EnumDeclaration node) {
    		System.out.println(">>> " + node);
    		return false;
    	}

    	public boolean visit(AnnotationTypeDeclaration node) {
    		System.out.println(">>> " + node);
    		return false;
    	}

    	public boolean visit(BreakStatement node) {
    		System.out.println(">>> " + node);
    		return false;
    	}*/

		public boolean visit(MethodInvocation methodInvocation) {
			String[] temp = methodInvocation.toString().split("\\(", 2);
			assert(temp.length > 0);
			String fullName = temp[0];
			for (String unallowedMethodInvocation : REMOVED_METHOD_INVOCATIONS) {
				boolean isMatching;
				if (unallowedMethodInvocation.contains("*")) {
					unallowedMethodInvocation = unallowedMethodInvocation.replace("*", "");
					isMatching = fullName.startsWith(unallowedMethodInvocation);
				} else {
					isMatching = fullName.equals(unallowedMethodInvocation);
				}

	            if (isMatching) {
	            	System.out.println(fullName);
	            	methodInvocation.getParent().delete();
	            	return false;
	            }
			}
			return false;
		}
    };

    @SuppressWarnings("unchecked")
	private static void removeUnallowedMethodInvocations(ConverterRelevantCatroidSource source) {
        CompilationUnit cu = source.getSourceAst();
        final List<AbstractTypeDeclaration> types = cu.types();
        assert types.size() > 0;

        for (AbstractTypeDeclaration abstractTypeDecl : types) {
            for (BodyDeclaration bodyDecl : new ArrayList<BodyDeclaration>(abstractTypeDecl.bodyDeclarations())) {
                if (bodyDecl.getNodeType() != ASTNode.METHOD_DECLARATION) {
                	continue;
                }

                MethodDeclaration methodDeclaration = (MethodDeclaration) bodyDecl;
                Block body = methodDeclaration.getBody();
                if ((body == null) || (body.statements().size() == 0)) {
                	continue;
                }
                methodDeclaration.accept(visitor);
            }
        }
    }

    public static void writePreprocessedCatrobatSource(final File inputProjectDir, File outputProjectDir) {
        writePreprocessedCatrobatSource(inputProjectDir, outputProjectDir, false);
    }

    public static void writePreprocessedCatrobatSource(final File inputProjectDir, File outputProjectDir, boolean overwrite) {
        // iterate over all classes which are part of Pocket Code serialization or a dependency for it
        FilteringProject project = new ConverterRelevantCatroidSource.FilteringProject(inputProjectDir, outputProjectDir);
        for (ConverterRelevantCatroidSource catroidSource : ConverterRelevantCatroidSource.converterRelevantSources(project)) {
            // if class is part of Pocket Code serialization XML
            if (catroidSource.isSerializationClass()) {
                // remove types from class type hierarchy in class
                removeUnsupportedClassHierarchyTypesIn(catroidSource);
                // remove all fields are not serializable (`transient` keyword) in class. Skip fields to be ignored
                // remove all methods which method name do not include a serialize field name in class. Skip method names to ignore.
                removeNonSerializedFieldsAndUnusedMethodsIn(catroidSource);
            }
            //  remove all unavailable import in class
            removeUnsupportedImportsIn(catroidSource, project);

            // remove unallowed method invocations
            removeUnallowedMethodInvocations(catroidSource);

            //  write modified class to output
            catroidSource.writeModifications(outputProjectDir);
        }
    }

	public static void main(String[] args) {
    	InputStream input = null;
		try {
			input = new FileInputStream(new File("config", "config.yml"));
	        Yaml yaml = new Yaml();
			@SuppressWarnings("unchecked")
			Config config = new Config((Map<String, Object>)yaml.load(input));

			// get parameters from config
	        final String catroidVersion = config.getString("catroid_version");
	        final String archiveExtension = config.getString("archive_extension");
	        final String URLString = config.getString("URL");
	        final String downloadPath = config.getString("download_path");
	        final String relativeCodeSourcePath = config.getString("relative_code_source_path");
	        final String outputSrcPath = config.getString("output_src_path");
	        final String outputLibPath = config.getString("output_lib_path");
	        final String xstreamVersion = config.getString("xstream_version");
	        final String xstreamLibExtension = config.getString("xstream_lib_extension");
	        final String xstreamLibraryDownloadURLString = config.getString("xstream_download_URL");

	        // include/exclude setup
	        REMOVED_CLASSES = config.getSet("removed_classes");
	        REMOVED_METHOD_INVOCATIONS = config.getSet("removed_method_invocations");
	        ADDITIONAL_SERIALIZATION_CLASSES = config.getSet("additional_serialization_classes");
	        PRESERVED_INTERFACES = config.getSet("preserved_interfaces");
	        ADDITIONAL_HELPER_CLASSES = config.getSet("additional_helper_classes");
	        classToPreservedFieldsMapping = config.getMap("class_to_preserved_fields_mapping");
	        classToPreservedMethodsMapping = config.getMap("class_to_preserved_methods_mapping");
	        removeFieldsMapping = config.getMap("remove_fields_mapping");
	        removeMethodsMapping = config.getMap("remove_methods_mapping");

	        // download Catroid code project from Github
	        File downloadDir = new File(downloadPath);
	        downloadDir.mkdirs(); // create intermediate recursive directories if needed...
	        if (downloadDir.isDirectory() == false) {
	        	System.err.println(downloadDir.getAbsolutePath() + " is not a directory!");
	        	System.exit(ExitCode.FAILURE);
	        }
	        File archiveFile = new File(downloadDir, catroidVersion + "." + archiveExtension);
	        if (archiveFile.exists() == false) {
	        	System.out.println("Downloading new release...");
	        	Util.downloadFile(new URL(URLString), archiveFile);
	        }

	        // extract ZIP archive
        	System.out.println("Extracting new release...");
	        String rootDirectoryPath = Util.extractZip(archiveFile, downloadDir.getAbsolutePath());
	        if (rootDirectoryPath == null) {
	        	System.exit(ExitCode.FAILURE);
	        }

	        // download XStream-library
	        File xstreamLibraryFile = new File(downloadDir, xstreamVersion + "." + xstreamLibExtension);
	        if (xstreamLibraryFile.exists() == false) {
	        	System.out.println("Downloading XStream library...");
	        	Util.downloadFile(new URL(xstreamLibraryDownloadURLString), xstreamLibraryFile);
	        }

	        // move XStream-library to output library directory
	    	File outputLibDir = new File(outputLibPath);
	    	outputLibDir.mkdirs(); // create intermediate recursive directories if needed...
	    	File xstreamOutputPath = new File(outputLibPath, "xstream-" + xstreamVersion
	    			+ "." + xstreamLibExtension);
	    	Files.copy(xstreamLibraryFile, xstreamOutputPath);

	        // check if directories exist
	    	File rootDirectoryDir = new File(downloadPath, rootDirectoryPath);
	    	if (rootDirectoryDir.exists() == false) {
	    		System.err.println(rootDirectoryDir.getAbsolutePath() + " is not a directory!");
	    		System.exit(ExitCode.FAILURE);
	    	}
	        File inputDir = new File(rootDirectoryDir, relativeCodeSourcePath);
	        if (inputDir.exists() == false) {
	        	System.err.println(inputDir.getAbsolutePath() + " is not a directory!");
	        	System.exit(ExitCode.FAILURE);
	        }
	    	File outputSrcDir = new File(outputSrcPath);
	    	outputSrcDir.mkdirs(); // create intermediate recursive directories if needed...
	    	Util.deleteDirectory(outputSrcDir); // delete directory of path but not intermediate!!

	    	// preprocess & filter
	        writePreprocessedCatrobatSource(inputDir, outputSrcDir);

		} catch (IOException exception) {
			exception.printStackTrace();
			System.exit(ExitCode.FAILURE);
		} finally {
			Util.close(input);
		}
		System.exit(ExitCode.SUCCESS);
    }
}
