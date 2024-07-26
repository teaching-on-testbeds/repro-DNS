import string
import random

def foo():
  f1 = open("attackerNamesE2.txt", "w")
  for j in range(200):
    for i in range(100):
      reqAttack = 'attack{}.referral.lan.'.format(i)
      f1.write("{} A\n".format(reqAttack))
  f1.close()
foo()
