import tkinter as tk
root = tk.Tk()
root.configure(bg="#1e1e2e")
root.title("Tkinter Color Test")
label = tk.Label(root, text="Testing background colors", bg="#1e1e2e", fg="#cdd6f4")
label.pack(padx=20, pady=20)
root.after(2000, lambda: root.destroy())
root.mainloop()
print("Tkinter color test works!")
