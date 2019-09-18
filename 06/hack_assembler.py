import hack_parser as parser, code, symbol_table as st
import sys 		# sys.argv returns a list of command line arguments

def char_test(chars, symbol_table, RAM_counter):
	"""
	Test whether the chars in an A-instruction represent an int or symbol. If 
	symbol, consult the symbol table and replace symbol with RAM address (if
	symbol not found, update symbol table). Return modified version of chars, 
	updated symbol_table, and updated RAM_counter.     
	"""
	try:
		int(chars)
	except ValueError:
		# Therefore, chars is a symbol
		if st.contains(chars, symbol_table):
			# Replace chars with numeric address in RAM or ROM
			chars = st.get_address(chars, symbol_table)
		else:
			# chars not found in symbol_table, thus is new variable
			st.add_entry(chars, RAM_counter, symbol_table)
			chars = RAM_counter # Replace chars with RAM address
			RAM_counter += 1

	return {'c': chars, 'st': symbol_table, 'ram': RAM_counter}

def first_pass(commands, symbol_table):
	"""
	Pass through the assembly program's commands and build the symbol table.
	Return the symbol table that will be used in the second pass.
	"""
	ROM_counter = -1	# First A/C instruction occupies ROM[0]
	for command in commands:
		c_type = parser.command_type(command)
		if c_type == "C_COMMAND" or c_type == "A_COMMAND":
			ROM_counter += 1
		else:
			# Associate the symbol of the command with the ROM address that
			# will eventually store the next command in the assembly program. 
			symbol_table[parser.symbol(command)] = (ROM_counter + 1)

	return symbol_table

def second_pass(commands, symbol_table, output_file):
	"""
	Pass through the assembly program's commands, parse each line, and translate
	commands into binary form, and write to .hack file that CPU can load in ROM.
	"""
	RAM_counter = 16 	# 16 is next free RAM address after predefined symbols
	with open(output_file, 'a') as f:
		for command in commands:
			c_type = parser.command_type(command)
			if c_type == "A_COMMAND":
				chars = parser.symbol(command)
				# Test whether chars in the A-instruction are symbol or number
				results = char_test(chars, symbol_table, RAM_counter)
				chars = results['c']
				symbol_table = results['st']
				RAM_counter = results['ram']
				# Translate chars into a instruction and write to f
				f.write(
					code.get_a_instruction(chars) + '\n'
				)
			elif c_type == "C_COMMAND":
				jump_mnemonic = parser.jump(command)
				dest_mnemonic = parser.dest(command)
				comp_mnemonic = parser.comp(command)
				f.write(
					"111" + 
					code.comp(comp_mnemonic) +
					code.dest(dest_mnemonic) +
					code.jump(jump_mnemonic) + '\n'
				)

def main(input_file, output_file):
	"""
	Runs assembler. Input should be an .asm file written in Hack assembly
	language, and output is a .hack file written in Hack machine code.
	Note that this assembler assumes that the .asm file is error-free. 
	"""
	# Construct and initialise symbol table with predefined labels
	symbol_table = st.initialise(st.constructor())
	# Generate list of assembly language commands based on input_file
	commands = parser.initialise(input_file)
	# Run first pass through commands to build symbol table
	symbol_table = first_pass(commands, symbol_table)
	# Run second pass through commands and write to output_file
	second_pass(commands, symbol_table, output_file)

# Execute main() with command line argument as input_file
main(sys.argv[1], (sys.argv[1]).split('.')[0] + '.hack')