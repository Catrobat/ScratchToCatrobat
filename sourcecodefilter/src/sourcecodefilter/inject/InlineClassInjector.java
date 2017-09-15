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

package sourcecodefilter.inject;

import java.util.ArrayList;
import java.util.List;
import java.util.Set;

import org.eclipse.jdt.core.dom.AST;
import org.eclipse.jdt.core.dom.ASTNode;
import org.eclipse.jdt.core.dom.AbstractTypeDeclaration;
import org.eclipse.jdt.core.dom.Block;
import org.eclipse.jdt.core.dom.BodyDeclaration;
import org.eclipse.jdt.core.dom.CompilationUnit;
import org.eclipse.jdt.core.dom.MethodDeclaration;
import org.eclipse.jdt.core.dom.MethodInvocation;
import org.eclipse.jdt.core.dom.Statement;
import org.eclipse.jdt.core.dom.TypeDeclaration;
import org.eclipse.jdt.core.dom.rewrite.ASTRewrite;
import org.eclipse.jdt.core.dom.rewrite.ListRewrite;
import org.eclipse.jface.text.Document;
import org.eclipse.text.edits.TextEdit;

import sourcecodefilter.ConverterRelevantCatroidSource;

public class InlineClassInjector {

	final private ConverterRelevantCatroidSource catroidSource;
	final private Set<String> codeOfInlineClassesToInject;

	public InlineClassInjector(ConverterRelevantCatroidSource catroidSource,
			Set<String> codeOfInlineClassesToInject) {
		this.catroidSource = catroidSource;
		this.codeOfInlineClassesToInject = codeOfInlineClassesToInject;
	}

	public void inject() {
    	/*
        CompilationUnit cu = catroidSource.getSourceAst();
        final List<AbstractTypeDeclaration> types = cu.types();
        assert types.size() > 0;

        AST ast = cu.getAST();
        ASTRewrite rewriter = ASTRewrite.create(ast);
        TypeDeclaration typeDecl = (TypeDeclaration) cu.types().get(0);
        MethodDeclaration methodDecl = typeDecl.getMethods()[0];
        Block block = methodDecl.getBody();

        MethodInvocation newInvocation = ast.newMethodInvocation();
        newInvocation.setName(ast.newSimpleName("add"));
        Statement newStatement = ast.newExpressionStatement(newInvocation);

        ListRewrite listRewrite = rewriter.getListRewrite(block, Block.STATEMENTS_PROPERTY);
		listRewrite.insertFirst(newStatement, null);

        types.add(new TypeDeclaration(null));
        for (AbstractTypeDeclaration abstractTypeDecl : types) {
        	if (abstractTypeDecl.getNodeType() == ASTNode.COMPILATION_UNIT) {
        		System.out.println(abstractTypeDecl.getName());
        		System.exit(0);
        	}
            for (BodyDeclaration bodyDecl : new ArrayList<BodyDeclaration>(abstractTypeDecl.bodyDeclarations())) {
                if (bodyDecl.getNodeType() != ASTNode.DECLARATION) {
                	continue;
                }
                if (bodyDecl.getNodeType() != ASTNode.METHOD_DECLARATION) {
                	continue;
                }

                MethodDeclaration methodDeclaration = (MethodDeclaration) bodyDecl;
                Block body = methodDeclaration.getBody();
                if ((body == null) || (body.statements().size() == 0)) {
                	continue;
                }
            }
        }
		 */
    }
}
