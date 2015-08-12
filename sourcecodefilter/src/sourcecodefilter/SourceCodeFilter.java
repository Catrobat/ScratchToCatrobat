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
import java.io.IOException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
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
import org.eclipse.jdt.core.dom.Modifier;
import org.eclipse.jdt.core.dom.SimpleType;
import org.eclipse.jdt.core.dom.Statement;
import org.eclipse.jdt.core.dom.Type;
import org.eclipse.jdt.core.dom.TypeDeclaration;
import org.eclipse.jdt.core.dom.VariableDeclarationFragment;
import org.eclipse.jface.text.BadLocationException;
import org.eclipse.jface.text.Document;
import org.eclipse.text.edits.MalformedTreeException;
import org.eclipse.text.edits.TextEdit;

import sourcecodefilter.ConverterRelevantCatroidSource.FilteringProject;

import com.google.common.base.Charsets;
//import com.google.common.collect.Sets;
import com.google.common.collect.Sets.SetView;
import com.google.common.io.Files;

class SourceCodeFilter {

    private static final String[] ADDITIONAL_SERIALIZATION_CLASSES = new String[] {
            "AllowedAfterDeadEndBrick",
            "Brick",
            "Constants",
            "DeadEndBrick",
            "DroneBrick",
            "DroneMoveBrick",
            "ElementType",
            "Formula",
            "FormulaElement",
            "Functions",
            "Operators",
            "NestingBrick",
            "ScreenModes",
            "ScreenValues",
            "ScriptBrick",
            "Sensors",
            "Look",
            "StorageHandler",
            "ProjectManager",
            "UserListBrick",
            "UserVariableBrick",
    };

    private static final Set<String> PRESERVED_INTERFACES = new HashSet<>(Arrays.asList(
    		"Brick",
    		"BroadcastMessage",
    		"Converter",
    		"LoopBeginBrick",
    		"MindstormsSensor",
    		"MindstormsCommand"
    ));

    static final String[] ADDITIONAL_HELPER_CLASSES = new String[] {
            "BroadcastMessage",
            "Constants",
            "CatroidFieldKeySorter",
            "UserVariablesContainer",
            "ConcurrentFormulaHashMap",
            "XStreamBrickConverter",
            "XStreamConcurrentFormulaHashMapConverter",
            "XStreamScriptConverter",
            "XStreamSettingConverter", // introduced in v0.95
            "LegoNXTSetting",
            "NXTPort",
            "NXTSensor",
            "NXTSensorType",
            "NXTSensorMode",
            "Command",
            "CommandType",
            "MindstormsReply",
            "LOOKUP",
            "XStreamToSupportCatrobatLanguageVersion095AndBefore", // introduced in v0.95
//            "XStreamToSupportCatrobatLanguageVersion092AndBefore", // removed in v0.95
            "XStreamUserVariableConverter",
            // exception classes
            "ProjectException",
            "MindstormsException",
            "CompatibilityProjectException",
            "LoadingProjectException",
            "OutdatedVersionProjectException",
            "FileChecksumContainer",
    };

