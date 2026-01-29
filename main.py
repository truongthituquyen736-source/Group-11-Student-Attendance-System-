import tkinter as tk
from gui import LoginScreen
import database

def main():
    # Khởi tạo DB
    database.init_db()
    
    # Tạo cửa sổ chính
    root = tk.Tk()
    root.title("Hệ Thống Điểm Danh Sinh Viên - Nhóm 11")
    root.geometry("1100x700")
    root.minsize(1000, 600)
    root.configure(bg="#f5f5f5")
    
    # Icon (nếu có)
    # root.iconbitmap("icon.ico")
    
    # Mở màn hình đăng nhập
    LoginScreen(root)
    
    # Chạy ứng dụng
    root.mainloop()

if __name__ == "__main__":
    main()
