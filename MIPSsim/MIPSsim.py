#!usr/bin/env python
# -*- coding:utf-8 -*-

"""On my honor, I have neither given nor received unauthorized aid on this assignment."""

import sys
import getopt
from functools import reduce

# 三种指令类型字典
category1 = {'000': 'J', '010': 'BEQ', '100': 'BGTZ', '101': 'BREAK', '110': 'SW', '111': 'LW'}
category2 = {'000': 'ADD', '001': 'SUB', '010': 'MUL', '011': 'AND', '100': 'OR', '101': 'XOR', '110': 'NOR'}
category3 = {'000': 'ADDI', '001': 'ANDI', '010': 'ORI', '011': 'XORI'}

proj_path = str(sys.path[0])
# print proj_path


# MIPS模拟器
def simulator(sample_path):
    '''处理文档'''
    fr = open(sample_path, 'r')
    cont = [inst.strip() for inst in fr.readlines()]
    contSize = len(cont)
    
    # 记录BREAK指令位置 axis前为指令 axis后为数据
    axis = 0
    for i in range(contSize):
        if cont[i][3:6] == '101':  axis = i + 1

    '''添加每条对应地址'''
    addr = 128    # 起始指令地址
    l = [cont[i]+'\t'+str(addr + i*4) for i in range(contSize)]      # 添加对应地址

    '''分别解析指令和数据'''
    instructions = [insParse(tl) for tl in l[0:axis]]   # axis前为指令 指令解析
    data = [dataParse(tl) for tl in l[axis:]]           # axis后为数据 数据解析

    disassembly = instructions + data           # 反汇编结果
    disassembly[-1] = disassembly[-1].strip()   # 把disassembly里(data后面)多出的最后一行空格去掉

    '''1、将反汇编结果disassembly写入文件'''
    with open(proj_path+'/generated_disassembly.txt', 'w') as f:
        f.writelines(disassembly)

    '''指令部分和数据部分预处理'''
    # 将指令装为{地址:指令}字典
    # 将数据装为{地址:值}字典
    mergeDict = lambda x, y: dict(x, **y)   # 将两个字典合并
    # 将所有字典合并
    inspart_dict = reduce(mergeDict, map(insToDict, instructions))
    datapart_dict = reduce(mergeDict, map(dataToDict, l[cut:]))

    '''2、将模拟结果simulation_trace_list写入文件'''
    with open(proj_path+'/generated_simulation.txt', 'w') as f:
        f.writelines(simulatorExe(inspart_dict, datapart_dict))


def insParse(il):
    leftmost = il[0:3]
    ll = []          # 添加指令解析部分
    # 第一类指令:
    if leftmost == '000':
        # 000 | opcode(3 bits) | Same as MIPS instruction
        opcode1, rs1, rt1, rd1 = il[3:6], il[6:11], il[11:16], il[16:21]
        # J | instr_index(26)
        j_addr = il[6:32]     # 跳转地址
        # BEQ | rs(5) | rt(5) | offset(16)     if rs = rt then branch
        # BGTZ | rs(5) | 00000 | offset(16)    if rs > 0 then branch
        # SW | base(5) | rt(5) | offset(16)     memory[base+offset] ← rt
        # LW | base(5) | rt(5) | offset(16)     rt ← memory[base+offset]
        offset = il[16:32]    # 跳转偏移量
        base = il[6:11]       # SW LW 的 base

        ll = il + '\t' + category1[opcode1]  # 添加指令类型
        # print(ll)

        if category1[opcode1] == 'J':
            ll += ' #'+str(int(j_addr, 2)*4)
        if category1[opcode1] == 'BEQ':
            ll += ' R'+str(int(rs1, 2))+', R'+str(int(rt1, 2))+', #'+str(int(offset, 2)*4)
        if category1[opcode1] == 'BGTZ':
            ll += ' R'+str(int(rs1, 2))+', #'+str(int(offset, 2)*4)
        if category1[opcode1] == 'SW' or category1[opcode1] == 'LW':
            ll += ' R'+str(int(rt1, 2))+', '+str(int(offset, 2))+'(R'+str(int(base, 2))+')'
        # print(ll)

    # 第二类指令:
    if leftmost == '110':
        # 110 | rs(5 bits) | rt(5 bits) | opcode(3 bits) | rd(5 bits) | 00000000000
        # rd ← rs (ins) rt
        rs2, rt2, opcode2, rd2 = il[3:8], il[8:13], il[13:16], il[16:21]
        ll = il + '\t' + category2[opcode2] + ' R' + str(int(rd2, 2))+', R'+str(int(rs2, 2))+', R'+str(int(rt2, 2))
        # print(ll)

    # 第三类指令:
    if leftmost == '111':
        # 111 | rs(5 bits) | rt(5 bits) | opcode(3 bits) | immediate_value(16 bits)
        # rt ← rs (ins) immediate
        rs3, rt3, opcode3, immediate = il[3:8], il[8:13], il[13:16], il[16:32]
        ll = il + '\t' + category3[opcode3] + ' R' + str(int(rt3, 2))+', R'+str(int(rs3, 2))+', #'+str(int(immediate, 2))
        # print(ll)

    ll += '\n'
    return ll

