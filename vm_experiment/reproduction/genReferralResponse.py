def foo():
        ATTACKERS_NUM = 50
        f = open("attackerNameServers.txt", "w")
        for j in range(ATTACKERS_NUM):
                for i in range(1500):
                        f.write("attack{1}     IN     NS   foo{0}attack{1}.delegation.com.\n".format(i, j))
        f.close()
foo()
