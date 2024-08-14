// 获取模态窗口
var modal = document.getElementById("uploadAvatarModal");

// 获取按钮
var btn = document.getElementById("uploadAvatarBtn");

// 获取 <span> 元素，点击关闭模态窗口
var span = document.getElementsByClassName("close")[0];

// 点击按钮打开模态窗口
btn.onclick = function() {
    modal.style.display = "block";
}

// 点击 <span> (x) 关闭模态窗口
span.onclick = function() {
    modal.style.display = "none";
}

// 在用户点击模态窗口外的区域时关闭模态窗口
window.onclick = function(event) {
    if (event.target == modal) {
        modal.style.display = "none";
    }
}

// 注意：在使用模态窗口时，需要在 HTML 文件中添加以下代码：