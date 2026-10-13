import struct,capstone,sys
e=open('SLPS_201.78','rb').read()
a=int(sys.argv[1],16); b=int(sys.argv[2],16)
md=capstone.Cs(capstone.CS_ARCH_MIPS,capstone.CS_MODE_MIPS32+capstone.CS_MODE_LITTLE_ENDIAN)
md.skipdata=True
base=0x100000-0x80
for ins in md.disasm(e[a-base:b-base],a): print(hex(ins.address),ins.mnemonic,ins.op_str)
