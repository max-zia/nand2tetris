import os       # os.listdir() returns everything in a directory
import re       # re.split(pattern, string) splits string by pattern  
import sys      # sys.exit() raised on syntax error
from helpers import collapse_string_constants

class JackTokeniser():
    """
    Removes all comments and whitespace from the input stream and breaks it
    into Jack-language tokens, as specified by the Jack grammar.
    """

    def __init__(self, input_file):
        """
        Appends every lexical atom (i.e., token) of the input file 
        to a list, and makes this available as an attribute (.tokens). 
        Removes comments, whitespace, and newline characters in the process.
        """
        with open(input_file) as f:
            # Read lines from file, removing whitespace, comments, and 
            # breaking down to lexical atoms / tokens with suitable regex.
            lines = [
                re.split('(\W)', l.split('//')[0].strip()) for l in f 
                if l[0] != '/' and l.strip() != '' 
                and l.split('/')[0].strip() != ''
                and l.split('/')[0].strip()[0] != '*'
            ]
        
        # Format the tokens stream
        tokens = [
            token for sublist in lines 
            for token in sublist 
            if token != '' and token != ' '
        ]

        # Check for string contents in tokens stream and collapse if necessary
        if '"' in tokens:
            collapse_string_constants(tokens)

        self.tokens = tokens
    
    def has_more_tokens(self):
        """
        Returns true if there are more tokens in the input.
        """
        if len(self.tokens) > 0:
            return True
    
    def advance(self):
        """
        Deletes the first token from self.tokens, simulating advance
        through the input_file. Only called if has_more_tokens() is true.
        """
        del self.tokens[0]
    
    def token_type(self):
        """
        Returns the type of the 'current' token (i.e., self.tokens[0]).
        """
        # Keywords and symbols for Jack language
        keywords = [
            'class', 'constructor', 'function', 'method', 'field', 'return',
            'static', 'var', 'int', 'char', 'boolean', 'void', 'true',
            'false', 'null', 'this', 'let', 'do', 'if', 'else', 'while'
        ]

        symbols = [
            '{', '}', '(', ')', '[', ']', '.', ',', ';',
            '/', '&', '|', '<', '>', '=', '~', '+', '-', '*',
        ]

        # Type tests
        if self.tokens[0] in keywords:
            return 'KEYWORD'
        elif self.tokens[0] in symbols:
            return 'SYMBOL'
        elif '"' in self.tokens[0]:
            return 'STRING_CONST'
        else:
            try:
                int(self.tokens[0])
                return 'INT_CONST'
            except ValueError:
                return 'IDENTIFIER'

    # Methods for returning the value of the current token.
    def keyword(self):
        return self.tokens[0]

    def symbol(self):
        return self.tokens[0]
    
    def identifier(self):
        return self.tokens[0]
    
    def int_val(self):
        return int(self.tokens[0])
    
    def string_val(self):
        return self.tokens[0][1:-1]


