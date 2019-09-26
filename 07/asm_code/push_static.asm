push static index

@filename.index
D=M

@SP 		// push value of D onto stack and increment SP 
A=M
M=D
@SP
M=M+1