import re
import os
from os import listdir
from os.path import join

# VM Translator
class RAM:
	SP = 0;				#RAM[0] - stack ptr
	LCL = 1 			#RAM[1] - ptr to local
	ARG = 2 			#RAM[2]	- ptr to argument 
	
	ptr0 = 3			#RAM[3] - ptr to THIS 
	ptr1 = 4 			#RAM[4] = ptr to THAT

	# [base_addr, last_addr, ...
	# ... list (to store all the values)]
	TEMP = 5					#RAM[5] to RAM[12] - temp segment
	GPReg = 13					#RAM[13] to RAM[15] - General Purpose Registers
	STATIC = 16					#RAM[16] to RAM[255] - Static Variables

	count_static = -1
	static_table = dict()

	def update_staticTable(static_arg2):
		# filename.j --- name of static variable ...
		# j is the count of static variables
		for var in RAM.static_table:
			if(var == vm_translator.filename + str(static_arg2)):
				# 1 indicates that the variable pre-existed
				return [RAM.static_table[var],1]	

		RAM.count_static = RAM.count_static + 1
		RAM.static_table[vm_translator.filename + str(static_arg2)] = vm_translator.filename + '.' + str(RAM.count_static)
		# -1 indicates that the variable was created
		return [RAM.static_table[vm_translator.filename + str(static_arg2)],-1]

class comp_opt:
	# to store the return address of called function
	fn = dict()
	cur_fn = ''		# the current function's name

	def add_fn(name):
		flag = -1
		comp_opt.cur_fn = name
		for fn_name in comp_opt.fn:
			if(fn_name == name):
				flag = 1

		if(flag == -1):
			comp_opt.fn[name] = 0

	def call_fn():
		flag = -1
		for fn_name in comp_opt.fn:
			if(fn_name == comp_opt.cur_fn):
				flag = 1
				comp_opt.fn[fn_name] = comp_opt.fn[fn_name] + 1

		if(flag == -1):
			comp_opt.fn[comp_opt.cur_fn] = 1

		return comp_opt.cur_fn + '$ret.' + str(comp_opt.fn[comp_opt.cur_fn])


	# class for compiler optimization
	def pop_into_D(code):
		# move the stack pointer one-step back
		code.append('@' + str(RAM.SP) +'\n')
		code.append('M=M-1\n')

		# the popped value is stored ...
		# ... in the D register
		code.append('@' + str(RAM.SP) +'\n')
		code.append('A=M\n')
		code.append('D=M\n')
		return

	def push_D_into_Stack(code):
		# push D into stack
		code.append('@' + str(RAM.SP) +'\n')
		code.append('A=M\n')
		code.append('M=D\n')

		# update stack ptr
		code.append('@'  + str(RAM.SP) +'\n')
		code.append('M=M+1\n')

	def store_GPR(code,offset):
		# stores D into the temp registers
		code.append('@' + str(RAM.GPReg+offset) + '\n')
		code.append('M=D\n')

	def access_GPR(code,offset,cond):
		# push into A/D from the temp registers
		code.append('@' + str(RAM.GPReg+offset) + '\n')
		if(cond == 'A'):	code.append('A=M\n')
		elif(cond == 'D'):	code.append('D=M\n')

	def access_memSegment(code, mem_ptr,offset,cond):
		# addr = base_addr + offset
		code.append('@' + str(offset) + '\n')
		code.append('D=A\n')

		# A/D stores the address to the asked memory
		code.append('@' + str(mem_ptr) + '\n')
		if(cond == 'A'):	code.append('A=D+M\n')		
		elif(cond == 'D'):	code.append('D=D+M\n')	

	def access_tempSegment(code, mem_ptr,offset,cond):
		# addr = base_addr + offset
		code.append('@' + str(offset) + '\n')
		code.append('D=A\n')

		# A/D stores the address to the asked memory
		code.append('@' + str(mem_ptr) + '\n')
		if(cond == 'A'):	code.append('A=D+A\n')		
		elif(cond == 'D'):	code.append('D=D+A\n')			