    static Map<String, Set<String>> classToPreservedFieldsMapping = new HashMap<String, Set<String>>() {
        {
            put("BroadcastReceiverBrick", new HashSet<String>(Arrays.asList("broadcastMessage")));
            //            put("Formula", new HashSet<String>(Arrays.asList("internFormula")));
            put("FormulaElement", new HashSet<String>(Arrays.asList("parent")));
            put("LegoNxtMotorMoveBrick", new HashSet<String>(Arrays.asList("motorEnum")));
            put("LegoNxtMotorStopBrick", new HashSet<String>(Arrays.asList("motorEnum")));
            put("LegoNxtMotorTurnAngleBrick", new HashSet<String>(Arrays.asList("motorEnum")));
            put("LegoNxtPlayToneBrick", new HashSet<String>(Arrays.asList("motorEnum")));
            put("PlaySoundBrick", new HashSet<String>(Arrays.asList("oldSelectedSound")));
            put("PointToBrick", new HashSet<String>(Arrays.asList("oldSelectedObject")));
            put("Script", new HashSet<String>(Arrays.asList("brick")));
            put("Sprite", new HashSet<String>(Arrays.asList("look", "isPaused", "newUserBrickNext")));
            put("SetLookBrick", new HashSet<String>(Arrays.asList("oldSelectedLook")));
            put("UserVariable", new HashSet<String>(Arrays.asList("value")));
            put("WhenScript", new HashSet<String>(Arrays.asList("position")));
            put("ProjectManager", new HashSet<String>(Arrays.asList("INSTANCE", "project", "currentScript", "currentSprite", "currentUserBrick")));
            put("IfLogicBeginBrick", new HashSet<String>(Arrays.asList("ifElseBrick", "ifEndBrick")));
            put("IfLogicElseBrick", new HashSet<String>(Arrays.asList("ifBeginBrick", "ifEndBrick")));
            put("IfLogicEndBrick", new HashSet<String>(Arrays.asList("ifBeginBrick", "ifElseBrick")));
            put("ForeverBrick", new HashSet<String>(Arrays.asList("loopEndBrick")));
            put("RepeatBrick", new HashSet<String>(Arrays.asList("loopEndBrick")));
            put("LoopEndBrick", new HashSet<String>(Arrays.asList("loopBeginBrick")));
            put("UserBrick", new HashSet<String>(Arrays.asList("lastDataVersion")));
            put("UserScriptDefinitionBrick", new HashSet<String>(Arrays.asList("brick")));
            put("UserScriptDefinitionBrickElements", new HashSet<String>(Arrays.asList("version")));

            // introduced in v0.95 {
            put("UserList", new HashSet<String>(Arrays.asList("list")));
            put("UserBrickParameter", new HashSet<String>(Arrays.asList("parent")));
            put("SetVariableBrick", new HashSet<String>(Arrays.asList("defaultPrototypeToken")));
            put("PhiroMotorMoveBackwardBrick", new HashSet<String>(Arrays.asList("motorEnum")));
            put("PhiroMotorMoveForwardBrick", new HashSet<String>(Arrays.asList("motorEnum")));
            put("PhiroMotorStopBrick", new HashSet<String>(Arrays.asList("motorEnum")));
            put("PhiroPlayToneBrick", new HashSet<String>(Arrays.asList("toneEnum")));
            put("PhiroRGBLightBrick", new HashSet<String>(Arrays.asList("eyeEnum")));
            // }
        }
    };

