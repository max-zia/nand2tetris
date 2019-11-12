import os       # os.listdir() returns everything in a directory
import re       # re.split(pattern, string) splits string by pattern  
import sys      # sys.exit() raised on syntax error
import uuid     # module used to generate unique IDs for VM labels
from helpers import collapse_string_constants

class JackTokeniser:
    """
    Removes all comments and whitespace from the input stream and breaks it
    into Jack-language tokens, as specified by the Jack grammar.
    """

    def __init__(self, input_file):
        """
        Constructs class with an array of tokens and a token pointer.
        """
        self.tokens = self.get_tokens(input_file)
        self.token_index = 0 
    
    def get_tokens(self, input_file):
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

        return tokens

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


class CompilationEngine:
    """
    Effects the compilation output. Takes a JackTokeniser and emits its 
    parsed structure into an output file.
    """

    def __init__(self, tokeniser, symbol_table, output_file, vm_writer):
        """
        Initialises all instances with a tokeniser and an open output file.
        """
        self.tokeniser = tokeniser
        self.vm_writer = vm_writer
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

    def get_id(self):
        """
        Generates a 3-character ID to ensure that all VM labels are unique. 
        """
        return uuid.uuid4().hex[:3]

    def get_methods(self):
        """
        Returns a list of methods that are in the current class.
        """
        methods = []
        i = 0
        while i < len(self.tokeniser.tokens):
            if self.tokeniser.tokens[i] == "method":
                methods.append(self.tokeniser.tokens[i + 2])
            i += 1
        
        return methods

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

        while True:
            dispatcher[self.tokeniser.current_token()]()
            if (self.tokeniser.current_token() not in dispatcher):
                break

    def compile_let(self):
        """
        Compiles a let statement.
        """
        # Array flag to signal whether a let arr[i] = x is being handled
        arr_flag = False

        # Dispatcher for checking variable scope 
        dispatcher = {
            0: self.symbol_table.subroutine_scope,
            1: self.symbol_table.class_scope
        }

        # VM code equivalent of variable "kinds"
        vars = {
            "ARG": "argument",
            "VAR": "local",
            "FIELD": "this",
            "STATIC": "static"
        }
        
        # Begin compiling
        self.eat(["let"]) 
        
        # Get varname, kind, and index by checking variable scope
        var_name = self.tokeniser.current_token()

        if var_name in self.symbol_table.subroutine_scope:
            key = 0
        elif var_name in self.symbol_table.class_scope:
            key = 1

        kind = vars[dispatcher[key][var_name][1]]
        index = dispatcher[key][var_name][2]

        self.eat(["varName"])

        # If necessary, handle array manipulation
        if self.tokeniser.current_token() == "[":
            arr_flag = True
            self.eat(["["])
            self.compile_expression()
            self.eat(["]"])
            self.vm_writer.write_push(kind, index)
            self.vm_writer.write_arithmetic("add")

        self.eat(["="])
        self.compile_expression()
        self.eat([";"]) 

        if arr_flag:
            # VM commands for writing a value into an arr[i]
            self.vm_writer.write_pop("temp", 0)
            self.vm_writer.write_pop("pointer", 1)
            self.vm_writer.write_push("temp", 0)
            self.vm_writer.write_pop("that", 0)
        else:
            # Pop the evaluated expression (which has just been placed
            # at the top of the stack) to var_name.        
            self.vm_writer.write_pop(kind, index)

    def compile_if(self):
        """
        Compiles an if statement, possibly with a trailing else clause.
        """
        self.eat(["if", "("])
        self.compile_expression()
        self.eat([")", "{"])

        # Compile body of IF and write to VM file
        id = self.get_id()
        self.vm_writer.write_if("IF_TRUE_" + id)
        self.vm_writer.write_goto("IF_FALSE_" + id)
        self.vm_writer.write_label("IF_TRUE_" + id)

        self.compile_statements()
        self.eat(["}"])
        
        # Check for trailing ELSE clause and compile if it exists
        if self.tokeniser.current_token() == "else":
            self.vm_writer.write_goto("IF_END_" + id)
            self.vm_writer.write_label("IF_FALSE_" + id)
            self.eat(["else", "{"])
            self.compile_statements()
            self.eat(["}"])
            self.vm_writer.write_label("IF_END_" + id)
        else:
            self.vm_writer.write_label("IF_FALSE_" + id)

    def compile_do(self):
        """
        Compiles a do statement and the subroutine call.
        """
        self.eat(["do"])
        self.compile_subroutine_call()
        self.eat([";"])

        # When compiling a do "sub" statement, where "sub" is a void method
        # or function, the caller of the corresponding VM function must pop
        # (and ignore) the returned value (which is always the constant 0).
        self.vm_writer.write_pop("temp", 0)

    def compile_while(self):
        """
        Compiles a while statement.
        """
        # Write WHILE_EXPRESSION label to VM file
        id = self.get_id()
        self.vm_writer.write_label("WHILE_EXP_" + id)

        # Continue compilation
        self.eat(["while", "("])
        self.compile_expression()

        # A boolean will have just been pushed to the stack due to the
        # expression that was just compiled. Therefore, test whether the while
        # loop code should be executed by negating this truth value, and
        # then writing an if-goto command. If false (value = 0), go to 
        # WHILE_END{id}, else continue. 
        self.vm_writer.write_arithmetic("not")
        self.vm_writer.write_if("WHILE_END_" + id)

        # Continue compilation
        self.eat([")", "{"])
        self.compile_statements()
        self.eat(["}"])

        # Write WHILE_END goto and end label to VM file
        self.vm_writer.write_goto("WHILE_EXP_" + id)
        self.vm_writer.write_label("WHILE_END_" + id)

    def compile_return(self):
        """
        Compiles a return statement, which may contain one expression.
        """
        self.eat(["return"])
        
        # Check whether the return statement returns an expression
        if self.tokeniser.current_token() != ";":
            self.compile_expression()
            self.vm_writer.write_return()
        else:
            self.vm_writer.write_push("constant", 0)
            self.vm_writer.write_return()
        
        self.eat([";"])

    # Methods for compiling program structure.
    def compile_class(self):
        """
        Compiles a complete class.
        """
        class_vars = ["static", "field"]
        subroutines = ["constructor", "function", "method"] 

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
    
    def compile_class_var_dec(self):
        """
        Compiles a static or field declaration.
        """
        # Update symbol table and eat tokens
        kind = self.tokeniser.current_token().upper()
        self.eat(["static|field"])

        type = self.tokeniser.current_token()
        self.eat(["int|char|boolean|className"]) 

        self.update_st(self.tokeniser.current_token(), type, kind)
        self.eat(["varName"])

        # Check for multiple variable declarations of same type and kind
        if self.tokeniser.current_token() != ";":
            while True:
                self.eat([","])
                self.update_st(self.tokeniser.current_token(), type, kind)
                self.eat(["varName"])
                if self.tokeniser.current_token() == ";":
                    break

        self.eat(";")
    
    def compile_subroutine(self):
        """
        Compiles a complete method, function, or constructor.
        """

        def compile_constructor():
            """
            Compiles constructor-specific VM commands.
            """
            # Count field variables to determine how many words in host RAM are
            # needed to represent an object instance of this class type.
            n_field_vars = 0
            for symbol, array in self.symbol_table.class_scope.items():
                kind = array[1]
                if kind == "FIELD":
                    n_field_vars += 1
            # Write VM commands
            self.vm_writer.write_push("constant", n_field_vars)
            self.vm_writer.write_call("Memory.alloc", 1)
            self.vm_writer.write_pop("pointer", 0)
        
        def update_method_st():
            """
            Updates method symbol table.
            """
            # The first argument for any method must be a reference to the object
            # on which the method is supposed to operate. Also, whenever a method
            # is defined, THIS (i.e., pointer 0) must be set to the base address
            # held in argument 0.
            self.symbol_table.define("this", self.tokeniser.tokens[1], "ARG")
        
        def compile_method():
            """
            Compiles method-specific VM commands.
            """
            self.vm_writer.write_push("argument", 0)
            self.vm_writer.write_pop("pointer", 0)

        # Reset the subroutine_scope symbol table for each new subroutine
        self.symbol_table.start_subroutine()
        subroutine_type = self.tokeniser.current_token()

        # Begin compiling subroutine declaration
        self.eat(["constructor|function|method"])
        self.eat(["int|char|boolean|void"])
        
        # Get subroutine name and continue
        name = self.tokeniser.tokens[1] + '.' + self.tokeniser.current_token()
        self.eat(["varName", "("])
        if subroutine_type == "method":
            update_method_st()
        self.compile_parameter_list()
        self.eat([")"])

        # Compile subroutine body
        self.eat(["{"])

        # Continue by compiling local variable declarations
        if self.tokeniser.current_token() == "var":
            while True:
                self.compile_var_dec()
                if self.tokeniser.current_token() != "var":
                    break

        # WRITE FUNCTION NAME TO VM FILE
        n_locals = self.symbol_table.var_count("VAR") 
        self.vm_writer.write_function(name, n_locals)

        # You could replace the following compile x with a DISPATCHER
        # COMPILE METHOD
        if subroutine_type == "method":
            compile_method()

        # COMPILE CONSTRUCTOR
        elif subroutine_type == "constructor":
            compile_constructor()
        
        # Continue by compiling statements in subroutine
        statement_types = ["let", "if", "while", "do", "return"] 
        if self.tokeniser.current_token() in statement_types:
            while True:
                self.compile_statements()
                if self.tokeniser.current_token() not in statement_types:
                    break 

        self.eat(["}"])

    def compile_parameter_list(self):
        """
        Compiles a (possibly empty) parameter list, not including the ().
        """
        if self.tokeniser.current_token() != ")":
            while True:
                type = self.tokeniser.current_token()
                self.eat(["int|char|boolean|className"])
                self.update_st(self.tokeniser.current_token(), type, "ARG")
                self.eat(["varName"])
                if self.tokeniser.current_token() == ")":
                    break
                self.eat([","])
    
    def compile_var_dec(self):
        """
        Compiles a variable declaration.
        """
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

    # Methods for compiling expressions.
    def compile_subroutine_call(self):
        """
        Compiles subroutine call.
        """
        subroutine_name = ""
        object_name = ""

        # Check whether the subroutine is attached to a user-defined or OS type
        if self.tokeniser.tokens[self.tokeniser.token_index + 1] == ".":
            object_name = self.tokeniser.current_token()
            self.eat(["className|varName", "."])

        subroutine_name += self.tokeniser.current_token()
        self.eat(["subroutineName", "("])

        # WRITE TO VM FILE
        n_args = 0
        st = self.symbol_table
        if len(object_name) > 0:
            if object_name in st.subroutine_scope:
                n_args += 1
                ref = st.subroutine_scope[object_name] 
                self.vm_writer.write_push("local", ref[2])
                subroutine_name = ref[0] + "." + subroutine_name
            elif object_name in st.class_scope:
                n_args += 1
                ref = st.class_scope[object_name] 
                self.vm_writer.write_push("this", ref[2])
                subroutine_name = ref[0] + "." + subroutine_name
            else: 
                subroutine_name = object_name + "." + subroutine_name

        elif subroutine_name in self.get_methods():
            n_args += 1
            subroutine_name = self.tokeniser.tokens[1] + "." + subroutine_name
            self.vm_writer.write_push("pointer", 0)

        n_args += self.compile_expression_list()
        self.eat([")"])


        self.vm_writer.write_call(subroutine_name, n_args)        

    def compile_expression(self):
        """
        Compiles an expression.
        """
        operators = {
            "+": "add", 
            "-": "sub",
            "*": "call Math.multiply 2",
            "/": "call Math.divide 2",
            "&": "and",
            "|": "or",
            "<": "lt", 
            ">": "gt",
            "=": "eq"
        }

        self.compile_term()

        # Check for multi-component term and write expression to file in
        # reverse Polish notation (i.e., operator comes last).
        if self.tokeniser.current_token() in operators:
            while True:
                operator = self.tokeniser.current_token()
                self.eat([self.tokeniser.current_token()])
                self.compile_term()

                # WRITE TO VM FILE
                self.vm_writer.write_arithmetic(operators[operator])
                
                # Check for another operator in the expression
                if self.tokeniser.current_token() not in operators:
                    break

    def compile_expression_list(self):
        """
        Compiles a (possibly empty) comma-separated list of expressions. Returns
        the number of expressions contained in the list.
        """
        # i counts the number of expressions in this expression list
        i = 0
        if self.tokeniser.current_token() != ")":
            i = 1
            while True:
                self.compile_expression()
                if self.tokeniser.current_token() == ")":
                    break
                self.eat([","])
                i += 1

        return i
    
    def compile_term(self):
        """
        Compiles a term.
        """
        # VM code equivalent of unary operators
        unary_operators = {
            "-": "neg",
            "~": "not"
        }

        # VM code equivalent of variable "kinds"
        vars = {
            "ARG": "argument",
            "VAR": "local",
            "FIELD": "this",
            "STATIC": "static"
        }

        # If current token is an identifier, test whether it is a variable,
        # an array entry, or a subroutine call by looking ahead one token.
        if self.tokeniser.token_type() == "IDENTIFIER":

            # Subroutine call
            if self.tokeniser.tokens[self.tokeniser.token_index + 1] == ("." or "("):
                self.compile_subroutine_call()

            # Variable or array manipulation
            else:
                var_name = self.tokeniser.current_token()
                # Dispatcher for checking variable scope 
                dispatcher = {
                    0: self.symbol_table.subroutine_scope,
                    1: self.symbol_table.class_scope
                }

                # Get variable kind and index
                if var_name in self.symbol_table.subroutine_scope:
                    key = 0
                elif var_name in self.symbol_table.class_scope:
                    key = 1

                kind = vars[dispatcher[key][var_name][1]]
                index = dispatcher[key][var_name][2]

                # Array entry
                if self.tokeniser.tokens[self.tokeniser.token_index + 1] == "[":
                    self.eat(["varName"])
                    self.eat(["["])
                    self.compile_expression()
                    self.eat(["]"])
                    self.vm_writer.write_push(kind, index)
                    self.vm_writer.write_arithmetic("add")
                    self.vm_writer.write_pop("pointer", 1)
                    self.vm_writer.write_push("that", 0)

                # Variable
                else:
                    self.vm_writer.write_push(kind, index)
                    self.eat(["varName"])

        else:
            # ( expression )
            if self.tokeniser.current_token() == "(":
                self.eat(["("])
                self.compile_expression()
                self.eat(")")

            # unary operator term
            elif self.tokeniser.current_token() in unary_operators:
                command = self.tokeniser.current_token()
                self.eat(["-|~"])
                self.compile_term()
                self.vm_writer.write_arithmetic(unary_operators[command])

            # keyword, string, or integer constants
            else:
                value = self.tokeniser.current_token()
                # String constant
                if self.tokeniser.token_type() == "STRING_CONST":
                    string = self.tokeniser.string_val()
                    self.vm_writer.write_string_constant(string)

                # Integer constant
                elif self.tokeniser.token_type() == "INT_CONST":
                    self.vm_writer.write_push("constant", value)

                # Boolean expressions
                elif value == "false" or value == "null":
                    self.vm_writer.write_push("constant", 0)
                elif value == "true":
                    self.vm_writer.write_push("constant", 1)
                    self.vm_writer.write_arithmetic("neg")
                
                # Pointers
                elif value == "this":
                    self.vm_writer.write_push("pointer", 0)


                self.eat(["STRING_CONST|INT_CONST|KEYWORD"])


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
    
    def start_subroutine(self):
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
    
    def var_count(self, kind):
        """
        Returns the number of variables of the given kind already defined
        in the current scope.
        """
        i = 0
        for k, v in self.subroutine_scope.items():
            if self.subroutine_scope[k][1] == kind:
                i += 1
        return i

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


