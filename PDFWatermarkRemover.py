import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import fitz
import cv2
import numpy as np
from fpdf import FPDF
from PIL import Image
import threading
import tempfile
import shutil
from reportlab.lib.pagesizes import A4

CONVERT_DPI = 200  # 默认设置转换图片的分辨率

class PDFWatermarkRemover:
    def __init__(self, root):
        self.root = root
        self.root.title("PDFWatermarkRemover")
        self.root.geometry("450x250")  # 设置窗口大小

        self.pdf_path = ""
        self.output_folder = ""
        
        self.dpi_var = tk.DoubleVar(value=CONVERT_DPI)
        self.state_str = tk.StringVar(value="准备中")
        self.progress_var = tk.DoubleVar(value=0)

        self.create_widgets()

    def create_widgets(self):
        # 添加 DPI 输入框
        ttk.Label(self.root, text="输入DPI值:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        dpi_entry = ttk.Entry(self.root, textvariable=self.dpi_var, width=30)
        dpi_entry.grid(row=0, column=1, padx=5, pady=5)

        # 添加 PDF 路径输入框
        ttk.Label(self.root, text="PDF文件路径:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.pdf_path_entry = ttk.Entry(self.root, width=30)
        self.pdf_path_entry.grid(row=1, column=1, padx=5, pady=5)

        # 添加选择PDF文件按钮
        ttk.Button(self.root, text="选择", command=self.choose_pdf).grid(row=1, column=2, padx=5, pady=5)

        # 添加输出文件夹路径输入框
        ttk.Label(self.root, text="输出文件夹路径:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.output_folder_entry = ttk.Entry(self.root, width=30)
        self.output_folder_entry.grid(row=2, column=1, padx=5, pady=5)

        # 添加选择输出文件夹按钮
        ttk.Button(self.root, text="保存", command=self.choose_output_folder).grid(row=2, column=2, padx=5, pady=5)

        # 添加状态标签
        ttk.Label(self.root, textvariable=self.state_str).grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)

        # 添加进度条
        self.progress_bar = ttk.Progressbar(self.root, length=310, mode="determinate", variable=self.progress_var)
        self.progress_bar.grid(row=3, column=1, columnspan=3, pady=10)

        # 添加去除水印并保存PDF按钮
        ttk.Button(self.root, text="去除水印并保存PDF", command=self.start_conversion_thread).grid(row=4, column=0, columnspan=3, padx=5, pady=10, sticky=tk.NSEW)

    def choose_pdf(self):
        self.pdf_path = filedialog.askopenfilename(title="选择PDF文件", filetypes=[("PDF files", "*.pdf")])
        if self.pdf_path:
            self.pdf_path_entry.delete(0, tk.END)
            self.pdf_path_entry.insert(0, self.pdf_path)
            messagebox.showinfo("信息", "PDF文件已选择。")

    def choose_output_folder(self):
        self.output_folder = filedialog.askdirectory(title="选择输出文件夹")
        if self.output_folder:
            self.output_folder_entry.delete(0, tk.END)
            self.output_folder_entry.insert(0, self.output_folder)
            messagebox.showinfo("信息", "输出文件夹已选择。")

    def start_conversion_thread(self):
        if not self.pdf_path or not self.output_folder:
            messagebox.showwarning("警告", "请先选择PDF文件和输出文件夹。")
            return

        self.disable_buttons()
        threading.Thread(target=self.convert_pdf).start()

    def convert_pdf(self):
        try:
            # 创建临时目录
            temp_dir = os.path.join(self.output_folder, "tmp")
            os.makedirs(temp_dir, exist_ok=True)

            images = self.pdf_to_images(temp_dir)
            self.images_to_pdf(images)
        except Exception as e:
            messagebox.showerror("错误", str(e))
        finally:
            self.enable_buttons()
            # 删除临时目录及其内容
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def pdf_to_images(self, temp_dir):
        images = []
        doc = fitz.open(self.pdf_path)
        dpi = self.dpi_var.get() / 72  # 使用用户输入的DPI设置

        self.state_str.set("PDF转图片")  # 更新状态栏
        for page_num in range(doc.page_count):
            page = doc[page_num]
            pix = page.get_pixmap(matrix=fitz.Matrix(dpi, dpi))
            image_path = os.path.join(temp_dir, f"page_{page_num + 1}.png")
            pix.save(image_path)
            images.append(image_path)
            self.remove_watermark(image_path)
            self.progress_var.set((page_num + 1) * 100 / doc.page_count)  # 更新进度条
            self.root.update_idletasks()
        return images

    def remove_watermark(self, image_path):
        img = cv2.imread(image_path)
        lower_hsv = np.array([160, 160, 160])
        upper_hsv = np.array([255, 255, 255])
        mask = cv2.inRange(img, lower_hsv, upper_hsv)
        img[mask == 255] = [255, 255, 255]
        cv2.imwrite(image_path, img)

    def images_to_pdf(self, image_paths):
        pdf_writer = FPDF(unit='pt', format='A4')
        self.state_str.set("合并图片生成PDF")  # 更新状态栏
        for index, image_path in enumerate(image_paths):
            with Image.open(image_path) as img:
                width, height = img.size
                dpi = self.dpi_var.get()
                ratio = min(A4[0] / width * dpi / 72, A4[1] / height * dpi / 72)
                img_resized = img.resize((int(width * ratio), int(height * ratio)))
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
                    img_resized.save(temp_file.name, format='PNG')
                pdf_writer.add_page()
                pdf_writer.image(temp_file.name, x=0, y=0, w=A4[0], h=A4[1])
                self.progress_var.set((index + 1) * 100 / len(image_paths))  # 更新进度条
                self.root.update_idletasks()
        pdf_writer.output(os.path.join(self.output_folder, 'output_file.pdf'))
        self.state_str.set("完成")  # 更新状态栏
        messagebox.showinfo("完成", f"水印已去除，PDF文件已保存至：{os.path.join(self.output_folder, 'output_file.pdf')}")

    def disable_buttons(self):
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.Button):
                widget.config(state=tk.DISABLED)

    def enable_buttons(self):
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.Button):
                widget.config(state=tk.NORMAL)

# 创建Tkinter窗口
if __name__ == "__main__":
    root = tk.Tk()
    app = PDFWatermarkRemover(root)
    root.mainloop()