    static Map<String, Set<String>> classToPreservedMethodsMapping = new HashMap<String, Set<String>>() {
        {
            put("Functions", new HashSet<String>(Arrays.asList("isFunction", "getFunctionByValue")));
            put("BroadcastScript", new HashSet<String>(Arrays.asList("setBroadcastMessage", "getBroadcastMessage", "getScriptBrick")));
            put("StartScript", new HashSet<String>(Arrays.asList("getScriptBrick")));
            put("WhenScript", new HashSet<String>(Arrays.asList("getScriptBrick")));
            put("Project", new HashSet<String>(Arrays.asList("ifLandscapeSwitchWidthAndHeight", "addSprite", "setName", "getName")));
            put("SoundInfo", new HashSet<String>(Arrays.asList("compareTo", "setTitle", "getTitle")));
            put("LookData", new HashSet<String>(Arrays.asList("setLookFilename")));
            put("FormulaElement",
                new HashSet<String>(Arrays.asList(
                    //                    "getInternTokenList",
                    "getRoot", "replaceElement", "replaceWithSubElement", "clone")));
            put("Formula", new HashSet<String>(Arrays.asList("getRoot", "clone")));
            put("PlaySoundBrick", new HashSet<String>(Arrays.asList("setSoundInfo")));
            put("StorageHandler", new HashSet<String>(Arrays.asList("getInstance", "setXstreamAliases", "getXMLStringOfAProject")));
            put("ScriptBrick", new HashSet<String>(Arrays.asList(/*"initScript", */"getScriptSafe")));
            //            put("Script", new HashSet<String>(Arrays.asList("init")));
            put("Sprite", new HashSet<String>(Arrays.asList(/*"init",*/"getLookDataList", "getScript", "getScriptIndex", "getNumberOfScripts", "getUserBrickList", "addScript")));
            put("UserVariablesContainer", new HashSet<String>(Arrays.asList("addSpriteUserVariableToSprite", "getOrCreateVariableListForSprite")));
            put("FormulaBrick", new HashSet<String>(Arrays.asList("addAllowedBrickField", "getFormulaWithBrickField", "setFormulaWithBrickField")));

            // introduced in v0.95 {
            put("DataContainer", new HashSet<String>(Arrays.asList("addUserBrickVariable", "addUserBrickUserVariableToUserBrick",
            	"addSpriteUserVariable", "addSpriteUserVariableToSprite", "addProjectUserVariable", "getOrCreateVariableListForUserBrick",
            	"getOrCreateVariableListForSprite", "cleanVariableListForSprite", "getUserVariable", "getUserVariableContext",
            	"findUserVariable", "getUserList", "addSpriteUserList", "addSpriteUserListToSprite", "addProjectUserList",
            	"getOrCreateUserListListForSprite", "findUserList", "getUserList"
            )));
            put("AddItemToUserListBrick", new HashSet<String>(Arrays.asList("initializeBrickFields")));
            put("ChangeTransparencyByNBrick", new HashSet<String>(Arrays.asList("initializeBrickFields")));
            put("DeleteItemOfUserListBrick", new HashSet<String>(Arrays.asList("initializeBrickFields")));
            put("InsertItemIntoUserListBrick", new HashSet<String>(Arrays.asList("initializeBrickFields")));
            put("LegoNxtMotorMoveBrick", new HashSet<String>(Arrays.asList("initializeBrickFields")));
            put("PhiroMotorMoveBackwardBrick", new HashSet<String>(Arrays.asList("initializeBrickFields")));
            put("PhiroMotorMoveForwardBrick", new HashSet<String>(Arrays.asList("initializeBrickFields")));
            put("PhiroPlayToneBrick", new HashSet<String>(Arrays.asList("initializeBrickFields")));
            put("PhiroRGBLightBrick", new HashSet<String>(Arrays.asList("initializeBrickFields")));
            put("ReplaceItemInUserListBrick", new HashSet<String>(Arrays.asList("initializeBrickFields")));
            put("SetTransparencyBrick", new HashSet<String>(Arrays.asList("initializeBrickFields")));

            put("LoopBeginBrick", new HashSet<String>(Arrays.asList("getLoopEndBrick", "setLoopEndBrick")));
            // }

            put("DroneMoveBrick", new HashSet<String>(Arrays.asList("initializeBrickFields")));
            put("GlideToBrick", new HashSet<String>(Arrays.asList("initializeBrickFields")));
            put("ChangeBrightnessByNBrick", new HashSet<String>(Arrays.asList("initializeBrickFields")));
            put("ChangeGhostEffectByNBrick", new HashSet<String>(Arrays.asList("initializeBrickFields")));
            put("ChangeSizeByNBrick", new HashSet<String>(Arrays.asList("initializeBrickFields")));
            put("ChangeVariableBrick", new HashSet<String>(Arrays.asList("initializeBrickFields")));
            put("ChangeVolumeByNBrick", new HashSet<String>(Arrays.asList("initializeBrickFields")));
            put("ChangeXByNBrick", new HashSet<String>(Arrays.asList("initializeBrickFields")));
            put("ChangeYByNBrick", new HashSet<String>(Arrays.asList("initializeBrickFields")));
            put("GoNStepsBackBrick", new HashSet<String>(Arrays.asList("initializeBrickFields")));
            put("IfLogicBeginBrick", new HashSet<String>(Arrays.asList("initializeBrickFields")));
            put("LegoNxtMotorActionBrick", new HashSet<String>(Arrays.asList("initializeBrickFields")));
            put("LegoNxtMotorTurnAngleBrick", new HashSet<String>(Arrays.asList("initializeBrickFields")));
            put("LegoNxtPlayToneBrick", new HashSet<String>(Arrays.asList("initializeBrickFields")));
            put("MoveNStepsBrick", new HashSet<String>(Arrays.asList("initializeBrickFields")));
            put("NoteBrick", new HashSet<String>(Arrays.asList("initializeBrickFields")));
            put("PlaceAtBrick", new HashSet<String>(Arrays.asList("initializeBrickFields")));
            put("PointInDirectionBrick", new HashSet<String>(Arrays.asList("initializeBrickFields")));
            put("RepeatBrick", new HashSet<String>(Arrays.asList("initializeBrickFields")));
            put("SetBrightnessBrick", new HashSet<String>(Arrays.asList("initializeBrickFields")));
            put("SetGhostEffectBrick", new HashSet<String>(Arrays.asList("initializeBrickFields")));
            put("SetSizeToBrick", new HashSet<String>(Arrays.asList("initializeBrickFields")));
            put("SetVariableBrick", new HashSet<String>(Arrays.asList("initializeBrickFields")));
            put("SetVolumeToBrick", new HashSet<String>(Arrays.asList("initializeBrickFields")));
            put("SetXBrick", new HashSet<String>(Arrays.asList("initializeBrickFields")));
            put("SetYBrick", new HashSet<String>(Arrays.asList("initializeBrickFields")));
            put("SpeakBrick", new HashSet<String>(Arrays.asList("initializeBrickFields")));
            put("TurnLeftBrick", new HashSet<String>(Arrays.asList("initializeBrickFields")));
            put("TurnRightBrick", new HashSet<String>(Arrays.asList("initializeBrickFields")));
            put("VibrationBrick", new HashSet<String>(Arrays.asList("initializeBrickFields")));
            put("WaitBrick", new HashSet<String>(Arrays.asList("initializeBrickFields")));
            put("UserBrick", new HashSet<String>(Arrays.asList("getUserScriptDefinitionBrickElements", "copyFormulasMatchingNames")));
            put("UserScriptDefinitionBrick", new HashSet<String>(Arrays.asList("setUserBrick", "getScriptSafe")));
            put("UserScriptDefinitionBrickElements", new HashSet<String>(Arrays.asList("getUserScriptDefinitionBrickElementList")));
            put("WhenBrick", new HashSet<String>(Arrays.asList("getScriptSafe")));
            put("BroadcastReceiverBrick", new HashSet<String>(Arrays.asList("getScriptSafe")));
            put("WhenStartedBrick", new HashSet<String>(Arrays.asList("getScriptSafe")));
            put("ProjectManager", new HashSet<String>(Arrays.asList("getInstance", "addSprite", "addScript", "spriteExists")));
        }
    };

