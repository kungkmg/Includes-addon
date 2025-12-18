import tkinter as tk
from tkinter import messagebox
import requests
import system

API_URL = "https://api-key.runaesike.online/verify"

def login_screen():
    window = tk.Tk()
    window.title("Login - Runaeshike Official")
    window.geometry("350x250")
    window.configure(bg="#121212")

    def check_key():
        key = entry_key.get().strip()
        if not key:
            messagebox.showwarning("Warning", "กรุณากรอก License Key")
            return
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.post(API_URL, json={"key": key}, headers=headers, timeout=10)
            try:
                data = response.json()
            except:
                messagebox.showerror("Server Error", f"Server ตอบกลับผิดพลาด: {response.status_code}\n{response.text[:100]}")
                return

            if data.get("success"):
                messagebox.showinfo("Success", f"ยินดีต้อนรับ!\n{data.get('message')}")
                window.destroy()
                system.run_main_system() 
            else:
                messagebox.showerror("Login Failed", data.get("message"))
                
        except requests.exceptions.ConnectionError:
            messagebox.showerror("Connection Error", "ไม่สามารถติดต่อ Server ได้\nตรวจสอบอินเทอร์เน็ต หรือ Server อาจจะล่ม")
        except Exception as e:
            messagebox.showerror("Error", f"เกิดข้อผิดพลาด: {str(e)}")
    tk.Label(window, text="LICENSE VERIFICATION", font=("Arial", 14, "bold"), bg="#121212", fg="#00e5ff").pack(pady=20)
    tk.Label(window, text="ใส่รหัสเพื่อปลดล็อกโปรแกรม:", bg="#121212", fg="white").pack()
    entry_key = tk.Entry(window, font=("Arial", 12), width=30, justify='center')
    entry_key.pack(pady=10)
    btn_login = tk.Button(window, text="ENTER SYSTEM", command=check_key, bg="#4CAF50", fg="white", font=("Arial", 10, "bold"), width=20, height=2)
    btn_login.pack(pady=20)
    tk.Label(window, text="© Runaeshike Official", bg="#121212", fg="#444", font=("Arial", 8)).pack(side="bottom", pady=5)

    window.mainloop()

if __name__ == "__main__":
    login_screen()
