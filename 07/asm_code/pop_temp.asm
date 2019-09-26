@2
D=A
@R5
D=D+A  		// D = base address held in LCL + index

@SP
A=M
M=D 		// write D into mem. location held in SP

@SP
A=M-1 		// store M[SP-1] in ARegister
D=M 		// store M[A]=M[SP-1] in DRegister

@SP
A=M
A=M
M=D

@SP
M=M-1 		// decrement SP