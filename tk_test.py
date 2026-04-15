import tkinter as tk
root = tk.Tk()
root.title("Tkinter Test")
root.geometry("200x100")
label = tk.Label(root, text="If you see this, Tkinter works!")
label.pack()
root.after(3000, lambda: root.destroy())
root.mainloop()
print("Tkinter works!")
