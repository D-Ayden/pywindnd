import typing


def _func(ls: typing.List[str]) -> None:
    for s in ls:
        print(s)


class OverError(Exception):
    pass


def drop_files(
    tk, func: typing.Callable = _func, force_unicode: bool = False, init: int = 260
) -> None:
    """拖拽文件，获取文件绝对路径
        drop file, get file's absolute path.

    Args:
        tk (_type_): tkinter 窗口或者对应的hwnd数字.
        func (typing.Callable, optional): callback func, Defaults to _func.
        force_unicode (bool, optional): Defaults to False.
        init (int, optional): The init value of the buffer.

    Raises:
        Exception: _description_

    """
    import ctypes
    import platform
    from ctypes.wintypes import DWORD

    hwnd = tk.winfo_id() if getattr(tk, "winfo_id", None) else tk

    if platform.architecture()[0] == "32bit":
        GetWindowLong = ctypes.windll.user32.GetWindowLongW
        SetWindowLong = ctypes.windll.user32.SetWindowLongW
        typ = DWORD

    if platform.architecture()[0] == "64bit":
        GetWindowLong = ctypes.windll.user32.GetWindowLongPtrA
        SetWindowLong = ctypes.windll.user32.SetWindowLongPtrA
        typ = ctypes.c_uint64

    prototype = ctypes.WINFUNCTYPE(typ, typ, typ, typ, typ)
    WM_DROP_FILES = 0x233
    GWL_WND_PROC = -4
    create_buffer = ctypes.create_unicode_buffer if force_unicode else ctypes.c_buffer
    func_DragQueryFile = (
        ctypes.windll.shell32.DragQueryFileW
        if force_unicode
        else ctypes.windll.shell32.DragQueryFile
    )

    def py_drop_func(hwnd, msg, wp, lp):
        global files
        if msg == WM_DROP_FILES:
            count = func_DragQueryFile(typ(wp), -1, None, None)
            file_buffer = create_buffer(init)
            files = []
            for i in range(count):
                func_DragQueryFile(typ(wp), i, file_buffer, ctypes.sizeof(file_buffer))
                drop_name = file_buffer.value
                files.append(drop_name)
            func(files)
            ctypes.windll.shell32.DragFinish(typ(wp))
        return ctypes.windll.user32.CallWindowProcW(
            *map(typ, (globals()[old], hwnd, msg, wp, lp))
        )

    # for limit hook number, protect computer.
    limit_num = 200
    for i in range(limit_num):
        if i + 1 == limit_num:
            # *TODO 引发一个特定的错误，而不是一般的错误
            raise OverError("Over hook limit number 200, for protect computer.")
        owp = f"old_wnd_proc_{i}"
        if owp not in globals():
            old, new = owp, f"new_wnd_proc_{i}"
            break

    globals()[old] = None
    globals()[new] = prototype(py_drop_func)

    ctypes.windll.shell32.DragAcceptFiles(hwnd, True)
    globals()[old] = GetWindowLong(hwnd, GWL_WND_PROC)
    SetWindowLong(hwnd, GWL_WND_PROC, globals()[new])


if __name__ == "__main__":

    def func(ls):
        def _local_lnk(link):
            """处理 link 指向的问题。"""
            import platform

            if platform.python_version().startswith("3") and type(link) is bytes:
                try:
                    _link = link.decode()
                except Exception:
                    _link = link.decode("gbk")
            else:
                _link = link
            try:
                import win32com.client

                shell = win32com.client.Dispatch("WScript.Shell")
                shortcut = shell.CreateShortCut(_link)
                return shortcut.Targetpath if shortcut.Targetpath.strip() else _link
            except Exception:
                return _link

        for i in ls:
            print("deal link:", _local_lnk(i))

    def test():
        """
        将 windows 桌面的图标拖拽到被挂钩的窗口内
        对加载到的图标路径进行对应处理的函数。
        """
        import tkinter

        tk = tkinter.Tk()
        drop_files(tk, func)
        tk.mainloop()

    test()
