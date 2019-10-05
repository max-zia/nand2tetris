import uuid 	# module used to generate unique ID for type_2_binary labels 
import os 		# # os.listdir() returns everything in a directory

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
		self.filename = input_file.split('.')[0].split('/')[-1]

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
		command_type is C_PUSH, C_POP, C_FUNCTION, or C_CALL.
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

	def close(self):
		"""
		Closes the .asm output_file.
		"""
		self.output_file.close()

	def set_filename(self, new_input_file):
		"""
		Called when the translation of a new vm file has started.
		"""
		self.filename = new_input_file.split('.')[0].split('/')[-1]

	def write_init(self):
		"""
		Writes assembly code that effects the VM initialisation (i.e., writes
		the so-called "bootstrap code" to the beginning of the .asm file).
		"""
		self.output_file.write('@256\nD=A\n@SP\nM=D\n')
		self.write_call('Sys.init', '0')

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

	def write_label(self, label):
		"""
		Writes assembly code that effects the label command (i.e., writes
		the specified label into the next line of the .asm file).
		"""
		self.output_file.write(f'({self.filename}.{label})\n')

	def write_goto(self, label):
		"""
		Writes assembly code that effects the goto command (i.e., an 
		unconditional jump to the specified label).
		"""
		self.output_file.write(f'@{self.filename}.{label}\n0;JMP\n')

	def write_if(self, label):
		"""
		Writes assembly code that effects the if-goto command (i.e., if the
		topmost value on the stack != 0, jump to label, else continue).
		"""
		self.output_file.write(f'@SP\nAM=M-1\nD=M\n@{self.filename}.{label}\nD;JNE\n')

	def write_call(self, function_name, num_args):
		"""
		Writes assembly code that effects the call command.
		"""
		# Generate unique label for the return address.
		identifier = uuid.uuid4().hex[:4]
		return_label = (f'{function_name}$ret.{identifier}')

		# Create a list to hold all of the .asm symbols that will be pushed 
		# to the stack to save the state of the calling function.
		saved_state = ['LCL', 'ARG', 'THIS', 'THAT']

		# Append 5 push commands to asm_code, pushing the value associated
		# with return_label, followed by the base addresses held in the
		# calling function's LCL, ARG, THIS, and THAT virtual mem. segments.
		asm_code = f'@{return_label}\nD=A\n@SP\nA=M\nM=D\n@SP\nM=M+1\n'

		for i in saved_state:
			asm_code += f'@{i}\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n'

		# Reposition ARG to point to the first of the called function's args,
		# which were pushed to the global stack prior to VM call command.
		# NOTE: ARG = M[SP] - (num_args + len(saved_state)).
		asm_code += f'@5\nD=A\n@{num_args}\nD=D+A\n@SP\nD=M-D\n@ARG\nM=D\n'

		# Reposition LCL to point to the current location of the stack pointer.
		# This serves as the base address of the called function's local vars.
		asm_code += '@SP\nD=M\n@LCL\nM=D\n'

		# Transfer control to the called function with an unconditional jump.
		asm_code += f'@{function_name}\n0;JMP\n'

		# Declare a label for the return address.
		asm_code += f'({return_label})\n'

		self.output_file.write(asm_code)

	def write_function(self, function_name, num_locals):
		"""
		Writes assembly code that effects the function command.
		"""
		# Declare a label for the function entry.
		asm_code = f'({function_name})\n'

		# Initialise local variables by pushing 0 to stack num_locals times
		for i in range(int(num_locals)):
			asm_code += f'@0\nD=A\n@SP\nA=M\nM=D\n@SP\nM=M+1\n'

		self.output_file.write(asm_code)

	def write_return(self):
		"""
		Writes assembly code that effects the function command.
		"""
		# FRAME = LCL, where FRAME points to the end of the saved state of
		# the calling function. Use R13 to store FRAME temp. var.
		asm_code = '@LCL\nD=M\n@R13\nM=D\n'

		# Put the return address in R14 as a temp. var, where RET = M[FRAME-5]
		asm_code += '@5\nD=D-A\nA=D\nD=M\n@R14\nM=D\n'

		# Since the function will have placed a return value at the top
		# of the stack, copy this return value for the caller by placing
		# it in the mem. location pointed to by ARG (i.e., M[ARG] = pop()).
		asm_code += '@SP\nA=M-1\nD=M\n@ARG\nA=M\nM=D\n'

		# Restore SP of the caller (i.e., M[SP] = M[ARG] + 1).
		asm_code += 'D=A\n@SP\nM=D+1\n'

		# Restore the state of the caller's THAT, THIS, ARG, and LCL pointers
		# by resetting base addresses according to the FRAME/R13 temp. var.
		saved_state = ['THAT', 'THIS', 'ARG', 'LCL']
		counter = 1
		for i in saved_state:
			asm_code += f'@{counter}\nD=A\n@R13\nA=M\nA=A-D\nD=M\n@{i}\nM=D\n'
			counter += 1

		# Go to return address in the caller's code with unconditional jump.
		asm_code += '@R14\nA=M\n0;JMP\n'

		self.output_file.write(asm_code)


class Initialiser():
	"""
	Initialises and runs the VM translator.
	"""

	def __init__(self, cli):
		"""
		All newly_created Initialiser instances have a list of VM files to be
		translated, which is available as an attribute (.vm_files). Also
		generates the file name of the .asm file to be written. Class takes
		the command line argument (cli) as its argument. 
		"""
		if '.vm' in cli:
			ls = [cli]
			asm_filename = cli.replace('vm', 'asm')
		else:
			ls = [cli + '/' + x for x in os.listdir(cli) if '.vm' in x]
			asm_filename = cli + '/' + cli.split('/')[1] + '.asm'

		self.vm_files = ls
		self.asm_filename = asm_filename

