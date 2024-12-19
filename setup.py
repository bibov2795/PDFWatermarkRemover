from cx_Freeze import setup, Executable

# 需要打包的 Python 文件
script = "PDFWatermarkRemover.py"

# 设置参数
build_exe_options = {
    "packages": [],  # 这里可以添加需要包含的包
    "excludes": [],  # 这里可以添加需要排除的包
}

# 设定应用程序信息
setup(
    name="PDFWatermarkRemoverApp",
    version="0.1",
    description="PDFWatermarkRemover application",
    options={"build_exe": build_exe_options},
    executables=[Executable(script, base="Win32GUI")],
)
