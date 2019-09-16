// Runs an infinite loop that listens to the keyboard input.
// When a key is pressed (any key), the program blackens the screen,
// i.e. writes "black" in every pixel;
// the screen should remain fully black as long as the key is pressed. 
// When no key is pressed, the program clears the screen, i.e. writes
// "white" in every pixel;
// the screen should remain fully clear as long as no key is pressed.

	@16384
	D=A
	@i 			// i points to first mem. word of screen memory map 
	M=D

(LOOP)
	@KBD 		// RAM address KBD = 24576 is the single-word memory map
				// that the Hack computer uses to interface with the
				// physical keyboard.
	D=M
	@BLACKEN
	D;JNE		// if KBD != 0, jump to BLACKEN
	@LOOP		// else, restart loop
	0;JMP

(BLACKEN)
	@i 			// for RAM addresses (16384 to 24575)
				// RAM[x] = -1 (i.e., 1111 1111 1111 1111)
	A=M 		// A=M[A]=M[i]
	M=-1 		// blacken every bit in i-th word of screen memory map
	@i
	M=M+1 		// i += 1
	D=M			// D=i
	@24575
	D=A-D 		// D=24575-i
	@END
	D;JEQ		// if (24575-i)=0, go to END
	@KBD
	D=M
	@BLACKEN
	D;JNE		// elif KBD != 0, jump to BLACKEN 
	@16384		// else, reset i and clear screen
	D=A
	@i
	M=D
	@CLEAR
	0;JMP

(CLEAR)
	@i
	A=M
	M=0 		// clear every bit in i-th word of screen memory map
	@i
	M=M+1 		// i += 1
	D=M			// D=i
	@24575
	D=A-D 		// D=24575-i
	@END
	D;JEQ		// if (24575-i)=0, go to END
	@KBD
	D=M
	@CLEAR
	D;JEQ 		// if KBD == 0, jump to CLEAR
	@16384 		// else, reset i and blacken screen
	D=A
	@i
	M=D
	@BLACKEN
	0;JMP

(END)
	@END  		// infinite loop in case of BLACKEN loop exceeding RAM length
	0;JMP