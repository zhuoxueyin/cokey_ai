# -*- coding: utf-8 -*-
"""双击停止 AIGC Platform — 不弹黑色命令窗口，以消息框显示结果。"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.argv = [sys.argv[0], "stop"]
exec(open(os.path.join(HERE, "_silent_helper.pyw"), encoding="utf-8").read())
