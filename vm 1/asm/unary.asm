@SP 		// load address of SP into ARegister
M=M-1  		// decrement value of SP
A=M 		// load value of SP into ARegister
M=-M 		// negate M[SP-1] and write to M[SP-1]

@SP
M=M+1 		// increment value of SP