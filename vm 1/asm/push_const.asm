@const
D=A  		// load value of constant into D register 

@SP 		// push const to M[SP] and increment value of SP 
A=M
M=D
@SP
M=M+1