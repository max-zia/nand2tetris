@2
D=A  		// load value of index into D register 
@LCL
A=D+M 		// A = index + base address stored in LCL
D=M 		// D = M[A] = value of segment[index]

@SP 		// push value of segment[index] onto stack and increment SP 
A=M
M=D
@SP
M=M+1