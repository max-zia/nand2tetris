import sys
from utils import Parser, CodeWriter, Initialiser

def main():
	# Create initialiser instance, and pass it command line argument
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
			initialiser.translate_file(parser, code_writer)

	code_writer.close()

main()
