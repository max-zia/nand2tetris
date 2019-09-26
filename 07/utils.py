import uuid 	# module used to generate unique ID for type_2_binary labels 

class Parser():
	"""
	Handles the parsing of a single .vm file. Reads VM commands, parses them,
	and provides convenient access to their components. Also removes all
	whitespace and comments.
	"""

	def __init__(self, input_file):
		"""
		Creates a list of VM commands based on an input file and makes this 
		available as an attribute (.commands) of an instance of Parser. Removes 
		comments, whitespace, and newline characters from the input file. 
		"""
		with open(input_file) as f:
			lines = [
				l.split('/')[0].strip() 
				for l in f 
				if l[0] != '/' 
				and l.strip() != ''
			]

		self.commands = lines

	def has_more_commands(self):
		"""
		Returns true if there are more commands in the input.
		"""
		if len(self.commands) > 0:
			return True

	def advance(self):
		"""
		Deletes the first command from self.commands, simulating advance 
		through the input_file. Only called if has_more_commands() is true.
		"""
		del self.commands[0]

	def command_type(self):
		"""
		Returns the type of the 'current' VM command (i.e., self.commands[0]).
		"""
		arithmetic_logic_commands = [
			'add', 'sub', 'neg', 'eq',
			'gt', 'lt', 'and', 'or', 'not'
		]

		# First term/symbol in command determines type, so grab this 
		first_term = self.commands[0].split()[0]

		# Use first_term to create the nine command types
		if first_term in arithmetic_logic_commands:
			return 'C_ARITHMETIC'
		elif first_term == 'if-goto':
			return 'C_IF'
		else:
			return 'C_' + first_term.upper()

	def arg1(self):
		"""
		Returns the first argument of the current VM command. Should not be
		called if command_type is C_RETURN, and the command itself is
		returned if command_type is C_ARITHMETIC
		"""
		return (
			self.commands[0] if self.command_type() == 'C_ARITHMETIC' 
			else self.commands[0].split()[1] 
		)

	def arg2(self):
		"""
		Returns the second argument of the current VM command. Called only if
		command_type us C_PUSH, C_POP, C_FUNCTION, or C_CALL.
		"""
		return self.commands[0].split()[2]

class CodeWriter():
	"""
	Translates VM commands into Hack assembly and writes these into .asm file.
	Conforms to the Standard VM Mapping on the Hack Platform.
	"""

	def __init__(self, output_file):
		"""
		All newly_created class instances have an open .asm output_file,
		available as an attribute (.output_file). 
		"""
		self.output_file = open(output_file, 'w')
		self.filename = self.output_file.name.split('.')[0].split('/')[-1]

	def close(self):
		"""
		Closes the .asm output_file.
		"""
		self.output_file.close()

	def set_filename(self, new_input_file):
		"""
		Called when the translation of a new vm file has started. Ensures that
		each VM file has its own 'static' virtual memory segment.
		"""
		self.filename = new_input_file.split('.')[0].split('/')[-1]

	def write_arithmetic(self, command):
		"""
		Writes assembly code to translate a given C_ARITHMETIC VM command.
		"""
		type_1_binary = {
			'add': 'D+M', 
			'sub': 'M-D', 
			'and': 'D&M', 
			'or': 'D|M'
		}

		type_2_binary = {
			'eq': 'JEQ',
			'gt': 'JGT',
			'lt': 'JLT'
		}

		unary = {
			'neg': '-M',
			'not': '!M'
		}

		if command in unary:
			asm_code = f'@SP\nM=M-1\nA=M\nM={unary[command]}\n@SP\nM=M+1\n'
		else:
			# type_1 and type_2 binary commands have the same first half
			asm_code = '@SP\nM=M-1\nA=M\nD=M\n@SP\nM=M-1\nA=M\n'

			# add second half of asm_code as appropriate
			if command in type_1_binary:
				asm_code += f'D={type_1_binary[command]}\nM=D\n@SP\nM=M+1\n'
			else:
				# create labels for jump commands with unique identifier
				identifier = uuid.uuid4().hex[:4]
				true_label = (command + '_true_' + identifier)
				return_label = (command + '_return_' + identifier)

				# append asm_code
				asm_code += (f'D=M-D\n@{true_label}\nD;{type_2_binary[command]}'
							f'\n@SP\nA=M\nM=0\n@{return_label}\n0;JMP\n'
							f'({true_label})\n@SP\nA=M\nM=-1\n@{return_label}'
							f'\n0;JMP\n({return_label})\n@SP\nM=M+1\n')

		self.output_file.write(asm_code)

	def write_push_pop(self, command, segment, index):
		"""
		Writes assembly code to translate a given C_PUSH or C_POP VM command.
		"""
		map_1 = {
			'local': 'LCL',
			'argument': 'ARG',
			'this': 'THIS',
			'that': 'THAT'
		}

		map_2 = {
			'pointer': 'R3',
			'temp': 'R5'
		}

		if command == 'C_PUSH':
			if segment == 'constant':
				asm_code = f'@{index}\nD=A\n'

			elif segment in map_1:
				asm_code = f'@{index}\nD=A\n@{map_1[segment]}\nA=D+M\nD=M\n' 

			elif segment in map_2:
				asm_code = f'@{index}\nD=A\n@{map_2[segment]}\nA=D+A\nD=M\n'

			elif segment == 'static':
				asm_code = f'@{self.filename}.{index}\nD=M\n'

			# all C_PUSH commands have the same second half
			asm_code += '@SP\nA=M\nM=D\n@SP\nM=M+1\n'

		elif command == 'C_POP':
			if segment == 'static':
				asm_code = f'@SP\nAM=M-1\nD=M\n@{self.filename}.{index}\nM=D\n'

			else:
				if segment in map_1:
					asm_code = f'@{index}\nD=A\n@{map_1[segment]}\nA=M\n'

				elif segment in map_2:
					asm_code = f'@{index}\nD=A\n@{map_2[segment]}\n'

				asm_code += ('D=D+A\n@SP\nA=M\nM=D\n'
							'@SP\nA=M-1\nD=M\n@SP\nA=M\n'
							'A=M\nM=D\n@SP\nM=M-1\n')

		self.output_file.write(asm_code)