class vm_translator:
	foldername = ''
	filename = ''
	count_if_else = -1

	def bootstrap():
		_file = open(vm_translator.foldername + '.asm','w')

		code = []
		# SP = 256
		code.append('@256\t\t//bootstrap code\n')
		code.append('D=A\t\t//bootstrap code\n')
		code.append('@' + str(RAM.SP) + '\t\t//bootstrap code\n')
		code.append('M=D\t\t//bootstrap code\n')

		# LCL = -1
		code.append('@1\t\t//bootstrap code\n')
		code.append('D=A\t\t//bootstrap code\n')
		code.append('D=-D\t\t//bootstrap code\n')
		code.append('@' + str(RAM.LCL) + '\t\t//bootstrap code\n')
		code.append('M=D\t\t//bootstrap code\n')

		# ARG = -2
		code.append('@2\t\t//bootstrap code\n')
		code.append('D=A\t\t//bootstrap code\n')
		code.append('D=-D\t\t//bootstrap code\n')
		code.append('@' + str(RAM.ARG) + '\t\t//bootstrap code\n')
		code.append('M=D\t\t//bootstrap code\n')

		# THIS = -3
		code.append('@3\t\t//bootstrap code\n')
		code.append('D=A\t\t//bootstrap code\n')
		code.append('D=-D\t\t//bootstrap code\n')
		code.append('@' + str(RAM.ptr0) + '\t\t//bootstrap code\n')
		code.append('M=D\t\t//bootstrap code\n')

		# THAT = -4
		code.append('@4\t\t//bootstrap code\n')
		code.append('D=A\t\t//bootstrap code\n')
		code.append('D=-D\t\t//bootstrap code\n')
		code.append('@' + str(RAM.ptr1) + '\t\t//bootstrap code\n')
		code.append('M=D\t\t//bootstrap code\n')

		temp_code =  cmd_translator.function_cmds('call','Sys.init',0)
		temp_code = re.sub('\n','\t\t//bootstrap code\n',temp_code)

		final_code = ''

		for line in code:
			final_code = final_code + line

		final_code = final_code + temp_code
		_file.write(final_code)
		_file.close()

		return

	def translate(pathname, filename):
		code  = ''	
		comment = ''
		assembly_code = ''
		vm_translator.filename = filename
		file_content = open(join(pathname, filename),'r')
		_file = open(vm_translator.foldername + '.asm','a')
		_file.write('//'+vm_translator.filename+'\n')
		for individual_line in file_content:
			code = ''
			comment = ''
			[cmd, arg1, arg2] = vm_translator.parser(individual_line)

			if(cmd != '-1'):
				cmd_type = vm_translator.find_cmd_type(cmd)
				if(cmd_type == 'error'):
					return 'error'
				
				if(cmd_type == 'arithmetic'):
					comment = '\t\t//' + cmd + '\n'
					
					if(arg1 == '-1'):
						if(arg2 == -1):
							code = cmd_translator.arithmetic_cmds(cmd)
						else:	
							print('Error - Arithmetic command cannot have a numeral argument!')
							return 'error'
					else:	
						print('Error - Arithmetic command cannot have a memory segment as an argument!')
						return 'error'

				elif(cmd_type == 'branching'):
					if(arg2 == -1):
						comment = '\t\t//' + cmd + ' ' + arg1 + '\n'
						code = cmd_translator.branching_cmds(cmd,arg1)
					else:	
						print('Error - Jump commands cannot have a numeral argument!')
						return 'error'

				elif(cmd_type == 'function'):
					if(arg1 != '-1'):
						comment = '\t\t//' + cmd + ' ' + arg1 + ' ' + str(arg2) + '\n'
					else:
						comment = '\t\t//' + cmd + '\n'
					code = cmd_translator.function_cmds(cmd,arg1,arg2)

				elif(cmd_type == 'mem_access'):
					comment = '\t\t//' + cmd + ' ' + arg1 + ' ' + str(arg2) + '\n'
					code = cmd_translator.mem_access_cmds(cmd,arg1,arg2)

			if(code == 'error'):		
				return 'error'

			check = 0
			for line in code:
				en_write = 1

				if(check == 0):
					if(line == '\n'):
						check = 1
				
				elif(check == 1):
					if(line == '\n'):
						en_write = 0

					else:
						check = 0

				if(en_write == 1):
					if(line == '\n'):
						_file.write('\t')
						_file.write(comment[:-1])

					_file.write(line)

		_file.close()
		return 'success'

	def parser(vm_code):
		cmd = arg1 = '-1'
		arg2 = -1
		vm_code = re.sub('\n','',vm_code)
		vm_code = re.sub('\t','',vm_code)
		vm_code = re.sub('//',' //',vm_code)
		
		temp_code = vm_code.split(' ')
		parsed_code = temp_code.copy()
		cmt_flag = False

		for word in parsed_code: 
			if word == '':
				temp_code.remove(word)

			elif cmt_flag == True:
				temp_code.remove(word)

			elif word[0] == '/':
				cmt_flag = True
				temp_code.remove(word)	
		
		if len(temp_code) == 1:
			cmd = temp_code[0]
		
		elif len(temp_code) == 2:
			cmd = temp_code[0]
			arg1 = temp_code[1]
		
		elif len(temp_code) == 3:
			cmd = temp_code[0]
			arg1 = temp_code[1]
			arg2 = int(temp_code[2])

		return [cmd, arg1, arg2]

	def find_cmd_type(cmd):
		# ARITHMETIC COMMANDS:
		if(cmd == 'add'):			return 'arithmetic'
		elif(cmd == 'sub'):			return 'arithmetic'
		elif(cmd == 'neg'):			return 'arithmetic'

		elif(cmd == 'eq'):			return 'arithmetic'
		elif(cmd == 'gt'):			return 'arithmetic'
		elif(cmd == 'lt'):			return 'arithmetic'

		elif(cmd == 'and'):			return 'arithmetic'
		elif(cmd == 'or'):			return 'arithmetic'
		elif(cmd == 'not'):			return 'arithmetic'


		# BRANCHING COMMANDS:
		elif(cmd == 'label'):		return 'branching'
		elif(cmd == 'goto'):		return 'branching'
		elif(cmd == 'if-goto'):		return 'branching'

		# FUNCTION COMMANDS:
		elif(cmd == 'function'):	return 'function'
		elif(cmd == 'call'):		return 'function'
		elif(cmd == 'return'):		return 'function'

		# MEMORY ACCESS COMMANDS:
		elif(cmd == 'pop'):			return 'mem_access'
		elif(cmd == 'push'):		return 'mem_access'

		else:
			print('Error - Unknown code syntax!')
			return 'error'

