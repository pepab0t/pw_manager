#!/usr/bin/python3

import os
import random as ran
import sqlite3 as sql
import sys
import tkinter as tk

import pyperclip as ppc
from cryptography.fernet import Fernet

HEIGHT, WIDTH = 375, 500

DB_PATH: str = f"{os.path.dirname(sys.argv[0])}/pw_data.db"

conn = sql.connect(DB_PATH)
cur = conn.cursor()


root = tk.Tk()
root.geometry(f"{WIDTH}x{HEIGHT}+{int(root.winfo_screenwidth()/2-WIDTH/2)}+{int(root.winfo_screenheight()/2-HEIGHT/2)}")
root.title('Password Manager')
# root.iconbitmap('./pw.ico')
root.config(background='#66ccff')
root.resizable(False, False)

# mainframe = tk.Frame(root, bg='#66ccff')
# mainframe.place(relwidth=1,relheight=1)
class Account():

    def create_admin(self, name, pw):
        # name = self.app.entry_user.get()
        # pw = self.app.entry_pw.get()
        k = Fernet.generate_key()
        f = Fernet(k)
        pw = self.hash_admin(f.encrypt(pw.encode()).decode(), k.decode()) #pw = f.encrypt(pw.encode()).decode() + k.decode() # can be hashed other way
        self.create_table('admin')
        cur.execute('INSERT INTO admin (name, password) VALUES (?, ?)', (name, pw))
        conn.commit()
        self.get_adm_info()

    @staticmethod
    def hash_admin(pw, key):
        '''pw encypted decoded, key decoded '''
        position = ran.randint(2,len(pw)-2)
        prev = ran.randint(0,9)
        past = ran.randint(0,9)
        return str(prev) + str(past) + pw[:position] + Account.__make_letters(prev) + key + Account.__make_letters(past) + pw[position:] + str(position) + str(len(str(position)))

    @staticmethod
    def unhash_admin(long_string):
        digits = int(long_string[-1])
        position = int(long_string[-1-digits:-1])
        prev = int(long_string[0])
        past = int(long_string[1])
        long_string = long_string[2:-1-digits]
        pw = long_string[:position] + long_string[position+44+past+prev:]
        key = long_string[position+prev:position+prev+44]
        return pw, key

    @staticmethod
    def __make_letters(amount):
        letters = []
        for i in range(amount):
            if ran.choice([True, False]):
                letters.append(chr(ran.randint(65,90)))
            else:
                letters.append(chr(ran.randint(97,122)))
        return ''.join(letters)

    @staticmethod
    def create_table(kind):
        cur.execute(f'DROP TABLE IF EXISTS {kind}')
        if kind == 'data':
            cur.execute(f'''
            CREATE TABLE {kind} (
                service TEXT,
                email TEXT,
                username TEXT,
                password TEXT,
                info TEXT
                )''')
        elif kind == 'admin':
            cur.execute(
                f'''CREATE TABLE {kind} (
                    name TEXT,
                    password TEXT
                )'''
            )
    
    def encoding(self, text):
        return self.f.encrypt(text.encode()).decode()

    def decoding(self, text):
        return self.f.decrypt(text.encode()).decode()

    def get_adm_info(self):
        cur.execute('SELECT name, password FROM admin')
        fetch = cur.fetchone()
        print(fetch)
        self.admin_name = fetch[0]
        self.admin_password, self.key = self.unhash_admin(fetch[1])
        # print('pw: '+self.admin_password)
        # print(self.unhash_admin(fetch[1]))
        self._f = Fernet(self.key)
        
    @property
    def f(self):
        return self._f

    # def validate_pw(self, entered_pw):
    #     if self.decoding(self.admin_password) == entered_pw:
    #         return True
    #     else:
    #         return False
        
    def change_admin(self, new_name, new_pw):
        new_pw = self.hash_admin(self.encoding(new_pw), self.key)
        cur.execute("DELETE FROM admin WHERE rowid=1")
        cur.execute('INSERT INTO admin (name, password) VALUES (?, ?)', (new_name, new_pw))
        conn.commit()
        self.get_adm_info()

    # def admin_approve(self):
    #     while True:
    #         enter_pw = getpass(' Current admin password: ')
    #         if self.validate_pw(enter_pw):
    #             return True
    #         elif enter_pw.lower() == 'k':
    #             print(' Process terminated.\n')
    #             os.system('pause')
    #             return False

