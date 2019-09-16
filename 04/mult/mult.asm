// Multiplies R0 and R1 and stores the result in R2.
// R1 and R2 are any integers (i.e., positive, negative, or zero).
// (R0, R1, R2 refer to RAM[0], RAM[1], and RAM[2], respectively.)

// initialise R2=0
	@R2
	M=0

// for all R0, R1 (if R0=0 | R1=0, R2=0)
// zero test for R0 and R1
	@R0
	D=M
	@ENDZERO
	D;JEQ			// if R0=0, go to ENDZERO
	@R1
	D=M
	@ENDZERO
	D;JEQ			// elif R1=0, go to ENDZERO

// f(a,b) = a*b (i.e. add R0 to itself R1 times)
// first, work with absolute values
	// check sign and store abs(R0) in M[x]
	@R0 
	D=M
	@x
	M=D 			// x=R0 (write M[R0] into M[x])
	@LT1
	D;JLT			// if x < 0, go to LT1
	@LT 			// else:
	0;JMP 			// unconditional jump to M[A]=LT, where 0 is arbitrary
(LT)
	// check sign and store abs(R1) in M[x]
	@R1
	D=M
	@y
	M=D
	@LT2
	D;JLT 			// if y < 0, go to LT2
	@ADD 			// else, go to ADD
	0;JMP
(LT1)
	@x
	M=-M 			// reverse sign for absolute value
	@LT
	0;JMP			// jump back to LT to get absolute value for R1
(LT2)
	@y
	M=-M
	@ADD
	0;JMP

// second, add abs(R0)=x to itself abs(R1)=y times, store in mem. location R2
(ADD)
	// While (y >= 1) { sum += x; y--; }
	@y
	D=M
	@CHECKSIGN_R0
	D;JLE			// if y <= 0, go to CHECKSIGN_R0 (break)
	@x				// else, R2 += x; y--
	D=M
	@R2
	M=D+M 			// R2=R2+x
	@y
	M=M-1 			// y=y-1
	@ADD
	0;JMP 			// go to ADD (loop)

// if (R0=0) or (R1=0), return 0
(ENDZERO)
	@R2
	M=0
	@500			// jump to arbitrary address (program end)
	0;JMP

// if R0 or R1 < 0, R2 must be negative
// if R0 and R1 < 0, R2 must be positive
(CHECKSIGN_R0)
	@R0
	D=M
	@ENDNEG_R0
	D;JLT			// if R0 < 0, negate R2
	@CHECKSIGN_R1	// else, go to CHECKSIGN_R1
	0;JMP
(CHECKSIGN_R1)
	@R1
	D=M
	@ENDNEG_R1
	D;JLT			// if R1 < 0, negate R2
	@500			// else, jump to arbitrary address (program end)
	0;JMP
(ENDNEG_R0)
	@R2
	M=-M 			// R2=-R2
	@CHECKSIGN_R1	// jump back to check sign of R1
	0;JMP
(ENDNEG_R1)
	@R2
	M=-M
	@500
	0;JMP 			// jump to arbitrary address (program end)