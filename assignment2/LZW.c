#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define TRUE 1
#define FALSE 0

#define DICTSIZE 4096                     /* allow 4096 entries in the dict  */
#define ENTRYSIZE 32

unsigned char dict[DICTSIZE][ENTRYSIZE];  /* of 30 chars max; the first byte */
                                          /* is string length; index 0xFFF   */
                                          /* will be reserved for padding    */
                                          /* the last byte (if necessary)    */

// These are provided below
int read12(FILE *infil);
int write12(FILE *outfil, int int12);
void strip_lzw_ext(char *fname);
void flush12(FILE *outfil);
void encode(FILE* in, FILE* out);
void decode(FILE* in, FILE* out);

int main(int argc, char *argv[]){

		
	if(argc < 3){
		//Checks to see if input file wasn't specified
		if(argc == 2){
			if(strcmp(argv[1], "e") == 0 || strcmp(argv[1], "d") == 0){
				printf("%s", "Error: No input file specified!");
				exit(1);
		}	} 

		//if file was specified then the mode specifier is not there
		printf("%s", "Invalid Usage, expected: LZW {filename} [e|d]");
		exit(4);
	}
	
	else if(strcmp(argv[2], "e") != 0 && strcmp(argv[2], "d") != 0){
		printf("%s", "Invalid Usage, expected: LZW {filename} [e|d]");
		exit(4);
	}

	
	if( strcmp(argv[2],"e") == 0){
		FILE* file = fopen(argv[1], "rb");
		char fname[100];
		strcpy(fname, argv[1]);
		strcat(fname, ".LZW");
		FILE* out = fopen(fname, "wb");
		encode(file, out);
		exit(0);
	}
	else{
		FILE* file = fopen(argv[1], "rb");
		char fname[100];
		strcpy(fname, argv[1]);
		strip_lzw_ext(fname);
		FILE* out = fopen(fname, "w");
		decode(file, out);
		exit(0);
	}	 
			
}

/*****************************************************************************/
/* encode() performs the Lempel Ziv Welch compression from the algorithm in  */
/* the assignment specification. The strings in the dictionary have to be    */
/* handled carefully since 0 may be a valid character in a string (we can't  */
/* use the standard C string handling functions, since they will interpret   */
/* the 0 as the end of string marker). Again, writing the codes is handled   */
/* by a separate function, just so I don't have to worry about writing 12    */
/* bit numbers inside this algorithm.                                        */
void encode(FILE *in, FILE *out) {
    // TODO implement
	int next_pos = 256;
	int wk_flag; // flag to indicate if wk is in the dictionary or not. 0 if not 1 if it is
	int x; // loop variable
	int code; // keep track of the code that will be output at the end of each iteration of the loop
	unsigned char w[32];
	unsigned char wk[32];

	w[0] = 0;

	for(x=0; x<256; x++){
		dict[x][1] = x;
		dict[x][0] = 1;
	}

	// set k to any value other than -1
	int k = 0;
	
	k = fgetc(in);
	while(k != EOF){
	
		// if end of dictionary reached add new entries starting from start of dictionary
		if(next_pos == 4095){
			next_pos = 256;
		}

		// if w[0] == 31 that means the entry is full because w[0] is the length and w[1] - w[31] is the string and positions beyond w[31] are accesible for some reason so must solve this issue
		// if w got really large that means this current w is already in the dict
		// to deal with it clear w and do a soft restart of the algorithm by having w = '' again but do not alter the dict or output
		// set w[0] = 0 because when program executes it will assume its a string of length 0 and fill it in from position 1
		if(w[0]	== 31){
			w[0] = 0;
		}

		// copy w into wk
		for(x = 0; x <= w[0]; x++){
			wk[x] = w[x];
		}
		
		// add k to wk so it is now w+k
		wk[0] = wk[0]+1;
		int wk_length = wk[0];
		wk[wk_length] = dict[k][1];


		// Check if wk is in the dictionary
		int i;

		// check all of dictionary in case at some point it was made full
		for(i = 0; i < 4095; i++){
			
			// if they have the same length check if it is the same string
			if(dict[i][0] == wk[0]){
			
				// loop through wk and the entry to see if they match
				int x;
				for(x = 1; x <= wk[0]; x++){
					
					// if the strings dont match set the flag to 0 and exit the current check loop
					if(dict[i][x] != wk[x]){
						wk_flag = 0;
						break;
					}

					// if last character of wk has been reached wihout breaking the loop then wk = dict[i]
					//
					if(x == wk[0]){
						// if the strings do match set the flag to 1 and change i to satisfy the exit condition
						wk_flag = 1;
						code = i; // because wk exists in the dictionary and w will be changed to wk this is the code to be output for this iteration
						i = 4096;	
					}
				}
			}
		}


		if(wk_flag == 1){
			
			// set w to wk
			int z;
			for(z = 0; z <= wk_length; z++){

				w[z] = wk[z];
			}
		}

		else{
	
			// find the code that corresponds to w
			int f;
			for(f = 0; f < 4095; f++){
				
				int y;
				for(y = 0; y <= w[0]; y++){
					
					if(dict[f][y] != w[y]){
						
						break;

	
					}
					if(y == w[0]){
						
						code = f;
						f = 4096; // change f to satisfy exit condition of outer for loop
					}
				}
			}
	
			write12(out, code);
	//		printf("%d", code);
	
			// add wk to dict
			int dict_counter;
			for(dict_counter = 0; dict_counter <= wk[0]; dict_counter++){

				dict[next_pos][dict_counter] = wk[dict_counter];
			}

			// change w to k.
			// Because K is  a single character no loop is needed
			w[0] = dict[k][0];
			w[1] = dict[k][1];

			next_pos++;
			
		}
		k = fgetc(in);
		wk_flag = 0; // reset the flag to avoide errors

		// if end of file reached output the last code
		if(k == EOF){

			int final;
			for(final = 0; final < 4095; final++){
				
				int y_end;
				for(y_end = 0; y_end <= w[0]; y_end++){
					
					if(dict[final][y_end] != w[y_end]){
						
						break;

	
					}
					if(y_end == w[0]){
						
						code = final;
						final = 4096; // change f to satisfy exit condition of outer for loop
					}
				}
			}
	
			write12(out, code);
	//		printf("%d", code);

		}
	}
	// write the padding marker and whatever code is remaining?
	int flush = write12(out, -1);

	// if flush is 0 then no bytes were written so do the same call again?
	// didnt work with if statement try loop instead
	if(flush == 0){
		flush12(out);
	}


}