class AccountData(Account):
    itms = {
        'site': '',
        'email': '',
        'username': '',
        'password': '',
        'info': ''
    }

    def __init__(self):
        # Account.__init__(self)
        try: 
            cur.execute('SELECT service FROM data')
        except sql.OperationalError:
            self.create_table('data')

    @staticmethod
    def remove_password(label: int):
        cur.execute('DELETE FROM data WHERE rowid={0}'.format(label))
        conn.commit()

    @staticmethod
    def all_names():
        cur.execute('VACUUM;')
        cur.execute('SELECT service, rowid FROM data')
        fetch = cur.fetchall() #[x[0].capitalize() for x in cur.fetchall()]
        fetch = [(x.capitalize(), i) for x, i in fetch]
        return fetch

    def view_password(self, label: int):
        cur.execute('SELECT * FROM data WHERE rowid={0}'.format(label))
        fetch = list(cur.fetchone())
        fetch[3] = self.decoding(fetch[3]) # decrypt password
        return zip([x.capitalize() for x in self.itms.keys()], fetch)

    def add_password(self, entries):
        itms = AccountData.itms
        for k, v in zip(itms.keys(), entries):
            if k == 'password':
                itms[k] = self.encoding(v)
            else:
                itms[k] = v
        cur.execute("INSERT INTO data (service, email, username, password, info) VALUES (?, ?, ?, ?, ?)", tuple(itms.values()))
        conn.commit()

    # def clean_all(self):
    #     pass

