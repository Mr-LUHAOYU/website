// 获取模态窗口
var modal = document.getElementById("uploadAvatarModal");
var bio_modal = document.getElementById("uploadBioModal");


// 获取按钮
var btn = document.getElementById("uploadAvatarBtn");
var bio_btn = document.getElementById("uploadBioBtn");


// 获取 <span> 元素，点击关闭模态窗口
var span = document.getElementsByClassName("close")[0];
var bio_span = document.getElementsByClassName("closeBio")[0];

// 点击按钮打开模态窗口
btn.onclick = function() {
    modal.style.display = "block";
}

bio_btn.onclick = function() {
    bio_modal.style.display = "block";
}



// 点击 <span> (x) 关闭模态窗口
span.onclick = function() {
    modal.style.display = "none";
}

bio_span.onclick = function() {
    bio_modal.style.display = "none";
}



// 在用户点击模态窗口外的区域时关闭模态窗口
window.onclick = function(event) {
    if (event.target == modal) {
        modal.style.display = "none";
    }else if (event.target == bio_modal) {
        bio_modal.style.display = "none";
    }else if (event.target == comment_modal) {
        comment_modal.style.display = "none";
    }
}


