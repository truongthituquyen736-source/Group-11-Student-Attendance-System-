
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import database as db
from auth import hash_password, verify_password, validate_email, validate_required
from datetime import datetime

class BaseDashboard:
    def __init__(self, root, user):
        self.root = root
        self.user = user
        self.content_frame = None
        self.create_sidebar()
    
    def create_sidebar(self):
        sidebar = tk.Frame(self.root, bg="#1976D2", width=220)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        
        tk.Label(sidebar, text="HỆ THỐNG\nĐIỂM DANH", font=("Segoe UI", 14, "bold"), bg="#1976D2", fg="white").pack(pady=20)
        tk.Label(sidebar, text=f"Xin chào,\n{self.user['full_name']}", font=("Segoe UI", 10), bg="#1976D2", fg="white").pack(pady=10)
        
        menu_frame = tk.Frame(sidebar, bg="#1976D2")
        menu_frame.pack(pady=20, fill="both", expand=True)
        
        self.menu_items = self.get_menu_items()
        for key, text, color in self.menu_items:
            tk.Button(menu_frame, text=text, bg=color, fg="white", font=("Segoe UI", 10, "bold"),
                      command=lambda k=key: self.switch_view(k), height=2, relief="flat").pack(fill="x", pady=2, padx=10)
        
        tk.Button(sidebar, text="Đổi mật khẩu", bg="#0288D1", fg="white", font=("Segoe UI", 10),
                  command=self.change_password_dialog).pack(side="bottom", fill="x", pady=5, padx=10)

        tk.Button(sidebar, text="Đăng xuất", bg="#D32F2F", fg="white", font=("Segoe UI", 10),
                command=self.logout).pack(side="bottom", fill="x", pady=20, padx=10)
    
    def get_menu_items(self): return []
    
    def switch_view(self, view_key):
        if self.content_frame: self.content_frame.destroy()
        self.content_frame = tk.Frame(self.root, bg="white")
        self.content_frame.pack(side="right", fill="both", expand=True, padx=20, pady=20)
        
        view_method = getattr(self, f"render_{view_key}_view", None)
        if view_method: view_method()
        else: tk.Label(self.content_frame, text="Chức năng đang phát triển...", font=("Segoe UI", 14), bg="white").pack(pady=50)
    
    def create_scrolled_treeview(self, parent, columns):
        frame = tk.Frame(parent)
        frame.pack(fill="both", expand=True, pady=5)
        ysb = ttk.Scrollbar(frame, orient="vertical")
        ysb.pack(side="right", fill="y")
        xsb = ttk.Scrollbar(frame, orient="horizontal")
        xsb.pack(side="bottom", fill="x")
        tree = ttk.Treeview(frame, columns=columns, show="headings", 
                            yscrollcommand=ysb.set, xscrollcommand=xsb.set)
        ysb.config(command=tree.yview); xsb.config(command=tree.xview)
        tree.pack(side="left", fill="both", expand=True)
        for c in columns:
            tree.heading(c, text=c); tree.column(c, width=150, minwidth=100)
        return tree

    def change_password_dialog(self):
        win = tk.Toplevel(self.root); win.title("Đổi mật khẩu"); win.geometry("300x200")
        tk.Label(win, text="Mật khẩu cũ:").pack(pady=5)
        e_old = tk.Entry(win, show="*"); e_old.pack()
        tk.Label(win, text="Mật khẩu mới:").pack(pady=5)
        e_new = tk.Entry(win, show="*"); e_new.pack()
        
        def save():
            if not verify_password(e_old.get(), self.user["password_hash"]):
                messagebox.showerror("Lỗi", "Mật khẩu cũ không đúng"); return
            if len(e_new.get()) < 6:
                messagebox.showerror("Lỗi", "Mật khẩu mới phải >= 6 ký tự"); return
            
            if db.update_password(self.user["id"], hash_password(e_new.get())):
                messagebox.showinfo("Thành công", "Đổi mật khẩu thành công!"); win.destroy()
            else: messagebox.showerror("Lỗi", "Không thể cập nhật")
        
        tk.Button(win, text="Lưu", command=save, bg="#28a745", fg="white").pack(pady=15)

    def logout(self):
        if messagebox.askyesno("Đăng xuất", "Bạn có chắc muốn đăng xuất?"):
            self.root.destroy(); import main; main.main()

