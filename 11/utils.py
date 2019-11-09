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

        self.tokens = tokens        # array for all tokens (as field var)
        self.token_index = 0        # pointer for current token (as field var)
    
    def current_token(self):
        """
        Returns the token that the token_index pointer is pointing to.
        """
        return self.tokens[self.token_index]

    def has_more_tokens(self):
        """
        Returns true if there are more tokens in the input.
        """
        if (len(self.tokens) - 1) > self.token_index:
            return True
    
    def advance(self):
        """
        Increments the token pointer.
        """
        self.token_index += 1
    
    def token_type(self):
        """
        Returns the type of the 'current' token.
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
        if self.current_token() in keywords:
            return 'KEYWORD'
        elif self.current_token() in symbols:
            return 'SYMBOL'
        elif '"' in self.current_token():
            return 'STRING_CONST'
        else:
            try:
                int(self.current_token())
                return 'INT_CONST'
            except ValueError:
                return 'IDENTIFIER'

    # Methods for returning the value of the current token.
    def keyword(self):
        return self.current_token()

    def symbol(self):
        return self.current_token()
    
    def identifier(self):
        return self.current_token()
    
    def int_val(self):
        return int(self.current_token())
    
    def string_val(self):
        return self.current_token()[1:-1]


class CompilationEngine():
    """
    Effects the compilation output. Takes a JackTokeniser and emits its 
    parsed structure into an output file.
    """

    def __init__(self, tokeniser, symbol_table, output_file):
        """
        Initialises all instances with a tokeniser and an open output file.
        """
        self.tokeniser = tokeniser
        self.symbol_table = symbol_table
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
        type = self.tokeniser.token_type()
        replace_text = ''

        # Get the XML tagname and text
        if type == 'SYMBOL':
            if self.tokeniser.symbol() == '&':
                replace_text = '&amp;'
            if self.tokeniser.symbol() == '<':
                replace_text = '&lt;'
            if self.tokeniser.symbol() == '>':
                replace_text = '&gt;'
            
            text = self.tokeniser.symbol()
            tag = type.lower()

        elif type == 'IDENTIFIER':
            text = self.tokeniser.identifier()
            tag = type.lower()

        elif type == 'KEYWORD':
            text = self.tokeniser.keyword()
            tag = type.lower()

        elif type == 'STRING_CONST':
            text = self.tokeniser.string_val()
            tag = 'stringConstant'

        elif type == 'INT_CONST':
            text = self.tokeniser.int_val()
            tag = 'integerConstant'

        # Write to file
        if type == "IDENTIFIER":
            st = self.symbol_table

            if text in st.subroutine_scope or text in st.class_scope:
                self.output_file.write(f'<{tag}>\n')
                self.output_file.write(f'\t<name> {text} </name>\n')
                self.output_file.write(f'\t<type> {st.type_of(text)} </type>\n')
                self.output_file.write(f'\t<kind> {st.kind_of(text)} </kind>\n')
                self.output_file.write(f'\t<index> {st.index_of(text)} </index>\n')
                self.output_file.write(f'</{tag}>\n')
            
            else:
                self.output_file.write(f'<{tag}>\n')
                self.output_file.write(f'\t<name> {text} </name>\n')
                self.output_file.write(f'</{tag}>\n')

        elif len(replace_text) == 0:
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
            if self.tokeniser.current_token() in token.split("|") or (
                ("varName" or "subroutineName" or "className" in token.split("|")) 
                and (self.tokeniser.token_type() == "IDENTIFIER")) or (
                ("INT_CONST" or "STRING_CONST" or "KEYWORD" in token.split("|"))
            ):
                self.write_current_token()
                self.tokeniser.advance()
            else:
                sys.exit(f"SyntaxError: expected {token} not {self.tokeniser.current_token()}")
    
    def update_st(self, name, type, kind):
        """
        Updates symbol table if an identifier with given name doesn't exist.
        """
        st = self.symbol_table
        if name not in st.subroutine_scope and name not in st.class_scope:
            self.symbol_table.define(name, type, kind)

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
            dispatcher[self.tokeniser.current_token()]()
            if (self.tokeniser.current_token() not in dispatcher):
                break
        self.output_file.write("</statements>\n")

    def compile_let(self):
        """
        Compiles a let statement.
        """
        self.output_file.write("<letStatement>\n")
        self.eat(["let", "varName"])

        if self.tokeniser.current_token() == "[":
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
            if self.tokeniser.current_token() == "else":
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
        if self.tokeniser.current_token() != ";":
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
        if self.tokeniser.current_token() in class_vars:
            while True:
                self.compile_class_var_dec()
                if self.tokeniser.current_token() not in class_vars:
                    break
        
        # Compile any subroutines 
        if self.tokeniser.current_token() in subroutines:
            while True:
                self.compile_subroutine()
                if self.tokeniser.current_token() not in subroutines:
                    break

        self.eat(["}"])
        self.output_file.write("</class>\n")
    
    def compile_class_var_dec(self):
        """
        Compiles a static or field declaration.
        """
        self.output_file.write("<classVarDec>\n")

        # Update symbol table and eat tokens
        kind = self.tokeniser.current_token()
        self.eat(["static|field"])

        type = self.tokeniser.current_token()
        self.eat(["int|char|boolean|className"]) 

        self.update_st(self.tokeniser.current_token(), type, kind)
        self.eat(["varName"])

        # Check for multiple variable declarations of same type
        if self.tokeniser.current_token() != ";":
            while True:
                self.eat([","])
                self.update_st(self.tokeniser.current_token(), type, kind)
                self.eat(["varName"])
                if self.tokeniser.current_token() == ";":
                    break

        self.eat(";")
        self.output_file.write("</classVarDec>\n")
    
    def compile_subroutine(self):
        """
        Compiles a complete method, function, or constructor.
        """
        # Compile subroutine declaration and update symbol table
        self.output_file.write("<subroutineDec>\n")
        
        # Reset the subroutine_scope symbol table for each new subroutine
        self.symbol_table.startSubroutine()

        # The first argument for any method must be a reference to the object
        # on which the method is supposed to operate.
        if self.tokeniser.current_token() == "method":
            self.symbol_table.define("this", self.tokeniser.tokens[1], "ARG")

        # Compile rest of subroutine declaration
        self.eat(["constructor|function|method"])
        self.eat(["int|char|boolean|void", "varName", "("])
        self.compile_parameter_list()
        self.eat([")"])

        # Compile subroutine body
        self.output_file.write("<subroutineBody>\n")
        self.eat(["{"])

        if self.tokeniser.current_token() == "var":
            while True:
                self.compile_var_dec()
                if self.tokeniser.current_token() != "var":
                    break
        
        statement_types = ["let", "if", "while", "do", "return"] 
        if self.tokeniser.current_token() in statement_types:
            while True:
                self.compile_statements()
                if self.tokeniser.current_token() not in statement_types:
                    break 

        self.eat(["}"])
        self.output_file.write("</subroutineBody>\n")
        self.output_file.write("</subroutineDec>\n")
    
    def compile_parameter_list(self):
        """
        Compiles a (possibly empty) parameter list, not including the ().
        """
        self.output_file.write("<parameterList>\n")
        
        if self.tokeniser.current_token() != ")":
            while True:
                type = self.tokeniser.current_token()
                self.eat(["int|char|boolean|className"])
                self.update_st(self.tokeniser.current_token(), type, "ARG")
                self.eat(["varName"])
                if self.tokeniser.current_token() == ")":
                    break
                self.eat([","])

        self.output_file.write("</parameterList>\n")
    
    def compile_var_dec(self):
        """
        Compiles a variable declaration.
        """
        self.output_file.write("<varDec>\n")  
        self.eat(["var"])

        # Update symbol table and eat tokens
        type = self.tokeniser.current_token()
        self.eat(["int|char|boolean|className"])
        self.update_st(self.tokeniser.current_token(), type, "VAR")
        self.eat(["varName"])

        # Check for multiple variable declarations of same type
        if self.tokeniser.current_token() != ";":
            while True:
                self.eat([","])
                self.update_st(self.tokeniser.current_token(), type, "VAR")
                self.eat(["varName"])
                if self.tokeniser.current_token() == ";":
                    break

        self.eat([";"])
        self.output_file.write("</varDec>\n")

    # Methods for compiling expressions.
    def compile_subroutine_call(self):
        """
        Compiles subroutine call.
        """
        if self.tokeniser.tokens[self.tokeniser.token_index + 1] == ".":
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
        if self.tokeniser.current_token() in op:
            while True:
                self.eat([self.tokeniser.current_token()])
                self.compile_term()
                if self.tokeniser.current_token() not in op:
                    break

        self.output_file.write("</expression>\n")

    def compile_expression_list(self):
        """
        Compiles a (possibly empty) comma-separated list of expressions.
        """
        self.output_file.write("<expressionList>\n")

        if self.tokeniser.current_token() != ")":
            while True:
                self.compile_expression()
                if self.tokeniser.current_token() == ")":
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
            # array entry
            if self.tokeniser.tokens[self.tokeniser.token_index + 1] == "[":
                self.eat(["varName"])
                self.eat(["["])
                self.compile_expression()
                self.eat(["]"])
            # subroutine call
            elif self.tokeniser.tokens[self.tokeniser.token_index + 1] == ("." or "("):
                self.compile_subroutine_call()
            # variable
            else:                                   
                self.eat(["varName"])
        
        else:
            # ( expression )
            if self.tokeniser.current_token() == "(":
                self.eat(["("])
                self.compile_expression()
                self.eat(")")
            # unary operator term
            elif self.tokeniser.current_token() in ["-", "~"]:
                self.eat(["-|~"])
                self.compile_term()
            # constant
            else:
                self.eat(["STRING_CONST|INT_CONST|KEYWORD"])
        
        self.output_file.write("</term>\n")


class SymbolTable:
    """
    Provides a symbol table abstraction. Associates identifier names found
    in the program with identifier properties needed for compilation (i.e., 
    type, kind, and running index). Has two nested scopes for class and subroutine.
    """
    
    def __init__(self, tokeniser):
        """
        Creates a new empty symbol table, which consists of two independent 
        hash tables (i.e., python dictionaries). Also, SymbolTables are 
        constructed with tokenisers of the class file they are being applied to.
        """
        self.tokeniser = tokeniser
        self.class_scope = {}
        self.subroutine_scope = {}
        
        # Hash table for running indices of each "kind" for each scope
        self.class_indices = {
            "STATIC": 0,
            "FIELD": 0,
            "ARG": 0,
            "VAR": 0
        }

        self.subroutine_indices = {
            "STATIC": 0,
            "FIELD": 0,
            "ARG": 0,
            "VAR": 0
        }
    
    def startSubroutine(self):
        """
        Starts a new subroutine scope (i.e., resets self.subroutine_scope).
        """
        self.subroutine_scope = {}                      # reset symbol table
        for k, v in self.subroutine_indices.items():    # reset indices
            self.subroutine_indices[k] = 0
    
    def define(self, name, type, kind):
        """
        Defines a new identifier of a given name, type, and kind, and assigns
        it a running index. Finishes by incrementing index for correct kind.
        """
        if kind == "FIELD" or kind == "STATIC":
            index = self.class_indices[kind]
            self.class_scope[name] = [type, kind, index]
            self.class_indices[kind] += 1

        elif kind == "ARG" or kind == "VAR":
            index = self.subroutine_indices[kind]
            self.subroutine_scope[name] = [type, kind, index]
            self.subroutine_indices[kind] += 1
    
    def index_of(self, name):
        """
        Returns the index assigned to the named identifier.
        """
        if name in self.subroutine_scope:
            return self.subroutine_scope[name][2] 
        elif name in self.class_scope:
            return self.class_scope[name][2] 
    
    def type_of(self, name):
        """
        Returns the type of the named identifier in the current scope.
        """
        if name in self.subroutine_scope:
            return self.subroutine_scope[name][0] 
        elif name in self.class_scope:
            return self.class_scope[name][0] 

    def kind_of(self, name):
        """
        Returns the kind of the named identifier in the current scope.
        """
        if name in self.subroutine_scope:
            return self.subroutine_scope[name][1] 
        elif name in self.class_scope:
            return self.class_scope[name][1]


class Initialiser():
    """
    Facilitates access to the .jack files that are to be translated.
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