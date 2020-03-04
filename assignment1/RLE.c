#include <stdio.h>
#include <string.h>
#include <stdlib.h>

void encode(char *input){
	char output[80]; // 80 because in the worst case the input is ACGT 10 times over and that makes the output 80 characters

	int pos = 0; //to keep track of output string position
	char *p; // p to navigate characters in string
	int count = '1'; // there will always at least be one character of whatever one we are looking at

	for(p = input; *p != '\0'; p++){

		char current = *p; // Current character
		char second = *(p+1); // next character
		output[pos] = current;
		if((current != 'A') &&
  		   (current != 'G') &&
		   (current != 'T') &&
		   (current != 'C')){
			printf("%s", "Error : String could not be encoded");
			exit(5);
		}


		if(current == second){
			count++;
		}
	
		else if(second == '\0'){
			output[pos+1] = count;
			output[pos+2] = second;
		}	
		else{
			output[pos+1] = count;
			count = '1';
			pos = pos + 2; // Move ahead two because pos + 1 is already used
		}	
	}
	printf("%s", output);	
	exit(0);
}

void decode(char *input){
	char *cur; //to navigate string
	char output[41];
	char *out_pointer = output;

	for(cur = input; *cur != '\0'; cur = cur+2){
		char length = *(cur+1);
		char count;
		
		// Ensure valid input
		if((*cur != 'A' &&
		   *cur != 'G' &&
		   *cur != 'C' &&
		   *cur != 'T') || !(length >= '1' && length <= '9')){
			printf("%s", "Error: String could not be decoded");
			exit(5);
		}
		
		// append to output string
		for(count = '0'; count < length; count++, out_pointer++){
			*out_pointer = *cur;
		}
	}
	*(out_pointer) = '\0';	
	printf("%s", output);
	exit(0);
}
		
int main(int argc, char *argv[]){

		
	if(argc < 3){
		//Checks to see if input file wasn't specified
		if(argc == 2){
			if(strcmp(argv[1], "e") == 0 || strcmp(argv[1], "d") == 0){
				printf("%s", "Error: No input file specified!");
				exit(1);
		}	} 

		//if file was specified then the mode specifier is not there
		printf("%s", "Invalid Usage, expected: RLE {filename} [e|d]");
		exit(4);
	}
	
	else if(strcmp(argv[2], "e") != 0 && strcmp(argv[2], "d") != 0){
		printf("%s", "Invalid Usage, expected: RLE {filename} [e|d]");
		exit(4);
	}

	FILE *file = fopen(argv[1], "r");
	if(file == NULL){
		printf("%s", "Read error: file not found or cannot be read");
		exit(2);
	}
	
	char buffer[41];
	fgets(buffer, 41, file);

	char *p;

	for(p = buffer; *p != '\0'; p++){
		if(*p == ' '){
			//make sure no non whitespace follows a whitespace
			if((*(p+1) >= 'a' && *(p+1) <= 'z') ||
			(*(p+1) >= 'A' && *(p+1) <= 'Z') ||
			(*(p+1) >= '0' && *(p+1) <= '9')){
					
				printf("%s", "Error: Invalid format");
				exit(3);
			}
		}
	}
	if( strcmp(argv[2],"e") == 0){
		encode(buffer);
	}
	else{
		decode(buffer);
	}	 
			
}

