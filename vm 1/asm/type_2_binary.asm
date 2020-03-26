@SP 		// load address of SP into ARegister
M=M-1  		// decrement value of SP
A=M 		// load value of SP into ARegister
D=M 		// load value of M[SP] into DRegister

@SP
M=M-1 		// decrement value of SP
A=M 		// load value of SP into ARegister
D=M-D 		// D = M[SP-2] - M[SP-1]

@TRUE
D;JGT 		// if d > 0, go to TRUE
@SP			// else, assign false
A=M
M=0
@RETURN
0;JMP

(TRUE)
	@SP
	A=M
	M=-1
	@RETURN
	0;JMP

(RETURN)
	@SP
	M=M+1 		// increment value of SP and continue

