from pathlib import Path
import struct,zipfile
class ClassFile:
 def __init__(self,b):
  self.b=b;self.pos=8;self.cp=[None];count=self.u2();i=1
  while i<count:
   tag=self.u1()
   if tag==1:n=self.u2();v=self.take(n).decode('utf8',errors='replace')
   elif tag in [3,4]:v=self.take(4)
   elif tag in [5,6]:v=self.take(8)
   elif tag in [7,8,16,19,20]:v=self.u2()
   elif tag in [9,10,11,12,17,18]:v=(self.u2(),self.u2())
   elif tag==15:v=(self.u1(),self.u2())
   else:raise ValueError(tag)
   self.cp.append((tag,v));i+=1
   if tag in [5,6]:self.cp.append(None);i+=1
  self.take(6);self.take(self.u2()*2)
  for _ in range(self.u2()):self.member(False)
  self.methods=[self.member(True) for _ in range(self.u2())]
 def take(self,n):v=self.b[self.pos:self.pos+n];self.pos+=n;return v
 def u1(self):return self.take(1)[0]
 def u2(self):return struct.unpack('>H',self.take(2))[0]
 def u4(self):return struct.unpack('>I',self.take(4))[0]
 def text(self,i):
  tag,v=self.cp[i]
  if tag==1:return v
  if tag in [7,8]:return self.text(v)
  if tag==12:return self.text(v[0])+self.text(v[1])
  if tag in [9,10,11]:return self.text(v[0])+'.'+self.text(v[1])
  return str((tag,v))
 def member(self,keep):
  self.u2();name=self.text(self.u2());desc=self.text(self.u2());code=None
  for _ in range(self.u2()):
   attr=self.text(self.u2());data=self.take(self.u4())
   if attr=='Code':size=struct.unpack('>I',data[4:8])[0];code=data[8:8+size]
  return (name,desc,code) if keep else None
 def refs(self,method):
  name,desc,code=method
  if code is None:return
  # For these small methods, validated reference tags rule out operand false matches.
  refs=[]
  for i,op in enumerate(code):
   if op in [0xb2,0xb3,0xb4,0xb5,0xb6,0xb7,0xb8,0xb9,0xbb,0xc0,0xc1] and i+2<len(code):
    cp=struct.unpack('>H',code[i+1:i+3])[0]
    if 0<cp<len(self.cp) and self.cp[cp] and self.cp[cp][0] in ([7] if op in [0xbb,0xc0,0xc1] else [9,10,11]):refs.append((i,hex(op),self.text(cp)))
   elif op==0x12 and i+1<len(code):
    cp=code[i+1]
    if 0<cp<len(self.cp) and self.cp[cp] and self.cp[cp][0]==8:refs.append((i,'ldc',repr(self.text(cp))))
  return name,desc,refs
jar=Path(r'D:\AI Studio 2026.1.1\lib\rapidminer-studio-core-12.1.1.jar')
targets={'com/rapidminer/MacroHandler.class':['getMacro','substitutePredefinedMacros','substituteMacros'], 'com/rapidminer/operator/Operator.class':['getParameterAsFile'], 'com/rapidminer/Process.class':['resolveFileName'], 'com/rapidminer/tools/expression/internal/function/process/MacroValue.class':['compute'], 'com/rapidminer/FileProcessLocation.class':['toString','getShortName']}
with zipfile.ZipFile(jar) as z:
 for n,methods in targets.items():
  c=ClassFile(z.read(n));print('\nCLASS',n)
  for method in c.methods:
   if method[0] in methods:print(c.refs(method))