class cmd_translator:
	def arithmetic_cmds(cmd):
		assembly_code = ''
		if cmd in ['add', 'sub']:		assembly_code = cmd_translator.add_sub(cmd)
		elif cmd in ['not', 'neg']:		assembly_code = cmd_translator.not_neg(cmd)
		elif cmd in ['and', 'or']:		assembly_code = cmd_translator.and_or(cmd)
		elif cmd in ['eq', 'gt', 'lt']: 	assembly_code = cmd_translator.eq_gt_lt(cmd)
		return assembly_code

	def branching_cmds(cmd, arg1):
		assembly_code = ''
		if(cmd == 'label'):		assembly_code = cmd_translator.label(arg1)
		elif(cmd == 'goto'):		assembly_code = cmd_translator.goto(arg1)
		elif(cmd == 'if-goto'):		assembly_code = cmd_translator.if_goto(arg1)
		return assembly_code

	def function_cmds(cmd, arg1, arg2):
		assembly_code = ''
		if(cmd == 'function'):		assembly_code = cmd_translator.function(arg1, arg2)
		elif(cmd == 'call'):		assembly_code = cmd_translator.call(arg1, arg2)
		elif(cmd == 'return'):		
			if(arg1 == '-1'):
				if(arg2 == -1):
					assembly_code = cmd_translator._return()
				else:
					print('Error - Return command cannot have a numeral argument!')
					return 'error'
			else:
				print('Error - Return command cannot have a secondary argument!')
				return 'error'

		return assembly_code

	def mem_access_cmds(cmd, arg1, arg2):
		assembly_code = ''
		if(cmd == 'pop'):
			if arg1 in ['this', 'that', 'pointer']:
				assembly_code = cmd_translator.pop_ptrs(arg1, arg2)
			else:	
				assembly_code = cmd_translator.pop_except_ptrs(arg1, arg2)
		elif(cmd == 'push'):	assembly_code = cmd_translator.push(arg1, arg2)
		return assembly_code

	# ARTHIMETIC COMMANDS:
	def add_sub(cmd):
		code = []
		comp_opt.pop_into_D(code)

		# add/sub D to the next element ...
		# ... in the stack
		code.append('@' + str(RAM.SP) +'\n')
		code.append('M=M-1\n')
		code.append('A=M\n')

		if(cmd=='add'):
			# add
			code.append('M=M+D\n')

		else:
			# sub
			code.append('M=M-D\n')

		# update stack pointer
		code.append('@' + str(RAM.SP) +'\n')
		code.append('M=M+1\n')

		final_code = ''
		for line in code:
	 		final_code = final_code + line
		return final_code

	def not_neg(cmd):
		code = []
		comp_opt.pop_into_D(code)

		if(cmd=='neg'):
			# neg
			code.append('D=-D\n')

		else:
			# not 
			code.append('D=!D\n')

		comp_opt.push_D_into_Stack(code)

		final_code = ''
		for line in code:
	 		final_code = final_code + line
		return final_code

	def and_or(cmd):
		code = []
		comp_opt.pop_into_D(code)			# last element into D register
		comp_opt.store_GPR(code, 0)			# D register into GPReg 
		comp_opt.pop_into_D(code)			# second-last element into D register

		if(cmd == 'and'):
			code.append('@' + str(RAM.GPReg) + '\n')
			code.append('D=D&M\n')

		elif(cmd == 'or'):
			code.append('@' + str(RAM.GPReg) + '\n')
			code.append('D=D|M\n')

		comp_opt.push_D_into_Stack(code)

		final_code = ''
		for line in code:
	 		final_code = final_code + line
		return final_code

	def eq_gt_lt(cmd):
		code = []
		vm_translator.count_if_else = vm_translator.count_if_else + 1

		comp_opt.pop_into_D(code)			# last element into D register
		comp_opt.store_GPR(code, 0)			# D register into GPReg 
		comp_opt.pop_into_D(code)			# second-last element into D register

		if(cmd == 'eq'):
			code.append('@' + str(RAM.GPReg) + '\n')
			code.append('D=D-M\n')

			code.append('@TRUE.' + str(vm_translator.count_if_else) + '\n')
			code.append('D;JEQ\n')
			code.append('@FALSE.' + str(vm_translator.count_if_else) + '\n')
			code.append('D;JNE\n')			

		elif(cmd == 'gt'):
			code.append('@' + str(RAM.GPReg) + '\n')
			code.append('D=D-M\n')

			code.append('@TRUE.' + str(vm_translator.count_if_else) + '\n')
			code.append('D;JGT\n')
			code.append('@FALSE.' + str(vm_translator.count_if_else) + '\n')
			code.append('D;JLE\n')	

		elif(cmd == 'lt'):
			code.append('@' + str(RAM.GPReg) + '\n')
			code.append('D=D-M\n')

			code.append('@TRUE.' + str(vm_translator.count_if_else) + '\n')
			code.append('D;JLT\n')
			code.append('@FALSE.' + str(vm_translator.count_if_else) + '\n')
			code.append('D;JGE\n')

		# true block
		code.append('(TRUE.' +  str(vm_translator.count_if_else) + ')\n')
		# push -1 for TRUE into stack
		code.append('@' + str(RAM.SP) + '\n')
		code.append('A=M\n')
		code.append('M=-1\n')
		code.append('@' + str(RAM.SP) + '\n')
		code.append('M=M+1\n')
		code.append('@END.' + str(vm_translator.count_if_else) + '\n')
		code.append('0;JMP\n')

		# false block
		code.append('(FALSE.' +  str(vm_translator.count_if_else) + ')\n')
		# push 0 for FALSE into stack
		code.append('@' + str(RAM.SP) + '\n')
		code.append('A=M\n')
		code.append('M=0\n')
		code.append('@' + str(RAM.SP) + '\n')
		code.append('M=M+1\n')
		code.append('@END.' + str(vm_translator.count_if_else) + '\n')
		code.append('0;JMP\n')

		# the end of if-else block
		code.append('(END.' + str(vm_translator.count_if_else) + ')\n')

		final_code = ''
		for line in code:
	 		final_code = final_code + line
		return final_code

	# BRANCHING COMMANDS:
	def label(arg1):
		code = []
		code.append('(' + arg1 + ')\n')

		final_code = ''
		for line in code:
	 		final_code = final_code + line
		return final_code

	def goto(arg1):
		code = []
		code.append('@' + arg1 + '\n')
		code.append('0;JMP\n')

		final_code = ''
		for line in code:
	 		final_code = final_code + line
		return final_code

	def if_goto(arg1):
		code = []
		comp_opt.pop_into_D(code)

		code.append('@' + arg1 + '\n')
		code.append('D;JNE\n')

		final_code = ''
		for line in code:
	 		final_code = final_code + line
		return final_code

	# FUNCTION COMMANDS:
	def function(arg1, arg2):
		comp_opt.add_fn(arg1)

		code = []
		code.append('(' + arg1  + ')\n')
		while(arg2 > 0):
			arg2 = arg2 - 1
			temp = cmd_translator.push('constant', 0)
			code.append(temp)

		final_code = ''
		for line in code:
	 		final_code = final_code + line
		return final_code


	def call(arg1, arg2):
		code=[]		

		# get retAddr
		retAddr = comp_opt.call_fn()
		
		# push retAddr
		code.append('@' + retAddr + '\n')
		code.append('D=A\n')
		comp_opt.push_D_into_Stack(code)

		# push LCL
		code.append('@' + str(RAM.LCL) + '\n')
		code.append('D=M\n')
		comp_opt.push_D_into_Stack(code)

		# push ARG 
		code.append('@' + str(RAM.ARG) + '\n')
		code.append('D=M\n')
		comp_opt.push_D_into_Stack(code)

		# push THIS
		code.append('@' + str(RAM.ptr0) + '\n')
		code.append('D=M\n')
		comp_opt.push_D_into_Stack(code)

		# push THAT
		code.append('@' + str(RAM.ptr1) + '\n')
		code.append('D=M\n')
		comp_opt.push_D_into_Stack(code)

		# ARG = SP - 5 - nArgs
		code.append('@5\n')
		code.append('D=A\n')

		code.append('@' + str(arg2) + '\n')
		code.append('D=D+A\n')

		code.append('@' +  str(RAM.SP) + '\n')
		code.append('D=M-D\n')

		code.append('@' + str(RAM.ARG) + '\n')
		code.append('M=D\n')

		code.append('@' + str(RAM.SP) + '\n')
		code.append('D=M\n')

		code.append('@' + str(RAM.LCL) + '\n')
		code.append('M=D\n')

		# LCL = SP
		code.append('@' + str(RAM.SP) + '\n')
		code.append('D=M\n')

		code.append('@' + str(RAM.LCL) + '\n')
		code.append('M=D\n')

		# function call statement
		code.append(cmd_translator.goto(arg1))

		# function return statement
		code.append('(' + retAddr + ')\n')

		final_code = ''
		for line in code:
	 		final_code = final_code + line
		return final_code


	def _return():
		code = []

		# endFrame = LCL, stored in GPR[0]
		# retAddr = *(endFrame - 5), stored in GPR[1]
		code.append('@' + str(RAM.LCL) + '\n')
		code.append('D=M\n')
		comp_opt.store_GPR(code,0)
		code.append('D=D-1\n')
		code.append('D=D-1\n')
		code.append('D=D-1\n')
		code.append('D=D-1\n')
		code.append('A=D-1\n')
		code.append('D=M\n')
		comp_opt.store_GPR(code,1)

		# ARG = pop(),	*A - value in RAM[A]
		comp_opt.pop_into_D(code)
		code.append('@' + str(RAM.ARG) + '\n')
		code.append('A=M\n')
		code.append('M=D\n')

		# SP = ARG+1
		code.append('@' + str(RAM.ARG) + '\n')
		code.append('D=M\n')
		code.append('@' + str(RAM.SP) + '\n') 
		code.append('M=D+1\n')

		# THAT = *(endFrame - 1)
		comp_opt.access_GPR(code,0,'D')
		code.append('AM=D-1\n')
		code.append('D=M\n')
		code.append('@' + str(RAM.ptr1) + '\n')
		code.append('M=D\n')

		# THIS = *(endFrame - 2)
		comp_opt.access_GPR(code,0,'D')
		code.append('AM=D-1\n')
		code.append('D=M\n')
		code.append('@' + str(RAM.ptr0) + '\n')
		code.append('M=D\n')

		# ARG = *(endFrame - 3)
		comp_opt.access_GPR(code,0,'D')
		code.append('AM=D-1\n')
		code.append('D=M\n')
		code.append('@' + str(RAM.ARG) + '\n')
		code.append('M=D\n')

		# LCL = *(endFrame - 4)
		comp_opt.access_GPR(code,0,'D')
		code.append('AM=D-1\n')
		code.append('D=M\n')
		code.append('@' + str(RAM.LCL) + '\n')
		code.append('M=D\n')

		# goto retAddr
		comp_opt.access_GPR(code,1,'A')	 
		code.append('0;JMP\n')
		final_code = ''
		for line in code:
	 		final_code = final_code + line
		return final_code


	# MEMORY ACCESS COMMANDS:
	def push(arg1, arg2):
		code = []
		if(arg1 == 'constant'):
			# push arg2 into D
			code.append('@' + str(arg2) + '\n')
			code.append('D=A\n')

		elif(arg1 == 'local'):
			comp_opt.access_memSegment(code,RAM.LCL,arg2,'A')
			code.append('D=M\n')

		elif(arg1 == 'argument'):
			comp_opt.access_memSegment(code,RAM.ARG,arg2,'A')
			code.append('D=M\n')


		elif(arg1 == 'temp'):
			comp_opt.access_tempSegment(code,RAM.TEMP,arg2,'A')
			code.append('D=M\n')


		elif(arg1 == 'static'):
			# static variables are actual assembly ...
			# ... variables, hence static 2 -> filename.variable_no
			static = RAM.update_staticTable(arg2)
			if(static[1] == -1):
				print('Error - Static variable not declared!')
				return 'error'
			
			# push argument static into D
			code.append('@' + static[0] + '\n')
			code.append('D=M\n')

		# Pointer - THIS and THAT
		elif(arg1 == 'pointer'):
			# pointer 0 - this
			if(arg2 == 0):
				# base addr + offset
				ptr = str(RAM.ptr0)
			
			# pointer 1 - that
			elif(arg2 == 1):
				# base addr + offset
				ptr = str(RAM.ptr1)

			else:
				print('Error - Pointer cannot refer to any value other than 0 or 1!')
				return 'error'

			# push argument ptr into D
			code.append('@' + ptr + '\n')
			code.append('D=M\n')

		elif(arg1 == 'this'):
			comp_opt.access_memSegment(code,RAM.ptr0,arg2,'A')
			code.append('D=M\n')

		elif(arg1 == 'that'):
			comp_opt.access_memSegment(code,RAM.ptr1,arg2,'A')
			code.append('D=M\n')

		comp_opt.push_D_into_Stack(code)

		final_code = ''
		for line in code:
	 		final_code = final_code + line
		return final_code

	def pop_except_ptrs(arg1, arg2):
		code = []
		comp_opt.pop_into_D(code)
		comp_opt.store_GPR(code,0)

		# to push the popped value ...
		# ... into the correct memory location
		if(arg1 == 'constant'):
			# constant can not be popped into
			print('Error - Constants cannot be re-assigned any value!')
			return'error'

		if arg1 in ['local', 'argument', 'temp']:
			if(arg1 == 'local'):			comp_opt.access_memSegment(code,RAM.LCL,arg2,'D')
			elif(arg1 == 'argument'):		comp_opt.access_memSegment(code,RAM.ARG,arg2,'D')
			elif(arg1 == 'temp'):			comp_opt.access_tempSegment(code,RAM.TEMP,arg2,'D')

			comp_opt.store_GPR(code,1)
			comp_opt.access_GPR(code,0,'D')
			comp_opt.access_GPR(code,1,'A')
			code.append('M=D\n')

		elif arg1 in ['static']:
			# static variables are actual assembly ...
			# ... variables, hence static 2 -> filename.variable_count
			static = RAM.update_staticTable(arg2)

			# push argument static into D
			code.append('@' + static[0] + '\n')
			code.append('M=D\n')

		final_code = ''
		for line in code:
	 		final_code = final_code + line
		return final_code

	def pop_ptrs(arg1, arg2):
		code = []
		comp_opt.pop_into_D(code)
		comp_opt.store_GPR(code,0)

		if arg1 in ['pointer']:
			# pointer 0 - this
			if(arg2 == 0):
				# base addr + offset
				ptr = str(RAM.ptr0)
			
			# pointer 1 - that
			elif(arg2 == 1):
				# base addr + offset
				ptr = str(RAM.ptr1)

			else:
				print('Error - Pointer cannot refer to any value other than 0 or 1!')
				return 'error'

			# push argument ptr into D
			code.append('@' + ptr + '\n')
			code.append('M=D\n')

		elif arg1 in ['this', 'that']:
			if(arg1 == 'this'):		comp_opt.access_memSegment(code,RAM.ptr0,arg2,'D')
			elif(arg1 == 'that'):	comp_opt.access_memSegment(code,RAM.ptr1,arg2,'D')

			comp_opt.store_GPR(code,1)
			comp_opt.access_GPR(code,0,'D')
			comp_opt.access_GPR(code,1,'A')
			code.append('M=D\n')

		final_code = ''
		for line in code:
	 		final_code = final_code + line
		return final_code


def input_foldername():
	foldername = input('Input foldername: ')
	return foldername

def main():
	foldername = input_foldername()
	vm_translator.foldername = foldername
	
	pathName = join(os.getcwd(),foldername)
	
	_vm_list = [txtfile for txtfile in listdir(pathName) if txtfile[-3:] == '.vm']
	vm_translator.bootstrap()
	
	for _file in _vm_list:
		assembly_code = vm_translator.translate(pathName, _file)
		if(assembly_code == 'error'):
			print('Compilation failed!')

	return		

if __name__ == '__main__':
	main()











