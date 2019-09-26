from utils import Parser, CodeWriter

parser1 = Parser('MemoryAccess/PointerTest/PointerTest.vm')
code_writer = CodeWriter('MemoryAccess/PointerTest/PointerTest.asm')

while parser1.has_more_commands():
	command = parser1.command_type()
	if command == 'C_ARITHMETIC':
		code_writer.write_arithmetic(parser1.arg1())
	elif command == 'C_PUSH' or 'C_POP':
		code_writer.write_push_pop(command, parser1.arg1(), parser1.arg2())
	parser1.advance()

code_writer.close()