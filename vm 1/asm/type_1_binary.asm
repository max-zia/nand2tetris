@SP 		// load address of SP into ARegister
M=M-1  		// decrement value of SP
A=M 		// load value of SP into ARegister
D=M 		// load value of M[SP] into DRegister

@SP
M=M-1 		// decrement value of SP
A=M 		// load value of SP into ARegister
D=D+M 		// D = M[SP-1] + M[SP-2] 

M=D 		// write sum into M[A] = M[SP-2]

@SP
M=M+1 		// increment value of SP