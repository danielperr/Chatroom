from tkinter import *

root = Tk()

left_frame = Frame(root)
right_frame = Frame(root)

left_frame.pack(side=LEFT, expand=1, fill=BOTH)
Label(left_frame, text='Left Label', bg='blue').pack(expand=1, fill=BOTH)

right_frame.pack(side=RIGHT, fill=BOTH)
Label(right_frame, text='Right Label', bg='red').pack(expand=1, fill=Y)

root.mainloop()