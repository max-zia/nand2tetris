"""
Translates Hack assembly language mnemonics into binary codes. Also creates
16-bit A-instruction
"""

# Dictionaries for assembly mnemonics and corresponding binary forms
dest_table = {
	'null': '000',
	'M': '001',
	'D': '010',
	'MD': '011',
	'A': '100',
	'AM': '101',
	'AD': '110',
	'AMD': '111',
}

jump_table = {
	'null': '000',
	'JGT': '001',
	'JEQ': '010',
	'JGE': '011',
	'JLT': '100',
	'JNE': '101',
	'JLE': '110',
	'JMP': '111',
}

comp_table = {			# Computations performed on the contents of the
	'0': '101010',		# A register and M (the memory location adressed by
	'1': '111111',		# A) share the same c-bits (i.e., the a-bit codes
	'-1': '111010',		# whether to use A or M[A]). Thus, we translate into
	'D': '001100', 		# binary form by (i) replacing all "M" with "A" in
	'A': '110000',		# mnemonic, and (ii) selecting the correct MSB for a.   
	'!D': '001101',
	'!A': '110001',
	'-D': '001111',
	'-A': '110011',
	'D+1': '011111',
	'A+1': '110111',
	'D-1': '001110',
	'A-1': '110010',
	'D+A': '000010',
	'D-A': '010011',
	'A-D': '000111',
	'D&A': '000000',
	'D|A': '010101',
}

def dest(mnemonic):
	"""
	Translates dest assembly language mnemonics into binary code.
	"""
	return dest_table[mnemonic]

def comp(mnemonic):
	"""
	Translates comp assembly language mnemonics into binary code.
	"""
	if 'M' in mnemonic:
		return '1' + comp_table[mnemonic.replace('M', 'A')]
	else:
		return '0' + comp_table[mnemonic]

def jump(mnemonic):
	"""
	Translates jump assembly language mnemonics into binary code.
	"""
	return jump_table[mnemonic]

def get_a_instruction(decimal):
	"""
	Convert decimal value (str) into 16-bit binary (str). Ensure that MSB
	is 0 because 0 is the op code for A instruction in machine language spec.
	"""
	digits = '' 			# store remainders after dividing integers by 2 
	x = int(decimal) 		# x stores integer quotient after each iteration
	while x > 0:
		digits += str(x % 2)
		x = int(x / 2)
	digits = digits[::-1]	# reverse digits to get binary value

	return digits.zfill(16) # use zfill() to pad zeros to create 16-bit value