class AdminDashboard(BaseDashboard):
    def get_menu_items(self):
        return [("users", "Quản lý Người dùng", "#7B1FA2"), ("classes", "Quản lý Lớp học", "#7B1FA2"), ("report", "Báo cáo Tổng hợp", "#E64A19")]
    
    def render_users_view(self):
        tk.Label(self.content_frame, text="QUẢN LÝ NGƯỜI DÙNG", font=("Segoe UI", 16, "bold"), fg="#7B1FA2", bg="white").pack(pady=10)
        f = tk.LabelFrame(self.content_frame, text="Thêm mới", bg="white"); f.pack(fill="x")
        entries = {}
        for i, (lbl, key) in enumerate([("User:",0), ("Tên:",1), ("Email:",2)]):
            tk.Label(f, text=lbl, bg="white").grid(row=0, column=i*2)
            e = tk.Entry(f); e.grid(row=0, column=i*2+1); entries[key] = e
        tk.Label(f, text="Role:", bg="white").grid(row=0, column=6)
        cb = ttk.Combobox(f, values=["STUDENT", "TEACHER", "ADMIN"], width=8); cb.current(0); cb.grid(row=0, column=7)
        def add():
            s, m = db.create_user_full(entries[0].get(), hash_password("123456"), entries[1].get(), entries[2].get(), cb.get())
            if s: messagebox.showinfo("OK", "Đã tạo. Pass: 123456"); load()
            else: messagebox.showerror("Err", m)
        tk.Button(f, text="Thêm", command=add, bg="green", fg="white").grid(row=0, column=8, padx=10)
        
        cols = ("ID", "Tên ĐN", "Họ Tên", "Email", "Vai Trò")
        tree = self.create_scrolled_treeview(self.content_frame, cols)
        def load():
            for i in tree.get_children(): tree.delete(i)
            for u in db.get_all_users(): tree.insert("", "end", values=list(u.values()))
        load()
        def delete():
            if not tree.selection(): return
            if messagebox.askyesno("Xóa", "Chắc chắn xóa?"): db.delete_user(tree.item(tree.selection()[0], "values")[0]); load()
        tk.Button(self.content_frame, text="Xóa", command=delete, bg="red", fg="white").pack(pady=5)

    def render_classes_view(self):
        tk.Label(self.content_frame, text="QUẢN LÝ LỚP HỌC", font=("Segoe UI", 16, "bold"), fg="#7B1FA2", bg="white").pack(pady=10)
        f = tk.LabelFrame(self.content_frame, text="Thêm lớp", bg="white"); f.pack(fill="x")
        tk.Label(f, text="Mã Lớp:", bg="white").grid(row=0, column=0)
        e_code = tk.Entry(f); e_code.grid(row=0, column=1)
        tk.Label(f, text="Tên Lớp:", bg="white").grid(row=0, column=2)
        e_name = tk.Entry(f); e_name.grid(row=0, column=3)
        teachers = db.get_all_teachers(); t_vals = [f"{t['id']} - {t['full_name']}" for t in teachers]
        tk.Label(f, text="GVCN:", bg="white").grid(row=0, column=4)
        cb_t = ttk.Combobox(f, values=t_vals); cb_t.grid(row=0, column=5)
        def add():
            if not e_code.get() or not cb_t.get(): return
            tid = cb_t.get().split(" - ")[0]
            s, m = db.create_class(e_code.get(), e_name.get(), tid)
            if s: messagebox.showinfo("OK", "Thêm lớp thành công"); load()
            else: messagebox.showerror("Err", m)
        tk.Button(f, text="Thêm", command=add, bg="green", fg="white").grid(row=0, column=6, padx=10)
        
        tree = self.create_scrolled_treeview(self.content_frame, ("ID","Mã","Tên","GVCN"))
        def load():
            for i in tree.get_children(): tree.delete(i)
            for c in db.get_all_classes(): tree.insert("", "end", values=(c['id'], c['class_code'], c['class_name'], c['teacher_name']))
        load()
        def delete():
            if tree.selection(): db.delete_class(tree.item(tree.selection()[0], "values")[0]); load()
        tk.Button(self.content_frame, text="Xóa Lớp", command=delete, bg="red", fg="white").pack()

    def render_report_view(self):
        tk.Label(self.content_frame, text="BÁO CÁO TỔNG HỢP", font=("Segoe UI", 16, "bold"), bg="white", fg="#E64A19").pack(pady=10)
        
        today = datetime.now()
        start_of_month = today.replace(day=1).strftime("%Y-%m-%d")
        today_str = today.strftime("%Y-%m-%d")

        filter_frame = tk.Frame(self.content_frame, bg="white")
        filter_frame.pack(pady=5)
        tk.Label(filter_frame, text="Từ:", bg="white").pack(side="left")
        from_entry = tk.Entry(filter_frame, width=12); from_entry.insert(0, start_of_month); from_entry.pack(side="left", padx=5)
        tk.Label(filter_frame, text="Đến:", bg="white").pack(side="left")
        to_entry = tk.Entry(filter_frame, width=12); to_entry.insert(0, today_str); to_entry.pack(side="left", padx=5)

        cols = ("Lớp", "Tên Lớp", "Sĩ số", "Tổng buổi", "Đi học", "Vắng", "Muộn")
        tree = self.create_scrolled_treeview(self.content_frame, cols)

        def load_report():
            for i in tree.get_children(): tree.delete(i)
            data = db.get_school_attendance_report(from_entry.get(), to_entry.get())
            for r in data: tree.insert("", "end", values=list(r.values()))
            
        tk.Button(filter_frame, text="Xem", command=load_report, bg="#E64A19", fg="white").pack(side="left", padx=10)
        load_report()

