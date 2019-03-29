# Assembly Compiler
class symbolTable:
	# all the tables are class variables
	symbol_table = {'R0':0, 'R1':1, 
						'R2':2,	'R3':3, 
						'R4':4, 'R5':5,	
						'R6':6, 'R7':7, 
						'R8':8, 'R9':9, 
						'R10':10, 'R11':11, 
						'R12':12, 'R13':13, 
						'R14':14, 'R15':15, 
						'SCREEN':16384, 'KBD':24576, 
						'SP':0, 'LCL':1, 'ARG':2,
						'THIS':3, 'THAT': 4
						}

	label_table = dict()
	var_table = dict()

	def append_label(symbol, value):
		symbolTable.label_table[symbol] = value

	def append_var(symbol, value):
		symbolTable.var_table[symbol] = value

	def find_symbol(symbol):
		for sym in symbolTable.symbol_table:
			if(sym == symbol):
				return symbolTable.symbol_table[symbol]

		return -1 

	def find_label(label):
		for lbl in symbolTable.label_table:
			if(lbl == label):
				return symbolTable.label_table[label]

		return -1 

	def find_var(variable):
		for var in symbolTable.var_table:
			if(var == variable):
				return symbolTable.var_table[variable]

		return -1


class compiler:
	def parser(assembly_code):
		if assembly_code not in ['\n']:
			# detects indentations before the code and ...
			# ... spaces, newline or comment succeeding ...
			# ... the code; 

			# passes the code after removing the ...
			# ... indents, spaces, and comments, ...
			# ... the code is within [start:end] 

			# sole comments might be indented too
			
			i = -1
			# start of the code-section of the line
			start = -100

			# end of the code-section of the line
			end = -100	
			for c in assembly_code:
				i = i+1

				if c not in [' ']:
					if(start == -100):
						start = i

				# the newline is a single character
				if c in [' ','/','\n']:	
					if(start != -100):
						end = i
						break
				
			# for comments, we get start = end = 0 ...
			# ... i.e. an empty string
			return assembly_code[start:end]

		return -1
	def initialise_labels(assembly_code, line_number):
		if(assembly_code[0] == '('):				
			symbolTable.append_label(assembly_code[1:-1], line_number)

	def initialise_vars(assembly_code, no_of_var):
		if(assembly_code[0] == '@'):
			if(assembly_code[1:].isnumeric() == False):
				if(symbolTable.find_symbol(assembly_code[1:]) == -1):
					if(symbolTable.find_label(assembly_code[1:]) == - 1):
						if(symbolTable.find_var(assembly_code[1:]) == - 1):
							symbolTable.append_var(assembly_code[1:], 16+no_of_var)
							no_of_var = no_of_var + 1

		return no_of_var 

	def replace_symbol(assembly_code):
		# symbols - pre-defined keywords, recognised, ...
		# ... by the compiler
		value = 0
		value = symbolTable.find_symbol(assembly_code)
		if(value != -1):
			return value

		else: 
			return assembly_code

	def replace_label(assembly_code):
		# label - line number where the ...
		# ... next jump is to occur
		address = 0
		address = symbolTable.find_label(assembly_code)
		if(address != -1):
			return address

		else: 
			return assembly_code	

	def replace_var(assembly_code):
		# var - variables storing RAM memory ...
		# ... addresses, to be accessed later
		value = 0
		value = symbolTable.find_var(assembly_code)
		if(value != -1):
			return value

		else: 
			return assembly_code			

	def assembly_to_machine(assembly_code):
		if(assembly_code[0] == '@'):
			assembly_code = compiler.replace_symbol(assembly_code[1:])
			assembly_code = compiler.replace_label(assembly_code)
			assembly_code = compiler.replace_var(assembly_code)
			machine_code = a_instruction.a_instruction(assembly_code)

		else:
			machine_code = c_instruction.c_instruction(assembly_code)

		return machine_code

	
class a_instruction:
	def a_instruction(value):
		binary = a_instruction.decimal_to_binary(value)
		binary = str(binary)

		machine_code = ''
		# op code = 0
		# NOTE: strings can not be appended using append() ...
		# ... they must be concatenated!
		machine_code = machine_code + '0'

		i = 15 
		# i - total digits in the binary form, remaining ...
		# ... (of the 14 digits) will be filled with 0
		l = len(binary) - 1
		while(i > 0):
			i = i -1
			if(i > l):
				machine_code = machine_code + '0'
			else:
				machine_code = machine_code + binary[l - i]

		return machine_code



	def decimal_to_binary(number):
		i = -1
		remainder = []
		bin_number = 0
		number = int(number)
		
		while(number > 0):
			i = i+1
			bin_number = bin_number + int(number%2)*pow(10,i)
			number=int(number/2)

		return bin_number