/*****************************************************************************/
/* decode() performs the Lempel Ziv Welch decompression from the algorithm   */
/* in the assignment specification.                                          */

void decode(FILE *in, FILE *out){
	int next_pos = 256;
	int x; // loop variable
	int code; // keep track of the code that will be output at the end of each iteration of the loop
	unsigned char w[32];
	int length;
	code = read12(in);
	
	for(x=0; x<256; x++){
		dict[x][1] = x;
		dict[x][0] = 1;
	}

	for(x = 256; x < 4095; x++){
		dict[x][0] = 0;
	}

	// set w to k and output k
	w[0] = dict[code][0];
	w[1] = dict[code][1];
	fprintf(out, "%c", dict[code][1]); // because first code will always be a standard ascii no need to loop through the whole entry

	code = read12(in);

	while( !feof(in) && code < 4095){

		// exit if code outside dictionary
		if(code > 4095){
			printf("%s", "Error: File could not be decoded");
			exit(5);
		}

		if(next_pos == 4095){
			next_pos = 256;
		}	
		// check if k is in the dictionary
		if(dict[code][0] != 0){

			length = dict[code][0];

			// output entry
			int entry_counter;
			for(entry_counter = 1; entry_counter <= length; entry_counter++){
					fprintf(out, "%c", dict[code][entry_counter]);
			}

			// add first character of k to w and add to dict
			w[0] = w[0] + 1;
			w[w[0]] = dict[code][1];

			for(entry_counter = 0; entry_counter <= w[0]; entry_counter++){
				dict[next_pos][entry_counter] = w[entry_counter];
			}
		}	

		else{
		// add first char of w to w
			w[0] = w[0] + 1;
			w[w[0]] = w[1];
			// add length to dict to reduce number of statements
			dict[next_pos][0] = w[0];
				
			// output the new w and add it to the dictionary

			int entry_ctr2;
			for(entry_ctr2 = 1; entry_ctr2 <= w[0]; entry_ctr2++){
				dict[next_pos][entry_ctr2] = w[entry_ctr2];
				fprintf(out, "%c", w[entry_ctr2]);
			}
		}

		next_pos++;
		// set w to dict[k]
		length = dict[code][0];
		for(x = 0; x <= length; x++){
			w[x] = dict[code][x];
		}
		code = read12(in);
	}
}