def dataParse(dl):
    if dl[0] == '0':   # 正数
        dl += '\t' + str(int(dl[0:32], 2))
    else:              # 负数
        dl += '\t-' + str((2147483647 ^ int(dl[1:32], 2))+1)
    dl += '\n'
    return dl


# 指令预处理
def insToDict(instructions):
    ins_dict = {}
    # 字典:  地址:32位指令
    ins_dict[instructions[33:36]] = instructions[0:32]
    ins_dict['instr'+instructions[33:36]] = instructions[37:].strip()
    # print(ins_dict)     # {'128': '11000000000000000000100000000000', 'instr128': 'ADD R1, R0, R0'} ...
    return ins_dict

# 数据预处理
def dataToDict(data):
    data_dict = {}
    # 字典:  地址:值
    if data[0] == '0':
        data_dict[data[-3:]] = int(data[0:32], 2)
    else:
        data_dict[data[-3:]] = -((2147483647 ^ int(data[1:32], 2))+1)
    # print(data_dict)    # {'184': -1}  {'188': -2} ...
    return data_dict


'''MIPS模拟器执行指令'''
def simulatorExe(inspart_dict, datapart_dict):
    cycle_number = 1
    data_sorted_list = sorted(datapart_dict.keys())
    registers = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    instr_address = 128
    is_execute = True            # 指令是否执行
    simulation_trace_list = []   # 模拟结果

    # simulation trace
    while is_execute:
        sim_list = '--------------------\nCycle:'+str(cycle_number)+'\t'+str(instr_address)+'\t'+inspart_dict['instr'+str(instr_address)]+'\n\n'
        instructions = inspart_dict[str(instr_address)]  # 11000000000000000000100000000000 ...
        # print(instructions)
        instr_address += 4
        cycle_number += 1
        leftmost = instructions[0:3]

        # 第一类指令:
        if leftmost == '000':
            # 000 | opcode(3 bits) | Same as MIPS instruction
            opcode1, rs1, rt1, rd1 = instructions[3:6], instructions[6:11], instructions[11:16], instructions[16:21]
            # J | instr_index(26)
            j_addr = instructions[6:32]    # 跳转地址
            # BEQ | rs(5) | rt(5) | offset(16)     if rs = rt then branch
            # BGTZ | rs(5) | 00000 | offset(16)    if rs > 0 then branch
            # SW | base(5) | rt(5) | offset(16)     memory[base+offset] ← rt
            # LW | base(5) | rt(5) | offset(16)     rt ← memory[base+offset]
            offset = instructions[16:32]   # 跳转偏移量
            base = instructions[6:11]      # SW LW 的 base

            if category1[opcode1] == 'J':
                instr_address = int(j_addr, 2) * 4    # 跳到该地址

            if category1[opcode1] == 'BEQ':
                if registers[int(rs1, 2)] == registers[int(rt1, 2)]:
                    instr_address += int(offset, 2) * 4     # 如果rs==rt  在该地址基础上偏移

            if category1[opcode1] == 'BGTZ':
                if registers[int(rs1, 2)] > 0:
                    instr_address += int(offset, 2)*4       # 如果rs>0  在该地址基础上偏移

            if category1[opcode1] == 'SW':                  # memory[base+offset] ← rt
                try:
                    datapart_dict[str(registers[int(base, 2)]+int(offset, 2))] = registers[int(rt1, 2)]
                except:
                    pass

            if category1[opcode1] == 'LW':      # rt ← memory[base+offset]
                try:
                    registers[int(rt1, 2)] = datapart_dict[str(registers[int(base, 2)]+int(offset, 2))]
                except:
                    pass

            if category1[opcode1] == 'BREAK':
                is_execute = False

        # 第二类指令:
        if leftmost == '110':
            # 110 | rs(5 bits) | rt(5 bits) | opcode(3 bits) | rd(5 bits) | 00000000000
            rs2, rt2, opcode2, rd2 = instructions[3:8], instructions[8:13], instructions[13:16], instructions[16:21]

            # rd ← rs (ins) rt
            if category2[opcode2] == 'ADD':
                registers[int(rd2, 2)] = registers[int(rs2, 2)] + registers[int(rt2, 2)]
            if category2[opcode2] == 'SUB':
                registers[int(rd2, 2)] = registers[int(rs2, 2)] - registers[int(rt2, 2)]
            if category2[opcode2] == 'MUL':
                registers[int(rd2, 2)] = registers[int(rs2, 2)] * registers[int(rt2, 2)]
            if category2[opcode2] == 'AND':
                registers[int(rd2, 2)] = registers[int(rs2, 2)] & registers[int(rt2, 2)]
            if category2[opcode2] == 'OR':
                registers[int(rd2, 2)] = registers[int(rs2, 2)] | registers[int(rt2, 2)]
            if category2[opcode2] == 'XOR':
                registers[int(rd2, 2)] = registers[int(rs2, 2)] ^ registers[int(rt2, 2)]
            if category2[opcode2] == 'NOR':
                registers[int(rd2, 2)] = (registers[int(rs2, 2)] | registers[int(rt2, 2)]) ^ 2147483648

        # 第三类指令:
        if leftmost == '111':
            # 111 | rs(5 bits) | rt(5 bits) | opcode(3 bits) | immediatediate_value(16 bits)
            rs3, rt3, opcode3, immediate = instructions[3:8], instructions[8:13], instructions[13:16], instructions[16:32]

            # rt ← rs (ins) immediate
            if category3[opcode3] == 'ADDI':
                registers[int(rt3, 2)] = registers[int(rs3, 2)] + int(immediate, 2)
            if category3[opcode3] == 'ANDI':
                registers[int(rt3, 2)] = registers[int(rs3, 2)] & int(immediate, 2)
            if category3[opcode3] == 'ORI':
                registers[int(rt3, 2)] = registers[int(rs3, 2)] | int(immediate, 2)
            if category3[opcode3] == 'XORI':
                registers[int(rt3, 2)] = registers[int(rs3, 2)] ^ int(immediate, 2)

        # Registers
        sim_list += 'Registers\nR00:'
        # R00: < tab > < int(R0) > < tab > < int(R1) > ... < tab > < int(R7) >
        for x in registers[0:8]:
            sim_list += '\t'+str(x)

        # R08: < tab > < int(R8) > < tab > < int(R9) > ... < tab > < int(R15) >
        sim_list += '\nR08:'
        for x in registers[8:16]:
            sim_list += '\t'+str(x)

        # R16: < tab > < int(R16) > < tab > < int(R17) > ... < tab > < int(R23) >
        sim_list += '\nR16:'
        for x in registers[16:24]:
            sim_list += '\t'+str(x)

        # R24: < tab > < int(R24) > < tab > < int(R25) > ... < tab > < int(R31) >
        sim_list += '\nR24:'
        for x in registers[24:]:
            sim_list += '\t'+str(x)

        #  < blank_line >
        # Data
        sim_list += '\n\nData\n184:'
        # < firstDataAddress >: < tab > < display 8 data words as integers with tabs in between >
        for x in data_sorted_list[0:8]:
            sim_list += '\t'+str(datapart_dict[x])

        sim_list += '\n216:'
        for x in data_sorted_list[8:16]:
            sim_list += '\t'+str(datapart_dict[x])

        sim_list += '\n\n'

        # if is_execute == False:
        #     sim_list = sim_list[-1].strip()

        simulation_trace_list.append(sim_list)

    return simulation_trace_list


def main(argv):
   inputfilename = ''
   try:
      opts, args = getopt.getopt(argv, "hi:", ["ifile="])     # 命令行参数
   except getopt.GetoptError:
      print('MIPSsim.py -i <inputfilename>')
      sys.exit(2)

   for opt, arg in opts:
      if opt == '-h':
         print('MIPSsim.py -i <inputfilename>')
         sys.exit()
      elif opt in ("-i", "--ifile"):
         inputfilename = arg
   # print('输入的文件为：', inputfilename)

   simulator(proj_path + '/' + inputfilename)

# print(len(sys.argv))
# print(type(sys.argv))
# print(str(sys.argv))
# for a in range(0, len(sys.argv)):
#   print(sys.argv[a])

if __name__ == "__main__":
   main(sys.argv[1:])
