"""
Keeps a correspondence between symbolic labels in a Hack assembly program
and numeric addresses.
"""

def constructor():
	"""
	Creates a new empty symbol table. In this case, the structure used to 
	represent the relationship between symbols in a Hack assembly program
	and RAM and ROM addresses is a hash table (i.e., a python dictionary).
	"""
	return {}

def initialise(symbol_table):
	"""
	Initialises symbol table with predefined symbols. Note that each one of
	the top five RAM locations can be referred to using two predefined labels.
	"""
	labels = [
		'SP', 'LCL', 'ARG', 'THIS', 'THAT',
		'R0', 'R1', 'R2', 'R3', 'R4', 'R5', 'R6', 'R7', 
		'R8', 'R9', 'R10', 'R11', 'R12', 'R13', 'R14', 'R15', 
		'SCREEN', 'KBD'
	]
	addresses = [
		0, 1, 2, 3, 4, 
		0, 1, 2, 3, 4, 5, 6, 7, 
		8, 9, 10, 11, 12, 13, 14, 15, 
		16384, 24576
	]

	# Update the symbol table by iterating through two lists simultaneously
	for label, address in zip(labels, addresses):
		symbol_table[label] = address

	return symbol_table

def add_entry(symbol, address, symbol_table):
	"""
	Adds the pair (symbol, address) to the symbol table.
	"""
	symbol_table[symbol] = address

def contains(symbol, symbol_table):
	"""
	Does the symbol table contain the given symbol?
	"""
	if symbol in symbol_table:
		return True
	else:
		return False

def get_address(symbol, symbol_table):
	"""
	Returns the address associated with a symbol.
	"""
	return symbol_table[symbol]