class App():
	color='#00aaff'
	font_title = ('Consolas', 20)
	font_text = ('Consolas', 12)

	def __init__(self, master):
		self.master = master
		self.master.bind('<Escape>', lambda event: self.master.quit())
		self.a = AccountData()
		self.load_name_data()
		self.colnames = [k.capitalize() for k, v in self.a.itms.items()]
		self.pw = ''

		try:
			self.a.get_adm_info()
		except (sql.OperationalError, TypeError):
			self.create_user_screen('quit', 'create')
		else:
			self.login()

	@staticmethod
	def place_frame(frame):
		frame.place(relx=0.5, rely=0.5, anchor='center')

	def destroy(self):
		for widget in self.master.winfo_children():
			widget.destroy()

	def init_button_quit(self, frame):
		self.button_quit = tk.Button(frame, text='Quit', command=root.quit)

	def create_user_screen(self, option, act='create'): # option is back/quit,  act is 'create'/'change'
		title: str = ''
		
		if act == 'create':
			title ='Create'
		elif act == 'change':
			title = 'Change'

		self.frame = tk.LabelFrame(self.master, bg=self.color, padx=10, pady=10)
		self.place_frame(self.frame)

		self.label_title = tk.Label(self.frame, text=f'{title} user', font=self.font_title, bg=self.color)
		self.label_title.grid(row=0, column=0, columnspan=2, pady=5)

		self.label_user = tk.Label(self.frame, text='Username: ', font=self.font_text, anchor='e', bg=self.color)
		self.label_user.grid(row=1, column=0, sticky='we', padx=1)

		self.label_pw = tk.Label(self.frame, text='Password: ', font=self.font_text, anchor='e', bg=self.color)
		self.label_pw.grid(row=2, column=0, sticky='we', padx=1)

		self.label_pw_confirm = tk.Label(self.frame, text='Password confirm: ', font=self.font_text, anchor='e', bg=self.color)
		self.label_pw_confirm.grid(row=3, column=0, sticky='we', padx=1)

		self.entry_user = tk.Entry(self.frame)
		self.entry_user.grid(row=1, column=1, padx=1)

		self.entry_pw = tk.Entry(self.frame, show="•")
		self.entry_pw.grid(row=2, column=1, padx=1)

		self.entry_pw_confirm = tk.Entry(self.frame, show="•")
		self.entry_pw_confirm.grid(row=3, column=1, padx=1)

		self.label_mess = tk.Label(self.frame, anchor='center', width=42, font=self.font_text, bg=self.color, fg='black')
		self.label_mess.grid(row=4, column=0, columnspan=2)

		self.button_quit = tk.Button(self.frame, width=10)
		self.button_quit.grid(row=5, column=0, sticky='we', padx=1)
		if option.lower() == 'quit':
			self.button_quit.config(text='Quit', command=root.quit)
		elif option.lower() == 'back':
			self.button_quit.config(text='Back', command=self.back_menu)

		self.button_signup = tk.Button(self.frame, text= 'Sign Up')
		self.button_signup.grid(row=5, column=1, sticky='we', padx=1)

		if act == 'create':
			self.button_signup.config(command=lambda: self.signup(option='create'))
			self.master.bind('<Return>', lambda event: self.signup(option='create'))
		elif act == 'change':
			self.button_signup.config(command=lambda: self.signup(option='change'))
			self.master.bind('<Return>', lambda event: self.signup(option='change'))

	def signup(self, event=None, option='create'): #option is change/create
		name = self.entry_user.get()
		pw = self.entry_pw.get()
		if len(name) < 1:
			self.label_mess.config(text='User must have name.')
		else:
			if len(self.entry_pw.get()) < 4:
				self.label_mess.config(text="Password must have at least 4 characters.")
			else:
				if pw == self.entry_pw_confirm.get():
					self.destroy()
					if option == 'change':
						self.a.change_admin(name, pw)
					elif option == 'create':
						self.a.create_admin(name, pw)
					self.master.unbind("<Return>")
					self.menu()
				else:
					self.label_mess.config(text="Passwords don't match.")

	def login(self):
		self.frame = tk.LabelFrame(self.master, bg=self.color, padx=20, pady=20)
		self.place_frame(self.frame)

		self.label_title = tk.Label(self.frame, text='Login', font=self.font_title, bg=self.color)
		self.label_title.grid(row=0, column=0, columnspan=2, pady=5)#place(relx=0.5, rely=0.1, anchor='n')

		self.label_user = tk.Label(self.frame, font=self.font_text, text='Username: ', anchor='e', bg=self.color)
		self.label_user.grid(row=1, column=0, sticky='we', padx=1)#place(relx=0.35, rely=0.35, anchor='ne')

		self.entry_user=tk.Entry(self.frame)
		self.entry_user.grid(row=1, column=1, sticky='we', padx=1)

		self.label_pw = tk.Label(self.frame, text='Password: ', font=self.font_text, anchor='e', bg=self.color)
		self.label_pw.grid(row=2, column=0, sticky='we', padx=1)#place(relx=0.35, rely=0.45, anchor='ne')

		self.entry_pw = tk.Entry(self.frame, show="•")
		self.entry_pw.grid(row=2, column=1, sticky='we', padx=1)

		self.label_mess = tk.Label(self.frame, width=30, anchor='center', font=self.font_text, bg=self.color, fg='black')
		self.label_mess.grid(row=3, column=0, columnspan=2)

		self.button_signin = tk.Button(self.frame, text='Sign in', command=self.signin)
		self.button_signin.grid(row=4, column=1, padx=1, sticky='we')

		self.init_button_quit(self.frame)
		self.button_quit.grid(row=4, column=0, padx=1, sticky='we')
		# self.master.bind('<Key>', lambda event: self.signin(event))
		self.master.bind('<Return>', lambda event: self.signin())

	def signin(self):
		if self.entry_user.get() == self.a.admin_name and self.entry_pw.get() == self.a.decoding(self.a.admin_password):
			self.destroy()
			self.master.unbind("<Return>")
			self.menu()
		else:
			# print(self.a.admin_name, self.a.decoding(self.a.admin_password), self.a.key, self.entry_pw.get())
			self.entry_pw.delete(0,'end')
			self.label_mess['text'] = 'Invalid username or password.'

	# self.mess_lab.configure(text = 'You pressed: ' + event.keysym)

	def menu(self):
		py=5
		self.master.unbind('<BackSpace>')

		self.frame = tk.LabelFrame(self.master, bg=self.color, pady=20, padx=20)
		self.place_frame(self.frame)

		self.label_title = tk.Label(self.frame, text='Main menu', font=self.font_title, bg=self.color)
		self.label_title.grid(row=0, column=0, columnspan=2, sticky='we')

		self.button_data = tk.Button(self.frame, text='Data', width=20, command=self.display_data)
		self.button_data.grid(row=1, column=0, columnspan=2, pady=py, padx=5)

		self.button_changeadmin = tk.Button(self.frame, text='Change login', width=20, command=self.change_user)
		self.button_changeadmin.grid(row=2, column=0, columnspan=2, pady=py, padx=5)

		self.init_button_quit(self.frame)
		self.button_quit.grid(row=3, column=0, pady=py, padx=5, sticky='we')

		self.button_logout = tk.Button(self.frame, text='Logout', command=self.logout)
		self.button_logout.grid(row=3, column=1, pady=py, padx=5, sticky='we')

	def logout(self):
		self.destroy()
		self.login()

	def change_user(self):
		self.top = tk.Toplevel(bg=self.color)
		self.top.geometry(f'300x150+{int(self.master.winfo_screenwidth()/2-150)}+{int(self.master.winfo_screenheight()/2-75)}')
		self.top.title('Approve')
		self.top.grab_set()

		self.top_frame = tk.Frame(self.top, bg=self.color, borderwidth=1)
		self.top_frame.place(relx=0.5, rely=0.5, anchor='center')

		px = 5
		w = 14
		self.label_title = tk.Label(self.top_frame, text='Approve admin password', font=self.font_text, bg=self.color)
		self.label_title.grid(row=0, column=0, columnspan=2, pady=5)

		self.label_pw = tk.Label(self.top_frame, text='Password:', font=self.font_text, width=w, bg=self.color)
		self.label_pw.grid(row=1, column=0, padx=px)

		self.label_pw_confirm = tk.Label(self.top_frame, text='Confirm:', font=self.font_text, width=w, bg=self.color)
		self.label_pw_confirm.grid(row=2, column=0, padx=px)

		self.entry_pw = tk.Entry(self.top_frame, show="•", width=w)
		self.entry_pw.grid(row=1, column=1, padx=px)

		self.entry_pw_confirm = tk.Entry(self.top_frame, show="•", width=w)
		self.entry_pw_confirm.grid(row=2, column=1, padx=px)

		self.label_mess = tk.Label(self.top_frame, anchor='center', font=self.font_text, fg='black', bg=self.color)
		self.label_mess.grid(row=3, column=0, columnspan=2, sticky='we')

		self.button_quit = tk.Button(self.top_frame, text='Close', width=w-2, command=self.back_menu)
		self.button_quit.grid(row=4, column=0)

		self.button_continue = tk.Button(self.top_frame, text= 'Continue', width=w-2, command=self.cont)
		self.button_continue.grid(row=4, column=1)

		self.top.bind('<Return>', lambda event: self.cont())

	def cont(self):
		if self.entry_pw.get() == self.a.decoding(self.a.admin_password) and self.entry_pw.get() == self.entry_pw_confirm.get():
			# self.top.unbind('<Return>')
			self.destroy()
			self.create_user_screen('back', 'change')
		else:
			self.label_mess.config(text='Wrong passwords.')

	def load_name_data(self):
		self.data = self.a.all_names()
		self.data.sort()

	def display_data(self):
		w = 8
		py = 0

		self.destroy()

		self.frame = tk.LabelFrame(self.master, bg=self.color, padx=20, pady=20)
		self.place_frame(self.frame)

		self.label_title = tk.Label(self.frame, bg=self.color, font=self.font_title, text='Your data')
		self.label_title.grid(row=0, column=0, columnspan=2)

		self.listbox_data = tk.Listbox(self.frame, height=12)
		self.listbox_data.grid(row=1, column=0, rowspan=20, padx=5, pady=py)

		for item in (x[0] for x in self.data):
			self.listbox_data.insert('end', item)

		self.button_select = tk.Button(self.frame, text='Select', width=w, command=lambda: self.select('view') if bool(self.data) else None)
		self.button_select.grid(row=1, column=1, pady=py)

		self.button_add = tk.Button(self.frame, text='Add', width=w, command=self.add)
		self.button_add.grid(row=2, column=1, pady=py)

		self.button_remove = tk.Button(self.frame, text='Remove', width=w, command=lambda: self.select('remove') if bool(self.data) else None)
		self.button_remove.grid(row=3, column=1, pady=py)

		self.button_back = tk.Button(self.frame, text='Back', width=w, command=self.back_menu)
		self.button_back.grid(row=18, column=1, pady=py)

		self.master.bind('<BackSpace>', lambda event: self.back_menu())

	def select(self, opt):	# opt is view/remove
		if len(list(map(int, self.listbox_data.curselection()))) == 0:
			return
		self.my_item = [x for x in self.data if x[0] == self.listbox_data.get('anchor')][0]
		self.my_rowid = self.my_item[1]
		# print(self.my_item)
		# print(list(self.a.view_password(self.my_rowid)))

		if opt == 'view':
			self.view()
		elif opt == 'remove':
			self.remove()

	def back_menu(self):
		self.destroy()
		self.menu()

	def view(self):
		self.destroy()

		my_data = list(self.a.view_password(self.my_rowid))

		max_w = max([len(x) if len(x) > len(y) else len(y) for x, y in my_data])
		self.frame = tk.LabelFrame(self.master, bg=self.color, padx=20, pady=20)
		self.place_frame(self.frame)

		self.label_title = tk.Label(self.frame, text='Overview', font=self.font_title, bg=self.color)
		self.label_title.grid(row=0, column=0, columnspan=2, sticky='we')

		i=1
		for k, v in my_data:
			my_label1 = tk.Label(self.frame, text=f"{k}:", font=self.font_text, anchor='e', width=max_w, bg=self.color)
			my_label1.grid(row=i, column=0, padx=2, sticky='e')
			if k == 'Password':
				self.pw = v
				self.label_password = tk.Label(self.frame, text=f"{v}", anchor='w', font=self.font_text, width=max_w, bg=self.color)
				self.label_password.config(text='••••••')
				self.label_password.grid(row=i, column=1, padx=2, sticky='w')
			else:
				my_label2 = tk.Label(self.frame, text=f"{v}", anchor='w', width=max_w, font=self.font_text, bg=self.color)
				my_label2.grid(row=i, column=1, padx=2, sticky='w')
			i += 1

		self.label_status = tk.Label(self.frame, width=22, font=self.font_text, bg=self.color)
		self.label_status.grid(row=i, column=0, columnspan=2, sticky='we')

		self.button_show = tk.Button(self.frame, text='Show', width=10, command=self.show)
		self.button_show.grid(row=i+1, column=1, padx=2, pady=2, sticky='w')

		self.button_copy = tk.Button(self.frame, text='Copy', width=10, command=self.copy)
		self.button_copy.grid(row=i+1, column=0, padx=2, pady=2, sticky='e')

		self.button_back = tk.Button(self.frame, text='Back', width=22, command=self.back_data)
		self.button_back.grid(row=i+2, column=0, pady=2, columnspan=2)

		self.master.bind('<BackSpace>', lambda event: self.back_data())

	def show(self):
		if self.label_password['text'] == '••••••':
			self.label_password.config(text=self.pw)
			self.button_show.config(text='Hide')
		else:
			self.label_password.config(text='••••••')
			self.button_show.config(text='Show')

	def copy(self):
		ppc.copy(self.pw)
		self.label_status.config(text='Coppied to clipboard!')

	def add(self):
		self.top = tk.Toplevel(bg=self.color)
		self.top.title('Add data')
		self.top.geometry(f'250x250+{int(self.master.winfo_screenwidth()/2-125)}+{int(self.master.winfo_screenheight()/2-125)}')
		self.top.grab_set()

		self.top_frame = tk.Frame(self.top, bg=self.color)
		self.top_frame.place(relx=0.5, rely=0.5, anchor='center')

		self.label_title = tk.Label(self.top_frame, text='Add new item', font=self.font_text, bg=self.color)
		self.label_title.grid(row=0, column=0, columnspan=2)

		i = 1
		self.entries=[]
		for key in self.colnames:
			tk.Label(self.top_frame, text=f"{key}:", font=self.font_text, bg=self.color).grid(row=i, column=0)
			e = tk.Entry(self.top_frame)
			e.grid(row=i, column=1)
			self.entries.append(e)
			i += 1

		self.label_mess = tk.Label(self.top_frame, font=self.font_text, width=20, bg=self.color)
		self.label_mess.grid(row=i, column=0, columnspan=2)

		self.button_addpw = tk.Button(self.top_frame, text='Add', width=10, command=self.add_item)
		self.button_addpw.grid(row=i+1, column=0, columnspan=2, pady=5)

		self.button_close = tk.Button(self.top_frame, text='Close', width=10, command=self.top.destroy)
		self.button_close.grid(row=i+2, column=0, columnspan=2)

		self.top.bind('<Return>', lambda event: self.add_item())

	def add_item(self):
		itms_to_database = []

		if len(self.entries[0].get()) == 0 or len(self.entries[3].get()) == 0:
			self.label_mess.config(text='Incorrect input.')
		else:
			for entry in self.entries:
				itms_to_database.append(entry.get())

			self.a.add_password(itms_to_database)
			self.load_name_data()
			self.back_data()

	def remove(self):
		self.a.remove_password(self.my_rowid)
		self.listbox_data.delete('anchor')
		self.load_name_data()

	def back_data(self):
		self.destroy()
		self.display_data()
		self.pw=''

def main():
	app = App(root)
	tk.mainloop()

if __name__ == '__main__':
	main()
