"""
Operates on a given command line argument, which points to either a .jack
file or a directory containing one or more such files. This program analyses
the syntax of the given .jack class files and emits VM commands. Since the
Jack grammar is LL(1), a recursive parsing algorithm (see CompilationEngine)
does the job nicely.
"""

import sys
import os
from utils import (
    JackTokeniser, Initialiser, CompilationEngine, SymbolTable, VMWriter
)

def main():
    """
    The driver for the Jack syntax analyser. Responsible for setting up and
    invoking Initialiser, JackTokeniser, SymbolTable, and CompilationEngine. 
    """
    # Pass Initialiser the cli to generate array of .jack files for compilation
    initialiser = Initialiser(sys.argv[1])

    # Generate dict of input files for translation and output files for writing
    file_names = {}
    for input_file in initialiser.files:
        vm_file = input_file.replace('jack', 'vm')
        file_names[input_file] = vm_file

    # Compile every .jack file and write to output
    for input_file, output_file in file_names.items():
        # Tokenise the input
        tokeniser = JackTokeniser(input_file)
        # Create a symbol table for the Jack class            
        symbol_table = SymbolTable(tokeniser) 
        # Create a vm_writer             
        vm_writer = VMWriter(output_file) 
        # Prepare the compilation engine, compile the class, and close
        engine = CompilationEngine(tokeniser, symbol_table, vm_writer)
        engine.compile_class()                            
        vm_writer.close() 

main()