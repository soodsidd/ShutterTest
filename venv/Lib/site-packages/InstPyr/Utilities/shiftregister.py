import collections

class shiftregister:
    def __init__(self,size):
        self.size=size
        self.buffer = collections.deque(maxlen=size)
        #initialize buffer
        for i in range(size):
            self.buffer.append(0)

    def push(self,val):
        self.buffer.append(val)

    def pop(self):
        a=self.buffer.pop()
        self.buffer.insert(0,0)
        return a

    def showlast(self,number):
        #show last N entries
        return list(self.buffer)[self.size-number:self.size]

    def data(self):
        return list(self.buffer)

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, val):
        self._size = int(val)
        self.buffer = collections.deque(maxlen=int(val))
        for i in range(int(val)):
            self.buffer.append(0)

    def __str__(self):
        return str(list(self.buffer))



if __name__=="__main__":
    a=shiftregister(10)

    for i in range(10):
        a.push(i)
        print(a)

    for i in range(10):
        a.pop()
        print(a)