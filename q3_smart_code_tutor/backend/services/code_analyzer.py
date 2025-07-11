"""
Code analyzer service for analyzing code structure and providing insights
"""
import ast
import logging
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CodeAnalysis:
    """Data class for code analysis results"""
    language: str
    complexity: int
    lines_of_code: int
    functions: List[Dict]
    classes: List[Dict]
    imports: List[str]
    variables: List[str]
    issues: List[Dict]
    suggestions: List[str]


class CodeAnalyzer:
    """Service for analyzing code structure and providing insights"""
    
    def __init__(self):
        self.python_issues = {
            "indentation": "Check for consistent indentation (4 spaces)",
            "naming": "Use snake_case for variables and functions, PascalCase for classes",
            "imports": "Group imports: standard library, third-party, local",
            "docstrings": "Add docstrings to functions and classes",
            "complexity": "Consider breaking down complex functions",
            "unused_variables": "Remove unused variables",
            "magic_numbers": "Replace magic numbers with named constants"
        }
        
        self.javascript_issues = {
            "var_usage": "Use const and let instead of var",
            "semicolons": "Add semicolons at the end of statements",
            "naming": "Use camelCase for variables and functions, PascalCase for classes",
            "arrow_functions": "Use arrow functions for short functions",
            "template_literals": "Use template literals for string interpolation",
            "async_await": "Use async/await instead of .then() chains",
            "strict_mode": "Add 'use strict' at the beginning of files"
        }
        
    async def analyze_code(self, code: str, language: str = "python") -> Dict[str, Any]:
        """Analyze code and return insights"""
        try:
            if language == "python":
                return await self._analyze_python_code(code)
            elif language == "javascript":
                return await self._analyze_javascript_code(code)
            else:
                return {"error": f"Unsupported language: {language}"}
                
        except Exception as e:
            logger.error(f"Code analysis error: {e}")
            return {"error": str(e)}
            
    async def _analyze_python_code(self, code: str) -> Dict[str, Any]:
        """Analyze Python code"""
        try:
            # Parse AST
            tree = ast.parse(code)
            
            # Extract information
            functions = []
            classes = []
            imports = []
            variables = []
            issues = []
            
            # Analyze AST nodes
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append({
                        "name": node.name,
                        "line": node.lineno,
                        "args": [arg.arg for arg in node.args.args],
                        "has_docstring": ast.get_docstring(node) is not None
                    })
                    
                elif isinstance(node, ast.ClassDef):
                    classes.append({
                        "name": node.name,
                        "line": node.lineno,
                        "methods": [n.name for n in node.body if isinstance(n, ast.FunctionDef)],
                        "has_docstring": ast.get_docstring(node) is not None
                    })
                    
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                        
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        imports.append(f"{module}.{alias.name}")
                        
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            variables.append(target.id)
                            
            # Check for issues
            issues = await self._check_python_issues(code, tree, functions, classes)
            
            # Generate suggestions
            suggestions = await self._generate_python_suggestions(code, functions, classes, issues)
            
            # Calculate complexity
            complexity = await self._calculate_complexity(tree)
            
            return {
                "language": "python",
                "complexity": complexity,
                "lines_of_code": len(code.splitlines()),
                "functions": functions,
                "classes": classes,
                "imports": imports,
                "variables": variables,
                "issues": issues,
                "suggestions": suggestions
            }
            
        except SyntaxError as e:
            return {
                "language": "python",
                "error": f"Syntax error: {e.msg} at line {e.lineno}",
                "issues": [{"type": "syntax_error", "message": e.msg, "line": e.lineno}]
            }
            
    async def _analyze_javascript_code(self, code: str) -> Dict[str, Any]:
        """Analyze JavaScript code"""
        try:
            functions = []
            classes = []
            imports = []
            variables = []
            issues = []
            
            # Extract functions using regex
            function_pattern = r'(?:function\s+(\w+)\s*\([^)]*\)|const\s+(\w+)\s*=\s*\([^)]*\)\s*=>|let\s+(\w+)\s*=\s*\([^)]*\)\s*=>)'
            function_matches = re.finditer(function_pattern, code)
            
            for match in function_matches:
                func_name = match.group(1) or match.group(2) or match.group(3)
                if func_name:
                    functions.append({
                        "name": func_name,
                        "line": code[:match.start()].count('\n') + 1,
                        "type": "function" if match.group(1) else "arrow_function"
                    })
                    
            # Extract classes
            class_pattern = r'class\s+(\w+)'
            class_matches = re.finditer(class_pattern, code)
            
            for match in class_matches:
                classes.append({
                    "name": match.group(1),
                    "line": code[:match.start()].count('\n') + 1
                })
                
            # Extract imports
            import_pattern = r'(?:import\s+(?:\{[^}]*\}|\w+)\s+from\s+[\'"][^\'"]+[\'"]|const\s+\w+\s*=\s*require\s*\([\'"][^\'"]+[\'"]\))'
            import_matches = re.finditer(import_pattern, code)
            
            for match in import_matches:
                imports.append(match.group(0))
                
            # Extract variables
            var_pattern = r'(?:const|let|var)\s+(\w+)'
            var_matches = re.finditer(var_pattern, code)
            
            for match in var_matches:
                variables.append(match.group(1))
                
            # Check for issues
            issues = await self._check_javascript_issues(code)
            
            # Generate suggestions
            suggestions = await self._generate_javascript_suggestions(code, functions, classes, issues)
            
            # Calculate complexity (simplified)
            complexity = len(functions) + len(classes) * 2
            
            return {
                "language": "javascript",
                "complexity": complexity,
                "lines_of_code": len(code.splitlines()),
                "functions": functions,
                "classes": classes,
                "imports": imports,
                "variables": variables,
                "issues": issues,
                "suggestions": suggestions
            }
            
        except Exception as e:
            return {
                "language": "javascript",
                "error": f"Analysis error: {str(e)}",
                "issues": [{"type": "analysis_error", "message": str(e)}]
            }
            
    async def _check_python_issues(self, code: str, tree: ast.AST, functions: List, classes: List) -> List[Dict]:
        """Check for Python code issues"""
        issues = []
        
        # Check for unused variables
        assigned_vars = set()
        used_vars = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        assigned_vars.add(target.id)
            elif isinstance(node, ast.Name):
                if isinstance(node.ctx, ast.Load):
                    used_vars.add(node.id)
                    
        unused_vars = assigned_vars - used_vars
        for var in unused_vars:
            issues.append({
                "type": "unused_variable",
                "message": f"Unused variable: {var}",
                "suggestion": "Remove or use the variable"
            })
            
        # Check function complexity
        for func in functions:
            if len(func["args"]) > 5:
                issues.append({
                    "type": "function_complexity",
                    "message": f"Function '{func['name']}' has too many parameters",
                    "suggestion": "Consider using a data class or dictionary"
                })
                
        # Check for missing docstrings
        for func in functions:
            if not func["has_docstring"]:
                issues.append({
                    "type": "missing_docstring",
                    "message": f"Function '{func['name']}' missing docstring",
                    "suggestion": "Add a docstring describing the function's purpose"
                })
                
        return issues
        
    async def _check_javascript_issues(self, code: str) -> List[Dict]:
        """Check for JavaScript code issues"""
        issues = []
        
        # Check for var usage
        if 'var ' in code:
            issues.append({
                "type": "var_usage",
                "message": "Using 'var' instead of 'const' or 'let'",
                "suggestion": "Replace 'var' with 'const' or 'let'"
            })
            
        # Check for missing semicolons
        lines = code.split('\n')
        for i, line in enumerate(lines):
            line = line.strip()
            if (line and not line.endswith(';') and 
                not line.endswith('{') and not line.endswith('}') and
                not line.startswith('//') and not line.startswith('/*') and
                not line.startswith('import') and not line.startswith('export')):
                issues.append({
                    "type": "missing_semicolon",
                    "message": f"Missing semicolon at line {i+1}",
                    "suggestion": "Add semicolon at the end of the statement"
                })
                
        # Check for template literals
        if '${' in code and '`' not in code:
            issues.append({
                "type": "string_interpolation",
                "message": "Using string concatenation instead of template literals",
                "suggestion": "Use template literals with backticks for string interpolation"
            })
            
        return issues
        
    async def _generate_python_suggestions(self, code: str, functions: List, classes: List, issues: List) -> List[str]:
        """Generate Python code suggestions"""
        suggestions = []
        
        # General suggestions
        if len(functions) > 10:
            suggestions.append("Consider breaking the code into multiple modules")
            
        if len(classes) == 0 and len(functions) > 5:
            suggestions.append("Consider organizing related functions into classes")
            
        # Type hints suggestion
        if 'def ' in code and ': ' not in code:
            suggestions.append("Consider adding type hints to function parameters")
            
        # List comprehension suggestion
        if 'for ' in code and 'append(' in code:
            suggestions.append("Consider using list comprehensions for better readability")
            
        return suggestions
        
    async def _generate_javascript_suggestions(self, code: str, functions: List, classes: List, issues: List) -> List[str]:
        """Generate JavaScript code suggestions"""
        suggestions = []
        
        # Arrow functions suggestion
        if 'function ' in code and len(functions) > 3:
            suggestions.append("Consider using arrow functions for shorter functions")
            
        # Async/await suggestion
        if '.then(' in code:
            suggestions.append("Consider using async/await instead of .then() chains")
            
        # Template literals suggestion
        if '+' in code and "'" in code:
            suggestions.append("Consider using template literals for string concatenation")
            
        return suggestions
        
    async def _calculate_complexity(self, tree: ast.AST) -> int:
        """Calculate cyclomatic complexity"""
        complexity = 1  # Base complexity
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
                
        return complexity 