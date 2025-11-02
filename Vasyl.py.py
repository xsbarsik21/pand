import base64
from customtkinter import *
import time
from PIL import Image
import io
from socket import socket, AF_INET, SOCK_STREAM
import threading
import os

HOST = '7.tcp.eu.ngrok.io'
PORT = 15391


class MainWindow(CTk):
    MENU_MAX_WIDTH = 200
    ANIM_DURATION_MS = 260
    PADDING = 5

    def __init__(self):
        super().__init__()
        self.geometry('600x500')
        self.title("Онлайн - чат Василь")

        # Коробка для меню. Початкова ширина = 0 (схована)
        self.frame = CTkFrame(self, width=0, height=self.winfo_height(), fg_color="#ffff00")
        self.frame.pack_propagate(False)  # щоб віджети не змінювали розмір frame
        self.frame.place(x=0, y=0)

        # Кнопка, що відкриває/закриває меню
        self.btn = CTkButton(self, text='➡️', command=self.toggle_menu, width=30, height=30)
        self.btn.place(x=0, y=0)

        # Напис
        self.label = CTkLabel(self.frame, text='Введи нік', text_color="green", font=("Sitka Banner", 20, "bold"))
        self.label.pack(pady=20)
        self.entry = CTkEntry(self.frame)
        self.entry.pack()

        # Поле чату і введення
        self.chat_field = CTkScrollableFrame(self)
        self.chat_field.place(x=0, y=30)

        self.message_entry = CTkEntry(self, placeholder_text='Тут напиши своє повідомлення ...')
        self.message_entry.place(x=0, y=250)

        self.send_button = CTkButton(self, text='➡️️', width=40, height=30, command=self.send_message,
                                     font=("Sitka Banner", 22, "bold"))
        self.send_button.place(x=200, y=250)

        self.label_theme = CTkOptionMenu(self.frame, values=['Світла', 'Темна'], command=self.change_theme)
        self.label_theme.pack(side='bottom', pady=20)
        self.theme = None  # змінна для зберігання поточної теми

        self.open_img_button = CTkButton(self, text="📁", width=40, height=30, command=self.open_image,
                                         font=("Sitka Banner", 20, "bold"))
        self.open_img_button.place(x=0, y=0)

        self.is_menu_open = False
        self.anim_job = None

        # Запускаємо адаптивний інтерфейс
        self.after(10, self.adaptive_ui)

        self.save_button = CTkButton(self.frame, text="Збережи", command=self.save_name,
                                     font=("Sitka Banner", 22, "bold"))
        self.save_button.pack(pady=20)

        # Поточний нік користувача (за замовчуванням)
        self.username = ""

        try:
            # Намагаємось підключитись до сервера
            self.sock = socket(AF_INET, SOCK_STREAM)
            self.sock.connect((HOST, PORT))
            hello = f"TEXT@{self.username}@[SYSTEM] {self.username} приєднався(лась) до чату!\n"
            self.sock.send(hello.encode('utf-8'))
            # Запускаємо нитку, що читає повідомлення від сервера
            threading.Thread(target=self.receive_message, daemon=True).start()
        except Exception as e:
            # Якщо не вдалось підключитись, показуємо повідомлення в чаті
            self.add_message(f"Не вдалося підключитися до сервера: {e}")

    @staticmethod
    def change_theme(value):
        if value == 'Темна':
            set_appearance_mode('dark')  # встановлюємо темну тему
        else:
            set_appearance_mode('light')  # встановлюємо світлу тему

    def toggle_menu(self):
        # Визначаємо кінцеву ширину: або повністю відкрити, або закрити
        target = self.MENU_MAX_WIDTH if not self.is_menu_open else 0
        # Якщо вже є запланована анімація, скасовуємо її
        if self.anim_job is not None:
            self.after_cancel(self.anim_job)
            self.anim_job = None
        # Беремо стартову ширину і час старту
        self.update_idletasks()
        start_width = self.frame.winfo_width()
        start_time = time.time()
        duration = self.ANIM_DURATION_MS / 1000.0

        def ease(t):  # Простенька easing-функція, потрібна для плавності анімації
            if t < 0.5:  # t від 0 до 1
                return 2 * t * t
            return -1 + (4 - 2 * t) * t

        def step():  # Одна функція-крок, яка оновлює ширину
            nonlocal start_width, target, start_time, duration
            now = time.time()
            elapsed = now - start_time
            t = min(1.0, max(0.0, elapsed / duration))
            eased = ease(t)
            new_w = int(start_width + (target - start_width) * eased)
            # Ставимо ширину меню
            self.frame.configure(width=new_w)
            # Кнопка має залишатися на краю меню
            btn_w = self.btn.winfo_reqwidth()
            self.btn.place(x=max(0, new_w - btn_w), y=0)
            if new_w > 24:  # Змінюємо стрілку для наочності
                self.btn.configure(text='⬅️')
            else:
                self.btn.configure(text='➡️')
            if t < 1.0:
                self.anim_job = self.after(16, step)  # повторюємо приблизно через 16 ms (~60 кадрів)
            else:
                self.anim_job = None
                self.frame.configure(width=target)
                if target == 0:
                    self.btn.place(x=0, y=0)
                    self.btn.configure(text='➡️')
                else:
                    self.btn.place(x=target - self.btn.winfo_reqwidth(), y=0)
                    self.btn.configure(text='⬅️')

        # Пуск першого кроку
        step()
        # Міняємо логічний стан
        self.is_menu_open = not self.is_menu_open

    def adaptive_ui(self):
        # Підганяємо інтерфейс до розміру вікна
        self.update_idletasks()
        menu_width = self.frame.winfo_width()
        win_width = self.winfo_width()
        win_height = self.winfo_height()
        send_btn_width = self.send_button.winfo_reqwidth()
        send_btn_height = self.send_button.winfo_reqheight()
        open_img_width = self.open_img_button.winfo_reqwidth()
        open_img_height = self.open_img_button.winfo_reqheight()
        input_height = self.message_entry.winfo_reqheight()

        # Оновлюємо висоту меню, щоб відповідала висоті вікна
        self.frame.configure(height=win_height)

        # Поле чату займає простір справа від меню і зверху
        self.chat_field.configure(width=max(10, win_width - menu_width), height=max(10, win_height - input_height - 40))
        self.chat_field.place(x=menu_width, y=30)

        # Поле вводу повідомлення підлаштовується по ширині
        self.message_entry.configure(
            width=max(10, win_width - menu_width - send_btn_width - open_img_width - self.PADDING * 3))
        self.message_entry.place(x=menu_width + self.PADDING, y=win_height - input_height - self.PADDING)

        # Кнопка відкриття зображення
        self.open_img_button.place(x=win_width - send_btn_width - open_img_width - self.PADDING * 2,
                                   y=win_height - open_img_height - self.PADDING)

        # Кнопка відправлення
        self.send_button.place(x=win_width - send_btn_width - self.PADDING,
                               y=win_height - send_btn_height - self.PADDING)

        # Викликаємо цю функцію через 50 мс знову — так інтерфейс постійно підганяється
        self.after(50, self.adaptive_ui)

    def add_message(self, message, img=None):
        message_frame = CTkFrame(self.chat_field, fg_color="#00b33c")
        message_frame.pack(padx=10, pady=5, anchor='w')

        wrap_len_size = self.winfo_width() - self.frame.winfo_width() - 40

        if not img:
            CTkLabel(message_frame, text=message, text_color="black",
                     wraplength=wrap_len_size, justify='left').pack(padx=10, pady=5)
        else:
            CTkLabel(message_frame, text=message, wraplength=wrap_len_size, fg_color="transparent",
                    image=img, compound='top', justify='left').pack(padx=10, pady=5)

    def send_message(self):
        # Беремо текст з поля вводу і відправляємо на сервер
        message = self.message_entry.get()
        if message:
            # Спершу додаємо своє повідомлення в локальний чат
            self.add_message(f"{self.username}: {message}")
            data = f"TEXT@{self.username}@{message}\n"
            try:
                # Відправляємо у сокет
                self.sock.sendall(data.encode())
            except:
                # Якщо щось піде не так — нічого не робимо (можна додати повідомлення про помилку)
                pass
        # Очищаємо поле вводу
        self.message_entry.delete(0, END)

    def receive_message(self):
        # Ця функція працює у фоні і читає дані від сервера
        buffer = "Василь"
        while True:
            try:
                chunk = self.sock.recv(4096)
                if not chunk:
                    # З'єднання закрите
                    break
                # Декодуємо частину (ігноруємо помилки декодування)
                buffer += chunk.decode('utf-8', errors='ignore')

                # Обробляємо рядки, які приходять із сервера (розділені \n)
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    self.handle_line(line.strip())
            except:
                # Якщо сталася помилка при читанні — виходимо з циклу
                break
        # Закриваємо сокет коли виходимо
        self.sock.close()

    def handle_line(self, line):
        # Обробляємо одну стрічку протоколу від сервера
        if not line:
            return
        # Розбиваємо по символу @ — за цим форматом приходять події
        parts = line.split("@", 3)
        msg_type = parts[0]

        if msg_type == "TEXT":
            # Повідомлення текстового типу: TEXT@автор@текст
            if len(parts) >= 3:
                author = parts[1]
                message = parts[2]
                self.add_message(f"{author}: {message}")
        elif msg_type == "IMAGE":
            # Повідомлення з зображенням: IMAGE@автор@ім'я_файлу@...
            if len(parts) >= 4:
                author = parts[1]
                filename = parts[2]
                b64_img = parts[3]
                try:
                    # Декодуємо base64 у байти, створюємо PIL-зображення, потім CTkImage
                    img_data = base64.b64decode(b64_img)
                    pil_img = Image.open(io.BytesIO(img_data))
                    ctk_img = CTkImage(pil_img, size=(300, 300))
                    self.add_message(f"{author} надіслав(ла) зображення: {filename}", img=ctk_img)
                except Exception as e:
                    # Якщо щось пішло не так, показуємо помилку в інтерфейсі
                    self.add_message(f"Помилка відображення зображення: {e}")
        else:
            # Якщо формат невідомий — просто показуємо рядок як є
            self.add_message(line)

    def save_name(self):
        new_name = self.entry.get().strip()
        if new_name:
            self.username = new_name
            self.add_message(f"Your new Nickname: {self.username}")
        self.entry.delete(0, END)

    def open_image(self):
        file_name = filedialog.askopenfilename()

        if not file_name:
            return
        try:
            with open(file_name, "rb") as f:
                raw = f.read()
                b64_data = base64.b64encode(raw).decode()
                short_name = os.path.basename(file_name)
                data = f"IMAGE@{self.username}@{short_name}@{b64_data}\n"
                self.sock.sendall(data.encode())
                self.add_message("", CTkImage(light_image=Image.open(file_name), size=(100, 100)))
        except Exception as e:
            self.add_message(f"Load Error: {e}")


# Створюємо та запускаємо головне вікно програми
win = MainWindow()
win.mainloop()