class c_instruction:
	def c_instruction(assembly_code):
		jmp_code = ''
		dest_code = ''
		comp_code = ''
		machine_code = '111'

		comp_code = c_instruction.comp(assembly_code)
		# if the code contains '=', then ...
		# ... it implies a destination statement
		if(assembly_code.find('=') != -1):
			dest_code = c_instruction.dest(assembly_code)
			jmp_code = '000'

		# if the code contains ';', then ...
		# ... it implies a jump statement
		elif(assembly_code.find(';') != -1):
			jmp_code = c_instruction.jmp(assembly_code)
			dest_code = '000'

		machine_code = machine_code + str(comp_code) + str(dest_code) + str(jmp_code)
		return machine_code

	def comp(assembly_code):
		comp_code = ''
		eq_pos = assembly_code.find('=')	
		sc_pos = assembly_code.find(';')	# semi-colon's position

		if(eq_pos == -1):
			comp_eqn = assembly_code[:sc_pos]
		elif(sc_pos == -1):				
			comp_eqn = assembly_code[eq_pos+1:]

		if(comp_eqn == '0'):	comp_code='0101010'
		elif(comp_eqn == '1'):	comp_code='0111111'
		elif(comp_eqn == '-1'):	comp_code='0111010'

		elif(comp_eqn == 'D'):	comp_code='0001100'

		elif(comp_eqn == 'A'):	comp_code = '0110000' 	
		elif(comp_eqn == 'M'):	comp_code='1110000'

		elif(comp_eqn == '!D'):	comp_code='0001101'
		elif(comp_eqn == '!A'):	comp_code='0110001'
		elif(comp_eqn == '!M'):	comp_code='1110001'

		elif(comp_eqn == '-D'):	comp_code='0001111'
		elif(comp_eqn == '-A'):	comp_code='0110011'
		elif(comp_eqn == '-M'):	comp_code='1110011'

		elif(comp_eqn == 'D+1'):	comp_code='0011111'
		elif(comp_eqn == 'A+1'):	comp_code='0110111'
		elif(comp_eqn == 'M+1'):	comp_code='1110111'
		
		elif(comp_eqn == 'D-1'):	comp_code='0001110'
		elif(comp_eqn == 'A-1'):	comp_code='0110010'
		elif(comp_eqn == 'M-1'):	comp_code='1110010'

		elif(comp_eqn == 'D+A'):	comp_code='0000010'
		elif(comp_eqn == 'D+M'):	comp_code='1000010'

		elif(comp_eqn == 'D-A'):	comp_code='0010011'
		elif(comp_eqn == 'D-M'):	comp_code='1010011'

		elif(comp_eqn == 'A-D'):	comp_code='0000111'
		elif(comp_eqn == 'M-D'):	comp_code='1000111'

		elif(comp_eqn == 'D&A'):	comp_code='0000000'
		elif(comp_eqn == 'D&M'):	comp_code='1000000'

		elif(comp_eqn == 'D|A'):	comp_code='0010101'
		elif(comp_eqn == 'D|M'):	comp_code='1010101'

		return comp_code

	def dest(assembly_code):
		dest_code = ''
		eq_pos = assembly_code.find('=')	
		dest_regs = assembly_code[:eq_pos]	# destination_registers

		if(dest_regs == 'M'):			dest_code = '001'
		elif(dest_regs == 'D'):			dest_code = '010'
		elif(dest_regs == 'MD'):		dest_code = '011'
		elif(dest_regs == 'A'):			dest_code = '100'
		elif(dest_regs == 'AM'):		dest_code = '101'
		elif(dest_regs == 'AD'):		dest_code = '110'
		elif(dest_regs == 'AMD'):		dest_code = '111'

		return dest_code

	def jmp(assembly_code):
		jmp_code = ''
		sc_pos = assembly_code.find(';')	# semi-colon's position

		jmp_cond = assembly_code[sc_pos+1:]	
		if(jmp_cond == 'JGT'):	jmp_code = '001'
		elif(jmp_cond == 'JEQ'):		jmp_code = '010'
		elif(jmp_cond == 'JGE'):		jmp_code = '011'
		elif(jmp_cond == 'JLT'):		jmp_code = '100'
		elif(jmp_cond == 'JNE'):		jmp_code = '101'
		elif(jmp_cond == 'JLE'):		jmp_code = '110'
		elif(jmp_cond == 'JMP'):		jmp_code = '111'

		return jmp_code


def input_filename():
	filename = input('Input filename: ')
	return filename


def read_file(filename, pass_count):
	machine_code = ''
	file_content = open(filename+'.asm','r')

	line_number = 0
	number_of_var = 0
	for individual_line in file_content:
		assembly_code = compiler.parser(individual_line)
		
		if(assembly_code != -1):
			if (assembly_code != ''):			# ignoring comments
				if(pass_count == 1): 
					compiler.initialise_labels(assembly_code, line_number)

				if assembly_code[0:1] not in ['(']:	
					line_number = line_number + 1
					# update line number, ignoring ...
					# ... newlines, white spaces, ...
					# ... comments and label declarations
					
					if(pass_count == 2):
						number_of_var = compiler.initialise_vars(assembly_code, number_of_var)

					if(pass_count == 3):
						statement = compiler.assembly_to_machine(assembly_code)	
						statement = statement + '\n'
						machine_code = machine_code + statement

	return machine_code


def write_file(machine_code, filename):
	_file = open(filename + '.hack','w')
	_file.write(machine_code)

	
def main():
	filename = input_filename()

	# first pass - labels
	read_file(filename,1)

	# second pass - variables
	read_file(filename,2)
	
	# third pass - compilation
	machine_code = read_file(filename,3)
	write_file(machine_code, filename)


if __name__ == '__main__':
	main()