/*****************************************************************************/
/* read12() handles the complexities of reading 12 bit numbers from a file.  */
/* It is the simple counterpart of write12(). Like write12(), read12() uses  */
/* static variables. The function reads two 12 bit numbers at a time, but    */
/* only returns one of them. It stores the second in a static variable to be */
/* returned the next time read12() is called.                                */
int read12(FILE *infil)
{
 static int number1 = -1, number2 = -1;
 unsigned char hi8, lo4hi4, lo8;
 int retval;

 if(number2 != -1)                        /* there is a stored number from   */
    {                                     /* last call to read12() so just   */
     retval = number2;                    /* return the number without doing */
     number2 = -1;                        /* any reading                     */
    }
 else                                     /* if there is no number stored    */
    {
     if(fread(&hi8, 1, 1, infil) != 1)    /* read three bytes (2 12 bit nums)*/
        return(-1);
     if(fread(&lo4hi4, 1, 1, infil) != 1)
        return(-1);
     if(fread(&lo8, 1, 1, infil) != 1)
        return(-1);

     number1 = hi8 * 0x10;                /* move hi8 4 bits left            */
     number1 = number1 + (lo4hi4 / 0x10); /* add hi 4 bits of middle byte    */

     number2 = (lo4hi4 % 0x10) * 0x0100;  /* move lo 4 bits of middle byte   */
                                          /* 8 bits to the left              */
     number2 = number2 + lo8;             /* add lo byte                     */

     retval = number1;
    }

 return(retval);
}

/*****************************************************************************/
/* write12() handles the complexities of writing 12 bit numbers to file so I */
/* don't have to mess up the LZW algorithm. It uses "static" variables. In a */
/* C function, if a variable is declared static, it remembers its value from */
/* one call to the next. You could use global variables to do the same thing */
/* but it wouldn't be quite as clean. Here's how the function works: it has  */
/* two static integers: number1 and number2 which are set to -1 if they do   */
/* not contain a number waiting to be written. When the function is called   */
/* with an integer to write, if there are no numbers already waiting to be   */
/* written, it simply stores the number in number1 and returns. If there is  */
/* a number waiting to be written, the function writes out the number that   */
/* is waiting and the new number as two 12 bit numbers (3 bytes total).      */
int write12(FILE *outfil, int int12)
{
 static int number1 = -1, number2 = -1;
 unsigned char hi8, lo4hi4, lo8;
 unsigned long bignum;

 if(number1 == -1)                         /* no numbers waiting             */
    {
     number1 = int12;                      /* save the number for next time  */
     return(0);                            /* actually wrote 0 bytes         */
    }

 if(int12 == -1)                           /* flush the last number and put  */
    number2 = 0x0FFF;                      /* padding at end                 */
 else
    number2 = int12;

 bignum = number1 * 0x1000;                /* move number1 12 bits left      */
 bignum = bignum + number2;                /* put number2 in lower 12 bits   */

 hi8 = (unsigned char) (bignum / 0x10000);                     /* bits 16-23 */
 lo4hi4 = (unsigned char) ((bignum % 0x10000) / 0x0100);       /* bits  8-15 */
 lo8 = (unsigned char) (bignum % 0x0100);                      /* bits  0-7  */

 fwrite(&hi8, 1, 1, outfil);               /* write the bytes one at a time  */
 fwrite(&lo4hi4, 1, 1, outfil);
 fwrite(&lo8, 1, 1, outfil);

 number1 = -1;                             /* no bytes waiting any more      */
 number2 = -1;

 return(3);                                /* wrote 3 bytes                  */
}

/** Write out the remaining partial codes */
void flush12(FILE *outfil)
{
 write12(outfil, -1);                      /* -1 tells write12() to write    */
}                                          /* the number in waiting          */

/** Remove the ".LZW" extension from a filename */
void strip_lzw_ext(char *fname)
{
    char *end = fname + strlen(fname);

    while (end > fname && *end != '.' && *end != '\\' && *end != '/') {
        --end;
    }
    if ((end > fname && *end == '.') &&
        (*(end - 1) != '\\' && *(end - 1) != '/')) {
        *end = '\0';
    }
}