    static Map<String, Set<String>> classToRemoveFieldsMapping = new HashMap<String, Set<String>>() {
    	{
    		put("Constants", new HashSet<String>(Arrays.asList("DEFAULT_ROOT", "TMP_PATH", "TMP_IMAGE_PATH", "TEXT_TO_SPEECH_TMP_PATH")));
    		put("Look", new HashSet<String>(Arrays.asList("actionsToRestart", "pixmap", "whenParallelAction", "shader")));
    		put("NXTSensor", new HashSet<String>(Arrays.asList("connection")));
    	}
    };

    static Map<String, Set<String>> classToRemoveMethodsMapping = new HashMap<String, Set<String>>() {
    	{
    		put("ProjectManager", new HashSet<String>(Arrays.asList("uploadProject", "loadProject", "cancelLoadProject",
    				"canLoadProject", "saveProject", "initializeDefaultProject", "initializeDroneProject",
    				"initializeNewProject", "deleteCurrentProject", "deleteProject", "renameProject",
    				"addSprite", "addScript", "spriteExists"
    		)));
    		put("Look", new HashSet<String>(Arrays.asList("createBrightnessContrastShader", "checkImageChanged", "setWhenParallelAction")));
    		put("NXTSensor", new HashSet<String>(Arrays.asList("resetScaledValue", "getSensorReadings", "getUpdateInterval", "updateLastSensorValue", "getLastSensorValue")));
    	}
    };

    private static ASTParser astParser = ASTParser.newParser(AST.JLS4);
    static {
        astParser.setKind(ASTParser.K_COMPILATION_UNIT);
    }

    // TODO: introduce `CatrobatClass` abstraction
    private Set<String> unfilteredClasses = null;
    private Set<String> filteringTargetClasses = null;
    private SetView<String> allClasses = null;