class TeacherDashboard(BaseDashboard):
    def get_menu_items(self): return [("attendance", "Quản lý Điểm danh", "#388E3C")]
    def render_attendance_view(self):
        tk.Label(self.content_frame, text="QUẢN LÝ ĐIỂM DANH", font=("Segoe UI", 16, "bold"), bg="white", fg="#388E3C").pack(pady=10)
        teacher_info = db.get_teacher_by_user_id(self.user["id"])
        if not teacher_info: tk.Label(self.content_frame, text="Lỗi: Chưa cấp quyền Giáo viên", fg="red").pack(); return
        self.classes = db.get_classes_for_teacher(teacher_info["id"])
        if not self.classes: tk.Label(self.content_frame, text="Giáo viên chưa được phân công lớp nào.", bg="white").pack(); return

        frame_top = tk.Frame(self.content_frame, bg="white"); frame_top.pack(fill="x", padx=20)
        self.cb_class = ttk.Combobox(frame_top, values=[f"{c['class_code']} - {c['subject_name']}" for c in self.classes], width=40, state="readonly")
        self.cb_class.current(0); self.cb_class.pack(side="left", padx=5)
        tk.Button(frame_top, text="Tải Dữ Liệu", bg="#1976D2", fg="white", command=self.load_session).pack(side="left")
        
        self.frame_ss = tk.Frame(self.content_frame, bg="white", pady=10); self.frame_ss.pack(fill="x", padx=20)
        self.lbl_stt = tk.Label(self.frame_ss, text="...", font=("Segoe UI", 10, "bold"), bg="white"); self.lbl_stt.pack(side="left")
        self.btn_open = tk.Button(self.frame_ss, text="Mở Buổi Học Mới", bg="#28a745", fg="white", command=self.open_ss)
        self.btn_close = tk.Button(self.frame_ss, text="Đóng Buổi Học", bg="#d32f2f", fg="white", command=self.close_ss)

        self.tree = self.create_scrolled_treeview(self.content_frame, ("ID","Mã","Tên","TT","Ghi chú"))
        self.tree.column("ID", width=0, stretch=False)
        self.tree.bind("<Double-1>", self.edit_att)

    def get_cid(self): return self.classes[self.cb_class.current()]["class_subject_id"]
    def load_session(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        self.curr_ss = db.get_open_session_for_class_subject(self.get_cid())
        if self.curr_ss:
            self.lbl_stt.config(text=f"Đang mở: {self.curr_ss['session_code']} (Ngày: {self.curr_ss['date']})", fg="green")
            self.btn_open.pack_forget(); self.btn_close.pack(side="right")
            recs = {r['student_id']: r for r in db.get_attendance_records_for_session(self.curr_ss['id'])}
        else:
            self.lbl_stt.config(text="Chưa có buổi học nào mở.", fg="#555")
            self.btn_close.pack_forget(); self.btn_open.pack(side="right"); recs = {}
        for s in db.get_students_in_class(self.classes[self.cb_class.current()]['class_id']):
            r = recs.get(s['student_id'])
            self.tree.insert("", "end", values=(s['student_id'], s['student_code'], s['full_name'], r['status'] if r else "---", r['note'] if r else ""))
    def open_ss(self):
        try:
            now_str = datetime.now().strftime('%Y-%m-%d')
            code = f"{self.classes[self.cb_class.current()]['subject_code']}_{now_str}"
            db.create_attendance_session(self.get_cid(), code, now_str, self.user["id"]); self.load_session()
            messagebox.showinfo("Thành công", f"Đã mở buổi học ngày {now_str}")
        except Exception as e: messagebox.showerror("Lỗi", f"Lỗi (Có thể đã mở rồi): {str(e)}")
    def close_ss(self):
        if messagebox.askyesno("Đóng", "Kết thúc buổi học?"): db.close_attendance_session(self.curr_ss['id']); self.load_session()
    def edit_att(self, event):
        if not self.curr_ss: return
        item = self.tree.selection(); 
        if not item: return
        vals = self.tree.item(item, "values")
        win = tk.Toplevel(self.root); win.title(f"Điểm danh: {vals[2]}")
        v = tk.StringVar(value=vals[3] if vals[3] != "---" else "PRESENT")
        tk.Radiobutton(win, text="Có mặt", variable=v, value="PRESENT").pack()
        tk.Radiobutton(win, text="Vắng", variable=v, value="ABSENT").pack()
        def save():
            tid = db.get_teacher_by_user_id(self.user["id"])["id"]
            db.upsert_attendance_record(self.curr_ss['id'], vals[0], v.get(), "", tid); self.load_session(); win.destroy()
        tk.Button(win, text="Lưu", command=save).pack()

class StudentDashboard(BaseDashboard):
    def get_menu_items(self): return [("attend", "Tự Điểm Danh", "#28a745"), ("history", "Lịch Sử", "#F57C00")]
    def render_attend_view(self):
        tk.Label(self.content_frame, text="ĐIỂM DANH HÔM NAY", font=("Segoe UI", 16, "bold"), bg="white").pack(pady=10)
        s_info = db.get_student_by_user_id(self.user["id"])
        if not s_info: return
        sessions = db.get_open_sessions_for_student(s_info['id'])
        if not sessions: tk.Label(self.content_frame, text="Không có buổi học nào đang mở.", bg="white").pack(); return
        for s in sessions:
            f = tk.Frame(self.content_frame, bg="#f8f9fa", bd=1, relief="solid"); f.pack(fill="x", padx=20, pady=5)
            tk.Label(f, text=f"{s['subject_name']} | {s['date']}", bg="#f8f9fa", font=("Segoe UI", 10, "bold")).pack(anchor="w")
            def mark(sid=s['id'], stid=s_info['id']):
                try: db.student_mark_attendance(stid, sid, "PRESENT", ""); messagebox.showinfo("OK", "Điểm danh thành công!")
                except Exception as e: messagebox.showerror("Lỗi", str(e))
            tk.Button(f, text="CÓ MẶT NGAY", bg="#28a745", fg="white", command=mark).pack(pady=5)
    def render_history_view(self):
        tk.Label(self.content_frame, text="LỊCH SỬ ĐIỂM DANH", font=("Segoe UI", 16, "bold"), bg="white", fg="#F57C00").pack(pady=10)
        cols = ("Ngày", "Môn Học", "Trạng Thái", "Ghi Chú")
        tree = self.create_scrolled_treeview(self.content_frame, cols)
        s_info = db.get_student_by_user_id(self.user["id"])
        if s_info:
            for h in db.get_student_history(s_info['id']): tree.insert("", "end", values=(h['date'], h['subject_name'], h['status'], h['note']))

class LoginScreen:
    def __init__(self, root):
        self.root = root
        f = tk.Frame(root, bg="white"); f.pack(expand=True)
        tk.Label(f, text="ĐĂNG NHẬP HỆ THỐNG", font=("Segoe UI", 20, "bold"), bg="white", fg="#1976D2").pack(pady=20)
        tk.Label(f, text="Tên đăng nhập:", bg="white").pack(anchor="w")
        self.eu = tk.Entry(f, width=30); self.eu.pack(pady=5)
        tk.Label(f, text="Mật khẩu:", bg="white").pack(anchor="w")
        self.ep = tk.Entry(f, width=30, show="*"); self.ep.pack(pady=5)
        self.ep.bind("<Return>", lambda e: self.login())
        
        btn_frame = tk.Frame(f, bg="white"); btn_frame.pack(pady=25)
        tk.Button(btn_frame, text="Đăng nhập", command=self.login, bg="#1976D2", fg="white", width=15).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Quên mật khẩu?", command=self.forgot_pw, bg="#757575", fg="white").pack(side="left", padx=5)

    def login(self):
        u = db.get_user_by_username(self.eu.get())
        if u and verify_password(self.ep.get(), u['password_hash']):
            self.root.winfo_children()[0].destroy()
            if u['role'] == "ADMIN": AdminDashboard(self.root, u)
            elif u['role'] == "TEACHER": TeacherDashboard(self.root, u)
            else: StudentDashboard(self.root, u)
        else: messagebox.showerror("Lỗi", "Sai tên đăng nhập hoặc mật khẩu")

    def forgot_pw(self):
        email = simpledialog.askstring("Quên mật khẩu", "Nhập email của bạn:")
        if not email: return
        token = db.request_password_reset(email)
        if token:
            messagebox.showinfo("Email gửi đi (Giả lập)", f"Mã Reset Token của bạn là: {token}\n\n(Hãy nhớ mã này để nhập ở bước sau)")
            self.open_reset_dialog()
        else:
            messagebox.showerror("Lỗi", "Email này không tồn tại trong hệ thống!")

    def open_reset_dialog(self):
        win = tk.Toplevel(self.root); win.title("Đặt lại mật khẩu"); win.geometry("350x250")
        tk.Label(win, text="Nhập mã Reset Token:", font=("Segoe UI", 10)).pack(pady=5)
        e_token = tk.Entry(win, width=30); e_token.pack(pady=5)
        tk.Label(win, text="Nhập mật khẩu mới:", font=("Segoe UI", 10)).pack(pady=5)
        e_pass = tk.Entry(win, width=30, show="*"); e_pass.pack(pady=5)
        
        def submit():
            token = e_token.get().strip(); new_pass = e_pass.get().strip()
            if not token or not new_pass: messagebox.showerror("Lỗi", "Vui lòng nhập đủ thông tin"); return
            if db.reset_password_with_token(token, hash_password(new_pass)):
                messagebox.showinfo("Thành công", "Mật khẩu đã được thay đổi! Hãy đăng nhập lại."); win.destroy()
            else: messagebox.showerror("Lỗi", "Mã Token không đúng hoặc đã hết hạn!")
        tk.Button(win, text="Xác nhận", command=submit, bg="#28a745", fg="white").pack(pady=20)
