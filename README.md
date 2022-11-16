# auto_comment
JD自动评价（评价晒单带图，追评，服务评价）

拉库命令 ql repo https://github.com/6dylan6/auto_comment.git "jd_" "" "jdspider"

如果运行报依赖错误，在运行评价依赖安装，没有问题不要运行

浏览器登录抓取CK（电脑端CK），添加变量PC_COOKIE，每次运行，最多评价10个订单

www的那个地址抓CK，登录后F12点到network，不要用命令document.cookie抓，会不完整，找带cookie的请求复制

感谢原库作者https://github.com/Dimlitter/jd_AutoComment  在其基础上进行修改优化，适配青龙面板，自动安装依赖

有问题欢迎提pr、issue

更新日志：
2022/11/6 新增多账号； 报错不停止运行；倒序评价，优先比较老的订单；
2022/11/16 修复有些订单匹配不到pid ；

![image](https://i.postimg.cc/NG6g4pHf/1.jpg)