class VMWriter:
    """
    Emits VM commands into a file, using the VM command syntax.
    """

    def __init__(self, output_file):
        """
        Creates a new file and prepares it for writing.
        """
        self.output_file = open(output_file, 'w')

    def close(self):
        """
        Closes the output_file.
        """
        self.output_file.close()
    
    def write_push(self, segment, index):
        """
        Writes a VM push command.
        """
        self.output_file.write(f"push {segment} {index}\n")
    
    def write_pop(self, segment, index):
        """
        Writes a VM pop command.
        """
        self.output_file.write(f"pop {segment} {index}\n")
    
    def write_function(self, name, n_locals):
        """
        Writes a VM function command.
        """
        self.output_file.write(f"function {name} {n_locals}\n")
    
    def write_call(self, name, n_args):
        """
        Writes a VM call command.
        """
        self.output_file.write(f"call {name} {n_args}\n")
    
    def write_arithmetic(self, command):
        """
        Writes a VM arithmetic command.
        """
        self.output_file.write(f"{command}\n")
    
    def write_return(self):
        """
        Writes a VM return command.
        """
        self.output_file.write("return\n")
    
    def write_label(self, label):
        """
        Writes a VM label command.
        """
        self.output_file.write(f"label {label}\n")
    
    def write_if(self, label):
        """
        Write a VM if-goto command.
        """
        self.output_file.write(f"if-goto {label}\n")
    
    def write_goto(self, label):
        """
        Write a VM goto command.
        """
        self.output_file.write(f"goto {label}\n")

    def write_string_constant(self, string):
        """
        Writes VM code for a string constant.
        """
        self.write_push("constant", len(string))
        self.write_call("String.new", 1)
        for char in string:
            self.write_push("constant", ord(char))
            self.write_call("String.appendChar", 2)

class Initialiser:
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