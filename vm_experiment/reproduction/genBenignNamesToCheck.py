import string
import random

def foo():
	f1 = open("benignNamesE2.txt", "w")
	for i in range(200):
            for j in range(100):
		reqBenign = 'b{}.benign.lan.'.format(j)    
		f1.write("{} A\n".format(reqBenign))
	f1.close()
foo()