    /*
    public SourceCodeFilter(File inputDir) {
        this.inputDir = inputDir;
        this.rootPath = inputDir.getAbsolutePath();
        this.filteringTargetClasses = parseSerializationRelevantClassNames(inputDir);
        this.unfilteredClasses = new HashSet<String>(Arrays.asList(ADDITIONAL_HELPER_CLASSES));
        this.allClasses = Sets.union(filteringTargetClasses, unfilteredClasses);
        //        Joiner joiner = Joiner.on(", ");
        //        assert this.filteringTargetClasses.containsAll(unfilteredClasses) : "Class is not available: "
        //                + joiner.join(Collections2.filter(unfilteredClasses, Predicates.not(Predicates.in(filteringTargetClasses))));

    }*/

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
                    if (!(PRESERVED_INTERFACES.contains(interfaceName))) {
                        iterator.remove();
                    }
                }
            }
        }
    }

    private static void applyChangesToAst(Document document, CompilationUnit unitAst) {
        TextEdit edits = unitAst.rewrite(document, null);
        try {
            edits.apply(document);
        } catch (MalformedTreeException e) {
            // TODO Auto-generated catch block
            e.printStackTrace();
        } catch (BadLocationException e) {
            // TODO Auto-generated catch block
            e.printStackTrace();
        }
    }

    private static boolean isOverriding(MethodDeclaration methodDeclaration) {
        for (IExtendedModifier modifier : (List<IExtendedModifier>) methodDeclaration.modifiers()) {
            if (modifier.isAnnotation() && ((Annotation) modifier).getTypeName().equals("Override")) {
                return true;
            }
        }
        return false;
    }

    private static void removeOverrideAnnotation(MethodDeclaration methodDeclaration) {
        for (Iterator<IExtendedModifier> iterator = ((List<IExtendedModifier>) methodDeclaration.modifiers()).iterator(); iterator.hasNext();) {
            IExtendedModifier modifier = iterator.next();
            if (modifier.isAnnotation()) {
                if (((Annotation) modifier).getTypeName().getFullyQualifiedName().equals("Override")) {
                    System.out.println("Removing @Override at " + methodDeclaration.getName().getIdentifier());
                    iterator.remove();
                }
            }
        }

        //        for (IExtendedModifier modifier : (List<IExtendedModifier>) methodDeclaration.modifiers()) {
        //            if (modifier.isAnnotation() && ((Annotation) modifier).getTypeName().equals("Override")) {
        //                return true;
        //            }
        //        }
        //        return false;
    }

    private static boolean isRelatedToTransientFields(final String methodName, Set<FieldDeclaration> transientFields) {
        for (FieldDeclaration fieldDeclaration : transientFields) {
            for (VariableDeclarationFragment varDeclFrgmt : ((List<VariableDeclarationFragment>) fieldDeclaration.fragments())) {
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

    private boolean isTargetClass(File sourceFile) {
        return filteringTargetClasses.contains(Files.getNameWithoutExtension(sourceFile.getName()));
    }

    static Set<String> parseSerializationRelevantClassNames(File baseDir) {
        File xstreamConfigurationSourceFile = new File(baseDir, "/org/catrobat/catroid/io/StorageHandler.java");
        if (!(xstreamConfigurationSourceFile.exists())) {
            throw new RuntimeException("Serialization configuration source must exist: " + xstreamConfigurationSourceFile.toString());
        }
        Set<String> classNames = new HashSet<String>();
        classNames.addAll(Arrays.asList(ADDITIONAL_SERIALIZATION_CLASSES));
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
        for (Iterator<ImportDeclaration> iterator = catroidSource.getSourceAst().imports().iterator(); iterator.hasNext();) {
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

            //  write modified class to output
            catroidSource.writeModifications(outputProjectDir);
        }
    }

    public static boolean deleteDirectory(File directory) {
    	if (directory.exists()) {
    		File[] files = directory.listFiles();
    		if (null != files) {
    			for (int i = 0; i < files.length; ++i) {
    				if (files[i].isDirectory()) {
    					deleteDirectory(files[i]);
    				} else {
    					files[i].delete();
    				}
    			}
    		}
    	}
    	return(directory.delete());
    }

    public static void main(String[] args) {
    	String sourcePath = "/Users/r4ll3/Development/Mobile/Android/Catroid_S2CC/catroid/src";
//    	String sourcePath = "/Users/r4ll3/Development/Mobile/Android/Catroid/catroid/src";
    	String destinationPath = "/Users/r4ll3/Desktop/catroid_v095/src";
//    	String destinationPath = "/Users/r4ll3/Desktop/catroid/src";
        File testInputDir = new File(sourcePath);
        File testOutputDir = new File(destinationPath);
    	deleteDirectory(testOutputDir);
        writePreprocessedCatrobatSource(testInputDir, testOutputDir);
    }

}
