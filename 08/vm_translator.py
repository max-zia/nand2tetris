import sys 				# sys.argv returns a list of command line arguments
from utils import Parser, CodeWriter, Initialiser

# Create initialiser instance
initialiser = Initialiser(sys.argv[1])

# Create code_writer instance and write bootstrap code to file
code_writer = CodeWriter(initialiser.asm_filename)
code_writer.write_init()

# Create list of parsers, one for each vm_file
parsers = [Parser(x) for x in initialiser.vm_files]

for parser in parsers:
	# Set filename of parser that is currently being translated
	code_writer.set_filename(parser.filename)

	# Parse the VM file
	while parser.has_more_commands():
		command = parser.command_type()

		# Stack arithmetic commands
		if command == 'C_ARITHMETIC':
			code_writer.write_arithmetic(parser.arg1())

		# Memory access commands
		elif command == 'C_PUSH' or command == 'C_POP':
			code_writer.write_push_pop(command, parser.arg1(), parser.arg2())

		# Program flow commands
		elif command == 'C_LABEL':
			code_writer.write_label(parser.arg1())
		elif command == 'C_GOTO':
			code_writer.write_goto(parser.arg1())
		elif command == 'C_IF':
			code_writer.write_if(parser.arg1())

		# Function calling commands
		elif command == 'C_CALL':
			code_writer.write_call(parser.arg1(), parser.arg2())
		elif command == 'C_FUNCTION':
			code_writer.write_function(parser.arg1(), parser.arg2())
		elif command == 'C_RETURN':
			code_writer.write_return()

		parser.advance()

code_writer.close()