class CompilationEngine():
    """
    Effects the compilation output. Takes a JackTokeniser and emits its 
    parsed structure into an output file.
    """

    def __init__(self, tokeniser, output_file):
        """
        Initialises all instances with a tokeniser and an open output file.
        """
        self.tokeniser = tokeniser
        self.output_file = open(output_file, 'w')
    
    # Helpers for the compilation process
    def close(self):
        """
        Closes the output file.
        """
        self.output_file.close()
    
    def write_current_token(self):
        """
        Writes the current token to the output_file.
        """
        current_token = self.tokeniser
        type = current_token.token_type()
        replace_text = ''

        # Get the XML tagname and text
        if type == 'SYMBOL':
            if current_token.symbol() == '&':
                replace_text = '&amp;'
            if current_token.symbol() == '<':
                replace_text = '&lt;'
            if current_token.symbol() == '>':
                replace_text = '&gt;'
            
            text = current_token.symbol()
            tag = type.lower()

        elif type == 'IDENTIFIER':
            text = current_token.identifier()
            tag = type.lower()

        elif type == 'KEYWORD':
            text = current_token.keyword()
            tag = type.lower()

        elif type == 'STRING_CONST':
            text = current_token.string_val()
            tag = 'stringConstant'

        elif type == 'INT_CONST':
            text = current_token.int_val()
            tag = 'integerConstant'

        # Write to file
        if len(replace_text) == 0:
            self.output_file.write(f'<{tag}> {text} </{tag}>\n')
        else:
            self.output_file.write(f'<{tag}> {replace_text} </{tag}>\n')
    
    def eat(self, tokens):
        """
        Consumes the current token, advances over it, and writes the token to 
        the output file. Raises a syntax error if the token is incorrect. Note
        that syntax error checking could certainly be improved here.
        """
        for token in tokens:
            if self.tokeniser.tokens[0] in token.split("|") or (
                ("varName" or "subroutineName" or "className" in token.split("|")) 
                and (self.tokeniser.token_type() == "IDENTIFIER")) or (
                ("INT_CONST" or "STRING_CONST" or "KEYWORD" in token.split("|"))
            ):
                self.write_current_token()
                self.tokeniser.advance()
            else:
                sys.exit(f"SyntaxError: expected {token} not {self.tokeniser.tokens[0]}")
    
    # Methods for compiling statements. 
    def compile_statements(self):
        """
        Compiles a sequence of statements, not including the enclosing {}.
        """
        # Hash table with callable values
        dispatcher = {
            "let": self.compile_let,
            "if": self.compile_if,
            "while": self.compile_while,
            "do": self.compile_do,
            "return": self.compile_return
        }

        self.output_file.write("<statements>\n")
        while True:
            dispatcher[self.tokeniser.tokens[0]]()
            if (self.tokeniser.tokens[0] not in dispatcher):
                break
        self.output_file.write("</statements>\n")

    def compile_let(self):
        """
        Compiles a let statement.
        """
        self.output_file.write("<letStatement>\n")
        self.eat(["let", "varName"])

        if self.tokeniser.tokens[0] == "[":
            self.eat(["["])
            self.compile_expression()
            self.eat(["]"])

        self.eat(["="])
        self.compile_expression()
        self.eat([";"]) 

        self.output_file.write("</letStatement>\n")

    def compile_if(self):
        """
        Compiles an if statement, possibly with a trailing else clause.
        """
        self.output_file.write("<ifStatement>\n")
        self.eat(["if", "("])
        self.compile_expression()
        self.eat([")", "{"])
        self.compile_statements()
        self.eat(["}"])
        
        # Check for trailing else clause
        try:
            if self.tokeniser.tokens[0] == "else":
                self.eat(["else", "{"])
                self.compile_statements()
                self.eat(["}"])
        except IndexError:
            pass

        self.output_file.write("</ifStatement>\n")

    def compile_do(self):
        """
        Compiles a do statement and the subroutine call.
        """
        self.output_file.write("<doStatement>\n")
        self.eat(["do"])
        self.compile_subroutine_call()
        self.eat([";"])
        self.output_file.write("</doStatement>\n")

    def compile_while(self):
        """
        Compiles a while statement.
        """
        self.output_file.write("<whileStatement>\n")
        self.eat(["while", "("])
        self.compile_expression()
        self.eat([")", "{"])
        self.compile_statements()
        self.eat(["}"])
        self.output_file.write("</whileStatement>\n")

    def compile_return(self):
        """
        Compiles a return statement, which may contain one expression.
        """
        self.output_file.write("<returnStatement>\n")
        self.eat(["return"])
        
        # Check whether the return statement returns an expression
        if self.tokeniser.tokens[0] != ";":
            self.compile_expression()
        
        self.eat([";"])
        self.output_file.write("</returnStatement>\n")

    # Methods for compiling program structure.
    def compile_class(self):
        """
        Compiles a complete class.
        """
        class_vars = ["static", "field"]
        subroutines = ["constructor", "function", "method"] 

        self.output_file.write("<class>\n")
        self.eat(["class", "className", "{"])

        # Compile any class variables
        if self.tokeniser.tokens[0] in class_vars:
            while True:
                self.compile_class_var_dec()
                if self.tokeniser.tokens[0] not in class_vars:
                    break
        
        # Compile any subroutines 
        if self.tokeniser.tokens[0] in subroutines:
            while True:
                self.compile_subroutine()
                if self.tokeniser.tokens[0] not in subroutines:
                    break

        self.eat(["}"])
        self.output_file.write("</class>\n")
    
    def compile_class_var_dec(self):
        """
        Compiles a static or field declaration.
        """
        self.output_file.write("<classVarDec>\n")
        self.eat(["static|field", "int|char|boolean|className", "varName"])

        # Check for multiple variable declarations of same type
        if self.tokeniser.tokens[0] != ";":
            while True:
                self.eat([",", "varName"])
                if self.tokeniser.tokens[0] == ";":
                    break

        self.eat(";")
        self.output_file.write("</classVarDec>\n")
    
    def compile_subroutine(self):
        """
        Compiles a complete method, function, or constructor.
        """
        # Compile subroutine declaration
        self.output_file.write("<subroutineDec>\n")
        self.eat(["constructor|function|method", "int|char|boolean|void", "varName", "("])
        self.compile_parameter_list()
        self.eat([")"])

        # Compile subroutine body
        self.output_file.write("<subroutineBody>\n")
        self.eat(["{"])

        if self.tokeniser.tokens[0] == "var":
            while True:
                self.compile_var_dec()
                if self.tokeniser.tokens[0] != "var":
                    break
        
        statement_types = ["let", "if", "while", "do", "return"] 
        if self.tokeniser.tokens[0] in statement_types:
            while True:
                self.compile_statements()
                if self.tokeniser.tokens[0] not in statement_types:
                    break 

        self.eat(["}"])
        self.output_file.write("</subroutineBody>\n")
        self.output_file.write("</subroutineDec>\n")
    
    def compile_parameter_list(self):
        """
        Compiles a (possibly empty) parameter list, not including the ().
        """
        self.output_file.write("<parameterList>\n")
        
        if self.tokeniser.tokens[0] != ")":
            while True:
                self.eat(["int|char|boolean|className", "varName"])
                if self.tokeniser.tokens[0] == ")":
                    break
                self.eat([","])

        self.output_file.write("</parameterList>\n")
    
    def compile_var_dec(self):
        """
        Compiles a variable declaration.
        """
        self.output_file.write("<varDec>\n")  
        self.eat(["var", "int|char|boolean|className", "varName"])

        # Check for multiple variable declarations of same type
        if self.tokeniser.tokens[0] != ";":
            while True:
                self.eat([",", "varName"])
                if self.tokeniser.tokens[0] == ";":
                    break

        self.eat([";"])
        self.output_file.write("</varDec>\n")

    # Methods for compiling expressions.
    def compile_subroutine_call(self):
        """
        Compiles subroutine call.
        """
        if self.tokeniser.tokens[1] == ".":
            self.eat(["className|varName"])
            self.eat(["."])

        self.eat(["subroutineName"])
        self.eat(["("])
        self.compile_expression_list()
        self.eat([")"])

    def compile_expression(self):
        """
        Compiles an expression.
        """
        op = ["+", "-", "*", "/", "&", "|", "<", ">", "="]

        self.output_file.write("<expression>\n")
        self.compile_term()

        # Check for multi-component term
        if self.tokeniser.tokens[0] in op:
            while True:
                self.eat([self.tokeniser.tokens[0]])
                self.compile_term()
                if self.tokeniser.tokens[0] not in op:
                    break

        self.output_file.write("</expression>\n")

    def compile_expression_list(self):
        """
        Compiles a (possibly empty) comma-separated list of expressions.
        """
        self.output_file.write("<expressionList>\n")

        if self.tokeniser.tokens[0] != ")":
            while True:
                self.compile_expression()
                if self.tokeniser.tokens[0] == ")":
                    break
                self.eat([","])

        self.output_file.write("</expressionList>\n")
    
    def compile_term(self):
        """
        Compiles a term.
        """
        self.output_file.write("<term>\n")  

        # If current token is an identifier, test whether it is a variable,
        # an array entry, or a subroutine call by looking ahead one token.
        if self.tokeniser.token_type() == "IDENTIFIER":
            if self.tokeniser.tokens[1] == "[":             # array entry
                self.eat(["varName"])
                self.eat(["["])
                self.compile_expression()
                self.eat(["]"])
            elif self.tokeniser.tokens[1] == ("." or "("):    # subroutine call
                self.compile_subroutine_call()
            else:                                           # variable
                self.eat(["varName"])
        
        else:
            if self.tokeniser.tokens[0] == "(":             # (expression)
                self.eat(["("])
                self.compile_expression()
                self.eat(")")
            elif self.tokeniser.tokens[0] in ["-", "~"]:    # unaryOp term
                self.eat(["-|~"])
                self.compile_term()
            else:
                self.eat(["STRING_CONST|INT_CONST|KEYWORD"])
        
        self.output_file.write("</term>\n")


class Initialiser():
    """
    Facilitates access to the .jack files that are to be translated. Contains
    some helper functions for the main translation process.
    """

    def __init__(self, cli):
        """
        All instances have a list of .jack files to be translated available
        as an attribute. The argument for constructing instances of this class
        are command line arguments (cli).
        """
        if '.jack' in cli:
            ls = [cli]
        else:
            ls = [cli + '/' + x for x in os.listdir(cli) if '.jack' in x]
        
        self.files = ls