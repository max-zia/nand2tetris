"""
Parses an assembly language command and provides convenient access to
the command's fields and symbols. In addition, removes all whitespace
and comments from the assembly language file.
"""

def initialise(input_file):
	"""
	Opens the input file (.asm) and appends all lines containing commands to a
	list, which is returned. Newline characters and whitespace are removed. 
	"""
	lines = [] 			# stores lines from input_file 
	commands = []		# stores commands from "cleaned" lines

	with open(input_file) as f:
		for line in f:
			lines.append(line)

	for line in lines:
		if line[0] != "/" and line != "\n":
			# ignore whitespace on LHS (necessary for files with tabbing)
			line = line.lstrip()
			# ignore comments on same line in .asm file
			line = line.split()[0]
			# ignore newline chars on RHS of every line
			commands.append(line.rstrip("\n"))

	return commands

def command_type(command):
	"""
	Returns the type of the current command.
	"""
	if command[0] == "@":
		return "A_COMMAND"
	elif command[0] == "(":
		return "L_COMMAND"
	else:
		return "C_COMMAND"

def symbol(command):
	"""
	Returns symbol or decimal Xxx of current command @Xxx or (Xxx).
	Only called when command_type() returns A_COMMAND or L_COMMAND. 
	"""
	if command[0] == "@":
		return command[1:]
	elif command[0] == "(":
		return command[1:-1]

def dest(command):
	"""
	Returns the dest mnemonic in the current C-command. Only called when
	command_type() returns C_COMMAND.
	"""
	if "=" in command:
		return command.split("=")[0]
	else:
		return "null"

def comp(command):
	"""
	Returns the comp mnemonic in the current C-command. Only called when
	command_type() returns C_COMMAND.
	"""
	if "=" in command:
		return command.split("=")[1]
	elif ";" in command:
		return command.split(";")[0]

def jump(command):
	"""
	Returns the jump mnemonic in the current C-command. Only called when
	command_type() returns C_COMMAND.
	"""
	if ";" in command:
		return command.split(";")[1]
	else:
		return "null"